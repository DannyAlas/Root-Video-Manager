import dis
from PyQt6 import QtCore, QtGui, QtWidgets
from threading import Thread
from collections import deque
import time
import cv2
import imutils

class CameraStreamWidget(QtWidgets.QWidget):
    """Independent camera feed
    Uses threading to grab camera frames in the background

    """

    def __init__(self, width, height, stream_link=0, aspect_ratio=False, parent=None, deque_size=1):
        super(CameraStreamWidget, self).__init__(parent)
        
        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)

        # Slight offset is needed since PyQt layouts have a built in padding
        # So add offset to counter the padding 
        self.offset = 16
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.maintain_aspect_ratio = aspect_ratio

        self.camera_stream_link = stream_link

        # Flag to check if camera is valid/working
        self.online = False
        self.capture = None
        self.video_frame = QtWidgets.QLabel()

        self.load_stream()
        
        # Start background frame grabbing
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()

        # Periodically set video frame to display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(1)

        print('Started camera: {}'.format(self.camera_stream_link))

    def load_stream(self):
        """Verifies stream link and open new stream if valid"""

        def load_stream_thread():
            print('Attempting: {}'.format(self.camera_stream_link))
            if self.verify_stream(self.camera_stream_link):
                self.capture = cv2.VideoCapture(self.camera_stream_link)
                self.online = True
        self.load_stream_thread = Thread(target=load_stream_thread, args=())
        self.load_stream_thread.daemon = True
        self.load_stream_thread.start()

    def verify_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if not cap.isOpened():
            return False
        cap.release()
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""

        while True:
            try:
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    status, frame = self.capture.read()
                    if status:
                        self.deque.append(frame)
                    else:
                        self.capture.release()
                        self.online = False
                else:
                    pass
            except AttributeError:
                pass

    def spin(self, seconds):
        """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

        time_end = time.time() + seconds
        while time.time() < time_end:
            QtWidgets.QApplication.processEvents()
            

    def set_frame(self):
        """Sets pixmap image to video frame"""

        if not self.online:
            self.spin(1)
            return

        if self.deque and self.online:
            # Grab latest frame
            frame = self.deque[-1]

            # Keep frame aspect ratio
            if self.maintain_aspect_ratio:
                self.frame = imutils.resize(frame, width=self.screen_width)
            # Force resize
            else:
                self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))

            # Add timestamp to cameras
            # cv2.rectangle(self.frame, (self.screen_width-190,0), (self.screen_width,50), color=(0,0,0), thickness=-1)
            # cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format.Format_BGR888)
            self.pix = QtGui.QPixmap.fromImage(self.img)
            self.video_frame.setPixmap(self.pix)

    def get_video_frame(self):
        return self.video_frame

    def resize_frame(self, width, height):
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.video_frame.resize(self.screen_width, self.screen_height)
        

    def save_video(self, filename):
        """Saves current deque into video file"""

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (self.screen_width, self.screen_height))

        for i in range(len(self.deque)):
            # Grab frame from deque and write to file
            frame = self.deque[i]
            out.write(frame)

        # Release everything if job is finished
        out.release()
        cv2.destroyAllWindows()

    def close(self):
        """Sets camera status to offline"""
        self.load_stream_thread.join()
        self.online = False
        self.capture.release()
        # delete self.capture
        del self

class CameraDialog(QtWidgets.QDialog):
    """Camera dialog info widget"""

    def __init__(self, stream_link=0):
        super(CameraDialog, self).__init__()
        self.selected_camera = stream_link
        self.init_gui()

    def init_gui(self):
        """Initialize widgets"""

        self.setMinimumSize(300, 100)
        self.setWindowTitle("Camera: {}".format(self.selected_camera))

        # Create widgets
        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.clicked.connect(self.close)

        # Create layout and add widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.ok_button)

        # Set dialog layout
        self.setLayout(self.layout)

        
class CameraDockWidget(QtWidgets.QDockWidget):
    """Camera viewer widget with stream and buttons"""

    def __init__(self, width, height, stream_link=0, aspect_ratio=False, parent=None, deque_size=1):
        super(CameraDockWidget, self).__init__(parent)
        self.stream_link = stream_link
        self.aspect_ratio = aspect_ratio
        self.deque_size = deque_size
        self.width = width
        self.height = height

        self.init_gui()

    def init_gui(self):
        """Initialize widgets"""

        self.setMinimumSize(self.width, self.height)
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.setWindowTitle("Camera: {}".format(self.stream_link))

        # Create camera stream widget
        self.camera_stream_widget = CameraStreamWidget(self.width, self.height, self.stream_link, self.aspect_ratio, deque_size=self.deque_size)
        self.setWidget(self.camera_stream_widget.get_video_frame())

        # Create toolbar
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setMovable(False)
        

        # Create buttons
        self.camera_selector_button = QtWidgets.QPushButton()
        self.camera_selector_button.setText("Save Video")
        self.camera_selector_button.clicked.connect(self.save_video)

        self.toolbar.addWidget(self.camera_selector_button)

    def select_camera(self):
        """Opens dialog to select camera"""

        # Create dialog
        self.camera_dialog = CameraDialog(self.stream_link)

        # Set camera if selected
        if self.camera_dialog.exec():
            self.stream_link = self.camera_dialog.selected_camera
            self.camera_stream_widget.close()
            self.camera_stream_widget = CameraStreamWidget(self.width, self.height, self.stream_link, self.aspect_ratio, deque_size=self.deque_size)
            self.setWidget(self.camera_stream_widget)
            self.camera_selector_button.setText("Camera: {}".format(self.stream_link))

    def save_video(self):
        """Opens dialog to save video"""
        import os
        # Get filename and save video
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Video', os.getenv('HOME'), 'Video Files (*.avi)')[0]
        if filename:
            self.camera_stream_widget.save_video(filename)

    def closeEvent(self, event):
        """Overrides close event to close camera stream"""
        print("close event")
        self.camera_stream_widget.close()
        event.accept()

    # when the dock widget is resized, resize the video frame accordingly
    def resizeEvent(self, event):
        """Overrides resize event to resize camera stream"""
        super(CameraDockWidget, self).resizeEvent(event)
        print("resize event")
        self.camera_stream_widget.resize_frame( self.width, self.height )
        event.accept()
        
