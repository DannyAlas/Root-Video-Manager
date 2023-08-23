import logging
import os
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtGui, QtWidgets

from RVM.bases import ProjectSettings, Trial
from RVM.camera.camera import Camera

if TYPE_CHECKING:
    from RVM.mainWindow import MainWindow

log = logging.getLogger()


class CameraPreviewWindow(QtWidgets.QMainWindow):
    def __init__(
        self, cam: Camera = None, boxNum: int = None, mainWin=None, parent=None
    ):
        super(CameraPreviewWindow, self).__init__(parent)
        self.cam = cam
        self.mainWin: MainWindow = mainWin

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
            trial=None,
        )
        log.debug(f"Created camera {camName} with camNum {camNum}")

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
        self,
        cameraWindow,
        fps,
        prevFPS,
        recFPS,
        animalId,
        boxId,
        mainWin: "MainWindow",
        parent=None,
    ):
        super(CameraWindowDockWidget, self).__init__(parent)
        self.cameraWindow: CameraWindow = cameraWindow
        self.cameraWindow.setParent(self)
        self.fps = fps
        self.prevFPS = prevFPS
        self.recFPS = recFPS
        self.animalId = animalId
        self.boxId = boxId
        self.closeable = True
        self.mainWin = mainWin
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

    def close(self):
        if self.cameraWindow.trial is not None:
            if self.cameraWindow.trial.state == "Running":
                self.closeable = False
                confimationDialog = QtWidgets.QMessageBox()
                confimationDialog.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                confimationDialog.setText(
                    f"BOX {self.boxId} is currently recording {self.animalId}. Are you sure you want to STOP this trial?"
                )
                confimationDialog.setWindowTitle("Warning")
                confimationDialog.setStandardButtons(
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No
                )
                confimationDialog.setDefaultButton(
                    QtWidgets.QMessageBox.StandardButton.No
                )
                ok = confimationDialog.exec()
                if ok == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.closeable = True
                    self.cameraWindow.trial.stop()
                    self.mainWin.updateStatus(
                        f"Stopped Trial: {self.cameraWindow.trial.uid}"
                    )
                    if self.cameraWindow.close():
                        # refresh the widgets because we just stopped a trial and the trial manager needs to update
                        self.mainWin.refreshAllWidgets(caller=self)
                        self.mainWin.removeDockWidget(self)
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                if self.cameraWindow.close():
                    self.mainWin.refreshAllWidgets(caller=self)
                    self.mainWin.removeDockWidget(self)
                    return True
                else:
                    return False
        else:
            if self.cameraWindow.close():
                self.mainWin.refreshAllWidgets(caller=self)
                self.mainWin.removeDockWidget(self)
                return True
            else:
                return False

    def closeEvent(self, event):
        if self.closeable:
            if self.close():
                event.accept()
            else:
                event.ignore()
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
        trial: Trial = None,
        mainWin=None,
        parent=None,
    ):
        super(CameraWindow, self).__init__(parent)
        self.cam = cam
        self.mainWin: MainWindow = mainWin
        self.camNum = camNum
        self.trial = trial

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
            camName=f"Box {self.trial.box.uid} - Animal {self.trial.animal.uid}",
            saveFolder=save_dir,
            fps=fps,
            prevFPS=prevFPS,
            recFPS=recFPS,
            trial=self.mainWin.projectSettings.getTrialFromId(self.trial.uid),
            mainWin=self,
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

        self.resizeButton = QtGui.QAction(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "resize.png")),
            "&Resize",
            self,
        )
        self.resizeButton.triggered.connect(self.resizeWindow)
        self.toolBar.addAction(self.resizeButton)

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
        self.trial.stop()
        self.cam.stopRecording()
        self.recordButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def resizeWindow(self):
        """resize the dock widget to the size of the video"""
        # calculate the offset from the toolbar
        self.toolBarHeight = self.toolBar.sizeHint().height()
        self.offset = self.height() - self.mainWidget.height() - self.toolBarHeight
        self.resize(self.cam.vc.imw, self.cam.vc.imh + self.offset)
        self.mainWidget.resize(self.cam.vc.imw, self.cam.vc.imh + self.offset)
        self.parent().resize(self.cam.vc.imw, self.cam.vc.imh + self.offset)

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
