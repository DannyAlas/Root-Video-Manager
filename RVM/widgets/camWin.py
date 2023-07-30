import os

from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Union
from RVM.bases import Trial
from RVM.camera.camera import Camera
from RVM.settings import ProjectSettings

class CameraWindow(QtWidgets.QMainWindow):
    """
    Represents a single Camera window in the GUI. Can be passed in a camera object or create one.
    """

    def __init__(
        self,
        projectSettings: ProjectSettings,
        trial: Trial,
        camNum: int,
        mainWin,
        cam: Union[Camera, None] = None,
        parent=None,
    ):
        super(CameraWindow, self).__init__(parent)

        # cannot be tabbed
        self.setDocumentMode(True)
        self._trial = trial
        self.cam = cam
        self.mainWin = mainWin
        self.camNum = camNum
        self.projectSettings = projectSettings

        self.initUI()

    def createCamera(self, fps: int, prevFPS: int, recFPS: int) -> None:
        """create a camera object"""
        if self.trial is None:
            raise ValueError(
                "The trial is None, please associate a trial with this camera"
            )
        self.cam = Camera(
            camNum=self.camNum,
            camName=f"Box {self.trial.box.uid} - Animal {self.trial.animal.uid}",
            saveFolder=self.projectSettings.video_location,
            fps=fps,
            prevFPS=prevFPS,
            recFPS=recFPS,
            guiWin=self,
        )

    @property
    def trial(self) -> Trial:
        return self._trial

    @trial.setter
    def trial(self, trial: Trial):
        self._trial = self.projectSettings.get_trial(trial.uid)
        self.setWindowTitle(f"Animal: {self.trial.uid} - Box: {self.trial.box.uid}")

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
        print(self.cam.vc.imw, self.cam.vc.imh)

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


class CameraWindowDockWidget(QtWidgets.QDockWidget):
    def __init__(
        self, cameraWindow: CameraWindow, parent=None
    ) -> None:
        super(CameraWindowDockWidget, self).__init__(parent)
        # cannot be tabbed
        self.setDocumentMode(True) # type: ignore
        self.cameraWindow = cameraWindow
        self.cameraWindow.setParent(self)
        self.closeable = True
        self.initUi()

    def initUi(self) -> None:
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.cameraWindow)
        self.setWindowTitle(f"Camera Window")

    def close(self) -> bool:
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
                    if self.cameraWindow.close():
                        self.parent().removeDockWidget(self)
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                if self.cameraWindow.close():
                    self.parent().removeDockWidget(self)
                    return True
                else:
                    return False
        else:
            if self.cameraWindow.close():
                self.parent().removeDockWidget(self)
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
        projectSettings: ProjectSettings,
        trial: Trial,
        camNum: int,
        mainWin,
        cam: Union[Camera, None] = None,
        parent=None,
    ):
        super(CameraWindow, self).__init__(parent)

        # cannot be tabbed
        self.setDocumentMode(True)
        self._trial = trial
        self.cam = cam
        self.mainWin = mainWin
        self.camNum = camNum
        self.projectSettings = projectSettings

        self.initUI()

    def createCamera(self, fps: int, prevFPS: int, recFPS: int) -> None:
        """create a camera object"""
        if self.trial is None:
            raise ValueError(
                "The trial is None, please associate a trial with this camera"
            )
        self.cam = Camera(
            camNum=self.camNum,
            camName=f"Box {self.trial.box.uid} - Animal {self.trial.animal.uid}",
            saveFolder=self.projectSettings.video_location,
            fps=fps,
            prevFPS=prevFPS,
            recFPS=recFPS,
            guiWin=self,
        )

    @property
    def trial(self) -> Trial:
        return self._trial

    @trial.setter
    def trial(self, trial: Trial):
        self._trial = self.projectSettings.get_trial(trial.uid)
        self.setWindowTitle(f"Animal: {self.trial.uid} - Box: {self.trial.box.uid}")

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
        print(self.cam.vc.imw, self.cam.vc.imh)

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
        self.boxNumberComboBox.addItems([box.uid for box in self.projectSettings.boxes])
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
            projectSettings=self.projectSettings,
            parent=self.mainWin,
            mainWin=self.mainWin,
        )
        box = self.projectSettings.getBoxFromId(self.boxNumberComboBox.currentText())
        if box is None:
            self.mainWin.messageBox(
                title="ERROR", text="Box not Found", severity="Critical"
            )
            return
        try:
            camera = self.projectSettings.video_devices[box.camera]
        except Exception as e:
            self.mainWin.messageBox(
                title="ERROR", text=f"FATAL ERROR: {e}", severity="Critical"
            )
            return
        self.cameraPreviewWindow.createCamera(
            camNum=list(self.projectSettings.video_devices.values()).index(camera),
            camName=camera,
            fps=30,
            prevFPS=30,
            recFPS=30,
        )
        self.cameraPreviewWindow.show()

    def accept(self) -> None:
        box = self.projectSettings.getBoxFromId(self.boxNumberComboBox.currentText())
        if box is None:
            self.mainWin.messageBox(
                title="ERROR", text="Box not Found", severity="Critical"
            )
            return
        try:
            camera = self.projectSettings.video_devices[box.camera]
        except Exception as e:
            self.mainWin.messageBox(
                title="ERROR", text=f"FATAL ERROR: {e}", severity="Critical"
            )
            return
        self.signals.finished.emit(
            CameraWindow(
                parent=self.mainWin,
                camNum=list(self.projectSettings.video_devices.values()).index(camera),
                mainWin=self.mainWin,
                boxId=self.boxNumberComboBox.currentText(),
                animalId=self.animalIdComboBox.currentText(),
            ),
            int(self.boxNumberComboBox.currentText()),
            self.animalIdComboBox.currentText(),
        )
        super().accept()
