# a dock widget for the trials

from PyQt6 import QtWidgets, QtCore, QtGui
from RVM.bases import ProjectSettings, Box, Animal, Trial, TrialBase
import os

class TrialManagerDockWidget(QtWidgets.QDockWidget):
    # state colors
    stateColors = {
        "Good": QtGui.QColor(11, 212, 125),
        "Bad": QtGui.QColor(212, 99, 99),
    }
    def __init__(self, projectSettings: ProjectSettings, parent):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.parent = parent
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Trial Manager")

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
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "add.png"))
        )
        self.createTrialButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.createTrialButton.clicked.connect(self.createTrial)

        self.deleteTrialButton = QtWidgets.QToolButton()
        self.deleteTrialButton.setText("Delete Trial")
        self.deleteTrialButton.setToolTip("Delete the selected box from the project")
        self.deleteTrialButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "delete.png"))
        )
        self.deleteTrialButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.deleteTrialButton.clicked.connect(self.deleteTrial)

        self.buttonLayout.addWidget(self.createTrialButton)
        self.buttonLayout.addWidget(self.deleteTrialButton)
        self.buttonLayout.addStretch(1)

        # a search bar for the tree widget
        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.textChanged.connect(self.searchTreeWidget)
        self.buttonLayout.addWidget(self.searchBar)

        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setHeaderLabels(["Trial ID", "Animal ID", "Box Name", "State", "Start Time", "End Time", "Notes"])
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
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
        self.editAction.triggered.connect(lambda: self.editTrial(self.treeWidget.currentItem()))
        self.deleteAction = QtGui.QAction("Delete", self)
        self.deleteAction.triggered.connect(lambda: self.deleteTrial(self.treeWidget.currentItem()))
        self.contextMenu.addAction(self.editAction)
        self.contextMenu.addAction(self.deleteAction)
        self.contextMenu.exec(self.treeWidget.mapToGlobal(pos))

    def updateTreeWidget(self):
        self.treeWidget.clear()
        for trial in self.projectSettings.trials:
            self.addTrialToTreeWidget(trial)

    def addTrialToTreeWidget(self, trial: Trial):
        trialItem = QtWidgets.QTreeWidgetItem(self.treeWidget)
        trialItem.setText(0, trial.uid)
        trialItem.setText(1, trial.animal.uid)
        trialItem.setText(2, trial.box.uid)
        trialItem.setText(3, trial.state)
        # adjust the color if the state is "Waiting"
        if trial.state == "Running":
            trialItem.setForeground(3, TrialManagerDockWidget.stateColors["Good"])
        elif trial.state in ["Failed",]:
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
        self.trialDialog = TrialDialog(self.projectSettings, mainWin=self.parent, parent=self)
        self.trialDialog.signals.okClicked.connect(lambda trial: self.addTrial(trial))
        self.trialDialog.exec()

    def editTrial(self, trialItem: QtWidgets.QTreeWidgetItem):
        trial = self.projectSettings.getTrialFromId(trialItem.text(0))
        self.trialDialog = TrialDialog(self.projectSettings, mainWin=self.parent, parent=self)
        self.trialDialog.loadTrial(trial)
        self.trialDialog.signals.okClicked.connect(self.updateTrial)
        self.trialDialog.exec()

    def deleteTrial(self, item, *args, **kwargs):
        if type(item) == QtWidgets.QTreeWidgetItem:
            trial = self.projectSettings.getTrialFromId(item.text(0))
        elif type(item) == Trial or type(item) == TrialBase:
            trial = item
        else:
            self.parent.messageBox("Error", "Could not delete box", "Warning")
            return
        self.parent.updateStatus("Deleting Trial {}".format(trial.uid))
        confim = self.parent.confirmBox("Delete trial", f"Are you sure you want to delete Trial: \n\nID: {trial.uid}")
        if confim:
            self.projectSettings.trials.remove(trial)
            self.updateTreeWidget()
            self.parent.updateStatus("Trial {} deleted".format(trial.uid))

    def refresh(self):
        self.updateTreeWidget()

class TrialDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(TrialBase)

class TrialDialog(QtWidgets.QDialog):

    def __init__(self, projectSettings: ProjectSettings, mainWin: QtWidgets.QMainWindow=None, parent: TrialManagerDockWidget=None):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = TrialDialogSignals()
        self.currentTrial = None
        self.parent = parent
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
        self.deleteButton.setIcon(QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "delete.png")))
        self.deleteButton.clicked.connect(self.deleteTrial)
        self.deleteButton.setStyleSheet("background-color: rgb(212, 99, 99);")
        self.deleteButton.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self.formLayout.addWidget(self.deleteButton)
        self.uidLineEdit = QtWidgets.QLineEdit()
        self.uidLineEdit.setReadOnly(True)
        self.uidLineEdit.setEnabled(False)
        self.formLayout.addRow("Trial ID", self.uidLineEdit)
        self.animalComboBox = QtWidgets.QComboBox()
        self.animalComboBox.addItems([animal.uid for animal in self.projectSettings.animals])
        self.formLayout.addRow("Animal ID", self.animalComboBox)
        self.boxComboBox = QtWidgets.QComboBox()
        self.boxComboBox.addItems([box.uid for box in self.projectSettings.boxes])
        self.formLayout.addRow("Box Name", self.boxComboBox)
        self.stateComboBox = QtWidgets.QComboBox()
        self.stateComboBox.addItems(Trial.avalible_states())
        self.formLayout.addRow("State", self.stateComboBox)
        self.startDateTimeEdit = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.startDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.formLayout.addRow("Start Time", self.startDateTimeEdit)
        self.endDateTimeEdit = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.endDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.formLayout.addRow("End Time", self.endDateTimeEdit)
        self.notesTextEdit = QtWidgets.QTextEdit()
        self.formLayout.addRow("Notes", self.notesTextEdit)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
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
        self.notesTextEdit.setText(trial.notes)

    def deleteTrial(self):
        if self.currentTrial is None:
            return
        self.parent.deleteTrial(self.currentTrial)
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
                animal=self.projectSettings.getAnimalFromId(self.animalComboBox.currentText()),
                box=self.projectSettings.getBoxFromId(self.boxComboBox.currentText()),
                state=self.stateComboBox.currentText(),
                start_time=self.startDateTimeEdit.dateTime().toPyDateTime(),
                end_time=self.endDateTimeEdit.dateTime().toPyDateTime(),
                notes=self.notesTextEdit.toPlainText()
            )

        else:
            self.currentTrial.animal = self.projectSettings.getAnimalFromId(self.animalComboBox.currentText())
            self.currentTrial.box = self.projectSettings.getBoxFromId(self.boxComboBox.currentText())
            self.currentTrial.state = self.stateComboBox.currentText()
            self.currentTrial.start_time = self.startDateTimeEdit.dateTime().toPyDateTime()
            self.currentTrial.end_time = self.endDateTimeEdit.dateTime().toPyDateTime()
            self.currentTrial.notes = self.notesTextEdit.toPlainText()


        self.signals.okClicked.emit(self.currentTrial)
        super().accept()


