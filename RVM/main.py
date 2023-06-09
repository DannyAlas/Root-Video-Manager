from PyQt6 import QtCore, QtGui, QtWidgets
from threading import Thread
from collections import deque
import time
import sys
import cv2
from camera import CameraDockWidget

class MainWinodw(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWinodw, self).__init__()
        self.setWindowTitle('Camera GUI')
        self.setGeometry(0, 0, 1280, 720)
        self.camera_dockwidgets = []
        
        self.initUI()
        
    def initUI(self):
        # create toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        # create exit action
        exit_action = QtWidgets.QWidgetAction(self)
        exit_action.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton))
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setToolTip('Exit application')
        exit_action.triggered.connect(self.close)
        self.toolbar.addAction(exit_action)
        # create fullscreen action
        fullscreen_action = QtWidgets.QWidgetAction(self)
        fullscreen_action.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton))
        fullscreen_action.setShortcut('Ctrl+F')
        fullscreen_action.setToolTip('Toggle fullscreen')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.toolbar.addAction(fullscreen_action)
        # create camera grabber action
        camera_grabber_action = QtWidgets.QWidgetAction(self)
        camera_grabber_action.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        camera_grabber_action.setShortcut('Ctrl+O')
        camera_grabber_action.setToolTip('Open camera grabber')
        camera_grabber_action.triggered.connect(self.cameraGetterFactory)
        self.toolbar.addAction(camera_grabber_action)


        # create a layout
        self.layout = QtWidgets.QVBoxLayout()

        # create a central widget
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
       
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def cameraGetterFactory(self):
        # create a new thread to get cameras
        QtCore.QThread.currentThread().setObjectName('main')
        self.thread = QtCore.QThread()
        self.cameraGetter = CameraGetter()
        self.cameraGetter.moveToThread(self.thread)
        self.thread.started.connect(self.cameraGetter.getCameras)
        # get the list from the signal
        self.cameraGetter.cameras.connect(self.addCameras)
        self.thread.start()


    def addCameras(self, cameras):
        # add the cameras to the combobox
        for camera in cameras:
            if camera in self.camera_dockwidgets:
                continue
            if camera == 1:
                continue
            print("AHHHHHHHHHHH",camera)
            self.camera_dockwidgets.append(CameraDockWidget(640, 480, camera))
            self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.camera_dockwidgets[-1])
            self.camera_dockwidgets[-1].show()

    def closeEvent(self, event):
        # stop all camera streams
        for camera in self.camera_dockwidgets:
            camera.closeEvent(QtCore.QEvent(QtCore.QEvent.Type.Close))
        # close the thread
        # self.thread.quit()
        # self.thread.wait()
        event.accept()
            




            

    

class CameraGetter(QtCore.QObject):
    # define a signal, which can emit a list of cameras
    cameras = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal()

    def __init__(self):
        super(CameraGetter, self).__init__()

    def getCameras(self):
        
        # get all available cameras
        index = 0
        camera_indexes = []
        max_numbers_of_cameras_to_check = 10
        while max_numbers_of_cameras_to_check > 0:
            capture = cv2.VideoCapture(index)
            if capture.read()[0]:
                camera_indexes.append(index)
                capture.release()
            index += 1
            max_numbers_of_cameras_to_check -= 1
        # emit the signal
        self.cameras.emit(camera_indexes)
        self.finished.emit()




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWinodw()
    main.show()
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    sys.exit(app.exec())






