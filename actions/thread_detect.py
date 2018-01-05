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

    def __init__(self, CAMERA):
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
        self.rounded_res = self.round_res(self.CAMERA.resolution)
        log.info('[+] Detect thread initialised')


    def stopit(self):
        self._stopper.set()
    
    
    def stopped(self):
        return self._stop_complete.is_set()


    def run(self):
        '''
        '''
        log.info( '[+] Detect Thread running')
        while True:
            #TODO: Rounding needs to be worked out automatically
            frame = np.empty((self.rounded_res[1] * self.rounded_res[0] * 3,), dtype=np.uint8)
            self.CAMERA.capture(frame, 'bgr', use_video_port=True)
            frame = frame.reshape((self.rounded_res[1], self.rounded_res[0], 3))
            frame = frame[:self.CAMERA.resolution[1], :self.CAMERA.resolution[0], :]
            try:
                print (frame.shape)
            except:
                print ('no frame')
            sleep(1.0)
            if self._stopper.is_set() == True:
                break
        self._stop_complete.is_set() == True
        log.info( '[+] Detect Thread exited run loop')


    def round_res(self, res):
        '''
        Round the resolution to tha expected from the camera
        '''
        return (res[0]+(res[0]%32), res[1]+(res[1]%16))