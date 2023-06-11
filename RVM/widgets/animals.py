# a dock widget for configuring the project animals

from calendar import c
from PyQt6 import QtWidgets, QtCore, QtGui
from RVM.bases import ProjectSettings, Animal
import os


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
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "add.png"))
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
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "delete.png"))
        )
        self.deleteAnimalsButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.deleteAnimalsButton.clicked.connect(self.deleteAnimals)

        self.buttonLayout.addWidget(self.createAnimalButton)
        self.buttonLayout.addWidget(self.deleteAnimalsButton)
        self.buttonLayout.addStretch(1)

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

    def updateAnimalFromItem(self, item: QtWidgets.QTreeWidgetItem, column: int):
        # get the animal id from the item
        animalId = item.text(0)
        # get the animal from the project settings
        animal = [
            animal
            for animal in self.projectSettings.animals
            if animal.animalId == animalId
        ]
        if animal is None:
            self.parent.statusBar.showMessage(
                "Could not find animal with id {}".format(animalId)
            )
            return
        if len(animal) == 0:
            self.parent.statusBar.showMessage(
                "Could not find animal with id {}".format(animalId)
            )
            return
        if len(animal) > 1:
            self.parent.statusBar.showMessage(
                "Multiple animals with id {}".format(animalId)
            )

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
        self.parent.statusBar.showMessage("Editing animal {}".format(item.text(0)))
        # load the animal from the project settings
        animal = [
            animal
            for animal in self.projectSettings.animals
            if animal.animalId == item.text(0)
        ]
        if animal is None:
            self.parent.statusBar.showMessage(
                "Could not find animal with id {}".format(item.text(0))
            )
            return
        if len(animal) == 0:
            self.parent.statusBar.showMessage(
                "Could not find animal with id {}".format(item.text(0))
            )
            return
        if len(animal) > 1:
            self.parent.statusBar.showMessage(
                "Multiple animals with id {}".format(item.text(0))
            )
        animal = animal[0]
        # create an instance of the animal dialog
        animalDialog = AnimalDialog(self.projectSettings, self)
        animalDialog.loadAnimal(animal)
        animalDialog.signals.okClicked.connect(self.updateAnimal)
        animalDialog.show()

    def updateAnimal(self, animal: Animal):
        # update the animal in the project settings
        for i, a in enumerate(self.projectSettings.animals):
            if a.animalId == animal.animalId:
                self.projectSettings.animals[i] = animal
                break
        # update the animal in the tree widget
        self.addAnimals()

    def addAnimal(self, animal: Animal):
        # add the animal to the project settings
        self.projectSettings.animals.append(animal)
        # add the animal to the tree widget
        self.addAnimals()

    def deleteAnimal(self, item: QtWidgets.QTreeWidgetItem, column: int):
        self.parent.statusBar.showMessage("Deleting animal {}".format(item.text(0)))
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
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "..", "logo.png"))
        )
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        ret = msgBox.exec()
        if ret == QtWidgets.QMessageBox.StandardButton.No:
            self.parent.statusBar.showMessage(
                "Canceled deletion of animal {}".format(item.text(0))
            )
            return
        # get the animal id from the item
        animalId = item.text(0)
        # get the animal from the project settings
        animal = [
            animal
            for animal in self.projectSettings.animals
            if animal.animalId == animalId
        ][0]
        if animal is None:
            self.parent.statusBar.showMessage(
                "Could not find animal with id {}".format(animalId)
            )
        # remove the animal from the project settings
        self.projectSettings.animals.remove(animal)
        # remove the animal from the tree widget
        self.treeWidget.takeTopLevelItem(self.treeWidget.indexOfTopLevelItem(item))

    def deleteAnimals(self):
        self.parent.statusBar.showMessage("Deleting animals")

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
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "..", "logo.png"))
        )
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        ret = msgBox.exec()
        if ret == QtWidgets.QMessageBox.StandardButton.No:
            self.parent.statusBar.showMessage("Canceled deletion of animals")
            return

        # loop through the selected items
        for item in selectedItems:
            # get the animal id from the item
            animalId = item.text(0)
            # get the animal from the project settings
            animal = [
                animal
                for animal in self.projectSettings.animals
                if animal.animalId == animalId
            ][0]
            if animal is None:
                self.parent.statusBar.showMessage(
                    "Could not find animal with id {}".format(animalId)
                )
                continue
            # remove the animal from the project settings
            self.projectSettings.animals.remove(animal)
            # remove the animal from the tree widget
            self.treeWidget.takeTopLevelItem(self.treeWidget.indexOfTopLevelItem(item))

    def addAnimals(self):
        # clear the tree widget
        self.treeWidget.clear()
        # add the animals to the tree widget
        for animal in self.projectSettings.animals:
            # create a new tree widget item
            treeWidgetItem = QtWidgets.QTreeWidgetItem()
            # set the text of the tree widget item
            treeWidgetItem.setText(0, animal.animalId)
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

    def reload(self, projectSettings: ProjectSettings):
        self.projectSettings = projectSettings
        self.addAnimals()


class AnimalDialogSignals(QtCore.QObject):
    okClicked = QtCore.pyqtSignal(Animal)


class AnimalDialog(QtWidgets.QDialog):
    def __init__(self, projectSettings: ProjectSettings, parent=None):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = AnimalDialogSignals()
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
        self.animalIdLineEdit = QtWidgets.QLineEdit()
        self.formLayout.addRow("Animal ID", self.animalIdLineEdit)

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
        # set the animal id to not be editable
        self.animalIdLineEdit.setReadOnly(True)
        # set the animal id
        self.animalIdLineEdit.setText(animal.animalId)
        # set the genotype
        self.genotypeLineEdit.setText(animal.genotype)
        # set the alive check box
        self.aliveCheckBox.setChecked(animal.alive)
        # set the notes
        self.notesTextEdit.setText(animal.notes)

    def checkInputs(self):
        # check if the animal id line edit is empty
        if self.animalIdLineEdit.text() == "":
            return False, "Animal ID cannot be empty"
        return True, ""

    def accept(self):
        # check the inputs
        ok, message = self.checkInputs()
        if not ok:
            # show the message box
            QtWidgets.QMessageBox.critical(self, "Error", message)
            return
        # create a new animal
        animal = Animal(
            animalId=self.animalIdLineEdit.text(),
            genotype=self.genotypeLineEdit.text(),
            alive=self.aliveCheckBox.isChecked(),
            notes=self.notesTextEdit.toPlainText(),
        )
        # emit the ok clicked signal
        self.signals.okClicked.emit(animal)
        # accept the dialog
        super().accept()
