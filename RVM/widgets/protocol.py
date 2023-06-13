# a dock widget for the trials

from math import e
from PyQt6 import QtWidgets, QtCore, QtGui
from RVM.bases import ProjectSettings, Box, Animal, Trial, Protocol, ProtocalBase
import os
from itertools import cycle
class ProtocolManagerDockWidget(QtWidgets.QDockWidget):
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
        self.setWindowTitle("Protocol Manager")

        self.centralWidget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.centralWidget.setLayout(self.layout)
        self.setWidget(self.centralWidget)

        self.buttonWidget = QtWidgets.QWidget()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonWidget.setLayout(self.buttonLayout)

        self.saveProtocolButton = QtWidgets.QToolButton()
        self.saveProtocolButton.setText("Save Protocol")
        self.saveProtocolButton.setToolTip("Save the current protocol")
        self.saveProtocolButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "diskette.png"))
        )
        self.saveProtocolButton.clicked.connect(self.saveProtocol)

        self.createProtocolButton = QtWidgets.QToolButton()
        self.createProtocolButton.setText("Create Protocol")
        self.createProtocolButton.setToolTip("Create a new protocol")
        self.createProtocolButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "add.png"))
        )
        self.createProtocolButton.clicked.connect(self.createProtocol)

        self.deleteProtocolButton = QtWidgets.QToolButton()
        self.deleteProtocolButton.setText("Delete Protocol")
        self.deleteProtocolButton.setToolTip("Delete the selected protocol")
        self.deleteProtocolButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "delete.png"))
        )
        self.deleteProtocolButton.clicked.connect(self.deleteProtocol)

        self.protocolSelector = QtWidgets.QComboBox()
        self.protocolSelector.currentIndexChanged.connect(self.updateSelectedProtocol)
        for protocol in self.projectSettings.protocols:
            self.protocolSelector.addItem(protocol.name)

        self.buttonLayout.addWidget(self.saveProtocolButton)
        self.buttonLayout.addWidget(self.createProtocolButton)
        self.buttonLayout.addWidget(self.protocolSelector)
        self.buttonLayout.addWidget(self.deleteProtocolButton)

        self.editorWidget = QtWidgets.QScrollArea()
        self.editorWidget.setWidgetResizable(True)
        self.editorWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.editorLayout = QtWidgets.QGridLayout()
        self.editorWidget.setLayout(self.editorLayout)

        self.protocolNameEdit = QtWidgets.QLineEdit()
        self.protocolNameEdit.setPlaceholderText("Protocol Name")

        self.protocolDescriptionEdit = QtWidgets.QTextEdit()
        self.protocolDescriptionEdit.setPlaceholderText("Protocol Description")

        self.modifyBoxesButton = QtWidgets.QToolButton()
        self.modifyBoxesButton.setToolTip("Modify Boxes")
        self.modifyBoxesButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "settings.png"))
        )
        self.modifyBoxesButton.clicked.connect(self.modifyBoxes)        
        self.boxSelector = QtWidgets.QListWidget()
        self.selectBoxesLabel = QtWidgets.QLabel()
        self.selectBoxesLabel.setText("Select Boxes")
        self.selectAllBoxesItem = QtWidgets.QListWidgetItem("Select All")
        self.selectAllBoxesItem.setFlags(self.selectAllBoxesItem.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsAutoTristate)
        self.selectAllBoxesItem.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.boxSelector.addItem(self.selectAllBoxesItem)
        for box in self.projectSettings.boxes:
            item = QtWidgets.QListWidgetItem(box.name)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.boxSelector.addItem(item)
        self.boxSelector.itemChanged.connect(lambda item: self.updateBoxListSelection(item))

        self.modifyAnimalsButton = QtWidgets.QToolButton()
        self.modifyAnimalsButton.setToolTip("Modify Boxes")
        self.modifyAnimalsButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.iconsDir, "settings.png"))
        )
        self.modifyAnimalsButton.clicked.connect(self.modifyAnimals)      
        self.animalSelectorLabel = QtWidgets.QLabel()
        self.animalSelectorLabel.setText("Select Animals")
        self.animalSelector = QtWidgets.QListWidget()
        self.selectAllAnimalsItem = QtWidgets.QListWidgetItem("Select All")
        self.selectAllAnimalsItem.setFlags(self.selectAllBoxesItem.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsAutoTristate)
        self.selectAllAnimalsItem.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.animalSelector.addItem(self.selectAllAnimalsItem)
        for animal in self.projectSettings.animals:
            item = QtWidgets.QListWidgetItem(animal.uid)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.animalSelector.addItem(item)
        self.animalSelector.itemChanged.connect(lambda item: self.updateAnimalListSelection(item))

        # add to layout
        self.editorLayout.addWidget(self.protocolNameEdit, 0, 0, 1, 2)
        self.editorLayout.addWidget(self.protocolDescriptionEdit, 1, 0, 1, 2)
        self.editorLayout.addWidget(self.selectBoxesLabel, 2, 0, 1, 2)
        self.editorLayout.addWidget(self.modifyBoxesButton, 2, 1, 1, 1)
        self.editorLayout.addWidget(self.boxSelector, 3, 0, 1, 2)
        self.editorLayout.addWidget(self.animalSelectorLabel, 4, 0, 1, 2)
        self.editorLayout.addWidget(self.modifyAnimalsButton, 4, 1, 1, 1)
        self.editorLayout.addWidget(self.animalSelector, 5, 0, 1, 2)

        self.layout.addWidget(self.buttonWidget)
        self.layout.addWidget(self.editorWidget)

    def saveProtocol(self):
        pass

    def updateProtocolName(self):
        pass

    def updateSelectedProtocol(self):
        pass

    def updateBoxList(self):
        self.boxSelector.clear()
        self.boxSelector.addItem(self.selectAllBoxesItem)
        for box in self.projectSettings.boxes:
            item = QtWidgets.QListWidgetItem(box.name)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.boxSelector.addItem(item)

    def searchTreeWidget(self):
        pass

    def deleteProtocol(self):
        pass
    
    def createProtocol(self):
        pass

    def modifyBoxes(self):
        boxManagerDockWidget = self.parent.boxManagerDockWidget
        # place the box manager dock widget in the center of the main window and show it
        # try detaching the dock widget first
        if not boxManagerDockWidget.isFloating():
            boxManagerDockWidget.setFloating(True)
        if not boxManagerDockWidget.isVisible():
            boxManagerDockWidget.show()
        boxManagerDockWidget.move(
            self.parent.geometry().center() - boxManagerDockWidget.rect().center()
        )
        boxManagerDockWidget.raise_()
        boxManagerDockWidget.activateWindow()

    def modifyAnimals(self):
        animalManagerDockWidget = self.parent.animalManagerDockWidget
        # place the box manager dock widget in the center of the main window and show it
        # try detaching the dock widget first
        if not animalManagerDockWidget.isFloating():
            animalManagerDockWidget.setFloating(True)
        if not animalManagerDockWidget.isVisible():
            animalManagerDockWidget.show()
        animalManagerDockWidget.move(
            self.parent.geometry().center() - animalManagerDockWidget.rect().center()
        )
        animalManagerDockWidget.raise_()
        animalManagerDockWidget.activateWindow()

    def addBoxToList(self, box: Box):
        item = QtWidgets.QListWidgetItem(box.name)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.boxSelector.addItem(item)

    def updateBoxListSelection(self, item):
        if item != self.selectAllBoxesItem:
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                allChecked = True
                for i in range(1, self.boxSelector.count()):
                    if self.boxSelector.item(i).checkState() != QtCore.Qt.CheckState.Checked:
                        allChecked = False
                        break
                if allChecked:
                    self.selectAllBoxesItem.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                self.selectAllBoxesItem.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
        if item == self.selectAllBoxesItem:
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                for i in range(1, self.boxSelector.count()):
                    self.boxSelector.item(i).setCheckState(QtCore.Qt.CheckState.Checked)
            elif item.checkState() == QtCore.Qt.CheckState.Unchecked:
                for i in range(1, self.boxSelector.count()):
                    self.boxSelector.item(i).setCheckState(QtCore.Qt.CheckState.Unchecked)
            elif item.checkState() == QtCore.Qt.CheckState.PartiallyChecked:
                allUnchecked = True
                for i in range(1, self.boxSelector.count()):
                    if self.boxSelector.item(i).checkState() == QtCore.Qt.CheckState.Checked:
                        allUnchecked = False
                        break
                if allUnchecked:
                    self.selectAllBoxesItem.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def updateAnimalListSelection(self, item):
        if item != self.selectAllAnimalsItem:
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                allChecked = True
                for i in range(1, self.animalSelector.count()):
                    if self.animalSelector.item(i).checkState() != QtCore.Qt.CheckState.Checked:
                        allChecked = False
                        break
                if allChecked:
                    self.selectAllAnimalsItem.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                # tri state to not uncheck all animals
                self.selectAllAnimalsItem.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
        if item == self.selectAllAnimalsItem:
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                for i in range(1, self.animalSelector.count()):
                    self.animalSelector.item(i).setCheckState(QtCore.Qt.CheckState.Checked)
            elif item.checkState() == QtCore.Qt.CheckState.Unchecked:
                for i in range(1, self.animalSelector.count()):
                    self.animalSelector.item(i).setCheckState(QtCore.Qt.CheckState.Unchecked)
            elif item.checkState() == QtCore.Qt.CheckState.PartiallyChecked:
                allUnchecked = True
                for i in range(1, self.animalSelector.count()):
                    if self.animalSelector.item(i).checkState() == QtCore.Qt.CheckState.Checked:
                        allUnchecked = False
                        break
                if allUnchecked:
                    self.selectAllAnimalsItem.setCheckState(QtCore.Qt.CheckState.Unchecked)


    def refresh(self):
        pass


class ProgramaticTrialCreator(QtWidgets.QDialog):
    def __init__(self, protocolManager: ProtocolManagerDockWidget, projectSettings: ProjectSettings, mainWin: QtWidgets.QMainWindow=None, parent=None): 
        super().__init__(parent=parent)
        self.protocolManager = protocolManager
        self.projectSettings = projectSettings
        self.mainWin = mainWin
        self.initUi()

    def initUi(self):
        # selected mice
        # selected boxes
        # number of trials
        # trial length
        # create button
        # cancel button
        pass

    def createTrials(self, protocol: Protocol, trial_num: int):
        animalBoxDict = {}
        for i,J in list(zip(protocol.animals, cycle(protocol.boxes))):
            animalBoxDict[i.uid] = J.uid
        trials = []
        for i in range(trial_num):
            for animal in protocol.animals:
                box = self.projectSettings.getBoxFromId(animalBoxDict[animal.uid])
                trials.append(Trial(animal=animal, box=box, protocol=protocol.uid))
        return trials



