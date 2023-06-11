import os
from typing import Literal
from PyQt6 import QtCore, QtGui, QtWidgets
from threading import Thread
from collections import deque
import time
import sys
from RVM.widgets import BoxManagerDockWidget, AnimalManagerDockWidget
from RVM.camera import Camera, CameraWindow
from capture_devices import devices
from RVM.bases import ProjectSettings, Box, Trial
import qdarktheme


class MainWinodw(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWinodw, self).__init__()
        self.setWindowTitle("Root Video Manager")
        self.qtsettings = QtCore.QSettings("RVM", "RVM")
        self.projectSettings = ProjectSettings()
        # get the directory of the this file
        self.icons_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "icons", "dark"
        )
        self.window().setWindowIcon(
            QtGui.QIcon(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "icons", "logo.png"
                )
            )
        )
        self.dockWidgets = []
        self.initSettings()
        self.initUI()

    def initSettings(self):
        latest_project_location = self.qtsettings.value("latest_project_location")
        # try to load the latest project
        if latest_project_location is not None:
            try:
                with open(os.path.join(latest_project_location, "settings.json")) as f:
                    self.projectSettings = ProjectSettings.fromJson(f.read())
            except:
                self.statusBar().showMessage(
                    "Failed to load the latest project settings"
                )
        # set position and size of the window from the settings
        try:
            self.loadProject(self.projectSettings)
            self.statusBar().showMessage(
                f"Loaded the latest project settings for {self.projectSettings.project_name}"
            )
        except:
            self.statusBar().showMessage("Failed to load the project settings")

        # TODO: spawn a thread to check for new devices instead of doing it here
        self.initDevices()

    def initDevices(self):
        self.videoDevices = self.getVideoDevices()
        self.projectSettings.video_devices = self.videoDevices

    def initUI(self):
        # create toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.newProjectButton = QtWidgets.QToolButton()
        self.newProjectButton.clicked.connect(self.newProjectWindow)
        self.newProjectButton.setToolTip("Create a new project")
        self.newProjectButton.setIcon(
            QtGui.QIcon(os.path.join(self.icons_dir, "new-document.png"))
        )
        self.newProjectButton.setText("New Project")
        self.newProjectButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.toolbar.addWidget(self.newProjectButton)

        # add a open project button
        self.openProjectButton = QtWidgets.QToolButton()
        self.openProjectButton.clicked.connect(self.openProjectExistingProject)
        self.openProjectButton.setToolTip("Open a project")
        self.openProjectButton.setIcon(
            QtGui.QIcon(os.path.join(self.icons_dir, "open-document.png"))
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
            QtGui.QIcon(os.path.join(self.icons_dir, "diskette.png"))
        )
        self.saveProjectButton.setText("Save Project")
        self.saveProjectButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.toolbar.addWidget(self.saveProjectButton)

        # add settings button
        self.settingsButton = QtWidgets.QToolButton()
        self.settingsButton.clicked.connect(self.settingsWindow)
        self.settingsButton.setToolTip("Settings")
        self.settingsButton.setIcon(
            QtGui.QIcon(os.path.join(self.icons_dir, "settings.png"))
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
        self.newProjectAction.triggered.connect(self.newProjectWindow)
        self.fileMenu.addAction(self.newProjectAction)
        self.openProjectAction = QtGui.QAction("Open Project", self)
        self.openProjectAction.triggered.connect(self.openProjectExistingProject)
        self.fileMenu.addAction(self.openProjectAction)
        self.settingsAction = QtGui.QAction("Project Settings", self)
        self.settingsAction.triggered.connect(self.settingsWindow)
        self.fileMenu.addAction(self.settingsAction)

        # allow dock widgets to be moved
        self.setDockOptions(
            QtWidgets.QMainWindow.DockOption.AllowTabbedDocks
            | QtWidgets.QMainWindow.DockOption.AllowNestedDocks
        )

        # create a dock widget for managing boxes
        self.boxManagerDockWidget = BoxManagerDockWidget(self.projectSettings, self)
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.boxManagerDockWidget
        )
        self.dockWidgets.append(self.boxManagerDockWidget)
        # create a dock widget for managing animals
        self.animalManagerDockWidget = AnimalManagerDockWidget(
            self.projectSettings, self
        )
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.animalManagerDockWidget
        )
        self.dockWidgets.append(self.animalManagerDockWidget)
        # create a status bar
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # # create a combobox for selecting the video device
        # self.videoDeviceComboBox = QtWidgets.QComboBox()
        # # add select device option
        # self.videoDeviceComboBox.addItem("Select Device")
        # self.videoDeviceComboBox.addItems(self.videoDevices.values())
        # self.videoDeviceComboBox.currentIndexChanged.connect(self.checkVideoDeviceOption)

        # # create a button for starting the video stream from the selected device
        # self.startVideoStreamButton = QtWidgets.QPushButton("Add Camera")
        # self.startVideoStreamButton.setEnabled(False)
        # self.startVideoStreamButton.clicked.connect(self.startVideoStream)

        # # add the combobox and button to the toolbar
        # self.toolbar.addWidget(self.videoDeviceComboBox)
        # self.toolbar.addWidget(self.startVideoStreamButton)

    def messageBox(
        self,
        title,
        text,
        severity: Literal[
            QtWidgets.QMessageBox.Icon.Information,
            QtWidgets.QMessageBox.Icon.Warning,
            QtWidgets.QMessageBox.Icon.Critical,
        ] = QtWidgets.QMessageBox.Icon.Information,
    ):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(severity)
        msg.setText(text)
        msg.setWindowTitle(title)
        okay = msg.addButton("Okay", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        msg.setDefaultButton(okay)
        msg.exec()

    def newProjectWindow(self):
        # create a new project window
        self.newProjectWindow = NewProjectWindow(parent=self)
        self.newProjectWindow.projectSettingsSignal.projectSettingsSignal.connect(
            self.newProject
        )
        self.newProjectWindow.show()

    def openProjectExistingProject(self):
        # open a existing project
        dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Project Folder", os.path.expanduser("~")
        )
        if dir == "":
            return
        # try to load the project
        try:
            with open(os.path.join(dir, "settings.json")) as f:
                self.projectSettings = ProjectSettings.fromJson(f.read())
            self.loadProject(self.projectSettings)
        except Exception as e:
            # pop up a error message
            self.messageBox(
                "Error",
                f"Failed to load project: {e}",
                QtWidgets.QMessageBox.Icon.Critical,
            )
        for dockWidget in self.dockWidgets:
            dockWidget.reload(self.projectSettings)

    def settingsWindow(self):
        self.newSettingsWindow = ProjectSettingsWindow(
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

    def startVideoStream(self):
        if self.videoDeviceComboBox.currentIndex() == 0:
            return
        # get the selected video devices index in the combobox
        videoDeviceIndex = self.videoDeviceComboBox.currentIndex() - 1
        # create a new camera window
        cameraWindow = CameraWindow(parent=self)
        cameraWindow.createCamera(
            camNum=videoDeviceIndex,
            camName=self.videoDeviceComboBox.currentText(),
            fps=30,
            prevFPS=30,
            recFPS=30,
        )
        # place the camera window inside a dock widget
        cameraDockWidget = QtWidgets.QDockWidget(
            self.videoDeviceComboBox.currentText(), self
        )
        cameraDockWidget.setWidget(cameraWindow)
        cameraDockWidget.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
            | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
            | QtCore.Qt.DockWidgetArea.TopDockWidgetArea
            | QtCore.Qt.DockWidgetArea.BottomDockWidgetArea
        )
        # set the dock widget to be floating
        cameraDockWidget.setFloating(True)
        # add the dock widget to the main window
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, cameraDockWidget
        )

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


# signal for passing the project settings to the main window
class NewProjectWindowSignals(QtCore.QObject):
    projectSettingsSignal = QtCore.pyqtSignal(ProjectSettings)


class NewProjectWindow(QtWidgets.QDialog):
    """A window for creating a new project"""

    def __init__(self, parent=None):
        super(NewProjectWindow, self).__init__(parent=parent)
        self.setWindowTitle("New Project")
        self.setGeometry(self.parent().x() + 100, self.parent().y() + 100, 400, 200)
        self.projectSettingsSignal = NewProjectWindowSignals()
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


class ProjectSettingsWindowSignal(QtCore.QObject):
    projectSettingsSignal = QtCore.pyqtSignal(ProjectSettings)


class ProjectSettingsWindow(QtWidgets.QDialog):
    """A window for editing the project settings"""

    def __init__(self, projectSettings: ProjectSettings, parent: QtWidgets.QMainWindow):
        super(ProjectSettingsWindow, self).__init__(parent=parent)
        self.setWindowTitle("Project Settings")
        self.setGeometry(self.parent().x() + 100, self.parent().y() + 100, 400, 200)
        self.signals = ProjectSettingsWindowSignal()
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
            self.projectSettings.project_location
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = MainWinodw()
    main.show()
    customStyleSheet = """
            QStatusBar {
                font-size: 14x;
                background-color: #333333;
                color: #ffffff;
            }
            QToolTip {
                color: #333333;
            }

            """
    qdarktheme.setup_theme(additional_qss=customStyleSheet)

    sys.exit(app.exec())
