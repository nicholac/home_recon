import os
import sys
import subprocess
from time import sleep, time
import threading
from threading import Thread

import numpy as np
import cv2

from support_funcs.logger import log

#Switch for dev / testing beyond Pi
if sys.platform.find('linux') != -1:
    from picamera.array import PiRGBArray
else:
    from tests.pi_camera_mock import PiRGBArray

#Rename this class to what your shell script does - no spaces, special chars - use CaMaL casing
class Detect(Thread):
    '''
    What does it do?
    '''

    def __init__(self, CAMERA, split_port, capture_res=(800,600), frame_rate=24):
        '''
        '''
        #Rename the super(THIS Classname) to the name of your class
        super(Detect, self).__init__()
        #This signal is set when the machine wants your class to stop
        self._stopper = threading.Event()
        #This signal says when the stop command has completed
        self._stop_complete = threading.Event()
        #Parsed data - see above
        self.CAMERA = CAMERA
        self.split_port = split_port
        self.capture_res = capture_res
        self.frame_rate = frame_rate
        log.info('[+] Detect thread initialised')


    def stopit(self):
        self._stopper.set()
    
    
    def stopped(self):
        return self._stop_complete.is_set()


    def run(self):
        '''
        '''
        #self.CAMERA.resolution = self.capture_res
        #self.CAMERA.framerate = self.frame_rate
        RAW_CAPTURE = PiRGBArray(self.CAMERA, size=self.capture_res)
        log.info( '[+] Detect Thread running')
        while True:
            frame = self.CAMERA.capture(RAW_CAPTURE, 
                                        format="bgr", 
                                        use_video_port=True)
            #self.CAMERA.capture('foo.jpg', use_video_port=True)
            # grab the raw NumPy array representing the image, then initialize the timestamp
            # and occupied/unoccupied text
            img = frame.array
            print (img.shape)
            sleep(0.5)
            # clear the stream in preparation for the next frame
            #RAW_CAPTURE.truncate(0)
            if self._stopper.is_set() == True:
                break
        self._stop_complete.is_set() == True
        log.info( '[+] Detect Thread exited run loop')

