from PyQt6.QtWidgets import QMainWindow, QToolBar, QStatusBar, QVBoxLayout
from PyQt6.QtCore import (QMutex, QObject, Qt, QThread, QTimer, pyqtSignal,
                          pyqtSlot)
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow, QMenuBar,
                             QStatusBar, QToolBar, QVBoxLayout, QWidget)
import os
from RVM.camera.camera import Camera

class CameraWindow(QMainWindow):
    """
    Represents a single Camera window in the GUI. Can be passed in a camera object or create one.
    """

    def __init__(self, cam: Camera = None, boxNum: int = None, mainWin=None, parent=None):
        super(CameraWindow, self).__init__(parent)
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
        save_dir = self.mainWin.projectSettings.project_location
        if not os.path.exists(save_dir):
            save_dir = os.path.expanduser('~')
        self.cam = Camera(camNum, camName, save_dir, fps, prevFPS, recFPS, self)

    def initUI(self):
        # set up the tool bar
        self.toolBar = QToolBar()
        self.previewButton = QAction(
            QIcon(os.path.join(self.mainWin.iconsDir, "camera.png")), "&Preview", self
        )
        self.previewButton.setEnabled(True)
        self.previewButton.triggered.connect(self.startPreview)
        self.toolBar.addAction(self.previewButton)

        self.recordButton = QAction(
            QIcon(os.path.join(self.mainWin.iconsDir, "cam-recorder.png")),
            "&Record",
            self,
        )
        self.recordButton.setEnabled(False)
        self.recordButton.triggered.connect(self.startRecording)
        self.toolBar.addAction(self.recordButton)

        self.stopButton = QAction(
            QIcon(os.path.join(self.mainWin.iconsDir, "stop-record.png")),
            "&Stop",
            self,
        )
        # inactivate the stop button until we start recording
        self.stopButton.setEnabled(False)
        self.stopButton.triggered.connect(self.stopRecording)
        self.toolBar.addAction(self.stopButton)

        self.addToolBar(self.toolBar)

        # set up the status bar
        self.statusBar = QStatusBar(self)
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
        self.mainLayout = QVBoxLayout(self.mainWidget)
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

    def closeEvent(self, event):
        """close the camera when the window is closed"""
        self.cam.close()
        super(CameraWindow, self).closeEvent(event)
