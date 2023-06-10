from PyQt6.QtCore import pyqtSignal, pyqtSlot, QMutex, QObject, QTimer, Qt
import datetime
import numpy as np
import time
import cv2
from queue import Queue


class vrSignals(QObject):
    """Defines the signals available from a running worker thread
    Supported signals are:
    finished: No data
    error: a string message and a bool whether this is worth printing to the log
    result:`object` data returned from processing, anything
    progress: `int` indicating % progress"""

    finished = pyqtSignal()
    error = pyqtSignal(str, bool)
    progress = pyqtSignal(str)
    frame = pyqtSignal(np.ndarray, bool)


class vidReader(QObject):
    """vidReader puts frame collection into the background, so frames from different cameras can be collected in parallel. this collects a single frame from a camera. status is a camStatus object, vc is a vc object (defined in camObj)"""

    def __init__(self, vc: QMutex):
        super(vidReader, self).__init__()
        self.signals = vrSignals()
        self.vc = vc
        self.lastFrame = []
        self.cameraName = self.vc.cameraName
        self.mspf = self.vc.mspf
        self.cont = self.vc.previewing or self.vc.recording
        self.startTime = datetime.datetime.now()  # time at beginning of reader
        self.lastTime = self.startTime  # time at beginning of last step
        self.dnow = self.startTime  # current time
        self.timeRec = 0  # time of video recorded
        self.timeElapsed = 0
        self.framesDropped = 0
        self.dt = 0
        self.sleepTime = 0

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
        frame = self.readFrame()  # read the frame
        if not self.cont:
            self.close()
            return
        self.sendNewFrame(frame)  # send back to window
        self.checkDrop(frame)  # check for dropped frames

    @pyqtSlot()
    def readFrame(self):
        """get a frame from the camera"""
        try:
            self.vc.lock()  # lock camera so only this thread can read frames
            frame = self.vc.readFrame()  # read frame
            mspf = self.vc.mspf  # update frame rate
            if not mspf == self.mspf:
                # update frame rate
                self.timer.stop()
                self.mspf = mspf
                self.timer.start(self.mspf)
            self.cont = self.vc.previewing or self.vc.recording  # whether to continue
            self.vc.unlock()  # unlock camera
        except Exception as e:
            if len(str(e)) > 0:
                self.signals.error.emit(f"Error collecting frame: {e}", True)
            if len(self.lastFrame) > 0:
                frame = self.lastFrame[0]
            else:
                self.signals.error.emit(f"Error collecting frame: no last frame", True)
                return
        else:
            self.lastFrame = [frame]
        return frame

    def sendFrame(self, frame: np.ndarray, pad: bool):
        """send a frame to the GUI"""
        self.signals.frame.emit(
            frame, pad
        )  # send the frame back to be displayed and recorded
        self.timeRec = self.timeRec + self.mspf / 1000  # keep track of time recorded

    def sendNewFrame(self, frame):
        """send a new frame back to the GUI"""
        self.sendFrame(frame, False)

    def checkDrop(self, frame):
        """check for dropped frames"""
        # check timing
        if not self.cont:
            return
        self.timeElapsed = (self.dnow - self.startTime).total_seconds()
        framesElapsed = int(
            np.floor((self.timeElapsed - self.timeRec) / (self.mspf / 1000))
        )

        if framesElapsed < 0:
            # not pausing enough. pause more next time
            self.dt = self.dt - 0.0005
        elif framesElapsed > 2:
            # if we've progressed at least 2 frames, fill that space with duplicate frames
            self.dt = self.dt + 0.0005  # pause less next time
            numfill = framesElapsed - 1
            for i in range(numfill):
                self.sendFrame(frame, True)

    def close(self):
        print("closing reader")
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        self.signals.finished.emit()


class prevSignals(QObject):
    """Defines the signals available from a running worker thread
    Supported signals are:
    finished: No data
    error: a string message and a bool whether this is worth printing to the log
    result:`object` data returned from processing, anything
    progress: `int` indicating % progress"""

    finished = pyqtSignal()
    error = pyqtSignal(str, bool)
    progress = pyqtSignal(str)
    frame = pyqtSignal(np.ndarray, bool)


class previewer(QObject):
    """previewer puts preview frame collection into the background, so frames from different cameras can be collected in parallel. vc is a vc object (defined in camObj)"""

    def __init__(self, vc: QMutex):
        super(previewer, self).__init__()
        self.signals = prevSignals()
        self.vc = vc
        self.lastFrame = []
        self.cameraName = self.vc.cameraName
        self.mspf = self.vc.prevmspf
        self.startTime = datetime.datetime.now()  # time at beginning of reader
        self.lastTime = self.startTime  # time at beginning of last step
        self.dnow = self.startTime  # current time
        self.timeRec = 0  # time of video recorded
        self.timeElapsed = 0
        self.framesDropped = 0
        self.dt = 0
        self.sleepTime = 0
        self.cont = True

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
        frame = self.readFrame()  # read the frame
        if not self.cont:
            self.close()
            return
        self.sendNewFrame(frame)  # send back to window

    @pyqtSlot()
    def readFrame(self):
        """get a frame from the camera"""
        try:
            self.vc.lock()  # lock camera so only this thread can read frames
            try:
                frame = self.vc.frame  # get the frame
            except Exception as e:
                frame = self.vc.readFrame()  # read frame
            mspf = self.vc.prevmspf  # update frame rate
            if not mspf == self.mspf:
                # update frame rate
                self.timer.stop()
                self.mspf = mspf
                self.timer.start(self.mspf)
            self.cont = self.vc.previewing  # whether to continue
            self.vc.unlock()  # unlock camera

        except Exception as e:
            if len(str(e)) > 0:
                self.signals.error.emit(f"Error collecting frame: {e}", True)
            if len(self.lastFrame) > 0:
                frame = self.lastFrame[0]
            else:
                self.signals.error.emit(f"Error collecting frame: no last frame", True)
                return
        else:
            self.lastFrame = [frame]
        return frame

    def sendFrame(self, frame: np.ndarray, pad: bool):
        """send a frame to the GUI"""
        if frame is None:
            return

        self.signals.frame.emit(
            frame, pad
        )  # send the frame back to be displayed and recorded

    def sendNewFrame(self, frame):
        """send a new frame back to the GUI"""
        self.sendFrame(frame, False)

    def close(self):
        print("closing reader")
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        self.signals.finished.emit()


class vwSignals(QObject):
    """Defines the signals available from a running worker thread
    Supported signals are:
    finished: No data
    error: a string message and a bool whether this is worth printing to the log
    result:`object` data returned from processing, anything
    progress: `int` indicating % progress"""

    finished = pyqtSignal()
    error = pyqtSignal(str, bool)
    progress = pyqtSignal(int)


class vidWriter(QObject):
    """The vidWriter creates a cv2.VideoWriter object at initialization, and it takes frames in the queue and writes them to file. This is a failsafe, so if the videowriter writes slower than the timer reads frames, then we can store those extra frames in memory until the vidWriter object can write them to the HD.
        https://www.pythonforthelab.com/blog/handling-and-sharing-data-between-threads/
    QRunnables run in the background. Trying to directly modify the GUI display from inside the QRunnable will make everything catastrophically slow, but you can pass messages back to the GUI using vrSignals.
    """

    def __init__(self, fn: str, vidvars: dict, frames: Queue):
        super(vidWriter, self).__init__()
        self.vFilename = fn
        self.recFPS = vidvars["recFPS"]
        self.recSPF = 1 / self.recFPS
        self.vw = cv2.VideoWriter(
            fn, vidvars["fourcc"], self.recFPS, (vidvars["imw"], vidvars["imh"])
        )
        self.saveFreq = int(
            round(vidvars["fps"] / self.recFPS)
        )  # save 1/this value of the frames fed into the queue
        self.signals = vwSignals()
        self.frames = frames
        self.vidvars = vidvars
        self.recording = True

        self.kill = False
        self.readFrames = 0  # total number of frames read
        self.recTime = 0

    @pyqtSlot()
    def run(self) -> None:
        """this loops until we receive a frame that is a string
        the save function will pass None to the frame queue when we are done recording
        """
        printFreq = 100

        while True:
            if self.kill:
                return
            time.sleep(1)
            # this gives the GUI enough time to start adding frames before we start saving, otherwise we get stuck in infinite loop where it's immediately checking again and again if there are frames
            while not self.frames.empty():
                # remove the first frame once it's written
                f = self.frames.get()
                frame = f[0]
                recTime = f[1]
                if frame is None:
                    # if this frame is a string, the video reader is done, and it's sent us a signal to stop
                    # we use this explicit signal instead of just stopping when the frame list is empty, just in case the writer is faster than the reader and manages to empty the queue before we're done reading frames
                    self.vw.release()
                    self.signals.finished.emit()
                    return

                self.readFrames += 1
                if (
                    self.readFrames % self.saveFreq == 0
                    and self.recTime < recTime + 2 * self.recSPF
                ) or (self.recTime < recTime - 2 * self.recSPF):
                    # on every saveFreqth frame, write to file
                    # don't write if we're over time, and write extra if we're under time
                    self.vw.write(frame)
                    self.recTime += self.recSPF

                size = int(self.frames.qsize())
                if size % printFreq == 1:
                    # on every 100th frame, tell the GUI how many frames we still have to write
                    self.signals.progress.emit(size)

    def close(self) -> None:
        """stop writing"""
        print("closing writer")
        self.kill = True
