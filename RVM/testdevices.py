# print all the devices connected to the computer
import sys
import os
import platform
import cv2
# get system
sysstr = platform.system()


# get all cameras connected to the computer
def get_cameras():
    cameras = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
    return cameras

