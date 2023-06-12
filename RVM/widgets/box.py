# a dock widget for the management of boxes in a project
# updates the project settings when a box is modified

from PyQt6 import QtWidgets, QtCore, QtGui
from RVM.bases import ProjectSettings, Protocol, Box, BoxBase
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
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "add.png"))
        )
        self.createBoxButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.createBoxButton.clicked.connect(self.createNewBox)

        self.deleteBoxButton = QtWidgets.QToolButton()
        self.deleteBoxButton.setText("Delete Box")
        self.deleteBoxButton.setToolTip("Delete the selected box from the project")
        self.deleteBoxButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "delete.png"))
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
        self.treeWidget.setHeaderLabels(["Box ID", "Name", "Trials", "Notes"])
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
        """
        Create a new box and add it to the project settings
        """
        newBoxDialog = BoxDialog(self.projectSettings, self, self.parent)
        newBoxDialog.signals.okClicked.connect(self.addBox)
        newBoxDialog.show()

    def addBox(self, box: Box):
        """
        Add a box to the project settings

        Parameters
        ----------
        box : Box
            The box to add to the project settings
        """
        self.projectSettings.boxes.append(box)
        self.updateBoxList()

    def deleteBoxes(self):
        pass

    def editBox(self, item: QtWidgets.QTreeWidgetItem, column: int):
        """
        Edit a box in the project settings

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem
            The item to edit
        column : int
            The column to edit
        """
        self.parent.updateStatus("Editing Box {}".format(item.text(0)))
        box = [box for box in self.projectSettings.boxes if box.uid == item.text(0)]
        if box is None:
            self.parent.updateStatus("Box {} not found".format(item.text(0)))
            return
        if len(box) == 0:
            self.parent.updateStatus("Box {} not found".format(item.text(0)))
            return
        box = box[0]
        editBoxDialog = BoxDialog(self.projectSettings, self, self.parent)
        editBoxDialog.loadBox(box)
        editBoxDialog.signals.okClicked.connect(self.updateBox)
        editBoxDialog.show()

    def updateBox(self, box: Box):
        """
        Update a box in the project settings

        Parameters
        ----------
        box : Box
            The box to update
        """
        for i in range(len(self.projectSettings.boxes)):
            if self.projectSettings.boxes[i].uid == box.uid:
                self.projectSettings.boxes[i] = box

        self.updateBoxList()

    def deleteBox(self, item, *args, **kwargs):
        """
        Delete a box from the project settings

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem || Box || BoxBase
            The item to delete
        """
        if type(item) == QtWidgets.QTreeWidgetItem:
            box = self.getBoxFromItem(item)
            print("Box from item", box)
        elif type(item) == Box or type(item) == BoxBase:
            box = item
        else:
            self.parent.messageBox("Error", "Could not delete box", "Warning")
            return
        
        self.parent.updateStatus("Deleting Box {}".format(box.uid))
        confim = self.parent.confirmBox("Delete Box", f"Are you sure you want to delete box {box.name}?\n\nID: {box.uid}")
        if not confim:
            return
        # remove the box from the project settings
        self.projectSettings.boxes.remove(box)
        # update the box list
        self.updateBoxList()
        self.parent.updateStatus("Deleted box {}".format(box.uid))

    def updateBoxList(self, protocol: Protocol = None):
        """
        Update the box list

        Parameters
        ----------
        protocol : Protocol, optional
            The protocol to use to update the box list, by default None
        """
        self.treeWidget.clear()
        camerasCombo = QtWidgets.QComboBox()
        camerasCombo.addItems(self.parent.videoDevices.values())

        if protocol is None:
            for box in self.projectSettings.boxes:
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, box.uid)
                item.setText(1, box.name)
                currentCamera = self.getCameraNameFromKey(box.camera)
                item.setText(2, currentCamera)
                self.treeWidget.setItemWidget(item, 1, camerasCombo)
                item.setText(3, box.notes)
                self.treeWidget.addTopLevelItem(item)
        else:
            for box in protocol.boxes:
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, box.uid)
                item.setText(1, box.name)
                currentCamera = self.getCameraNameFromKey(box.camera)
                item.setText(2, currentCamera)
                self.treeWidget.setItemWidget(item, 1, camerasCombo)
                item.setText(3, box.notes)
                self.treeWidget.addTopLevelItem(item)

    def getBoxFromItem(self, item: QtWidgets.QTreeWidgetItem, *args, **kwargs):
        """
        Helper function to get the associated box from a QTreeWidgetItem for the Box

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem
        column : int

        Returns
        -------
        box : Box

        Raises
        ------
        Exception
            If the box cannot be found or if multiple boxes are found
        """
        # get the box id from the item
        boxId = item.text(0)
        # get the box from the project settings
        box = [box for box in self.projectSettings.boxes if box.uid == boxId]
        if box is None:
            raise Exception("Could not find box with id {}".format(boxId))
        if len(box) == 0:
            raise Exception("Could not find box with id {}".format(boxId))
        if len(box) > 1:
            raise Exception("Found multiple boxes with id {}".format(boxId))
        box = box[0]
        return box

    def updateBoxFromItem(self, item: QtWidgets.QTreeWidgetItem, column: int):
        """
        Helper function to update a box from a QTreeWidgetItem

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem
            The item to update
        column : int
            The column to update
        """
        # get the box id from the item
        boxId = item.text(0)
        # get the box from the project settings
        box = [box for box in self.projectSettings.boxes if box.uid == boxId][0]
        if box is None:
            self.parent.updateStatus(
                "Could not find box with id {}".format(boxId)
            )
        # update the box from the item
        if column == 1:
            box.name = item.text(1)
        elif column == 2:
            box.camera = self.getCameraKeyFromName(item.text(2))
        elif column == 3:
            box.notes = item.text(3)

    def reload(self):
        """
        Reload the box list
        """
        self.updateBoxList()

    def getCameraNameFromKey(self, key: str) -> str:
        """
        Get the camera name from the camera key

        Parameters
        ----------
        key : str
            The camera key

        Returns
        -------
        str
            The camera name
        """
        try:
            return self.parent.videoDevices[key]
        except KeyError:
            return ""

    def getCameraKeyFromName(self, name: str) -> str:
        """
        Get the camera key from the camera name

        Parameters
        ----------
        name : str
            The camera name

        Returns
        -------
        str
            The camera key
        """
        return [
            key for key, value in self.parent.videoDevices.items() if value == name
        ][0]


class BoxDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(BoxBase)


class BoxDialog(QtWidgets.QDialog):
    def __init__(self, projectSettings: ProjectSettings, parent=None, mainWin: QtWidgets.QMainWindow=None):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = BoxDialogSignals()
        self.currentBox = None
        self.parent = parent
        self.mainWin = mainWin
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
        self.boxNameLineEdit = QtWidgets.QLineEdit()
        self.boxNameLineEdit.setPlaceholderText("Enter a box name")

        # create the camera combo box
        self.cameraComboBox = QtWidgets.QComboBox()
        self.cameraComboBox.addItems(self.mainWin.videoDevices.values())

        # preview button
        self.previewButton = QtWidgets.QPushButton("Preview")
        self.previewButton.clicked.connect(self.preview)

        # create the notes text edit
        self.notesTextEdit = QtWidgets.QTextEdit()
        self.notesTextEdit.setPlaceholderText("Enter notes about the box")

        # add the widgets to the form layout
        self.formLayout.addRow("Box Name", self.boxNameLineEdit)
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

        # delete button
        self.deleteButton = QtWidgets.QPushButton("Delete")
        self.deleteButton.clicked.connect(self.deleteBox)
        
        # add the buttons to the button layout
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.deleteButton)

    def checkInputs(self):
        if self.boxNameLineEdit.text() == "":
            return False, "Please enter a box name"
        return True, ""

    def preview(self):
        videoDeviceIndex = self.cameraComboBox.currentIndex()
        cameraWindow = CameraWindow(parent=self)
        cameraWindow.createCamera(
            camNum=videoDeviceIndex,
            camName=self.cameraComboBox.currentText(),
            fps=60,
            prevFPS=60,
            recFPS=60,
        )
        cameraWindow.startPreview()
        cameraWindow.show()

    def loadBox(self, box: Box):
        self.currentBox = box
        self.boxNameLineEdit.setText(box.name)
        try:
            self.cameraComboBox.setCurrentIndex(
                self.cameraComboBox.findText(self.mainWin.videoDevices[box.camera])
            )
        except:
            self.cameraComboBox.setCurrentIndex(0)
        self.notesTextEdit.setText(box.notes)

    def deleteBox(self):
        if self.currentBox is None:
            return
        self.parent.deleteBox(self.currentBox)

    def accept(self) -> None:
        ok, message = self.checkInputs()
        if not ok:
            self.mainWin.updateStatus(message)
            self.mainWin.messageBox("Error", message, "Critical")
            return
        # get the key for the selected camera
        cameraKey = [
            key
            for key, value in self.mainWin.videoDevices.items()
            if value == self.cameraComboBox.currentText()
        ]
        if cameraKey is None:
            self.mainWin.updateStatus(
                "Could not find camera {}".format(self.cameraComboBox.currentText())
            )
            return
        if len(cameraKey) == 0:
            self.mainWin.updateStatus(
                "Could not find camera {}".format(self.cameraComboBox.currentText())
            )
            return
        cameraKey = cameraKey[0]

        if self.currentBox is None:
            self.currentBox = Box(
                name=self.boxNameLineEdit.text(),
                camera=cameraKey,
                notes=self.notesTextEdit.toPlainText(),
            )
        else:
            self.currentBox.name = self.boxNameLineEdit.text()
            self.currentBox.camera = cameraKey
            self.currentBox.notes = self.notesTextEdit.toPlainText()

        self.signals.okClicked.emit(self.currentBox)
        super().accept()
