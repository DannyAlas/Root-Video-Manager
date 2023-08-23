# a dock widget for the management of boxes in a project
# updates the project settings when a box is modified

import os

from PyQt6 import QtCore, QtGui, QtWidgets

from RVM.bases import Box, BoxBase, ProjectSettings, Protocol
from RVM.widgets.camWin import CameraPreviewWindow


class BoxManagerDockWidgetSignals(QtCore.QObject):
    boxCreated = QtCore.pyqtSignal(Box)
    boxDeleted = QtCore.pyqtSignal(Box)
    boxUpdated = QtCore.pyqtSignal(Box)


class BoxManagerDockWidget(QtWidgets.QDockWidget):
    def __init__(self, projectSettings: ProjectSettings, parent):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.parent = parent
        self.signals = BoxManagerDockWidgetSignals()
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
        self.deleteBoxButton.clicked.connect(self.deleteBoxes)

        self.previewAllBoxCamerasButton = QtWidgets.QToolButton()
        self.previewAllBoxCamerasButton.setText("Preview Box Cameras")
        self.previewAllBoxCamerasButton.setToolTip("Preview all box cameras")
        self.previewAllBoxCamerasButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "camera.png"))
        )
        self.previewAllBoxCamerasButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.previewAllBoxCamerasButton.clicked.connect(self.previewAllBoxCameras)

        self.buttonLayout.addWidget(self.createBoxButton)
        self.buttonLayout.addWidget(self.deleteBoxButton)
        self.buttonLayout.addWidget(self.previewAllBoxCamerasButton)
        self.buttonLayout.addStretch(1)

        # a search bar for the tree widget
        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.textChanged.connect(self.searchTreeWidget)
        self.buttonLayout.addWidget(self.searchBar)

        # create box list widget
        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.treeWidget.setHeaderLabels(["Box ID", "Camera", "Notes"])
        self.treeWidget.setColumnCount(3)
        self.treeWidget.itemChanged.connect(self.updateBoxFromItem)
        self.treeWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)
        self.treeWidget.itemDoubleClicked.connect(self.editBox)
        self.treeWidget.setSortingEnabled(True)

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
        self.deleteAction.triggered.connect(self.deleteBoxes)
        self.contextMenu.addAction(self.editAction)
        self.contextMenu.addAction(self.deleteAction)
        self.contextMenu.exec(self.treeWidget.mapToGlobal(pos))

    def searchTreeWidget(self, text: str):
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            for j in range(item.columnCount()):
                if text.lower() in item.text(j).lower():
                    item.setHidden(False)
                    break
                else:
                    item.setHidden(True)

    def createNewBox(self):
        """
        Create a new box and add it to the project settings
        """
        newBoxDialog = BoxDialog(self.projectSettings, self.parent, self)
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
        self.parent.refreshAllWidgets(self)
        self.signals.boxCreated.emit(box)

    def deleteBoxes(self):
        for item in self.treeWidget.selectedItems():
            # FIXME: this is somehow returning an already deleted box??
            self.deleteBox(item)

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
        box = self.getBoxFromItem(item)
        editBoxDialog = BoxDialog(self.projectSettings, self.parent, self)
        editBoxDialog.loadBox(box)
        editBoxDialog.signals.okClicked.connect(self.updateBox)
        editBoxDialog.show()

    def previewAllBoxCameras(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            self.previewCamera(item)

    def previewCamera(self, item):
        if type(item) == QtWidgets.QTreeWidgetItem:
            box = self.getBoxFromItem(item)
        elif type(item) == Box or type(item) == BoxBase:
            box = self.projectSettings.getBoxFromId(item.uid)
        else:
            self.parent.messageBox("Error", "Could not preview camera", "Warning")
            return

        try:
            self.parent.updateStatus("Previewing Camera For Box {}".format(box.uid))
            self.cameraPreviewWindow = CameraPreviewWindow(
                parent=self.parent, mainWin=self.parent
            )
            self.cameraPreviewWindow.createCamera(
                camNum=list(self.parent.videoDevices.keys()).index(box.camera),
                camName=f"Box {box.uid} Camera",
                fps=30,
                prevFPS=30,
                recFPS=30,
            )
            self.cameraPreviewWindow.show()
        except Exception as e:
            self.parent.messageBox(
                "Error", f"Could not preview camera\n\n{e}", "Warning"
            )

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
        self.parent.refreshAllWidgets(self)

    def deleteBox(self, item, *args, **kwargs):
        """
        Delete a box from the project settings

        Parameters
        ----------
        item : QtWidgets.QTreeWidgetItem || Box || BoxBase
            The item to delete
        """
        if type(item) == QtWidgets.QTreeWidgetItem:
            try:
                box = self.getBoxFromItem(item)
            except:
                return
        elif type(item) == Box or type(item) == BoxBase:
            box = item
        else:
            self.parent.messageBox("Error", "Could not delete box", "Warning")
            return

        self.parent.updateStatus("Deleting Box {}".format(box.uid))
        confim = self.parent.confirmBox(
            "Delete Box", f"Are you sure you want to delete Box: {box.uid}?"
        )
        if not confim:
            return
        # remove the box from the project settings
        self.projectSettings.boxes.remove(box)
        # update the box list
        self.updateBoxList()
        self.parent.updateStatus("Deleted box {}".format(box.uid))
        self.parent.refreshAllWidgets(self)

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
                currentCamera = self.getCameraNameFromKey(box.camera)
                item.setText(1, currentCamera)
                self.treeWidget.setItemWidget(item, 1, camerasCombo)
                item.setText(2, box.notes)
                self.treeWidget.addTopLevelItem(item)
        else:
            for box in protocol.boxes:
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, box.uid)
                currentCamera = self.getCameraNameFromKey(box.camera)
                item.setText(1, currentCamera)
                self.treeWidget.setItemWidget(item, 1, camerasCombo)
                item.setText(2, box.notes)
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
        box = self.projectSettings.getBoxFromId(boxId)
        if box is None:
            raise Exception("Could not find box with id {}".format(boxId))
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
        box = self.projectSettings.getBoxFromId(boxId)
        if box is None:
            self.parent.updateStatus("Could not find box with id {}".format(boxId))
        # update the box from the item
        elif column == 1:
            box.camera = self.getCameraKeyFromName(item.text(1))
        elif column == 2:
            box.notes = item.text(2)

    def refresh(self):
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

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        return super().closeEvent(event)


class BoxDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(BoxBase)


class BoxDialog(QtWidgets.QDialog):
    def __init__(
        self,
        projectSettings: ProjectSettings,
        mainWin: QtWidgets.QMainWindow = None,
        parent=None,
    ):
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
        self.boxIdLineEdit = QtWidgets.QLineEdit()
        self.boxIdLineEdit.setPlaceholderText("Enter a box ID")

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

        # delete button
        self.deleteButton = QtWidgets.QPushButton("Delete")
        self.deleteButton.clicked.connect(self.deleteBox)

        # add the buttons to the button layout
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.deleteButton)

    def checkInputs(self):
        if self.currentBox is None:
            if not str(self.boxIdLineEdit.text()).isalnum():
                return False, "Box ID must not contain special characters"
            if self.boxIdLineEdit.text() == "":
                return False, "Please enter a box ID"
            if self.boxIdLineEdit.text() in [
                box.uid for box in self.projectSettings.boxes
            ]:
                return False, "Box ID already exists please enter a unique box ID"
            if self.cameraComboBox.currentText() == "":
                return False, "Please select a camera"
        if self.cameraComboBox.currentText() in [
            self.mainWin.videoDevices.get(box.camera, "")
            for box in self.projectSettings.boxes
            if box.uid != self.boxIdLineEdit.text()
        ]:
            return (
                False,
                f"Camera '{self.cameraComboBox.currentText()}' already in use please select a different camera",
            )

        return True, ""

    def preview(self):
        self.cameraPreviewWindow = CameraPreviewWindow(
            parent=self.mainWin, mainWin=self.mainWin
        )
        try:
            self.cameraPreviewWindow.createCamera(
                camNum=list(self.mainWin.videoDevices.values()).index(
                    self.cameraComboBox.currentText()
                ),
                camName=self.cameraComboBox.currentText(),
                fps=30,
                prevFPS=30,
                recFPS=30,
            )
            self.cameraPreviewWindow.show()
        except Exception as e:
            self.mainWin.messageBox(
                title="ERROR",
                text=f"Could Not Preview Camera\n\n{e}",
                severity="Critical",
            )
            return

    def loadBox(self, box: Box):
        self.currentBox = box
        self.boxIdLineEdit.setText(box.uid)
        self.boxIdLineEdit.setReadOnly(True)
        self.boxIdLineEdit.setEnabled(False)
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
                uid=self.boxIdLineEdit.text(),
                camera=cameraKey,
                notes=self.notesTextEdit.toPlainText(),
            )
        else:
            self.currentBox.uid = self.boxIdLineEdit.text()
            self.currentBox.camera = cameraKey
            self.currentBox.notes = self.notesTextEdit.toPlainText()

        self.signals.okClicked.emit(self.currentBox)
        super().accept()
