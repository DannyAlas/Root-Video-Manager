import os
from PyQt6 import QtCore, QtGui, QtWidgets
from threading import Thread
from collections import deque
import time
import sys
import cv2
from RVM.camera import Camera, CameraWindow
from capture_devices import devices
from RVM.bases import ProjectSettings, Box, Trial

class MainWinodw(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWinodw, self).__init__()
        self.setWindowTitle("Root Video Manager")
        self.setGeometry(0, 0, 1280, 720)
        self.qtsettings = QtCore.QSettings("RVM", "RVM")
        self.projectSettings = ProjectSettings()
        # get the directory of the this file
        self.icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "dark")
        self.window().setWindowIcon(QtGui.QIcon(os.path.join(self.icons_dir, "logo.png")))
        self.initSettings()
        self.initUI()
    
    def initSettings(self):
        latest_project_location = self.qtsettings.value("latest_project_location")
        print(latest_project_location)
        # try to load the latest project
        if latest_project_location is not None:
            try:
                with open(os.path.join(latest_project_location, "settings.json")) as f:
                    self.projectSettings = ProjectSettings.fromJson(f.read())
            except:
                return
        # set position and size of the window from the settings
        try:
            self.loadProject(self.projectSettings)
        except:
            return

    def initUI(self):
        # create toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        self.newProjectButton = QtWidgets.QPushButton()
        self.newProjectButton.clicked.connect(self.newProjectWindow)
        self.newProjectButton.setToolTip("Create a new project")
        self.newProjectButton.setIcon(QtGui.QIcon(os.path.join(self.icons_dir, "new-document.png")))
        self.toolbar.addWidget(self.newProjectButton)

        # add a open project button
        self.openProjectButton = QtWidgets.QPushButton()
        self.openProjectButton.clicked.connect(self.openProjectExistingProject)
        self.openProjectButton.setToolTip("Open a project")
        self.openProjectButton.setIcon(QtGui.QIcon(os.path.join(self.icons_dir, "open-document.png")))
        self.toolbar.addWidget(self.openProjectButton)
        
        # add settings button
        self.settingsButton = QtWidgets.QPushButton()
        self.settingsButton.clicked.connect(self.settingsWindow)
        self.settingsButton.setToolTip("Settings")
        self.settingsButton.setIcon(QtGui.QIcon(os.path.join(self.icons_dir, "settings.png")))
        self.toolbar.addSeparator()
        self.toolbar.addSeparator()
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.settingsButton)

        # menu bar
        self.menuBar = self.menuBar()
        self.fileMenu = self.menuBar.addMenu("File")
        self.newProjectAction = QtGui.QAction("New Project", self)
        self.newProjectAction.triggered.connect(self.newProjectWindow)
        self.fileMenu.addAction(self.newProjectAction)
        self.openProjectAction = QtGui.QAction("Open Project", self)
        self.openProjectAction.triggered.connect(self.openProjectExistingProject)
        self.fileMenu.addAction(self.openProjectAction)
        self.settingsAction = QtGui.QAction("Project Settings", self)
        self.settingsAction.triggered.connect(self.settingsWindow)
        self.fileMenu.addAction(self.settingsAction)

        # the main widget will have 2 parts, the left part will be the list of boxes and the right part will be the selected boxs settings

        # create a widget for the left part
        self.boxListWidget = BoxListWidget(self.projectSettings)


        # create a widget for the right part
        self.boxSettingsWidget = QtWidgets.QWidget()
        self.boxSettingsWidgetLayout = QtWidgets.QVBoxLayout()
        self.boxSettingsWidget.setLayout(self.boxSettingsWidgetLayout)
        self.boxSettingsWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.boxSettingsWidget.setStyleSheet("background-color: rgb(50, 50, 50);")

        # create a splitter for the left and right part
        self.boxListSettingsSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.boxListSettingsSplitter.addWidget(self.boxListWidget)
        self.boxListSettingsSplitter.addWidget(self.boxSettingsWidget)
        self.boxListSettingsSplitter.setStretchFactor(0, 1)
        self.boxListSettingsSplitter.setStretchFactor(1, 3)
        self.boxListSettingsSplitter.setStyleSheet("background-color: rgb(50, 50, 50);")

        # create a status bar
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        # add the widgets to the main window
        self.setCentralWidget(self.boxListSettingsSplitter)


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

    def newProjectWindow(self):
        # create a new project window
        self.newProjectWindow = NewProjectWindow(parent=self)
        self.newProjectWindow.projectSettingsSignal.projectSettingsSignal.connect(self.newProject)
        self.newProjectWindow.show()

    def openProjectExistingProject(self):
        # open a existing project
        dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Project Folder", os.path.expanduser("~"))
        if dir == "":
            return
        # try to load the project
        try:
            with open(os.path.join(dir, "settings.json")) as f:
                self.projectSettings = ProjectSettings.fromJson(f.read())
            self.loadProject(self.projectSettings)
        except:
            return

    def settingsWindow(self):
        self.newSettingsWindow = ProjectSettingsWindow(self.projectSettings, parent=self)
        self.newSettingsWindow.signals.projectSettingsSignal.connect(self.reloadProject)
        self.newSettingsWindow.show()
        
    def newProject(self, projectSettings: ProjectSettings):
        # create a new project
        self.projectSettings = projectSettings

        # create a settings json file for the project
        self.projectSettings.save(self.projectSettings.project_location)
        # use QSettings to save the latest project location
        self.qtsettings.setValue("latest_project_location", self.projectSettings.project_location)

    def loadProject(self, projectSettings: ProjectSettings):
        self.window().setWindowTitle("Root Video Manager - " + self.projectSettings.project_name)
        # set position and size of the window from the settings
        self.resize(self.projectSettings.window_size[0], self.projectSettings.window_size[1])
        self.move(self.projectSettings.window_position[0], self.projectSettings.window_position[1])

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
        cameraWindow.createCamera(camNum=videoDeviceIndex, camName=self.videoDeviceComboBox.currentText(), fps=30, prevFPS=30, recFPS=30)
        cameraWindow.show()

    def getVideoDevices(self) -> dict:
        d_list = devices.run_with_param(device_type="video", alt_name=True,list_all=True, result_=True)
        # the list is ordered by device-name and alternative-name
        # grab the device name and alternative name from the list and use alt as key and device as value
        d_dict = {}
        for i in range(0,len(d_list),2):
            # use the alternative name as the key
            alt_name_str = d_list[i+1]
            alt_name = alt_name_str.split(":")[1].strip()
            # use the device name as the value
            device_name_str = d_list[i]
            device_name = device_name_str.split(":")[1].strip()
            d_dict[alt_name] = device_name
        return d_dict
        
    def saveSettings(self):
        # save position and size of the window
        self.projectSettings.window_position = (self.pos().x(), self.pos().y())
        self.projectSettings.window_size = (self.size().width(), self.size().height())

        # save the settings to a json file
        self.projectSettings.save()

    def closeEvent(self, event):
        # stop all camera streams
        self.saveSettings()        
        event.accept()

class BoxListWidget(QtWidgets.QDockWidget):

    def __init__(self, projectSettings: ProjectSettings, parent=None):
        super(BoxListWidget, self).__init__(parent=parent)
        self.initUI()

    def initUI(self):
        # remove the title bar
        self.setTitleBarWidget(QtWidgets.QWidget())
        
        # create an upper widget for buttons and a lower widget for the list
        self.upperWidget = QtWidgets.QWidget()
        self.lowerWidget = QtWidgets.QWidget()

        # create a layout for the upper widget
        self.upperWidgetLayout = QtWidgets.QHBoxLayout()
        self.upperWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.upperWidgetLayout.setSpacing(0)
        self.upperWidget.setLayout(self.upperWidgetLayout)

        # create a layout for the lower widget
        self.lowerWidgetLayout = QtWidgets.QVBoxLayout()
        self.lowerWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.lowerWidgetLayout.setSpacing(0)
        self.lowerWidget.setLayout(self.lowerWidgetLayout)

        # create a button for adding a new box
        self.addBoxButton = QtWidgets.QPushButton("Add Box")
        self.addBoxButton.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", "add.png")))
        self.addBoxButton.clicked.connect(self.addBox)

        # add the button to the upper widget
        self.upperWidgetLayout.addWidget(self.addBoxButton)

        # create a scroll area for the lower widget
        self.lowerWidgetScrollArea = QtWidgets.QScrollArea()
        self.lowerWidgetScrollArea.setWidgetResizable(True)
        self.lowerWidgetScrollArea.setWidget(self.lowerWidget)

        # create a layout for the widget
        self.widgetLayout = QtWidgets.QVBoxLayout()
        self.widgetLayout.setContentsMargins(0, 0, 0, 0)
        self.widgetLayout.setSpacing(0)
        self.widgetLayout.addWidget(self.upperWidget)
        self.widgetLayout.addWidget(self.lowerWidgetScrollArea)

        # create a widget for the dock
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(self.widgetLayout)
    


    def addBox(self):
        # create a new box
        newBox = QtWidgets.QWidget()
        newBoxLayout = QtWidgets.QHBoxLayout()
        newBox.setLayout(newBoxLayout)
        newBox.setFixedHeight(50)
        newBox.setContentsMargins(0, 0, 0, 0)




        
    
        # add the box to the lower widget
        self.lowerWidgetLayout.addWidget(newBox)


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
        self.selectProjectDirectoryButton = QtWidgets.QPushButton("Select Project Directory")
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
        self.projectDirectoryLabel.setText(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

    def createProject(self):
        # get the project name
        projectName = self.projectNameLabel.text()
        # get the project directory
        projectDirectory = self.projectDirectoryLabel.text()
        # create a new project
        project = ProjectSettings(project_name = projectName, project_location = projectDirectory)
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
        self.projectDirectoryLabel = QtWidgets.QLineEdit(self.projectSettings.project_location)
        self.projectDirectoryLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projectDirectoryLabel.setReadOnly(True)

        # button for selecting the project directory
        self.selectProjectDirectoryButton = QtWidgets.QPushButton("Select Project Directory")
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
        self.projectDirectoryLabel.setText(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

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
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    sys.exit(app.exec())
