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
        #Background storage
        self.AVG_BG = None
        self.config = config
        #Mobile net dnn
        self.net = cv2.dnn.readNetFromCaffe(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            '..', 'models', 'ssd_mobilenet_object_detection',
                                            self.config['detect']['mobile_net']['model']), 
                                            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            '..', 'models', 'ssd_mobilenet_object_detection',
                                            self.config['detect']['mobile_net']['weights']))
        self.net_swap_rb = False
        self.net_classNames = { 0: 'background',
            1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat',
            5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat', 9: 'chair',
            10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
            14: 'motorbike', 15: 'person', 16: 'pottedplant',
            17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor' }
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
                #num_people, out_img = self.detect_people(gray, frame)
                #if num_people > 0 and time()-start > self.config['detect']['_throttle']:
                num_dets, out_img = detect_people_dnn(frame)
                if out_img and time()-start > self.config['detect']['_throttle']:
                    log.info( '[+] Detect Thread found some valid objects: %s', num_dets)
                    #Submit the detection
                    chk = submit_detection(self.config['global']['cloud_api_images'], 
                                            out_img, self.config['global']['unit_id'], 
                                            datetime.now().isoformat(), 
                                            0, 'unverified')
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
        log.debug('People Detected:{}'.format(len(people)))
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
    

    def detect_people_dnn(self, frame):
        '''
        Detect people using mobilenet dnn
        '''
        blob = cv2.dnn.blobFromImage(frame, 
                                     self.config['detect']['mobile_net']['inScaleFactor'], 
                                     (self.config['detect']['mobile_net']['inWidth'], 
                                     self.config['detect']['mobile_net']['inHeight']), 
                                     (self.config['detect']['mobile_net']['meanVal'], 
                                     self.config['detect']['mobile_net']['meanVal'], 
                                     self.config['detect']['mobile_net']['meanVal']), 
                                     self.net_swap_rb)
        net.setInput(blob)
        detections = net.forward()

        cols = frame.shape[1]
        rows = frame.shape[0]

        if cols / float(rows) > self.config['detect']['mobile_net']['WHRatio']:
            cropSize = (int(rows * self.config['detect']['mobile_net']['WHRatio']), rows)
        else:
            cropSize = (cols, int(cols / self.config['detect']['mobile_net']['WHRatio']))

        y1 = int((rows - cropSize[1]) / 2)
        y2 = y1 + cropSize[1]
        x1 = int((cols - cropSize[0]) / 2)
        x2 = x1 + cropSize[0]
        frame = frame[y1:y2, x1:x2]

        cols = frame.shape[1]
        rows = frame.shape[0]

        #Detections from classes we care about
        num_valid_detections = 0
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.config['detect']['mobile_net_thresh']:
                class_id = int(detections[0, 0, i, 1])

                xLeftBottom = int(detections[0, 0, i, 3] * cols)
                yLeftBottom = int(detections[0, 0, i, 4] * rows)
                xRightTop   = int(detections[0, 0, i, 5] * cols)
                yRightTop   = int(detections[0, 0, i, 6] * rows)

                cv2.rectangle(frame, (xLeftBottom, yLeftBottom), (xRightTop, yRightTop),
                                (0, 255, 0))
                if class_id in classNames and class_id in self.config['detect']['mobile_net_watchclasses']:
                    num_valid_detections+=1
                    label = classNames[class_id] + ": " + str(confidence)
                    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

                    yLeftBottom = max(yLeftBottom, labelSize[1])
                    cv2.rectangle(frame, (xLeftBottom, yLeftBottom - labelSize[1]),
                                            (xLeftBottom + labelSize[0], yLeftBottom + baseLine),
                                            (255, 255, 255), cv2.FILLED)
                    cv2.putText(frame, label, (xLeftBottom, yLeftBottom),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))
        if num_valid_detections > 0:
            return num_valid_detections, frame
        else:
            return 0, None



    def detect_motion(self, frame):
        '''
        Detect motion based on our windowed background
        '''
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.AVG_BG is None:
            self.AVG_BG = gray.copy().astype("float")

        cv2.accumulateWeighted(gray, self.AVG_BG, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.AVG_BG))
        thresh = cv2.threshold(frameDelta, 5, 255,
                            cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[1]

        if len(cnts) == 0:
            return None
        # loop over the contours
        for c in cnts:
        # if the contour is too small, ignore it
            if cv2.contourArea(c) < self.config['detect']['motion_thresh']:
                continue

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        #Return the annotated frame
        return frame
