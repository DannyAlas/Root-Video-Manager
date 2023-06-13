import os
from typing import Literal
from PyQt6 import QtCore, QtGui, QtWidgets
from bases import ProjectSettings
from widgets import (
    BoxManagerDockWidget, AnimalManagerDockWidget, TrialManagerDockWidget, ProtocolManagerDockWidget
)
from capture_devices import devices

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Root Video Manager")
        self.qtsettings = QtCore.QSettings("RVM", "RVM")
        self.projectSettings = ProjectSettings()
        self.dockWidgets = []
        
        self.iconsDir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "icons", "dark"
        )
        self.window().setWindowIcon(
            QtGui.QIcon(
                os.path.join(
                    self.iconsDir, "..", "logo.png"
                )
            )
        )
        # set the icon for the windows taskbar
        
        # create a status bar
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        self.initSettings()
        self.initUI()

    def initSettings(self):
        latest_project_location = self.qtsettings.value("latest_project_location")
        if latest_project_location is not None:
            try:
                self.projectSettings.load(latest_project_location)
                self.updateStatus(
                    f"Loaded the latest project settings for {self.projectSettings.project_name}"
                )
            except:
                self.updateStatus(
                    "Failed to load the latest project settings"
                )
        try:
            self.loadProject(self.projectSettings)
            self.updateStatus(
                f"Loaded the latest project settings for {self.projectSettings.project_name}"
            )
        except:
            self.updateStatus("Failed to load the project settings")

        # TODO: spawn a thread to check for new devices instead of doing it here
        self.initDevices()

    def updateStatus(self, message: str, timeout: int = 0):
        self.statusBar.showMessage(message, timeout)

    def initDevices(self):
        self.videoDevices = self.getVideoDevices()
        to_del = []
        for key, val in self.projectSettings.video_devices.items():
            # if the key is not in the new devices, remove it from the project settings and Box
            if key not in self.videoDevices:
                for box in self.projectSettings.boxes:
                    if key == box.camera:
                        box.camera = ""
                to_del.append(key)
        for key in to_del:
            del self.projectSettings.video_devices[key]
        self.projectSettings.video_devices = self.videoDevices

    def getVideoDevices(self) -> dict:
        d_list = devices.run_with_param(
            device_type="video", alt_name=True, list_all=True, result_=True
        )
        # the list is ordered by device-name and alternative-name
        # grab the device name and alternative name from the list and use alt as key and device as value
        d_dict = {}
        for i in range(0, len(d_list), 2):
            # use the alternative name as the key
            alt_name_str = d_list[i + 1]
            alt_name = alt_name_str.split(":")[1].strip()
            # use the device name as the value
            device_name_str = d_list[i]
            device_name = device_name_str.split(":")[1].strip()
            d_dict[alt_name] = device_name

        # if there are any duplicate device names, add a number to the end of the name
        for key, value in d_dict.items():
            if list(d_dict.values()).count(value) > 1:
                # get the index of the current key
                index = list(d_dict.keys()).index(key)
                # add a number to the end of the key
                d_dict[key] = value + f" ({index+1})"

        return d_dict
  
    def initUI(self):
        # create toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.newProjectButton = QtWidgets.QToolButton()
        self.newProjectButton.clicked.connect(self.NewProjectDialog)
        self.newProjectButton.setToolTip("Create a new project")
        self.newProjectButton.setIcon(
            QtGui.QIcon(os.path.join(self.iconsDir, "new-document.png"))
        )
        self.newProjectButton.setText("New Project")
        self.newProjectButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.toolbar.addWidget(self.newProjectButton)

        # add a open project button
        self.openProjectButton = QtWidgets.QToolButton()
        self.openProjectButton.clicked.connect(self.openExistingProject)
        self.openProjectButton.setToolTip("Open a project")
        self.openProjectButton.setIcon(
            QtGui.QIcon(os.path.join(self.iconsDir, "open-document.png"))
        )
        self.openProjectButton.setText("Open Project")
        self.openProjectButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.toolbar.addWidget(self.openProjectButton)

        # save project button
        self.saveProjectButton = QtWidgets.QToolButton()
        self.saveProjectButton.clicked.connect(self.saveSettings)
        self.saveProjectButton.setToolTip("Save the project")
        self.saveProjectButton.setIcon(
            QtGui.QIcon(os.path.join(self.iconsDir, "diskette.png"))
        )
        self.saveProjectButton.setText("Save Project")
        self.saveProjectButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.toolbar.addWidget(self.saveProjectButton)

        # add a combobox and add button next to it for protocols
        self.protocolComboBox = QtWidgets.QComboBox()
        for protocol in self.projectSettings.protocols:
            self.protocolComboBox.addItem(protocol.name)
        self.protocolComboBox.currentTextChanged.connect(self.protocolChanged)
        self.toolbar.addWidget(self.protocolComboBox)
        self.addProtocolButton = QtWidgets.QToolButton()
        self.addProtocolButton.clicked.connect(self.addProtocol)
        self.addProtocolButton.setToolTip("Add a new protocol")
        self.addProtocolButton.setIcon(
            QtGui.QIcon(os.path.join(self.iconsDir, "add.png"))
        )
        self.toolbar.addWidget(self.addProtocolButton)

        # add settings button
        self.settingsButton = QtWidgets.QToolButton()
        self.settingsButton.clicked.connect(self.settingsWindow)
        self.settingsButton.setToolTip("Settings")
        self.settingsButton.setIcon(
            QtGui.QIcon(os.path.join(self.iconsDir, "settings.png"))
        )
        self.toolbar.addSeparator()
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.toolbar.addWidget(spacer)
        self.toolbar.addWidget(self.settingsButton)

        # menu bar
        self.menuBar = self.menuBar()
        self.fileMenu = self.menuBar.addMenu("File")
        self.saveProjectAction = QtGui.QAction("Save Project", self)
        self.saveProjectAction.triggered.connect(self.saveSettings)
        self.fileMenu.addAction(self.saveProjectAction)
        self.newProjectAction = QtGui.QAction("New Project", self)
        self.newProjectAction.triggered.connect(self.NewProjectDialog)
        self.fileMenu.addAction(self.newProjectAction)
        self.openProjectAction = QtGui.QAction("Open Project", self)
        self.openProjectAction.triggered.connect(self.openExistingProject)
        self.fileMenu.addAction(self.openProjectAction)
        self.settingsAction = QtGui.QAction("Project Settings", self)
        self.settingsAction.triggered.connect(self.settingsWindow)
        self.fileMenu.addAction(self.settingsAction)
        self.viewMenu = self.menuBar.addMenu("View")

        # allow dock widgets to be moved
        self.setDockOptions(
            QtWidgets.QMainWindow.DockOption.AllowTabbedDocks
            | QtWidgets.QMainWindow.DockOption.AllowNestedDocks
        )
        self.createDockWidgets()

    def createDockWidgets(self):
        self.boxManagerDockWidget = BoxManagerDockWidget(self.projectSettings, self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.boxManagerDockWidget)
        self.viewMenu.addAction(self.boxManagerDockWidget.toggleViewAction())
        self.animalManagerDockWidget = AnimalManagerDockWidget(self.projectSettings, self)
        self.viewMenu.addAction(self.animalManagerDockWidget.toggleViewAction())
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.animalManagerDockWidget)
        self.trialManagerDockWidget = TrialManagerDockWidget(self.projectSettings, self)
        self.viewMenu.addAction(self.trialManagerDockWidget.toggleViewAction())
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.trialManagerDockWidget)
        self.protocolManagerDockWidget = ProtocolManagerDockWidget(self.projectSettings, self)
        self.viewMenu.addAction(self.protocolManagerDockWidget.toggleViewAction())
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.protocolManagerDockWidget)


    def protocolChanged(self, text):
        # refresh the open dock widgets to reflect the new protocol
        pass

    def addProtocol(self):
        pass

    def messageBox(
        self,
        title,
        text,
        severity: Literal["Information", "Warning", "Critical", "Question"] = "Information",
    ):
        severity = {
            "Information": QtWidgets.QMessageBox.Icon.Information,
            "Warning": QtWidgets.QMessageBox.Icon.Warning,
            "Critical": QtWidgets.QMessageBox.Icon.Critical,
            "Question": QtWidgets.QMessageBox.Icon.Question,
        }[severity]
        msg = QtWidgets.QMessageBox()
        msg.setWindowIcon(QtGui.QIcon(os.path.join(self.iconsDir, "..", "logo.png")))
        msg.setIcon(severity)
        msg.setText(text)
        msg.setWindowTitle(title)
        okay = msg.addButton("Okay", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        msg.setDefaultButton(okay)
        msg.exec()

    def confirmBox(self, title, text):
        msg = QtWidgets.QMessageBox()
        msg.setWindowIcon(QtGui.QIcon(os.path.join(self.iconsDir, "..", "logo.png")))
        msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg.setText(text)
        msg.setWindowTitle(title)
        yes = msg.addButton("Yes", QtWidgets.QMessageBox.ButtonRole.YesRole)
        no = msg.addButton("No", QtWidgets.QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(no)
        msg.exec()
        return msg.clickedButton() == yes

    def NewProjectDialog(self):
        # create a new project window
        self.NewProjectDialog = NewProjectDialog(parent=self)
        self.NewProjectDialog.projectSettingsSignal.projectSettingsSignal.connect(
            self.newProject
        )
        self.NewProjectDialog.show()

    def openExistingProject(self):
        # open a existing project
        dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Project Folder", os.path.expanduser("~")
        )
        if dir == "":
            self.updateStatus("No project selected")
        try:
            self.projectSettings.load(dir)
            self.loadProject(self.projectSettings)
        except Exception as e:
            # pop up a error message
            self.messageBox(
                "Error",
                f"Failed to load project: {e}",
                severity="Critical",
            )
        for dockWidget in self.findChildren(QtWidgets.QDockWidget):
            dockWidget.refresh()

    def settingsWindow(self):
        self.newSettingsWindow = ProjectSettingsDialog(
            self.projectSettings, parent=self
        )
        self.newSettingsWindow.signals.projectSettingsSignal.connect(self.reloadProject)
        self.newSettingsWindow.show()

    def newProject(self, projectSettings: ProjectSettings):
        # create a new project
        self.projectSettings = projectSettings

        # create a settings json file for the project
        self.projectSettings.save(self.projectSettings.project_location)
        # use QSettings to save the latest project location
        self.qtsettings.setValue(
            "latest_project_location", self.projectSettings.project_location
        )

    def loadProject(self, projectSettings: ProjectSettings):
        self.window().setWindowTitle(
            "Root Video Manager - " + self.projectSettings.project_name
        )
        # set position and size of the window from the settings
        self.resize(
            self.projectSettings.window_size[0], self.projectSettings.window_size[1]
        )
        self.move(
            self.projectSettings.window_position[0],
            self.projectSettings.window_position[1],
        )

    def reloadProject(self):
        # save the project
        self.saveSettings()
        # load the project
        self.loadProject(self.projectSettings)

    def checkVideoDeviceOption(self):
        if self.videoDeviceComboBox.currentIndex() == 0:
            self.startVideoStreamButton.setEnabled(False)
        else:
            self.startVideoStreamButton.setEnabled(True)


    def saveSettings(self):
        # save position and size of the window
        self.projectSettings.window_position = (self.pos().x(), self.pos().y())
        self.projectSettings.window_size = (self.size().width(), self.size().height())

        # save the settings to a json file
        self.projectSettings.save()
        self.qtsettings.setValue(
            "latest_project_location", self.projectSettings.project_location
        )

    def closeEvent(self, event):
        # stop all camera streams
        self.saveSettings()
        event.accept()

class NewProjectDialogSignals(QtCore.QObject):
    projectSettingsSignal = QtCore.pyqtSignal(ProjectSettings)


class NewProjectDialog(QtWidgets.QDialog):
    """A window for creating a new project"""

    def __init__(self, parent=None):
        super(NewProjectDialog, self).__init__(parent=parent)
        self.setWindowTitle("New Project")
        self.setGeometry(self.parent().x() + 100, self.parent().y() + 100, 400, 200)
        self.projectSettingsSignal = NewProjectDialogSignals()
        self.initUI()

    def initUI(self):
        # label for the project name
        self.projectNameLabel = QtWidgets.QLineEdit("Project Name")
        self.projectNameLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projectNameLabel.setReadOnly(False)
        self.projectNameLabel.setClearButtonEnabled(True)

        # label for the project directory
        self.projectDirectoryLabel = QtWidgets.QLineEdit("Select Project Directory")
        self.projectDirectoryLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projectDirectoryLabel.setReadOnly(True)

        # button for selecting the project directory
        self.selectProjectDirectoryButton = QtWidgets.QPushButton(
            "Select Project Directory"
        )
        self.selectProjectDirectoryButton.clicked.connect(self.selectProjectDirectory)

        # button for creating the project
        self.createProjectButton = QtWidgets.QPushButton("Create Project")
        self.createProjectButton.clicked.connect(self.createProject)

        # create a layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.projectNameLabel, 0, 0, 1, 2)
        self.layout.addWidget(self.projectDirectoryLabel, 1, 0)
        self.layout.addWidget(self.selectProjectDirectoryButton, 1, 1)
        self.layout.addWidget(self.createProjectButton, 2, 1, 1, 1)

        # set the layout
        self.setLayout(self.layout)

    def selectProjectDirectory(self):
        self.projectDirectoryLabel.setText(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        )

    def createProject(self):
        # get the project name
        projectName = self.projectNameLabel.text()
        # get the project directory
        projectDirectory = self.projectDirectoryLabel.text()
        # create a new project
        project = ProjectSettings(
            project_name=projectName, project_location=projectDirectory
        )
        # close the window
        self.projectSettingsSignal.projectSettingsSignal.emit(project)
        self.close()


class ProjectSettingsDialogSignal(QtCore.QObject):
    projectSettingsSignal = QtCore.pyqtSignal(ProjectSettings)


class ProjectSettingsDialog(QtWidgets.QDialog):
    """A window for editing the project settings"""

    def __init__(self, projectSettings: ProjectSettings, parent: QtWidgets.QMainWindow):
        super(ProjectSettingsDialog, self).__init__(parent=parent)
        self.setWindowTitle("Project Settings")
        self.setGeometry(self.parent().x() + 100, self.parent().y() + 100, 400, 200)
        self.signals = ProjectSettingsDialogSignal()
        self.projectSettings = projectSettings
        self.initUI()

    def initUI(self):
        # label for the project name
        self.projectNameLabel = QtWidgets.QLineEdit(self.projectSettings.project_name)
        self.projectNameLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projectNameLabel.setReadOnly(False)
        self.projectNameLabel.setClearButtonEnabled(True)

        # label for the project directory
        self.projectDirectoryLabel = QtWidgets.QLineEdit(
            str(self.projectSettings.project_location)
        )
        self.projectDirectoryLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projectDirectoryLabel.setReadOnly(True)

        # button for selecting the project directory
        self.selectProjectDirectoryButton = QtWidgets.QPushButton(
            "Select Project Directory"
        )
        self.selectProjectDirectoryButton.clicked.connect(self.selectProjectDirectory)

        # button for creating the project
        self.saveProjectSettingsButton = QtWidgets.QPushButton("Save Project Settings")
        self.saveProjectSettingsButton.clicked.connect(self.saveProjectSettings)

        # create a layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.projectNameLabel, 0, 0, 1, 2)
        self.layout.addWidget(self.projectDirectoryLabel, 1, 0)
        self.layout.addWidget(self.selectProjectDirectoryButton, 1, 1)
        self.layout.addWidget(self.saveProjectSettingsButton, 2, 1, 1, 1)

        # set the layout
        self.setLayout(self.layout)

    def selectProjectDirectory(self):
        self.projectDirectoryLabel.setText(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        )

    def saveProjectSettings(self):
        # get the project name
        projectName = self.projectNameLabel.text()
        # get the project directory
        projectDirectory = self.projectDirectoryLabel.text()
        # create a new project
        self.projectSettings.project_name = projectName
        self.projectSettings.project_location = projectDirectory
        # emit the signal
        self.signals.projectSettingsSignal.emit(self.projectSettings)
        # close the window
        self.close()
