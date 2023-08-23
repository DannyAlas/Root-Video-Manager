import logging
import os
import sys
from typing import Literal, Union

from bases import ProjectSettings
from devices import check_ffmpeg, get_devices
from PyQt6 import QtCore, QtGui, QtWidgets
from widgets import *

log = logging.getLogger()


def logging_exept_hook(exctype, value, traceback):
    log.critical(f"{str(exctype).upper()}: {value}\n{traceback}")
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = logging_exept_hook


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, logging_level=logging.DEBUG):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Root Video Manager")
        self.qtsettings = QtCore.QSettings("RVM", "RVM")
        self.projectSettings = ProjectSettings()
        self.logging_level = logging_level
        self.iconsDir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "icons", "dark"
        )
        self.window().setWindowIcon(
            QtGui.QIcon(os.path.join(self.iconsDir, "..", "logo.png"))
        )
        # set the icon for the windows taskbar

        # create a status bar
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        self.initSettings()
        self.initLogging()
        self.initUI()
        self.initMenus()

    def initSettings(self):
        latest_project_location = self.qtsettings.value("latest_project_location")
        if latest_project_location is not None:
            try:
                self.projectSettings.load(latest_project_location)
                self.updateStatus(
                    f"Loaded the latest project settings for {self.projectSettings.project_name}"
                )
            except:
                self.updateStatus("Failed to load the latest project settings")
        try:
            self.loadProject(self.projectSettings)
            self.updateStatus(
                f"Loaded the latest project settings for {self.projectSettings.project_name}"
            )
        except:
            self.updateStatus("Failed to load the project settings")

        logging.basicConfig(
            filename=os.path.join(self.projectSettings.project_location, "log.txt"),
            filemode="a",
            format="%(asctime)s - %(levelname)s: %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )
        # TODO: spawn a thread to check for new devices instead of doing it here
        self.initDevices()

    def initLogging(self):
        self.log = logging.getLogger()
        logFormatter = logging.Formatter(
            "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s \n",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

        fileHandler = logging.FileHandler(
            f"{os.path.join(self.projectSettings.project_location, 'log.txt')}"
        )
        for handler in self.log.handlers:
            if isinstance(handler, logging.FileHandler):
                self.log.removeHandler(handler)
        fileHandler.setFormatter(logFormatter)
        self.log.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        self.log.addHandler(consoleHandler)

        self.log.setLevel(self.logging_level)

    def updateLoggingFile(self):
        if self.projectSettings is None:
            return
        if not os.path.exists(self.projectSettings.project_location):
            return
        if not os.path.exists(
            os.path.join(self.projectSettings.project_location, "log.txt")
        ):
            # create a new log file
            with open(
                os.path.join(self.projectSettings.project_location, "log.txt"), "w"
            ) as file:
                file.write("")
        if self.log is None:
            self.log = logging.getLogger()
        fileHandler = logging.FileHandler(
            f"{os.path.join(self.projectSettings.project_location, 'log.txt')}"
        )
        fileHandler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s \n",
                datefmt="%m/%d/%Y %I:%M:%S %p",
            )
        )
        for handler in self.log.handlers:
            if isinstance(handler, logging.FileHandler):
                self.log.removeHandler(handler)
        self.log.addHandler(fileHandler)

    def updateStatus(self, message: str, timeout: int = 0):
        log.info(message)
        self.statusBar.showMessage(message, timeout)

    def initDevices(self):
        self.videoDevices = self.getVideoDevices()
        to_del = []
        for key, val in self.projectSettings.video_devices.items():
            # if the key is not in the new devices, remove it from the project settings and Box
            if key not in self.videoDevices.keys():
                for box in self.projectSettings.boxes:
                    if key == box.camera:
                        box.camera = ""
                to_del.append(key)
        for key in to_del:
            del self.projectSettings.video_devices[key]
        self.projectSettings.video_devices = self.videoDevices
        self.refreshAllWidgets(self)

    def initMenus(self):
        # a layout menu in the view menu
        self.layoutMenu = QtWidgets.QMenu("Layout", self)
        self.viewMenu.addMenu(self.layoutMenu)

        # to the layout menu, add a oraganize videos action
        self.organizeVideosAction = QtGui.QAction("Recording", self)
        self.organizeVideosAction.triggered.connect(self.recordingLayout)
        self.layoutMenu.addAction(self.organizeVideosAction)

        # IO menu
        self.ioMenu = QtWidgets.QMenu("IO", self)
        self.menuBar.addMenu(self.ioMenu)
        # to the IO menu, add a refresh video devices action
        self.refreshVideoDevicesAction = QtGui.QAction("Refresh Video Devices", self)
        self.refreshVideoDevicesAction.triggered.connect(self.initDevices)
        self.ioMenu.addAction(self.refreshVideoDevicesAction)

    def getCameraWindowGrid(self):
        """
        Get a grid layout of the CameraWindowDockWidget

        Returns
        -------
        QtWidgets.QGridLayout
            A grid layout with all the CameraWindowDockWidgets
        """
        dws = []
        for dw in self.findChildren(QtWidgets.QDockWidget):
            # if the widget is a CameraWindowDockWidget add it to the list
            if isinstance(dw, CameraWindowDockWidget):
                dws.append(dw)

        if len(dws) > 0:
            # figure out the number of rows and columns
            num_rows = int(len(dws) ** 0.5)
            num_cols = int(len(dws) / num_rows)
            # create a grid layout
            grid = QtWidgets.QGridLayout()
            # add the dock widgets to the grid
            for i in range(num_rows):
                for j in range(num_cols):
                    grid.addWidget(dws[i * num_cols + j], i, j)
            return grid
        else:
            return None

    def recordingLayout(self):
        # closes all the dock widgets except for the CameraWindowDockWidgets
        for dw in self.findChildren(QtWidgets.QDockWidget):
            if not isinstance(dw, CameraWindowDockWidget):
                dw.close()
        # get the grid layout of the CameraWindowDockWidgets
        grid = self.getCameraWindowGrid()
        if grid is not None:
            # create a new widget and set the layout
            class Widget(QtWidgets.QWidget):
                def __init__(self):
                    super(Widget, self).__init__()
                    self.setLayout(grid)

                def removeDockWidget(self, dockWidget):
                    self.layout().removeWidget(dockWidget)
                    dockWidget.closeEvent(event=QtGui.QCloseEvent())

                def close(self):
                    for dw in self.findChildren(QtWidgets.QDockWidget):
                        dw.close()
                        self.removeDockWidget(dw)
                    super(Widget, self).close()

                def refresh(self):
                    pass

            widget = Widget()
            widget.setLayout(grid)
            # create a new dock widget and set the widget
            dockWidget = QtWidgets.QDockWidget("Recording Layout", self)
            dockWidget.setWidget(widget)
            # add the dock widget to the main window
            self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)

    def getVideoDevices(self) -> dict:
        check_ffmpeg()
        return get_devices()["video"]

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

        # add vertical spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.toolbar.addWidget(spacer)

        # add button for CreateCameraDialog
        # self.addCameraButton = QtWidgets.QToolButton()
        # self.addCameraButton.clicked.connect(self.OpenCreateCameraDialog)
        # self.addCameraButton.setToolTip("Add a new camera")
        # self.addCameraButton.setIcon(
        #     QtGui.QIcon(os.path.join(self.iconsDir, "add.png"))
        # )
        # self.addCameraButton.setText("Add Camera")
        # self.addCameraButton.setToolButtonStyle(
        #     QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        # )
        # self.toolbar.addWidget(self.addCameraButton)

        # self.previewAllCamerasButton = QtWidgets.QToolButton()
        # self.previewAllCamerasButton.clicked.connect(self.previewAllCameras)
        # self.previewAllCamerasButton.setToolTip("Preview all cameras")
        # self.previewAllCamerasButton.setIcon(
        #     QtGui.QIcon(os.path.join(self.iconsDir, "camera.png"))
        # )
        # self.previewAllCamerasButton.setText("Preview All")
        # self.previewAllCamerasButton.setToolButtonStyle(
        #     QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        # )
        # self.toolbar.addWidget(self.previewAllCamerasButton)

        # self.recordAllCamerasButton = QtWidgets.QToolButton()
        # self.recordAllCamerasButton.clicked.connect(self.recordAllCameras)
        # self.recordAllCamerasButton.setToolTip("Record all cameras")
        # self.recordAllCamerasButton.setIcon(
        #     QtGui.QIcon(os.path.join(self.iconsDir, "cam-recorder.png"))
        # )
        # self.recordAllCamerasButton.setText("Record All")
        # self.recordAllCamerasButton.setToolButtonStyle(
        #     QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        # )
        # self.toolbar.addWidget(self.recordAllCamerasButton)

        # self.stopAllCamerasButton = QtWidgets.QToolButton()
        # self.stopAllCamerasButton.clicked.connect(self.stopAllCameras)
        # self.stopAllCamerasButton.setToolTip("Stop all cameras")
        # self.stopAllCamerasButton.setIcon(
        #     QtGui.QIcon(os.path.join(self.iconsDir, "stop-record.png"))
        # )
        # self.stopAllCamerasButton.setText("Stop All")
        # self.stopAllCamerasButton.setToolButtonStyle(
        #     QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        # )
        # self.toolbar.addWidget(self.stopAllCamerasButton)

        # add a combobox and add button next to it for protocols
        # self.protocolComboBox = QtWidgets.QComboBox()
        # for protocol in self.projectSettings.protocols:
        #     self.protocolComboBox.addItem(protocol.uid)
        # self.protocolComboBox.currentTextChanged.connect(self.protocolChanged)
        # self.toolbar.addWidget(self.protocolComboBox)
        # self.addProtocolButton = QtWidgets.QToolButton()
        # self.addProtocolButton.clicked.connect(self.addProtocol)
        # self.addProtocolButton.setToolTip("Add a new protocol")
        # self.addProtocolButton.setIcon(
        #     QtGui.QIcon(os.path.join(self.iconsDir, "add.png"))
        # )
        # self.toolbar.addWidget(self.addProtocolButton)

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

    def addCameraDockWidget(
        self, cameraWindow: CameraWindow, boxId: int, animalId: str
    ) -> Union[CameraWindowDockWidget, None]:
        msg_str = None
        for dockWidget in self.findChildren(CameraWindowDockWidget):
            if dockWidget.boxId == boxId:
                msg_str = f"A camera with the BOX ID of {boxId} already exists. Please choose a different box id."
            elif dockWidget.animalId == animalId:
                msg_str = f"A camera with the ANIMAL ID {animalId} already exists. Please choose a different animal id."

        if msg_str is not None:
            self.messageBox(title="ERROR", text=msg_str, severity="Critical")
            return

        # wrap the camera window in a dock widget
        dockWidget = CameraWindowDockWidget(
            cameraWindow=cameraWindow,
            boxId=boxId,
            animalId=animalId,
            fps=30,
            recFPS=30,
            prevFPS=30,
            mainWin=self,
            parent=self,
        )
        # add the dock widget to the main window
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)
        # add the dock widget to the view menu
        self.viewMenu.addAction(dockWidget.toggleViewAction())
        return dockWidget

    def previewAllCameras(self):
        for dockWidget in self.findChildren(CameraWindowDockWidget):
            dockWidget.cameraWindow.startPreview()

    def recordAllCameras(self):
        for dockWidget in self.findChildren(CameraWindowDockWidget):
            dockWidget.cameraWindow.startRecording()

    def stopAllCameras(self):
        for dockWidget in self.findChildren(CameraWindowDockWidget):
            dockWidget.cameraWindow.stopRecording()

    def createDockWidgets(self):
        self.boxManagerDockWidget = BoxManagerDockWidget(self.projectSettings, self)
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.boxManagerDockWidget
        )
        self.viewMenu.addAction(self.boxManagerDockWidget.toggleViewAction())
        self.animalManagerDockWidget = AnimalManagerDockWidget(
            self.projectSettings, self
        )
        self.viewMenu.addAction(self.animalManagerDockWidget.toggleViewAction())
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.animalManagerDockWidget
        )
        self.trialManagerDockWidget = TrialManagerDockWidget(
            self.projectSettings, self, self
        )
        self.viewMenu.addAction(self.trialManagerDockWidget.toggleViewAction())
        self.addDockWidget(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.trialManagerDockWidget
        )
        # self.protocolManagerDockWidget = ProtocolManagerDockWidget(
        #     self.projectSettings, self
        # )
        # self.viewMenu.addAction(self.protocolManagerDockWidget.toggleViewAction())
        # self.addDockWidget(
        #     QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.protocolManagerDockWidget
        # )

    def protocolChanged(self, text):
        # call the refresh method on the dock widgets
        pass

    def addProtocol(self):
        pass

    def messageBox(
        self,
        title,
        text,
        severity: Literal[
            "Information", "Warning", "Critical", "Question"
        ] = "Information",
    ):
        severity = {
            "Information": QtWidgets.QMessageBox.Icon.Information,
            "Warning": QtWidgets.QMessageBox.Icon.Warning,
            "Critical": QtWidgets.QMessageBox.Icon.Critical,
            "Question": QtWidgets.QMessageBox.Icon.Question,
        }[severity]
        if severity == QtWidgets.QMessageBox.Icon.Question:
            log.info(f"QUESTION: {text}")
        elif severity == QtWidgets.QMessageBox.Icon.Warning:
            log.warning(f"WARNING: {text}")
        elif severity == QtWidgets.QMessageBox.Icon.Critical:
            log.critical(f"CRITICAL: {text}")
        elif severity == QtWidgets.QMessageBox.Icon.Information:
            log.info(f"INFO: {text}")

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
        # save the current project if it exists
        if self.projectSettings is not None:
            self.saveSettings()
        # open a existing project
        dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Project Folder", os.path.expanduser("~")
        )
        if dir == "":
            self.updateStatus("No project selected")
            return
        try:
            self.projectSettings.load(dir)
            self.loadProject(self.projectSettings)
        except Exception as e:
            # pop up a error message
            self.messageBox(
                "Error",
                f"Failed to load project: \n{e}",
                severity="Critical",
            )
            self.projectSettings.load(dir_path=dir, check=False)
            self.projectSettings.repairSettings()
            self.loadProject(self.projectSettings)
        self.refreshAllWidgets(self)

    def refreshAllWidgets(
        self, caller: Union[QtWidgets.QDockWidget, QtWidgets.QMainWindow]
    ):
        """
        Refresh all widgets except the caller widget. The caller widget is the widget that called this method and it should handle its own refresh.

        Parameters
        ----------
        caller : QtWidgets.QDockWidget
            The widget that called this method.
        """
        for dockWidget in self.findChildren(QtWidgets.QDockWidget):
            if dockWidget != caller:
                try:
                    dockWidget.refresh()
                except:
                    pass

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
        self.updateLoggingFile()

    def loadProject(self, projectSettings: ProjectSettings = None):
        if projectSettings is not None:
            self.projectSettings = projectSettings
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
        self.updateLoggingFile()

    def reloadProject(self):
        # save the project
        self.saveSettings()
        # load the project
        self.loadProject(self.projectSettings)
        self.updateLoggingFile()

    def saveSettings(self):
        # save position and size of the window
        self.projectSettings.window_position = (self.pos().x(), self.pos().y())
        self.projectSettings.window_size = (self.size().width(), self.size().height())

        # save the settings to a json file
        self.projectSettings.save()
        self.qtsettings.setValue(
            "latest_project_location", self.projectSettings.project_location
        )
        self.updateLoggingFile()

    def closeEvent(self, event):
        # stop all camera streams
        for dw in self.findChildren(QtWidgets.QDockWidget):
            if isinstance(dw, CameraWindowDockWidget):
                aceept = dw.close()
                if not aceept:
                    event.ignore()
                    return
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


def get_main_win():
    return QtWidgets.QApplication.instance().mainWindow
