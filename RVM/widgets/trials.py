# a dock widget for the trials

import datetime
import logging
import os
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtGui, QtWidgets

from RVM.bases import Animal, Box, ProjectSettings, Trial, TrialBase
from RVM.widgets.camWin import (CameraPreviewWindow, CameraWindow,
                                CameraWindowDockWidget)

if TYPE_CHECKING:
    from RVM.mainWindow import MainWindow

log = logging.getLogger()


class TrialManagerDockWidget(QtWidgets.QDockWidget):
    # state colors
    stateColors = {
        "Good": QtGui.QColor(11, 212, 125),
        "Bad": QtGui.QColor(212, 99, 99),
    }

    def __init__(
        self, projectSettings: ProjectSettings, mainWin: "MainWindow", parent=None
    ):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.mainWin = mainWin
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Trial Manager")
        self.setFilters()

        # central widget
        self.centralWidget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.centralWidget.setLayout(self.layout)
        self.setWidget(self.centralWidget)

        # create button widget
        self.buttonWidget = QtWidgets.QWidget()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonWidget.setLayout(self.buttonLayout)

        # create buttons
        self.createTrialButton = QtWidgets.QToolButton()
        self.createTrialButton.setText("Add Trial")
        self.createTrialButton.setToolTip("Add a new box to the project")
        self.createTrialButton.setIcon(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "add.png"))
        )
        self.createTrialButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.createTrialButton.clicked.connect(self.createTrial)

        self.deleteTrialButton = QtWidgets.QToolButton()
        self.deleteTrialButton.setText("Delete Trial")
        self.deleteTrialButton.setToolTip("Delete the selected box from the project")
        self.deleteTrialButton.setIcon(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "delete.png"))
        )
        self.deleteTrialButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.deleteTrialButton.clicked.connect(self.deleteDeterminer)

        self.runSelectedButton = QtWidgets.QToolButton()
        self.runSelectedButton.setText("Run Selected")
        self.runSelectedButton.setToolTip("Run the selected trials")
        self.runSelectedButton.setIcon(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "play-button.png"))
        )
        self.runSelectedButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.runSelectedButton.clicked.connect(self.openRunDialog)

        # a checkbox to hide completed trials
        self.showAllCheckBox = QtWidgets.QCheckBox()
        self.showAllCheckBox.setText("Show All")
        self.showAllCheckBox.setToolTip("Show All Trials")
        self.showAllCheckBox.stateChanged.connect(self.updateFilter)

        self.stopAllButton = QtWidgets.QToolButton()
        self.stopAllButton.setText("Stop All")
        self.stopAllButton.setToolTip("Stop all running trials")
        self.stopAllButton.setIcon(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "stop.png"))
        )
        self.stopAllButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.stopAllButton.clicked.connect(self.stopTrials)

        self.buttonLayout.addWidget(self.createTrialButton)
        self.buttonLayout.addWidget(self.deleteTrialButton)
        self.buttonLayout.addWidget(self.runSelectedButton)
        self.buttonLayout.addWidget(self.stopAllButton)
        self.buttonLayout.addStretch(1)

        # a search bar for the tree widget
        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.textChanged.connect(self.searchTreeWidget)
        self.buttonLayout.addWidget(self.searchBar)
        self.buttonLayout.addWidget(self.showAllCheckBox)

        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setHeaderLabels(
            [
                "Trial ID",
                "Animal ID",
                "Box ID",
                "State",
                "Start Time",
                "End Time",
                "Notes",
            ]
        )
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.treeWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)
        self.treeWidget.itemDoubleClicked.connect(self.editTrial)
        self.layout.addWidget(self.buttonWidget)
        self.layout.addWidget(self.treeWidget)

        self.updateTreeWidget()

    def showContextMenu(self, pos):
        if self.treeWidget.currentItem() is None:
            return
        if self.treeWidget.itemAt(pos) is not self.treeWidget.currentItem():
            return
        self.contextMenu = QtWidgets.QMenu()
        self.editAction = QtGui.QAction("Edit", self)
        self.editAction.triggered.connect(
            lambda: self.editTrial(self.treeWidget.currentItem())
        )
        self.previewAction = QtGui.QAction("Preview", self)
        self.previewAction.triggered.connect(
            lambda: self.previewCamera(self.treeWidget.currentItem())
        )
        self.deleteAction = QtGui.QAction("Delete", self)
        self.deleteAction.triggered.connect(self.deleteDeterminer)
        self.duplicateAction = QtGui.QAction("Duplicate", self)
        self.duplicateAction.triggered.connect(
            lambda: self.duplicateTrial(self.treeWidget.currentItem())
        )
        self.contextMenu.addAction(self.editAction)
        self.contextMenu.addAction(self.previewAction)
        self.contextMenu.addAction(self.deleteAction)
        self.contextMenu.addAction(self.duplicateAction)

        if self.treeWidget.currentItem().text(3) != "Waiting":
            # disable preview if the trial is not running
            self.previewAction.setEnabled(False)

        self.contextMenu.exec(self.treeWidget.mapToGlobal(pos))

    def setFilters(self, filters: dict = None):
        if filters is None:
            self.trialFilters = {
                "State": ["Running", "Waiting"],
            }

    def updateFilter(self):
        if self.showAllCheckBox.isChecked():
            self.trialFilters["State"] = []
        else:
            self.trialFilters["State"] = ["Running", "Waiting"]
        self.updateTreeWidget()

    def filteringCriteria(self, trial: Trial):
        """Checks if a trial passes the filtering criteria"""
        if self.trialFilters["State"] and trial.state not in self.trialFilters["State"]:
            return True
        return False

    def updateTreeWidget(self):
        self.treeWidget.clear()
        for trial in self.projectSettings.trials:
            if self.filteringCriteria(trial):
                continue
            try:
                self.addTrialToTreeWidget(trial)
            except Exception as e:
                print(e)
                continue

    def addTrialToTreeWidget(self, trial: Trial):
        trialItem = QtWidgets.QTreeWidgetItem(self.treeWidget)
        trialItem.setText(0, trial.uid)
        trialItem.setText(1, trial.animal.uid)
        trialItem.setText(2, trial.box.uid)
        trialItem.setText(3, trial.state)
        # adjust the color if the state is "Waiting"
        if trial.state == "Running":
            trialItem.setForeground(3, TrialManagerDockWidget.stateColors["Good"])
        elif trial.state in [
            "Failed",
        ]:
            trialItem.setForeground(3, TrialManagerDockWidget.stateColors["Bad"])
        trialItem.setText(4, str(trial.start_time))
        trialItem.setText(5, str(trial.end_time))
        trialItem.setText(6, trial.notes)

    def searchTreeWidget(self, text: str):
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            for j in range(item.columnCount()):
                if text.lower() in item.text(j).lower():
                    item.setHidden(False)
                    break
                else:
                    item.setHidden(True)

    def addTrial(self, trial: Trial):
        self.projectSettings.trials.append(trial)
        self.addTrialToTreeWidget(trial)

    def updateTrial(self, trial: Trial):
        worked = self.projectSettings.updateTrial(trial)
        if not worked:
            return
        self.updateTreeWidget()

    def updateTrialFromItem(self, item: QtWidgets.QTreeWidgetItem, column: int):
        trial = self.projectSettings.getTrialFromId(item.text(0))
        if column == 0:
            trial.uid = item.text(0)
        elif column == 1:
            trial.animal = self.projectSettings.getAnimalFromId(item.text(1))
        elif column == 2:
            trial.box = self.projectSettings.getBoxFromId(item.text(2))
        elif column == 3:
            trial.state = item.text(3)
        elif column == 4:
            trial.start_time = item.text(4)
        elif column == 5:
            trial.end_time = item.text(5)
        elif column == 6:
            trial.notes = item.text(6)
        self.updateTrial(trial)

    def createTrial(self):
        self.trialDialog = TrialEditDialog(
            self.projectSettings, mainWin=self.mainWin, parent=self
        )
        self.trialDialog.signals.okClicked.connect(lambda trial: self.addTrial(trial))
        self.trialDialog.exec()

    def editTrial(self, trialItem: QtWidgets.QTreeWidgetItem):
        trial = self.projectSettings.getTrialFromId(trialItem.text(0))
        self.trialDialog = TrialEditDialog(
            self.projectSettings, mainWin=self.mainWin, parent=self
        )
        self.trialDialog.loadTrial(trial)
        self.trialDialog.signals.okClicked.connect(self.updateTrial)
        self.trialDialog.exec()

    def duplicateTrial(self, *args, **kwargs):
        # get selected trials
        for trialItem in self.treeWidget.selectedItems():
            trial = self.projectSettings.getTrialFromId(trialItem.text(0))
            # new trial with same parameters
            newTrial = Trial(
                animal=trial.animal,
                box=trial.box,
                start_time=trial.start_time,
                end_time=trial.end_time,
                notes=trial.notes,
            )
            self.addTrial(newTrial)

    def deleteDeterminer(self):
        if len(self.treeWidget.selectedItems()) == 1:
            self.deleteTrial(self.treeWidget.currentItem())
        elif len(self.treeWidget.selectedItems()) > 1:
            self.deleteMultipleTrials()

    def deleteMultipleTrials(self):
        confim = self.mainWin.confirmBox(
            "Delete trials",
            f"Are you sure you want to delete {len(self.treeWidget.selectedItems())} trials?",
        )
        if confim:
            for item in self.treeWidget.selectedItems():
                self.projectSettings.trials.remove(
                    self.projectSettings.getTrialFromId(item.text(0))
                )
            self.updateTreeWidget()

    def deleteTrial(self, item, *args, **kwargs):
        if type(item) == QtWidgets.QTreeWidgetItem:
            trial = self.projectSettings.getTrialFromId(item.text(0))
        elif type(item) == Trial or type(item) == TrialBase:
            trial = item
        else:
            self.mainWin.messageBox("Error", "Could not delete box", "Warning")
            return
        self.mainWin.updateStatus("Deleting Trial {}".format(trial.uid))
        confim = self.mainWin.confirmBox(
            "Delete trial",
            f"Are you sure you want to delete Trial: \n\nID: {trial.uid}",
        )
        if confim:
            self.projectSettings.trials.remove(trial)
            self.updateTreeWidget()
            self.mainWin.updateStatus("Trial {} deleted".format(trial.uid))

    def previewCamera(self, item):
        if type(item) == QtWidgets.QTreeWidgetItem:
            trial = self.projectSettings.getTrialFromId(item.text(0))
        elif type(item) == Trial or type(item) == TrialBase:
            trial = item
        else:
            self.mainWin.messageBox("Error", "Could not preview trial", "Warning")
            return

        if trial.state == "Waiting":
            try:
                self.mainWin.updateStatus("Previewing Trial {}".format(trial.uid))
                self.cameraPreviewWindow = CameraPreviewWindow(
                    parent=self.mainWin, mainWin=self.mainWin
                )
                self.cameraPreviewWindow.createCamera(
                    camNum=list(self.mainWin.videoDevices.keys()).index(
                        trial.box.camera
                    ),
                    camName=self.mainWin.videoDevices[trial.box.camera],
                    fps=30,
                    prevFPS=30,
                    recFPS=30,
                )
                self.cameraPreviewWindow.show()
            except Exception as e:
                log.debug(e)
                if trial.box.camera == "":
                    self.mainWin.messageBox(
                        "Error",
                        f"No camera selected for box {trial.box.uid}",
                        "Warning",
                    )
                else:
                    self.mainWin.messageBox("Error", str(e), "Warning")
        else:
            self.mainWin.messageBox(
                "Error", "Cannot preview a running trial", "Warning"
            )

    def getVideoPath(self, trial: Trial):
        file_name = f"{trial.animal.uid}_BOX{trial.box.uid}_{trial.uid}.avi"
        # ensure the file name is doesn't have any invalid characters
        invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        for char in invalid_chars:
            file_name = file_name.replace(char, "_")

        # Video directory
        video_dir = os.path.join(self.projectSettings.project_location, "Videos")
        # create the video directory if it doesn't exist
        if not os.path.exists(video_dir):
            log.debug(f"Creating video directory {video_dir}")
            os.mkdir(video_dir)

        return str(os.path.join(video_dir, file_name))

    def runTrials(self, trials_to_run: list[TrialBase]):
        for trial in trials_to_run:
            # create a new camera window
            trial.video_location = self.getVideoPath(trial)
            try:
                cameraWindow = CameraWindow(
                    parent=self.mainWin,
                    camNum=list(self.mainWin.videoDevices.keys()).index(
                        trial.box.camera
                    ),
                    mainWin=self.mainWin,
                    trial=trial,
                )
                dw = self.mainWin.addCameraDockWidget(
                    cameraWindow, trial.box.uid, trial.animal.uid
                )
                if dw is None:
                    continue

                cameraWindow.show()

                dw.cameraWindow.startRecording()
                dw.cameraWindow.startPreview()
                trial.start_time = datetime.datetime.now()
                trial.state = "Running"
                self.updateTrial(trial)

                self.mainWin.updateStatus(f"Running Trial {trial.uid}")

            except Exception as e:
                # get traceback
                import traceback

                log.debug(f"{traceback.format_exc()}\m\t{e}")
                self.mainWin.messageBox(
                    "Error",
                    f"Could not run trial {trial.uid}",
                    "Critical",
                )

        self.runDialog.close()
        self.runDialog = None

    def stopTrials(self):
        for trial in self.projectSettings.trials:
            if trial.state == "Running":
                trial.state = "Finished"
                trial.end_time = datetime.datetime.now()
                self.updateTrial(trial)
        for dockWidget in self.mainWin.findChildren(CameraWindowDockWidget):
            dockWidget.cameraWindow.stopRecording()
            dockWidget.close()

        self.mainWin.updateStatus("Stopped Trials")

    def openRunDialog(self):
        # get the selected trials
        selectedTrials = []
        for item in self.treeWidget.selectedItems():
            trial = self.projectSettings.getTrialFromId(item.text(0))
            if trial.state == "Waiting":
                selectedTrials.append(trial)

        # create the run dialog
        self.runDialog = RunTrialsDialog(
            trials=selectedTrials,
            projectSettings=self.projectSettings,
            mainWin=self.mainWin,
            parent=self,
        )
        self.runDialog.signals.okClicked.connect(lambda: self.runTrials(selectedTrials))
        self.runDialog.exec()

    def addCameraDockWidget(
        self, cameraWindow: CameraWindow, boxId: int, animalId: str
    ):
        msg_str = None
        for dockWidget in self.mainWin.findChildren(CameraWindowDockWidget):
            if dockWidget.boxId == boxId:
                msg_str = f"A camera with the BOX ID of {boxId} already exists. Please choose a different box id."
            elif dockWidget.animalId == animalId:
                msg_str = f"A camera with the ANIMAL ID {animalId} already exists. Please choose a different animal id."

        if msg_str is not None:
            self.messageBox(title="ERROR", text=msg_str, severity="Critical")
            return

        # wrap the camera window in a dock widget
        dockWidget = CameraWindowDockWidget(
            cameraWindow=cameraWindow,
            boxId=boxId,
            animalId=animalId,
            fps=30,
            recFPS=30,
            prevFPS=30,
            mainWin=self.mainWin,
            parent=self.mainWin,
        )
        # add the dock widget to the main window
        self.mainWin.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dockWidget
        )
        dockWidget.cameraWindow.startPreview()
        # add the dock widget to the view menu
        self.mainWin.addAction(dockWidget.toggleViewAction())
        return dockWidget

    def refresh(self):
        self.updateTreeWidget()

    def closeEvent(self, event):
        return super().closeEvent(event)


class TrialEditDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(TrialBase)


class TrialEditDialog(QtWidgets.QDialog):
    def __init__(
        self,
        projectSettings: ProjectSettings,
        mainWin: QtWidgets.QMainWindow = None,
        parent: TrialManagerDockWidget = None,
    ):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = TrialEditDialogSignals()
        self.currentTrial = None
        self.mainWin = parent
        self.mainWin = mainWin
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Trial")

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.formLayout = QtWidgets.QFormLayout()
        self.layout.addLayout(self.formLayout)

        # a small icon button to delete in the top left
        self.deleteButton = QtWidgets.QPushButton()
        self.deleteButton.setIcon(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "delete.png"))
        )
        self.deleteButton.clicked.connect(self.deleteTrial)
        self.deleteButton.setStyleSheet("background-color: rgb(212, 99, 99);")
        self.deleteButton.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum
        )
        self.formLayout.addWidget(self.deleteButton)
        self.uidLineEdit = QtWidgets.QLineEdit()
        self.uidLineEdit.setReadOnly(True)
        self.uidLineEdit.setEnabled(False)
        self.formLayout.addRow("Trial ID", self.uidLineEdit)
        self.animalComboBox = QtWidgets.QComboBox()
        self.animalComboBox.addItems(
            [animal.uid for animal in self.projectSettings.animals]
        )
        self.formLayout.addRow("Animal ID", self.animalComboBox)
        self.boxComboBox = QtWidgets.QComboBox()
        self.boxComboBox.addItems([box.uid for box in self.projectSettings.boxes])
        self.formLayout.addRow("Box ID", self.boxComboBox)
        self.stateComboBox = QtWidgets.QComboBox()
        self.stateComboBox.addItems(Trial.avalible_states())
        self.formLayout.addRow("State", self.stateComboBox)
        self.startDateTimeEdit = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.startDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.formLayout.addRow("Start Time", self.startDateTimeEdit)
        self.endDateTimeEdit = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.endDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.formLayout.addRow("End Time", self.endDateTimeEdit)
        self.videoLocationLineEdit = QtWidgets.QLineEdit()
        self.videoLocationLineEdit.setReadOnly(True)
        self.videoLocationLineEdit.setEnabled(False)
        self.formLayout.addRow("Video Location", self.videoLocationLineEdit)
        self.openVideoLocationButton = QtWidgets.QPushButton("Open")
        self.openVideoLocationButton.clicked.connect(self.openVideoLocation)
        self.formLayout.addRow("", self.openVideoLocationButton)
        self.notesTextEdit = QtWidgets.QTextEdit()
        self.formLayout.addRow("Notes", self.notesTextEdit)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)

    def loadTrial(self, trial: Trial):
        self.currentTrial = trial
        self.uidLineEdit.setText(trial.uid)
        self.animalComboBox.setCurrentText(trial.animal.uid)
        self.boxComboBox.setCurrentText(trial.box.uid)
        self.stateComboBox.setCurrentText(trial.state)
        self.startDateTimeEdit.setDateTime(trial.start_time)
        self.endDateTimeEdit.setDateTime(trial.end_time)
        self.videoLocationLineEdit.setText(str(trial.video_location))
        self.notesTextEdit.setText(trial.notes)

    def openVideoLocation(self):
        if self.currentTrial is None:
            return
        if self.currentTrial.video_location is None:
            return
        if not os.path.exists(self.currentTrial.video_location):
            return
        # open file location
        import subprocess

        subprocess.Popen(
            r'explorer /select,"{}"'.format(self.currentTrial.video_location)
        )

    def deleteTrial(self):
        if self.currentTrial is None:
            return
        self.mainWin.deleteTrial(self.currentTrial)
        self.accept()

    def validate(self):
        ok = True
        error = ""
        return ok, error

    def accept(self):
        ok, error = self.validate()
        if not ok:
            self.mainWin.messageBox("Error", error, "Critical")
            return

        if self.currentTrial is None:
            self.currentTrial = Trial(
                animal=self.projectSettings.getAnimalFromId(
                    self.animalComboBox.currentText()
                ),
                box=self.projectSettings.getBoxFromId(self.boxComboBox.currentText()),
                state=self.stateComboBox.currentText(),
                start_time=self.startDateTimeEdit.dateTime().toPyDateTime(),
                end_time=self.endDateTimeEdit.dateTime().toPyDateTime(),
                notes=self.notesTextEdit.toPlainText(),
            )

        else:
            self.currentTrial.animal = self.projectSettings.getAnimalFromId(
                self.animalComboBox.currentText()
            )
            self.currentTrial.box = self.projectSettings.getBoxFromId(
                self.boxComboBox.currentText()
            )
            self.currentTrial.state = self.stateComboBox.currentText()
            self.currentTrial.start_time = (
                self.startDateTimeEdit.dateTime().toPyDateTime()
            )
            self.currentTrial.end_time = self.endDateTimeEdit.dateTime().toPyDateTime()
            self.currentTrial.notes = self.notesTextEdit.toPlainText()

        self.signals.okClicked.emit(self.currentTrial)
        super().accept()


class RunTrialsDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(list)


class RunTrialsDialog(QtWidgets.QDialog):
    def __init__(
        self,
        trials: list[TrialBase],
        projectSettings: ProjectSettings,
        mainWin: QtWidgets.QMainWindow = None,
        parent: TrialManagerDockWidget = None,
    ):
        super().__init__(parent)
        self.trials = trials
        self.projectSettings = projectSettings
        self.signals = RunTrialsDialogSignals()
        self.currentTrial = None
        self.mainWin = parent
        self.mainWin = mainWin
        self.initUi()

    def initUi(self):
        # will display a list of the trials with checkboxes and a button to open all the cameras and then a button to start the trials
        self.setWindowTitle("Run Trials")

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        # a label for the trials table
        self.trialsLabel = QtWidgets.QLabel("Run Trials:")

        # a table to display the trials
        self.trialsTable = QtWidgets.QTableWidget()
        self.trialsTable.setColumnCount(3)
        self.trialsTable.setHorizontalHeaderLabels(["Trial ID", "Animal ID", "Box ID"])
        self.trialsTable.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection
        )
        self.trialsTable.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # a button to start the trials
        self.startTrialsButton = QtWidgets.QPushButton("Start Trials")
        # set the color of the button to QtGui.QColor(212, 99, 99)
        self.startTrialsButton.setStyleSheet(
            "background-color: rgb(212, 99, 99); color: rgb(255, 255, 255);"
        )
        self.startTrialsButton.clicked.connect(self.startTrials)

        # add the widgets to the layout
        self.layout.addWidget(self.trialsLabel, 0, 0, 1, 2)
        self.layout.addWidget(self.trialsTable, 1, 0, 1, 2)
        self.layout.addWidget(self.startTrialsButton, 2, 0, 1, 2)

        # populate the table
        self.populateTable()

    def populateTable(self):
        self.trialsTable.setRowCount(len(self.trials))
        for i, trial in enumerate(self.trials):
            self.trialsTable.setItem(i, 0, QtWidgets.QTableWidgetItem(trial.uid))
            self.trialsTable.setItem(i, 1, QtWidgets.QTableWidgetItem(trial.animal.uid))
            self.trialsTable.setItem(i, 2, QtWidgets.QTableWidgetItem(trial.box.uid))
        # run validation on the table
        ok, error_type, errored_item_ids = self.validateTrials()
        if not ok:
            self.startTrialsButton.setEnabled(False)
            self.startTrialsButton.setStyleSheet(
                "background-color: rgb(70, 70, 70); color: rgb(255, 255, 255);"
            )
            # highlight the errored items
            for i in range(self.trialsTable.rowCount()):
                if self.trialsTable.item(i, 1).text() in errored_item_ids:
                    self.trialsTable.item(i, 1).setBackground(QtGui.QColor(212, 99, 99))
                    # add the tooltip
                    self.trialsTable.item(i, 1).setToolTip(
                        "This animal is used in more than one trial."
                    )
            for i in range(self.trialsTable.rowCount()):
                if self.trialsTable.item(i, 2).text() in errored_item_ids:
                    self.trialsTable.item(i, 2).setBackground(QtGui.QColor(212, 99, 99))
                    # add the tooltip
                    self.trialsTable.item(i, 2).setToolTip(
                        "This box is used in more than one trial."
                    )
        # resize the dialog to fit the table
        self.resize(self.trialsTable.sizeHint().width() + 100, self.sizeHint().height())

    def validateTrials(self):
        animals = []
        errored_animals = []
        for trial in self.trials:
            animals.append(trial.animal.uid)
        for animal in animals:
            if animals.count(animal) > 1:
                errored_animals.append(animal)
        boxes = []
        errored_boxes = []
        for trial in self.trials:
            boxes.append(trial.box.uid)
        for box in boxes:
            if boxes.count(box) > 1:
                errored_boxes.append(box)

        if len(errored_animals) > 0 and len(errored_boxes) > 0:
            return False, "Animals and Boxes", errored_animals + errored_boxes
        elif len(errored_animals) > 0:
            return False, "Animals", errored_animals
        elif len(errored_boxes) > 0:
            return False, "Boxes", errored_boxes
        return True, "", []

    def startTrials(self):
        self.signals.okClicked.emit(self.trials)
        self.accept()
