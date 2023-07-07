import datetime
import os
import sys
from queue import Queue
from typing import Dict, List

import cv2
import numpy as np
from PyQt6.QtCore import QMutex, QObject, Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
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

from RVM.camera.camThreads import previewer, vidReader, vidWriter


class VideoCaptureSignals(QObject):
    status = pyqtSignal(str, bool)


class VideoCapture(QMutex):
    """holds the videoCapture object and surrounding functions"""

    def __init__(
        self, camNum: int, cameraName: str, fps: int, prevFPS: int, recFPS: int
    ):
        super(VideoCapture, self).__init__()
        # this is to get around some weirdness with the QMutex ids
        # TODO: test if this is still necessary MIGHT NOT BE
        self._id = id(self)
        self.camNum = camNum
        self.cameraName = cameraName
        self.signals = VideoCaptureSignals()
        self.connected = False
        self.previewing = False  # is the live preview on?
        self.recording = False  # are we collecting frames for a video?
        self.writing = False  # are we writing video frames to file?
        self.updateFPS(fps)
        self.updatePrevFPS(prevFPS)

    @property
    def id(self):
        return self._id

    def updateStatus(self, msg: str, log: bool = False):
        """update the status bar by sending a signal"""
        print(msg)
        self.signals.status.emit(str(msg), log)

    def updateFPS(self, fps):
        print(f"updating fps to {fps}")
        self.fps = fps
        self.mspf = int(round(1000.0 / self.fps))

    def updatePrevFPS(self, prevFPS):
        self.previewFPS = prevFPS
        self.prevmspf = int(round(1000.0 / self.previewFPS))
        print(f"updating preview fps to {self.previewFPS}")

    def connectVC(self):
        try:
            self.camDevice = cv2.VideoCapture(self.camNum, cv2.CAP_DSHOW)
            self.camDevice.set(
                cv2.CAP_PROP_BUFFERSIZE, 1
            )  # limit buffer size to one frame
            # set the fourcc to MJPG
            # self.camDevice.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        except Exception as e:
            self.updateStatus(f"Failed connect to {self.cameraName}: {e}")
            self.connected = False
            return
        else:
            self.connected = True
        self.imw = int(self.camDevice.get(3))  # image width (px)
        self.imh = int(self.camDevice.get(4))  # image height (px)

    def getFrameRate(self) -> float:
        """Determine the native device frame rate"""
        if self.camDevice is None:
            self.updateStatus(
                f"Cannot get frame rate from {self.cameraName}: device not connected",
                True,
            )
            return 0
        fps = self.camDevice.get(cv2.CAP_PROP_FPS) / 2  # frames per second
        if fps > 0:
            return int(fps)
        else:
            self.updateStatus(
                f"Invalid auto frame rate returned from {self.cameraName}: {fps}", True
            )
            return 0

    @pyqtSlot()
    def readFrame(self):
        """Get a frame from the webcam using cv2.VideoCapture.read()"""
        try:
            rval, frame = self.camDevice.read()
        except:
            self.updateStatus("Error reading frame", True)

        if not rval:
            self.updateStatus("Error reading frame", True)

        else:
            self.frame = frame
            return frame

    def closeVC(self):
        """Close the webcam device"""
        try:
            if self.camDevice is not None:
                self.camDevice.release()
            else:
                self.updateStatus(
                    f"Cannot close {self.cameraName}: device not connected", True
                )
        except:
            self.updateStatus(f"Error closing {self.cameraName}", True)
        else:
            self.updateStatus(f"{self.cameraName} closed", True)
            self.connected = False


class CameraSignals(QObject):
    finishedClose = pyqtSignal()
    finishedOpen = pyqtSignal()


class VideoDisplay(QLabel):
    """A QLabel where we always repaint the most recent frame"""

    def __init__(self, parent=None):
        super(VideoDisplay, self).__init__(parent)

    def paintEvent(self, event):
        if self.pixmap() is not None:
            self.setPixmap(self.pixmap())
        super(VideoDisplay, self).paintEvent(event)

    def update(self):
        self.repaint()


class Camera(QObject):
    """A VideoCapture object that reads frames from a webcam, and has methods for recording and previewing.

    Frames are read by a separate thread, and stored in a queue. The queue is read by the preview thread and the recording thread AND ONLY CLEARED BY THE RECORDING THREAD.

    Parameters
    ----------
    camNum : int
        The camera number, as returned by cv2.VideoCapture(camNum)
    camName : str
        The camera name, as returned by cv2.VideoCapture(camNum)
    saveFolder : str
        The folder where videos are saved
    fps : int
        The frame rate of the camera
    prevFPS : int
        The frame rate of the preview
    recFPS : int
        The frame rate of the recording
    guiWin : QMainWindow
        The main window of the GUI

    Note
    ----
    - Reading frames from a webcam is a blocking operation, so we need to run it in a separate thread.
    - Reading frames requires that the queue be locked, so we need to use a QMutex.

    """

    def __init__(
        self,
        camNum: int,
        camName: str,
        saveFolder: str,
        fps: int,
        prevFPS: int,
        recFPS: int,
        guiWin: QMainWindow,
        boxId: int,
        animalId: int,
    ):
        super(Camera, self).__init__()
        self.guiWin = guiWin
        self.signals = CameraSignals()
        self.camNum = camNum
        self.camName = camName
        self.fps = fps
        self.prevFPS = prevFPS
        self.recFPS = recFPS

        # TEMPORARY
        self.boxId = boxId
        self.animalId = animalId

        self.readerRunning = False
        self.prevRunning = False
        self.previewing = False
        self.recording = False
        self.writing = False
        self.reader = None
        self.deviceOpen = False
        self.frames = Queue()
        self.framesSincePrev = 0
        self.prevWindow = VideoDisplay()
        self.fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")
        self.mspf = int(round(1000.0 / self.fps))

        self.ext = ".avi"

        if not os.path.isdir(saveFolder):
            self.saveFolder = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            self.saveFolder = saveFolder
        self.resetVidStats()

        self.vc = None

    def createVC(self):
        """Create a VideoCapture object"""
        self.vc = VideoCapture(
            self.camNum, self.camName, self.fps, self.prevFPS, self.recFPS
        )
        self.vc.connectVC()
        self.deviceOpen = self.vc.connected
        return self.deviceOpen

    def resetVidStats(self) -> None:
        """Reset video stats, to start a new video"""
        self.startTime = 0  # the time when we started the video
        self.timeRec = 0  # how long the video is
        self.framesDropped = 0  # how many frames we've dropped
        self.totalFrames = 0  # how many frames are in the video
        self.fleft = 0  # how many frames we still need to write to file
        with self.frames.mutex:
            self.frames.queue.clear()
        self.lastFrame = (
            []
        )  # last frame collected. kept in a list of one cv2 frame to make it easier to pass between functions
        self.startTime = datetime.datetime.now()
        self.lastTime = self.startTime
        self.fnum = 0
        self.rids = []  # vidReader ids

    def startPreview(self) -> None:
        """Start live preview"""
        # critFramesToPrev reduces the live display frame rate,
        # so only have to update the display at a comfortable viewing rate.
        # if the camera is at 200 fps, the video will be saved at full rate but
        # preview will only show at 15 fps
        if not self.deviceOpen:
            self.updateStatus(f"Opening {self.camName} preview...")
            self.createVC()

        self.updateFramesToPrev()
        self.previewing = True
        self.vc.lock()
        self.vc.previewing = True
        self.vc.unlock()
        self.startReader()  # this only starts the reader if we're not already recording
        self.startPreviewer()

    def startRecording(self) -> None:
        """start recording a video"""
        if not self.deviceOpen:
            self.updateStatus(f"Opening {self.camName} preview...")
            self.createVC()
        if self.writing:
            if not self.writeWarning:
                self.writeWarning = True
            QTimer.singleShot(50, self.startRecording)  # stop previewing and recording
        else:
            self.createWriter()

    def startReader(self) -> None:
        """start updating preview or recording"""
        if not self.readerRunning:
            self.readerRunning = True
            # if self.diag>1:
            #     logging.debug(f'Starting {self.cameraName} reader')

            # https://realpython.com/python-pyqt-qthread/
            self.readThread = QThread()
            # Step 3: Create a worker object
            self.readWorker = vidReader(
                self.vc
            )  # creates a new thread to read frames to GUI
            # Step 4: Move worker to the thread
            self.readWorker.moveToThread(self.readThread)
            # Step 5: Connect signals and slots
            self.readThread.started.connect(self.readWorker.run)
            self.readWorker.signals.finished.connect(self.readThread.quit)
            self.readWorker.signals.finished.connect(self.readWorker.deleteLater)
            self.readThread.finished.connect(self.readWorker.close)
            self.readThread.finished.connect(self.readThread.deleteLater)
            self.readWorker.signals.error.connect(self.updateStatus)
            self.readWorker.signals.frame.connect(self.receiveRecFrame)
            self.readWorker.signals.progress.connect(self.printDiagnostics)
            # Step 6: Start the thread
            self.readThread.start()
            print("start reader")

    def startPreviewer(self) -> None:
        """start updating preview"""
        if not self.prevRunning:
            self.prevRunning = True
            # if self.diag>1:
            #     logging.debug(f'Starting {self.cameraName} reader')

            # https://realpython.com/python-pyqt-qthread/
            self.prevThread = QThread()
            # Step 3: Create a worker object
            self.prevWorker = previewer(
                self.vc
            )  # creates a new thread to read frames to GUI
            # Step 4: Move worker to the thread
            self.prevWorker.moveToThread(self.prevThread)
            # Step 5: Connect signals and slots
            self.prevThread.started.connect(self.prevWorker.run)
            self.prevWorker.signals.finished.connect(self.prevThread.quit)
            self.prevWorker.signals.finished.connect(self.prevWorker.deleteLater)
            self.prevThread.finished.connect(self.prevWorker.close)
            self.prevThread.finished.connect(self.prevThread.deleteLater)
            self.prevWorker.signals.error.connect(self.updateStatus)
            self.prevWorker.signals.frame.connect(self.receivePrevFrame)
            self.prevWorker.signals.progress.connect(self.printDiagnostics)
            self.prevThread.start()
            print("starting previewer")

    def getFilename(self) -> str:
        """determine the file name for the file we're about to record."""

        try:
            self.saveFolder = str(self.saveFolder)
            if not os.path.exists(self.saveFolder):
                os.makedirs(self.saveFolder)
            print(f"save folder: {self.saveFolder}")
            # datetime.datetime.now format as YYYY-MM-DD_HHMMSS
            fn = (
                os.path.abspath(self.saveFolder)
                + os.sep
                + str(self.animalId)
                + "_"
                + "BOX"
                + str(self.boxId)
                + "_"
                + datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                + self.ext
            )
            fullfn = os.path.abspath(fn)
            if os.path.exists(fullfn):
                # TODO: add a dialog warning system for overwriting files
                print(f"File {fullfn} already exists. Will overwrite.")
            return fullfn
        except Exception as e:
            print(f"Error getting filename: {e}")
            return "UNKNOWN"

    def createWriter(self) -> None:
        """create a videoWriter object"""
        self.writeWarning = False
        self.recording = True
        self.writing = True
        self.vc.lock()
        self.vc.recording = True
        self.vc.writing = True
        self.vc.unlock()
        self.resetVidStats()  # this resets the frame list, and other vars
        fn = self.getFilename()  # generate a new file name for this video
        self.vFilename = fn
        vidvars = {
            "fourcc": self.fourcc,
            "fps": self.fps,
            "recFPS": self.recFPS,
            "imw": self.vc.imw,
            "imh": self.vc.imh,
            "cameraName": self.camName,
        }
        print(f"Creating video file {fn}")
        self.writeThread = QThread()
        self.writeWorker = vidWriter(
            fn, vidvars, self.frames
        )  # creates a new thread to write frames to file

        self.writeWorker.moveToThread(self.writeThread)
        self.writeThread.started.connect(self.writeWorker.run)
        self.writeWorker.signals.finished.connect(self.writeThread.quit)
        self.writeWorker.signals.finished.connect(self.writeWorker.deleteLater)
        self.writeThread.finished.connect(self.writeThread.deleteLater)
        self.writeWorker.signals.finished.connect(self.doneRecording)
        self.writeWorker.signals.progress.connect(self.writingRecording)
        self.writeWorker.signals.error.connect(self.updateStatus)
        self.writeThread.start()

        self.updateStatus(f"Recording {self.vFilename} ... ", True)
        # QThreadPool.globalInstance().start(recthread)          # start writing in a background thread
        self.startReader()  # this only starts the reader if we're not already previewing

    def setFrameRate(self, fps: float) -> int:
        """Set the frame rate of the camera.

        Parameters
        ----------
        fps : float
            The desired frame rate.

        Returns
        -------
        int
            0 if successful, 1 if not.
        """
        if self.recording:
            print("Cannot change frame rate while recording.")
            return

        if self.fps == fps:
            return 1
        else:
            self.fps = fps
            self.mspf = int(round(1000.0 / self.fps))  # ms per frame
            self.updateFramesToPrev()  # update the preview downsample rate
            if hasattr(self, "vc"):
                # update the vc object
                self.vc.lock()
                self.vc.updateFPS(self.fps)
                self.vc.unlock()
            return 0

    def saveFrame(self, frame: np.ndarray) -> None:
        """Save the frame to the video file.

        Parameters
        ----------
        frame : np.ndarray
            The frame to save
        """
        if not self.recording:
            return

        try:
            self.frames.put(
                [frame, self.timeRec]
            )  # add the frame to the queue that videoWriter is watching
        except:
            # stop recording if we can't write
            self.updateStatus(f"Error writing to video", True)
        else:
            # display the time recorded
            self.timeRec = self.timeRec + self.mspf / 1000
            self.totalFrames += 1

    def updateFramesToPrev(self):
        """Calculate the number of frames to downsample for preview"""
        self.critFramesToPrev = max(round(self.fps / self.prevFPS), 1)
        self.framesSincePrev = self.critFramesToPrev

    def updatePrevWindow(self, frame: np.ndarray) -> None:
        """Update the display with the new pixmap"""
        image = QImage(
            frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888
        ).rgbSwapped()
        self.prevWindow.setPixmap(QPixmap.fromImage(image))
        self.prevWindow.update()

    def updatePrevFrame(self, frame: np.ndarray) -> None:
        """Update the live preview window"""
        # update the preview
        if not self.previewing:
            return
        if type(frame) == np.ndarray:
            self.framesSincePrev = 1
            # convert frame to pixmap in separate thread and update window when done
            self.updatePrevWindow(frame)
        else:
            self.updateStatus(f"Frame is empty", True)

    @pyqtSlot(np.ndarray, bool)
    # def receiveFrame(self, frame:np.ndarray, frameNum:int, vrid:int, checkDrop:bool=True):
    def receiveRecFrame(self, frame: np.ndarray, pad: bool):
        """Receive a frame from the vidReader thread.

        Parameters
        ----------
        frame : np.ndarray
            The frame to be displayed.
        pad : bool
            Whether the frame is a filler frame.
        """

        self.lastFrame = [frame]
        self.saveFrame(frame)  # save to file
        if pad:
            self.framesDropped += 1

    @pyqtSlot(int)
    def writingRecording(self, fleft: int) -> None:
        """Updates the status to say that the video is still being saved.

        Parameters
        ----------
        fleft : int
            Number of frames left to write.
        """

        if not self.recording:
            self.fleft = fleft
            self.updateRecordStatus()

    @pyqtSlot()
    def doneRecording(self) -> None:
        """update the status box when we're done recording"""
        self.writing = False
        self.vc.lock()
        self.vc.writing = False
        self.vc.unlock()
        self.updateRecordStatus()

    @pyqtSlot(np.ndarray, bool)
    def receivePrevFrame(self, frame: np.ndarray, pad: bool):
        """receive a frame from the vidReader thread. pad indicates whether the frame is a filler frame"""
        self.lastFrame = [frame]
        self.updatePrevFrame(frame)  # update the preview window

    def stopReader(self) -> None:
        """this only stops the reader if we are neither recording nor previewing"""
        if not self.recording and not self.previewing and self.readerRunning:
            self.readerRunning = False

    def stopRecording(self) -> None:
        """stop collecting frames for the video"""
        if not self.recording:
            return
        self.frames.put(
            [None, 0]
        )  # this tells the vidWriter that this is the end of the video
        self.recording = False
        if hasattr(self, "vc"):
            self.vc.lock()
            self.vc.recording = False  # this helps the frame reader and the status update know we're not reading frames
            self.vc.unlock()
        self.stopReader()  # only turns off the reader if we're not recording or previewing

    def stopPreviewer(self) -> None:
        if not self.recording and not self.previewing and self.prevRunning:
            self.prevRunning = False

    def stopPreview(self) -> None:
        """stop live preview. This freezes the last frame on the screen."""
        self.previewing = False
        if hasattr(self, "vc"):
            self.vc.lock()
            self.vc.previewing = False
            self.vc.unlock()
        self.stopReader()  # this only stops the reader if we are neither recording nor previewing
        self.stopPreviewer()

    @pyqtSlot(str, bool)
    def updateStatus(self, st: str, log: bool = False) -> None:
        """updates the status"""
        print(st)
        # send the status to the status bar
        try:
            self.guiWin.statusBar.showMessage(st)
        except:
            pass

    def printDiagnostics(self, st: str) -> None:
        """prints diagnostics"""
        print(st)

    def updateRecordStatus(self) -> None:
        """updates the status bar during recording and during save.
        We turn off logging because this updates so frequently that we would flood the log with updates.
        """
        log = False
        if self.recording:
            s = "Recording "
        elif self.writing:
            s = "Writing "
        else:
            s = "Recorded "
            log = True
        saveFreq = int(round(self.fps / self.recFPS))
        s += f"{self.vFilename} {self.timeRec:2.2f} s, "
        if self.writing and not self.recording:
            s += f"{int(np.floor(self.fleft/saveFreq))}/{int(np.floor(self.totalFrames/saveFreq))} frames left"
        else:
            s += f"{int(np.floor(self.framesDropped/saveFreq))}/{int(np.floor(self.totalFrames/saveFreq))} frames dropped"
        self.updateStatus(s, log)

    def closeCam(self) -> None:
        """disconnect from the camera when the window is closed"""
        self.signals.finishedClose.connect(self.finishClose)
        if self.previewing:
            self.stopPreview()
        if self.recording:
            self.stopRecording()
        if hasattr(self, "vc") and self.vc is not None:
            self.vc.lock()
            self.vc.recording = False
            self.vc.previewing = False
            self.vc.unlock()
        self.signals.finishedClose.emit()

    def close(self) -> None:
        """this gets triggered when the whole window is closed. Disconnects from the cameras and deletes videoCapture objects"""
        self.closeCam()  # tell reader to stop

    def finishClose(self) -> None:
        """finish closing the camera"""
        if hasattr(self, "vc") and self.vc is not None:
            self.vc.closeVC()
            self.vc = None
        self.deleteLater()
