# a base camera class for all cameras
from PyQt6.QtCore import QObject, pyqtSignal, QMutex


class vcSignals(QObject):
    status = pyqtSignal(str,bool)

class vc(QMutex):
    """the videoCapture object and surrounding functions"""
    
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

class Camera(object):
    """
    A base camera class with a queue to store frames and methods to preview and record video.

    """
    