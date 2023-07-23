# a dock widget for configuring the project animals

import os

from PyQt6 import QtCore, QtGui, QtWidgets

from RVM.bases import Animal, ProjectSettings


class AnimalManagerDockWidget(QtWidgets.QDockWidget):
    def __init__(self, projectSettings: ProjectSettings, parent):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.parent = parent
        self.initUi()

    def initUi(self):
        # Set the title of the dock widget
        self.setWindowTitle("Animal Manager")

        # create the central widget
        self.centralWidget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.centralWidget.setLayout(self.layout)
        self.setWidget(self.centralWidget)

        # create the button widget
        self.buttonWidget = QtWidgets.QWidget()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonWidget.setLayout(self.buttonLayout)

        # add an add animal button
        self.createAnimalButton = QtWidgets.QToolButton()
        self.createAnimalButton.setText("Add Animal")
        self.createAnimalButton.setToolTip("Add a new animal to the project")
        self.createAnimalButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "add.png"))
        )
        self.createAnimalButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.createAnimalButton.clicked.connect(self.createNewAnimal)

        # add a delete animals button
        self.deleteAnimalsButton = QtWidgets.QToolButton()
        self.deleteAnimalsButton.setText("Delete Animals")
        self.deleteAnimalsButton.setToolTip(
            "Delete the selected animals from the project"
        )
        self.deleteAnimalsButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "delete.png"))
        )
        self.deleteAnimalsButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.deleteAnimalsButton.clicked.connect(self.deleteAnimals)

        self.buttonLayout.addWidget(self.createAnimalButton)
        self.buttonLayout.addWidget(self.deleteAnimalsButton)
        self.buttonLayout.addStretch(1)

        # a search bar for the tree widget
        self.searchBar = QtWidgets.QLineEdit()
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.textChanged.connect(self.searchTreeWidget)
        self.buttonLayout.addWidget(self.searchBar)

        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.treeWidget.setHeaderLabels(["Animal ID", "Genotype", "Alive", "Notes"])
        self.treeWidget.setColumnCount(4)
        self.treeWidget.itemChanged.connect(self.updateAnimalFromItem)
        self.treeWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)
        self.treeWidget.itemDoubleClicked.connect(self.editAnimal)
        self.treeWidget.setSortingEnabled(True)

        self.layout.addWidget(self.buttonWidget)
        self.layout.addWidget(self.treeWidget)

        self.addAnimals()

    def showContextMenu(self, pos: QtCore.QPoint):
        # if we don't have an item selected and are not over an item, return
        if self.treeWidget.currentItem() is None:
            return
        if self.treeWidget.itemAt(pos) is not self.treeWidget.currentItem():
            return
        # create the context menu
        self.contextMenu = QtWidgets.QMenu()
        # create the delete action
        self.editAction = QtGui.QAction("Edit", self)
        self.editAction.triggered.connect(
            lambda: self.editAnimal(self.treeWidget.currentItem(), 0)
        )
        self.deleteAction = QtGui.QAction("Delete", self)
        self.deleteAction.triggered.connect(
            lambda: self.deleteAnimal(self.treeWidget.currentItem(), 0)
        )

        # add the delete action to the context menu
        self.contextMenu.addAction(self.editAction)
        self.contextMenu.addAction(self.deleteAction)
        # show the context menu
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

    def updateAnimalFromItem(self, item: QtWidgets.QTreeWidgetItem, column: int):
        # get the animal id from the item
        uid = item.text(0)
        # get the animal from the project settings
        animal = self.projectSettings.get_animal(uid)
        if animal is None:
            self.parent.updateStatus("Could not find animal with id {}".format(uid))
            return
        if len(animal) == 0:
            self.parent.updateStatus("Could not find animal with id {}".format(uid))
            return
        if len(animal) > 1:
            self.parent.updateStatus("Multiple animals with id {}".format(uid))

        animal = animal[0]
        # update the animal from the item
        animal.genotype = item.text(1)
        animal.alive = item.checkState(2) == QtCore.Qt.CheckState.Checked
        animal.notes = item.text(3)

    def createNewAnimal(self):
        # create an instance of the new animal dialog
        animalDialog = AnimalDialog(self.projectSettings, self)
        animalDialog.show()
        animalDialog.signals.okClicked.connect(self.addAnimal)

    def editAnimal(self, item: QtWidgets.QTreeWidgetItem, column: int):
        self.parent.updateStatus("Editing animal {}".format(item.text(0)))
        # load the animal from the project settings
        animal = self.projectSettings.get_animal(item.text(0))
        if animal is None:
            self.parent.updateStatus(
                "Could not find animal with id {}".format(item.text(0))
            )
            return
        # create an instance of the animal dialog
        animalDialog = AnimalDialog(self.projectSettings, self)
        animalDialog.loadAnimal(animal)
        animalDialog.signals.okClicked.connect(self.updateAnimal)
        animalDialog.show()

    def updateAnimal(self, animal: Animal):
        # update the animal in the project settings
        self.projectSettings.update_animal(animal)
        # update the animal in the tree widget
        self.addAnimals()
        self.parent.refreshAllWidgets(self)

    def addAnimal(self, animal: Animal):
        # add the animal to the project settings
        self.projectSettings.add_animal(animal)
        # add the animal to the tree widget
        self.addAnimals()
        self.parent.refreshAllWidgets(self)

    def deleteAnimal(self, item: QtWidgets.QTreeWidgetItem, column: int):
        self.parent.updateStatus("Deleting animal {}".format(item.text(0)))
        # dialog to confirm deletion
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(f"Are you sure you want to delete \n{item.text(0)}?")
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        msgBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        # set the window title
        msgBox.setWindowTitle("Delete Animal?")
        msgBox.setWindowIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "..", "logo.png"))
        )
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        ret = msgBox.exec()
        if ret == QtWidgets.QMessageBox.StandardButton.No:
            self.parent.updateStatus(
                "Canceled deletion of animal {}".format(item.text(0))
            )
            return
        # get the animal id from the item
        uid = item.text(0)
        # get the animal from the project settings
        animal = self.projectSettings.get_animal(uid)
        if animal is None:
            self.parent.updateStatus("Could not find animal with id {}".format(uid))
        # remove the animal from the project settings
        self.projectSettings.delete_animal(animal)
        # remove the animal from the tree widget
        self.treeWidget.takeTopLevelItem(self.treeWidget.indexOfTopLevelItem(item))

    def deleteAnimals(self):
        self.parent.updateStatus("Deleting animals")

        # get all of the selected items
        selectedItems = self.treeWidget.selectedItems()
        # if we don't have any selected items, return
        if len(selectedItems) == 0:
            return
        # dialog to confirm deletion
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(f"Are you sure you want to delete {len(selectedItems)} animals?")
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        msgBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        # set the window title
        msgBox.setWindowTitle("Delete Animals?")
        msgBox.setWindowIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "..", "logo.png"))
        )
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        ret = msgBox.exec()
        if ret == QtWidgets.QMessageBox.StandardButton.No:
            self.parent.updateStatus("Canceled deletion of animals")
            return

        # loop through the selected items
        for item in selectedItems:
            # get the animal id from the item
            uid = item.text(0)
            # get the animal from the project settings
            animal = self.projectSettings.get_animal(uid)
            if animal is None:
                self.parent.updateStatus("Could not find animal with id {}".format(uid))
                continue
            # remove the animal from the project settings
            self.projectSettings.delete_animal(animal)
            # remove the animal from the tree widget
            self.treeWidget.takeTopLevelItem(self.treeWidget.indexOfTopLevelItem(item))

    def addAnimals(self):
        # clear the tree widget
        self.treeWidget.clear()
        # add the animals to the tree widget
        for animal in self.projectSettings.animals:
            # create a new tree widget item
            treeWidgetItem = QtWidgets.QTreeWidgetItem()
            treeWidgetItem.setText(0, animal.uid)
            treeWidgetItem.setText(1, animal.genotype)
            treeWidgetItem.setCheckState(
                2,
                QtCore.Qt.CheckState.Checked
                if animal.alive
                else QtCore.Qt.CheckState.Unchecked,
            )
            # set checkbox not editable
            treeWidgetItem.setFlags(
                treeWidgetItem.flags() & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable
            )
            treeWidgetItem.setTextAlignment(2, QtCore.Qt.AlignmentFlag.AlignCenter)
            treeWidgetItem.setText(3, animal.notes)
            # add the tree widget item to the tree widget
            self.treeWidget.addTopLevelItem(treeWidgetItem)

    def refresh(self):
        self.addAnimals()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        return super().closeEvent(event)


class AnimalDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(Animal)


class AnimalDialog(QtWidgets.QDialog):
    def __init__(self, projectSettings: ProjectSettings, parent=None):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = AnimalDialogSignals()
        self.currentAnimal = None
        self.parent = parent
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Animal")

        # create the layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # create the form layout
        self.formLayout = QtWidgets.QFormLayout()
        self.layout.addLayout(self.formLayout)

        # create the animal id line edit
        self.uidLineEdit = QtWidgets.QLineEdit()
        self.formLayout.addRow("Animal ID", self.uidLineEdit)
        # add a tool tip to the right of the line edit
        self.uidLineEdit.setToolTip(
            "The animal ID is a unique identifier for the animal. It is case sensitive."
        )

        # create the genotype line edit
        self.genotypeLineEdit = QtWidgets.QLineEdit()
        self.formLayout.addRow("Genotype", self.genotypeLineEdit)

        # create the alive check box
        self.aliveCheckBox = QtWidgets.QCheckBox()
        self.formLayout.addRow("Alive", self.aliveCheckBox)
        self.aliveCheckBox.setChecked(True)

        # create the notes text edit
        self.notesTextEdit = QtWidgets.QTextEdit()
        self.formLayout.addRow("Notes", self.notesTextEdit)

        # create the button box
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    def loadAnimal(self, animal: Animal):
        self.currentAnimal = animal
        # set the animal id to not be editable
        self.uidLineEdit.setReadOnly(True)
        self.uidLineEdit.setEnabled(False)
        # set the animal id
        self.uidLineEdit.setText(animal.uid)
        # set the genotype
        self.genotypeLineEdit.setText(animal.genotype)
        # set the alive check box
        self.aliveCheckBox.setChecked(animal.alive)
        # set the notes
        self.notesTextEdit.setText(animal.notes)

    def deleteAnimal(self):
        if self.currentAnimal is None:
            self.parent.updateStatusBar("Error: No animal selected")
        self.parent.deleteAnimal(self.currentAnimal)

    def checkInputs(self):
        if self.currentAnimal is None:
            # check the current animal id
            uid = self.uidLineEdit.text()
            if uid == "":
                return False, "Animal ID cannot be empty"
            if uid in [animal.uid for animal in self.projectSettings.animals]:
                return False, "Animal ID already exists"
        return True, "Updated animal"

    def accept(self):
        # check the inputs
        ok, message = self.checkInputs()
        if not ok:
            # show the message box
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        # create a new animal
        animal = Animal(
            uid=self.uidLineEdit.text(),
            genotype=self.genotypeLineEdit.text(),
            alive=self.aliveCheckBox.isChecked(),
            notes=self.notesTextEdit.toPlainText(),
        )
        # emit the ok clicked signal
        self.signals.okClicked.emit(animal)
        # accept the dialog
        super().accept()
