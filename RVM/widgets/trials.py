# a dock widget for the trials

from PyQt6 import QtWidgets, QtCore, QtGui
from RVM.bases import ProjectSettings, Box, Trial, Animal
import os


class TrialManagerDockWidget(QtWidgets.QDockWidget):
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
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "add.png"))
        )
        self.createTrialButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.createTrialButton.clicked.connect(self.createTrial)

        self.deleteTrialButton = QtWidgets.QToolButton()
        self.deleteTrialButton.setText("Delete Trial")
        self.deleteTrialButton.setToolTip("Delete the selected box from the project")
        self.deleteTrialButton.setIcon(
            QtGui.QIcon(os.path.join(self.parent.icons_dir, "delete.png"))
        )
        self.deleteTrialButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.deleteTrialButton.clicked.connect(self.deleteBox)

        self.buttonLayout.addWidget(self.createTrialButton)
        self.buttonLayout.addWidget(self.deleteTrialButton)
        self.buttonLayout.addStretch(1)

        # self.treeWidget = QtWidgets.QTreeWidget()
        # self.treeWidget.setHeaderLabels(["Trial ID", "Animal ID", "Box ID", "Camera ID", "Notes"])
        # self.treeWidget.itemChanged.connect(self.updateBoxFromItem)
        # self.treeWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        # self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)
