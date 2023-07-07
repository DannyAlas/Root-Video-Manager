from PyQt6 import QtWidgets, QtCore, QtGui
import os
from RVM.camera.camera import Camera
from RVM.bases import ProjectSettings

class CameraPreviewWindow(QtWidgets.QMainWindow):
    def __init__(
        self, cam: Camera = None, boxNum: int = None, mainWin=None, parent=None
    ):
        super(CameraPreviewWindow, self).__init__(parent)
        self.cam = cam
        self.mainWin = mainWin

        if self.cam is None:
            # create a camera object
            self.createCamera(boxNum, f"Camera {boxNum}", 30, 30, 30)

        self.initUI()

    def createCamera(
        self, camNum: int, camName: str, fps: int, prevFPS: int, recFPS: int
    ) -> None:
        """create a camera object"""
        # get the directory to save the video to
        save_dir = self.mainWin.projectSettings.project_location
        if not os.path.exists(save_dir):
            save_dir = str(os.path.expanduser("~"))
        self.cam = Camera(
            camNum=camNum,
            camName=camName,
            saveFolder=save_dir,
            fps=fps,
            prevFPS=prevFPS,
            recFPS=recFPS,
            guiWin=self,
            boxId=0,
            animalId=0,
        )

    def initUI(self):
        # set up the tool bar
        # self.toolBar = QtWidgets.QToolBar()
        # self.previewButton = QtGui.QAction(
        #     QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "camera.png")),
        #     "&Preview",
        #     self,
        # )
        # self.previewButton.setEnabled(True)
        # self.previewButton.triggered.connect(self.startPreview)
        # self.toolBar.addAction(self.previewButton)

        # self.addToolBar(self.toolBar)

        # set up the status bar
        self.statusBar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusBar)

        # set up the window
        self.setWindowTitle(self.cam.camName)
        # set default window size
        self.resize(640, 480)

    def startPreview(self):
        """start the live preview"""
        self.cam.startPreview()
        # set up the main window
        self.mainWidget = self.cam.prevWindow
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.mainWidget)
        self.setWindowTitle(f"Previewing {self.cam.camName}")
        self.resize(self.cam.vc.imw, self.cam.vc.imh)

    def show(self):
        """Overrides the default show method to preview the camera."""
        self.startPreview()
        super(CameraPreviewWindow, self).show()
        

    def close(self):
        """
        Stops the video player thread.
        """
        # stop the threads
        self.cam.close()
        return True

    def closeEvent(self, event):
        """
        Overrides the default close event to stop the video player thread.
        """
        if self.close():
            event.accept()
        else:
            event.ignore()


class CameraWindowDockWidget(QtWidgets.QDockWidget):
    def __init__(
        self, cameraWindow, fps, prevFPS, recFPS, animalId, boxId, parent=None
    ):
        super(CameraWindowDockWidget, self).__init__(parent)
        self.cameraWindow = cameraWindow
        self.fps = fps
        self.prevFPS = prevFPS
        self.recFPS = recFPS
        self.animalId = animalId
        self.boxId = boxId
        self.initUi()

    def initUi(self):
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.cameraWindow)
        self.cameraWindow.createCamera(
            fps=self.fps,
            prevFPS=self.prevFPS,
            recFPS=self.recFPS,
        )
        self.setWindowTitle(f"Animal: {self.animalId} - Box: {self.boxId}")

    def closeEvent(self, event):
        if self.cameraWindow.close():
            event.accept()
            # close the dock widget in the main window
            self.parent().removeDockWidget(self)
        else:
            event.ignore()


class CameraWindow(QtWidgets.QMainWindow):
    """
    Represents a single Camera window in the GUI. Can be passed in a camera object or create one.
    """

    def __init__(
        self,
        cam: Camera = None,
        camNum: int = None,
        boxId: int = None,
        animalId=None,
        mainWin=None,
        parent=None,
    ):
        super(CameraWindow, self).__init__(parent)
        self.cam = cam
        self.mainWin = mainWin
        self.camNum = camNum
        self.boxId = boxId
        self.animalId = animalId

        if self.cam is None:
            # create a camera object
            self.createCamera(30, 30, 30)

        self.initUI()

    def createCamera(self, fps: int, prevFPS: int, recFPS: int) -> None:
        """create a camera object"""
        # get the directory to save the video to
        save_dir = os.path.join(self.mainWin.projectSettings.project_location, "Videos")
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except:
                save_dir = str(os.path.expanduser("~"))
        self.cam = Camera(
            camNum=self.camNum,
            camName=f"Camera {self.camNum}",
            saveFolder=save_dir,
            fps=fps,
            prevFPS=prevFPS,
            recFPS=recFPS,
            boxId=self.boxId,
            animalId=self.animalId,
            guiWin=self,
        )

    def initUI(self):
        # set up the tool bar
        self.toolBar = QtWidgets.QToolBar()
        self.previewButton = QtGui.QAction(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "camera.png")),
            "&Preview",
            self,
        )
        self.previewButton.setEnabled(True)
        self.previewButton.triggered.connect(self.startPreview)
        self.toolBar.addAction(self.previewButton)

        self.recordButton = QtGui.QAction(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "cam-recorder.png")),
            "&Record",
            self,
        )
        self.recordButton.setEnabled(False)
        self.recordButton.triggered.connect(self.startRecording)
        self.toolBar.addAction(self.recordButton)

        self.stopButton = QtGui.QAction(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "stop-record.png")),
            "&Stop",
            self,
        )
        # inactivate the stop button until we start recording
        self.stopButton.setEnabled(False)
        self.stopButton.triggered.connect(self.stopRecording)
        self.toolBar.addAction(self.stopButton)

        self.addToolBar(self.toolBar)

        # set up the status bar
        self.statusBar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusBar)

        # set up the window
        self.setWindowTitle(self.cam.camName)
        # set default window size
        self.resize(640, 480)

    def startPreview(self):
        """start the live preview"""
        self.cam.startPreview()
        # set up the main window
        self.mainWidget = self.cam.prevWindow
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.mainWidget)
        self.resize(self.cam.vc.imw, self.cam.vc.imh)
        self.previewButton.setEnabled(False)
        self.recordButton.setEnabled(True)

    def startRecording(self):
        """save the video"""
        self.cam.startRecording()
        self.recordButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    def stopRecording(self):
        """stop saving the video"""
        self.cam.stopRecording()
        self.recordButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def close(self):
        """
        Stops the video player thread.
        """
        # stop the threads
        self.cam.close()
        return True

    def closeEvent(self, event):
        """
        Overrides the default close event to stop the video player thread.
        """
        if self.close():
            event.accept()
            super(CameraWindow, self).closeEvent(event)
        else:
            event.ignore()


class CreateCameraDialogSignals(QtCore.QObject):
    """Signals for the CreateCameraDialog class"""

    # signal to create a camera
    finished = QtCore.pyqtSignal(CameraWindow, int, str)


class CreateCameraDialog(QtWidgets.QDialog):
    def __init__(
        self,
        projectSettings: ProjectSettings,
        mainWin,
        parent=None,
    ):
        super().__init__(parent)
        self.projectSettings = projectSettings
        self.signals = CreateCameraDialogSignals()
        self.parent = parent
        self.mainWin = mainWin
        self.cameraWindow = None
        self.cameraPreviewWindow = None
        self.initUi()

    def initUi(self):
        self.setWindowTitle("New Box")

        # create the layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # create the form layout
        self.formLayout = QtWidgets.QGridLayout()
        self.layout.addLayout(self.formLayout)
        self.formLayout.setVerticalSpacing(20)
        self.formLayout.setHorizontalSpacing(20)

        # create the box id number input
        self.boxNumberComboBox = QtWidgets.QComboBox()
        self.boxNumberComboBox.setPlaceholderText("Select a box")
        self.boxNumberComboBox.addItems(
            [box.uid for box in self.projectSettings.boxes]
        )
        # create the animal id line edit
        self.animalIdComboBox = QtWidgets.QComboBox()
        self.animalIdComboBox.setPlaceholderText("Select an animal")
        self.animalIdComboBox.addItems(
            [animal.uid for animal in self.projectSettings.animals]
        )
        # preview button
        self.previewButton = QtWidgets.QPushButton("Preview")
        self.previewButton.clicked.connect(self.preview)

        # add the widgets to the layout
        self.formLayout.addWidget(QtWidgets.QLabel("Box ID"), 0, 0)
        self.formLayout.addWidget(self.boxNumberComboBox, 0, 1)
        self.formLayout.addWidget(QtWidgets.QLabel("Animal Id"), 1, 0)
        self.formLayout.addWidget(self.animalIdComboBox, 1, 1)
        self.formLayout.addWidget(self.previewButton, 2, 0, 1, 2)

        # create the button layout
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttonLayout)

        # create the ok button
        self.okButton = QtWidgets.QPushButton("Ok")
        self.okButton.clicked.connect(self.accept)

        # create the cancel button
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)

        # add the buttons to the button layout
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)

    def preview(self):
        self.cameraPreviewWindow = CameraPreviewWindow(
            parent=self.mainWin, mainWin=self.mainWin
        )
        box = self.projectSettings.getBoxFromId(self.boxNumberComboBox.currentText())
        if box is None:
            self.mainWin.messageBox(title="ERROR", text="Box not Found", severity="Critical")
            return
        try:
            camera = self.mainWin.videoDevices[box.camera]
        except Exception as e:
            self.mainWin.messageBox(title="ERROR", text=f"FATAL ERROR: {e}", severity="Critical")
            return
        self.cameraPreviewWindow.createCamera(
            camNum=list(self.mainWin.videoDevices.values()).index(camera),
            camName=camera,
            fps=30,
            prevFPS=30,
            recFPS=30,
        )
        self.cameraPreviewWindow.show()

    def accept(self) -> None:
        box = self.projectSettings.getBoxFromId(self.boxNumberComboBox.currentText())
        if box is None:
            self.mainWin.messageBox(title="ERROR", text="Box not Found", severity="Critical")
            return
        try:
            camera = self.mainWin.videoDevices[box.camera]
        except Exception as e:
            self.mainWin.messageBox(title="ERROR", text=f"FATAL ERROR: {e}", severity="Critical")
            return
        self.signals.finished.emit(
            CameraWindow(
                parent=self.mainWin,
                camNum=list(self.mainWin.videoDevices.values()).index(camera),
                mainWin=self.mainWin,
                boxId=self.boxNumberComboBox.currentText(),
                animalId=self.animalIdComboBox.currentText(),
            ),
            int(self.boxNumberComboBox.currentText()),
            self.animalIdComboBox.currentText(),
        )
        super().accept()
