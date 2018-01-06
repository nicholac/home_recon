import os
import sys
import subprocess
from time import sleep, time
import threading
from threading import Thread
from datetime import datetime

import numpy as np
import cv2
import requests

#Home Recon Modules
from support_funcs.logger import log
from support_funcs.cloud_api import submit_detection

#Switch for dev / testing beyond Pi
if sys.platform.find('linux') != -1:
    from picamera.array import PiRGBArray
else:
    from tests.pi_camera_mock import PiRGBArray

DEBUG_MODE = False

#Rename this class to what your shell script does - no spaces, special chars - use CaMaL casing
class Detect(Thread):
    '''
    Detects objects / movement etc
    '''

    def __init__(self, CAMERA, config):
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
        #Cascades
        self.UPPER_BODY_CASCADE = cv2.CascadeClassifier('/usr/local/share/OpenCV/haarcascades/haarcascade_upperbody.xml')
        self.config = config
        log.info('[+] Detect thread initialised')


    def stopit(self):
        self._stopper.set()
    
    
    def stopped(self):
        return self._stop_complete.is_set()


    def run(self):
        '''
        '''
        log.info( '[+] Detect Thread running')
        start = time()
        while True:
            #TODO: Rounding needs to be worked out automatically
            frame = np.empty((self.rounded_res[1] * self.rounded_res[0] * 3,), dtype=np.uint8)
            self.CAMERA.capture(frame, 'bgr', use_video_port=True)
            frame = frame.reshape((self.rounded_res[1], self.rounded_res[0], 3))
            frame = frame[:self.CAMERA.resolution[1], :self.CAMERA.resolution[0], :]
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                num_people, out_img = self.detect_people(gray, frame)
                if num_people > 0 and time()-start > self.config['detect']['_throttle']:
                    #Submit the detection
                    chk = submit_detection(self.config['global']['cloud_api_images'], 
                                            out_img, self.config['global']['unit_id'], 
                                            datetime.now().isoformat(), 
                                            num_people, 'unverified')
                    #If we submitted successfully then reset the throttle
                    if chk == 201:
                        start = time()
            except Exception as exc:
                exc_info = (type(exc), exc, exc.__traceback__)
                log.info( '[+] Detect Thread exception: %s', exc_info)
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


    def detect_people(self, grey_frame, bgr_frame):
        #people = full_body_cascade.detectMultiScale(gray)
        people = self.UPPER_BODY_CASCADE.detectMultiScale(grey_frame, 
                                                          self.config['detect']['_scale'], 
                                                          self.config['detect']['_range'])
        log.info('People Detected:{}'.format(len(people)))
        if len(people) > 0:
            for (x,y,w,h) in people:
                cv2.rectangle(bgr_frame,(x,y),(x+w,y+h),(255,0,0),2)
                roi_gray = grey_frame[y:y+h, x:x+w]
                roi_color = bgr_frame[y:y+h, x:x+w]

            if DEBUG_MODE:
                # show the frame
                cv2.imshow("Frame", bgr_frame)
                key = cv2.waitKey(1) & 0xFF

            return len(people), bgr_frame

        else:
            return 0, None