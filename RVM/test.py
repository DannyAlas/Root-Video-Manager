from re import T
import typing
from PyQt6 import QtCore
import cv2
from PyQt6.QtCore import QObject, pyqtSignal, QMutex, pyqtSlot, QTimer, Qt, QThread
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
import sys
import numpy as np
import datetime

class vcSignals(QObject):
    status = pyqtSignal(str,bool)
    
class vc(QMutex):
    '''holds the videoCapture object and surrounding functions'''
    
    def __init__(self, cameraName:str, diag:int, fps:int, prevFPS:int, recFPS:int):
        super(vc,self).__init__()
        self.cameraName = cameraName
        self.signals = vcSignals()
        self.diag = diag
        self.connected = False
        self.previewing = False                   # is the live preview on?
        self.recording = False                    # are we collecting frames for a video?
        self.writing = False                       # are we writing video frames to file?
        self.updateFPS(fps)
        self.updatePrevFPS(prevFPS)
        
    def updateStatus(self, msg:str, log:bool):
        '''update the status bar by sending a signal'''
        self.signals.status.emit(str(msg), log)
        
    def updateFPS(self, fps):
        self.fps = fps
        self.mspf = int(round(1000./self.fps))
        
    def updatePrevFPS(self, prevFPS):
        self.previewFPS = prevFPS
        self.prevmspf = int(round(1000./self.previewFPS))

class webcamVC(vc):
    '''holds a videoCapture object that reads frames from a webcam. lock this so only one thread can collect frames at a time'''
    
    def __init__(self, webcamNum:int, cameraName:str, width:int, height:int, fps:int, prevFPS:int, recFPS:int):
        super(webcamVC,self).__init__(cameraName, 0, fps, prevFPS, recFPS)
        self.webcamNum = webcamNum
        self.width = width
        self.height = height
        self.previewing = True
        self.connectVC()

    def connectVC(self):
        try:
            self.camDevice = cv2.VideoCapture(self.webcamNum, cv2.CAP_DSHOW)
            self.camDevice.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # limit buffer size to one frame
            # set the resolution
            self.camDevice.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camDevice.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        except Exception as e:
            self.updateStatus(f'Failed connect to {self.cameraName}: {e}')
            self.connected = False
            return
        else:
            self.connected = True
        self.imw = int(self.camDevice.get(3))               # image width (px)
        self.imh = int(self.camDevice.get(4))               # image height (px)
            
    def getFrameRate(self) -> float:
        '''Determine the native device frame rate'''
        fps = self.camDevice.get(cv2.CAP_PROP_FPS)/2 # frames per second
        if fps>0:
            return int(fps)
        else:
            self.updateStatus(f'Invalid auto frame rate returned from {self.cameraName}: {fps}', True)
            return 0

    def getExposure(self):
        '''Read the current exposure on the camera'''
        return 1000*2**self.camDevice.get(cv2.CAP_PROP_EXPOSURE)
    
    def readFrame(self):
        '''get a frame from the webcam using cv2 '''
        try:
            rval, frame = self.camDevice.read()
        except:
            self.updateStatus('Error reading frame', True)
            raise ValueError('Error reading frame')
        if not rval:
            self.updateStatus('Error reading frame', True)
            raise ValueError('Error reading frame')
        else:
            self.frame = frame
            return frame
        
        # return np.zeros((self.imh, self.imw, 3), dtype='uint8')

    def close(self):
        '''close the videocapture object'''
        if hasattr(self, 'camDevice') and not self.camDevice==None:
            try:
                self.camDevice.release()
            except Exception as e:
                self.updateStatus(f'Failed to release cam device for {self.cameraName}: {e}')
                pass

class prevSignals(QObject):
    '''Defines the signals available from a running worker thread
        Supported signals are:
        finished: No data
        error: a string message and a bool whether this is worth printing to the log
        result:`object` data returned from processing, anything
        progress: `int` indicating % progress '''
    
    finished = pyqtSignal()
    error = pyqtSignal(str, bool)
    progress = pyqtSignal(str)
    frame = pyqtSignal(np.ndarray, bool)

            
class previewer(QObject):
    '''previewer puts preview frame collection into the background, so frames from different cameras can be collected in parallel. vc is a vc object (defined in camObj)'''
    
    def __init__(self, vc:QMutex):
        super(previewer, self).__init__()
        self.signals = prevSignals()
        self.vc = vc
        self.lastFrame = []
        self.cameraName = self.vc.cameraName
        self.diag = self.vc.diag
        self.mspf = self.vc.prevmspf
        self.startTime = datetime.datetime.now()  # time at beginning of reader
        self.lastTime = self.startTime   # time at beginning of last step
        self.dnow = self.startTime   # current time
        self.timeRec = 0             # time of video recorded
        self.timeElapsed = 0
        self.framesDropped = 0
        self.dt = 0
        self.sleepTime = 0
        self.cont=True

        
    @pyqtSlot()    
    def run(self) -> None:
        '''Run this function when this thread is started. Collect a frame and return to the gui'''
        if self.diag>1:
            # if we're in super debug mode, print header for the table of frames
            self.signals.progress.emit('Camera name\t\tFrame t\tTotal t\tRec t\tSleep t\tAdj t')

        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.start(self.mspf)
        self.timerRunning = True
                
    def loop(self):
        '''run this on each loop iteration'''
        self.lastTime = self.dnow
        self.dnow = datetime.datetime.now()
        frame = self.readFrame()  # read the frame
        if not self.cont:
            self.timer.stop()
            self.signals.finished.emit()
            return
        self.sendNewFrame(frame) # send back to window

    @pyqtSlot()
    def readFrame(self):
        '''get a frame from the camera'''
        try:
            self.vc.lock()     # lock camera so only this thread can read frames
            frame = self.vc.readFrame() # read the frame
            
            mspf = self.vc.prevmspf    # update frame rate
            if not mspf==self.mspf:
                # update frame rate
                self.timer.stop()
                self.mspf = mspf
                self.timer.start(self.mspf)
            self.diag = self.vc.diag    # update logging
            self.cont = self.vc.previewing    # update continue flag
            self.vc.unlock()   # unlock camera
        except Exception as e:
            if len(str(e))>0:
                self.signals.error.emit(f'Error collecting frame: {e}', True)
            if len(self.lastFrame)>0:
                frame = self.lastFrame[0]
            else:
                self.signals.error.emit(f'Error collecting frame: no last frame', True)
                return
        else:
            self.lastFrame = [frame]
        return frame
    
    def sendFrame(self, frame:np.ndarray, pad:bool):
        '''send a frame to the GUI'''
        
        self.signals.frame.emit(frame, pad)  # send the frame back to be displayed and recorded
        
    def sendNewFrame(self, frame):
        '''send a new frame back to the GUI'''
        self.sendFrame(frame, False)
                    
    def close(self):
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        self.cont = False
        
        self.signals.finished.emit()

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Camera Preview'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.cameras = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)        
        self.statusBar().showMessage('Ready')
        self.createPreviewer()

        self.show()

    def createPreviewer(self):
        """Camera previewer"""
        # camera previewer window
        self.preview = QLabel(self)
        self.preview.resize(1920, 1080)
        self.preview.move(0,0)
        self.preview.setScaledContents(True)
        self.preview.show()

        # camera previewer thread
        self.previewThread = QThread()
        self.previewThread.start()
        self.cameras.append(webcamVC(0, 'cam1', 1920, 1080, 30, 30, 30))
        self.previewer = previewer(self.cameras[0])
        self.previewer.moveToThread(self.previewThread)
        self.previewer.signals.frame.connect(self.updatePreview)
        self.previewer.signals.error.connect(self.updateStatus)
        self.previewer.signals.progress.connect(self.updateStatus)
        self.previewer.signals.finished.connect(self.previewThread.quit)
        self.previewer.signals.finished.connect(self.previewer.deleteLater)
        self.previewer.signals.finished.connect(self.previewThread.deleteLater)
        self.previewer.run()

    def updatePreview(self, frame, pad):
        """Update the preview window"""
        if pad:
            frame = cv2.copyMakeBorder(frame, 0, 0, 0, 0, cv2.BORDER_CONSTANT, value=[0,0,0])
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
        self.preview.setPixmap(QPixmap.fromImage(frame))

    def updateStatus(self, msg, error=False):
        """Update the status bar"""
        if error:
            self.statusBar().setStyleSheet('color: red')
        else:
            self.statusBar().setStyleSheet('color: black')
        self.statusBar().showMessage(msg)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())