"""
########################## W.I.P. NOT FUNCTIONAL ##########################
commiting to use on other computer

this is a temp widget that will be replaced later with a more comprehensive solution. Needed for immediate lab use so please ignore the mess - Daniel will fix soon

There is nothing more permanent than a temporary solution ;)

TODO: create a mutex that will hold the cv2 capture and helper methods (i.e. a modified VideoCapture class), then extend the video player to be the thread that reads from the mutex, then the widget will be the gui that controls the video player thread. The tdt readers will be a class the gui uses to get timestamp and recording data. 
"""

import os
from PyQt6 import QtCore, QtGui, QtWidgets
from RVM.camera.camThreads import vidAnalysis, vidReader, previewer
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenuBar,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
from PyQt6.QtCore import QMutex, QObject, Qt, QThread, QTimer, pyqtSignal, pyqtSlot
import cv2
import datetime


class videoPlayerSignals(QObject):
    frame = pyqtSignal(np.ndarray)


class videoPlayer(QObject):
    """thread for playing videos"""

    def __init__(self, vc, fps, parent=None):
        super(videoPlayer, self).__init__()
        self.signals = videoPlayerSignals()
        self.vc = vc
        self.mutex = QMutex()
        self.running = False
        self.paused = False
        self.frame = None
        self.frameRate = fps
        self.frameCount = 0
        self.frameCountMax = int(self.vc.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frameCountMin = 0
        self.frameCountStep = 1
        self.frameCountStepMax = 100
        self.frameCountStepMin = 1
        self.frameCountStep = 1
        self.mspf = int(1000 / self.frameRate)
        self.startTime = datetime.datetime.now()
        self.dnow = self.startTime
        self.lastFrame = []
        self.cont = True
        self.run()

    @pyqtSlot()
    def run(self) -> None:
        """Run this function when this thread is started. Collect a frame and return to the gui"""

        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.start(self.mspf)
        self.timerRunning = True

    def loop(self):
        """run this on each loop iteration"""
        self.lastTime = self.dnow
        self.dnow = datetime.datetime.now()
        if self.paused:
            return
        frame = self.readFrame()  # read the frame
        # emit the frame
        if frame is not None:
            self.sendFrame(frame)
        else:
            print("no frame")

    @pyqtSlot()
    def readFrame(self):
        """get a frame from the camera"""
        try:
            # lock the mutex
            self.mutex.lock()
            # read the frame
            frame = self.vc.read()[1]
            # increment the frame count
            self.frameCount = self.frameCount + self.frameCountStep
        except Exception as e:
            if len(str(e)) > 0:
                print(f"Error collecting frame: {e}", True)
            if len(self.lastFrame) > 0:
                frame = self.lastFrame[0]
            else:
                print(f"Error collecting frame: no last frame", True)
                return
        else:
            self.lastFrame = [frame]
        return frame

    def seek(self, frameCount):
        """seek to a specific frame"""
        self.frameCount = self.frameCount + frameCount
        if self.frameCount < self.frameCountMin:
            self.frameCount = self.frameCountMin
        if self.frameCount > self.frameCountMax:
            self.frameCount = self.frameCountMax

        assert (
            self.frameCount >= self.frameCountMin
            and self.frameCount <= self.frameCountMax
        ), "frame count out of bounds"

        self.vc.set(cv2.CAP_PROP_POS_FRAMES, self.frameCount)
        frame = self.readFrame()
        if frame is not None:
            self.sendFrame(frame)

    def sendFrame(self, frame):
        """send the frame to the gui"""
        self.signals.frame.emit(frame)

    def stop(self):
        """stop the thread"""
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        self.running = False
        self.timerRunning = False
        self.vc.release()


class VideoScoringWidget(QtWidgets.QMainWindow):
    """widget for scoring videos"""

    def __init__(self, mainWin=None, parent=None):
        super().__init__(parent)
        self.mainWin = mainWin
        self.playerThread = None
        self.setWindowTitle("Video Scoring")
        self.setWindowIcon(
            QtGui.QIcon(os.path.join(self.mainWin.iconsDir, "..", "logo.png"))
        )
        # central widget is a Qlabel
        self.prevWindow = QtWidgets.QLabel()
        self.prevWindow.setScaledContents(True)
        self.prevWindow.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.prevWindow.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(QtWidgets.QVBoxLayout())
        self.centralWidget.layout().addWidget(self.prevWindow)

        self.cap = cv2.VideoCapture(
            r"H:\D-E mice Recording Backup\FiPho-230208\d91\FiPho-230208_d91_Cam1.avi"
        )
        self.playerWorker = videoPlayer(self.cap, fps=self.cap.get(cv2.CAP_PROP_FPS))
        self.resize(
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        # play button
        self.played = False
        self.playButton = QtWidgets.QPushButton("Play")
        self.playButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.playButton.clicked.connect(self.playVideo)
        self.centralWidget.layout().addWidget(self.playButton)

        self.show()

    def updatePrevWindow(self, frame: np.ndarray, *args, **kwargs) -> None:
        """Update the display with the new pixmap"""
        image = QImage(
            frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888
        ).rgbSwapped()
        self.prevWindow.setPixmap(QPixmap.fromImage(image))

    def playVideo(self):
        """play the video"""
        if self.played:
            return
        self.playerThread = QThread()
        self.playerWorker.signals.frame.connect(self.updatePrevWindow)
        self.playerWorker.moveToThread(self.playerThread)
        self.playerThread.started.connect(self.playerWorker.run)
        self.playerThread.start()
        self.played = True

    # override the key press event
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Space:
            self.playerWorker.paused = not self.playerWorker.paused
        elif event.key() == QtCore.Qt.Key.Key_Left:
            self.playerWorker.seek(-10)
        elif event.key() == QtCore.Qt.Key.Key_Right:
            self.playerWorker.seek(10)

    def toggleViewAction(self):
        """toggle the view action"""
        # minimize the window if it is not minimized
        if self.isMinimized():
            self.showNormal()

    def closeEvent(self, event):
        """close the camera when the window is closed"""
        self.playerWorker.stop()
        if self.playerThread is not None and self.playerThread.isRunning():
            self.playerThread.quit()
            self.playerThread.wait()
        self.cap.release()
        event.accept()
