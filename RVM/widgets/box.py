# a dock widget for the management of boxes in a project
# updates the project settings when a box is modified

from PyQt6 import QtWidgets, QtCore, QtGui
from RVM.bases import ProjectSettings, Box
import os
from RVM.camera import Camera, CameraWindow


class BoxManagerDockWidget(QtWidgets.QDockWidget):
    def __init__(self, projectSettings: ProjectSettings, parent):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.parent = parent
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Box Manager")

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
        self.createBoxButton = QtWidgets.QToolButton()
        self.createBoxButton.setText("Add Box")
        self.createBoxButton.setToolTip("Add a new box to the project")
        self.createBoxButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "add.png"))
        )
        self.createBoxButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.createBoxButton.clicked.connect(self.createNewBox)

        self.deleteBoxButton = QtWidgets.QToolButton()
        self.deleteBoxButton.setText("Delete Box")
        self.deleteBoxButton.setToolTip("Delete the selected box from the project")
        self.deleteBoxButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "delete.png"))
        )
        self.deleteBoxButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.deleteBoxButton.clicked.connect(self.deleteBox)

        self.buttonLayout.addWidget(self.createBoxButton)
        self.buttonLayout.addWidget(self.deleteBoxButton)
        self.buttonLayout.addStretch(1)

        # create box list widget
        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setHeaderLabels(["Box ID", "Camera", "Trials", "Notes"])
        self.treeWidget.setColumnCount(4)
        self.treeWidget.itemChanged.connect(self.updateBoxFromItem)
        self.treeWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)

        self.layout.addWidget(self.buttonWidget)
        self.layout.addWidget(self.treeWidget)

        self.updateBoxList()

    def showContextMenu(self, pos: QtCore.QPoint):
        if self.treeWidget.currentItem() is None:
            return
        if self.treeWidget.itemAt(pos) is not self.treeWidget.currentItem():
            return
        self.contextMenu = QtWidgets.QMenu()
        self.editAction = QtGui.QAction("Edit", self)
        self.editAction.triggered.connect(
            lambda: self.editBox(self.treeWidget.currentItem(), 0)
        )
        self.deleteAction = QtGui.QAction("Delete", self)
        self.deleteAction.triggered.connect(
            lambda: self.deleteBox(self.treeWidget.currentItem(), 0)
        )
        self.contextMenu.addAction(self.editAction)
        self.contextMenu.addAction(self.deleteAction)
        self.contextMenu.exec(self.treeWidget.mapToGlobal(pos))

    def createNewBox(self):
        newBoxDialog = BoxDialog(self.projectSettings, self.parent)
        newBoxDialog.signals.okClicked.connect(self.addBox)
        newBoxDialog.show()

    def addBox(self, box: Box):
        self.projectSettings.boxes.append(box)
        self.updateBoxList()

    def deleteBoxes(self):
        pass

    def editBox(self, item: QtWidgets.QTreeWidgetItem, column: int):
        self.parent.statusBar.showMessage("Editing Box {}".format(item.text(0)))
        box = [box for box in self.projectSettings.boxes if box.boxId == item.text(0)]
        if box is None:
            self.parent.statusBar.showMessage("Box {} not found".format(item.text(0)))
            return
        if len(box) == 0:
            self.parent.statusBar.showMessage("Box {} not found".format(item.text(0)))
            return
        box = box[0]
        editBoxDialog = BoxDialog(self.projectSettings, self.parent)
        editBoxDialog.loadBox(box)
        editBoxDialog.signals.okClicked.connect(self.updateBox)
        editBoxDialog.show()

    def updateBox(self, box: Box):
        for i in range(len(self.projectSettings.boxes)):
            if self.projectSettings.boxes[i].boxId == box.boxId:
                self.projectSettings.boxes[i] = box
                break
        self.updateBoxList()

    def deleteBox(self, item: QtWidgets.QTreeWidgetItem, column: int):
        self.parent.statusBar.showMessage("Deleting Box {}".format(item.text(0)))
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(f"Are you sure you want to delete \nBox {item.text(0)}?")
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        msgBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        # set the window title
        msgBox.setWindowTitle("Delete Box?")
        msgBox.setWindowIcon(
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "..", "logo.png"))
        )
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        ret = msgBox.exec()
        if ret == QtWidgets.QMessageBox.StandardButton.No:
            self.parent.statusBar.showMessage(
                "Canceled deletion of animal {}".format(item.text(0))
            )
            return
        # get the box id from the item
        boxId = item.text(0)
        # get the box from the project settings
        box = [box for box in self.projectSettings.boxes if box.boxId == boxId]
        if box is None:
            self.parent.statusBar.showMessage("Could not find box {}".format(boxId))
            return
        if len(box) == 0:
            self.parent.statusBar.showMessage("Could not find box {}".format(boxId))
            return
        box = box[0]
        # remove the box from the project settings
        self.projectSettings.boxes.remove(box)
        # update the box list
        self.updateBoxList()
        self.parent.statusBar.showMessage("Deleted box {}".format(boxId))

    def updateBoxList(self):
        self.treeWidget.clear()
        camerasCombo = QtWidgets.QComboBox()
        camerasCombo.addItems(self.parent.videoDevices.values())
        for box in self.projectSettings.boxes:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, box.boxId)
            currentCamera = self.getCameraNameFromKey(box.camera)
            camerasCombo.setCurrentIndex(camerasCombo.findText(currentCamera))
            item.setText(1, currentCamera)
            self.treeWidget.setItemWidget(item, 1, camerasCombo)
            item.setText(2, str(box.trials))
            item.setText(3, box.notes)
            self.treeWidget.addTopLevelItem(item)

    def updateBoxFromItem(self, item: QtWidgets.QTreeWidgetItem, column: int):
        # get the box id from the item
        boxId = item.text(0)
        # get the box from the project settings
        box = [box for box in self.projectSettings.boxes if box.boxId == boxId][0]
        if box is None:
            self.parent.statusBar.showMessage(
                "Could not find box with id {}".format(boxId)
            )
        # update the box from the item
        if column == 0:
            box.boxId = item.text(0)
        elif column == 1:
            box.camera = self.getCameraKeyFromName(item.text(1))
        elif column == 2:
            box.trials = item.text(2)
        elif column == 3:
            box.notes = item.text(3)

    def reload(self, projectSettings: ProjectSettings):
        self.projectSettings = projectSettings
        self.updateBoxList()

    def getCameraNameFromKey(self, key: str) -> str:
        return self.parent.videoDevices[key]

    def getCameraKeyFromName(self, name: str) -> str:
        return [
            key for key, value in self.parent.videoDevices.items() if value == name
        ][0]


class BoxDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(Box)


class BoxDialog(QtWidgets.QDialog):
    def __init__(self, projectSettings: ProjectSettings, parent=None):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = BoxDialogSignals()
        self.parent = parent
        self.initUi()

    def initUi(self):
        self.setWindowTitle("New Box")

        # create the layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # create the form layout
        self.formLayout = QtWidgets.QFormLayout()
        self.layout.addLayout(self.formLayout)

        # create the box id line edit
        self.boxIdLineEdit = QtWidgets.QLineEdit()
        self.boxIdLineEdit.setPlaceholderText("Enter a box id")

        # create the camera combo box
        self.cameraComboBox = QtWidgets.QComboBox()
        self.cameraComboBox.addItems(self.parent.videoDevices.values())

        # preview button
        self.previewButton = QtWidgets.QPushButton("Preview")
        self.previewButton.clicked.connect(self.preview)

        # create the notes text edit
        self.notesTextEdit = QtWidgets.QTextEdit()
        self.notesTextEdit.setPlaceholderText("Enter notes about the box")

        # add the widgets to the form layout
        self.formLayout.addRow("Box ID", self.boxIdLineEdit)
        self.formLayout.addRow("Camera", self.cameraComboBox)
        self.formLayout.addRow("", self.previewButton)
        self.formLayout.addRow("Notes", self.notesTextEdit)

        # create the button layout
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttonLayout)

        # create the ok button
        self.okButton = QtWidgets.QPushButton("Ok")
        self.okButton.clicked.connect(self.accept)

        # create the cancel button
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)

        # add the buttons to the button layout
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)

    def checkInputs(self):
        if self.boxIdLineEdit.text() == "":
            return False, "Please enter a box id"
        return True, ""

    def preview(self):
        videoDeviceIndex = self.cameraComboBox.currentIndex()
        cameraWindow = CameraWindow(parent=self)
        cameraWindow.createCamera(
            camNum=videoDeviceIndex,
            camName=self.cameraComboBox.currentText(),
            fps=30,
            prevFPS=30,
            recFPS=30,
        )
        cameraWindow.startPreview()
        cameraWindow.show()

    def loadBox(self, box: Box):
        self.boxIdLineEdit.setText(box.boxId)
        self.boxIdLineEdit.setReadOnly(True)
        self.cameraComboBox.setCurrentIndex(
            self.cameraComboBox.findText(self.parent.videoDevices[box.camera])
        )
        self.notesTextEdit.setText(box.notes)

    def accept(self) -> None:
        ok, message = self.checkInputs()
        if not ok:
            self.parent.statusBar.showMessage(message)
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        # get the key for the selected camera
        cameraKey = [
            key
            for key, value in self.parent.videoDevices.items()
            if value == self.cameraComboBox.currentText()
        ][0]
        box = Box(
            boxId=self.boxIdLineEdit.text(),
            camera=cameraKey,
            trials=[],
            notes=self.notesTextEdit.toPlainText(),
        )
        self.signals.okClicked.emit(box)
        super().accept()
