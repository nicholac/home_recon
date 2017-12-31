'''
Created on 30 Dec 2017

@author: dusted-ipro

Todo:
- heartbeat - msg and snap
- commands from slack?
- low light
- wifi capture messages
- test multiple clients

'''
import time
from datetime import datetime
import os
import logging
import traceback
import hashlib
from random import random

import numpy as np
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera

from slackclient import SlackClient

DEBUG_MODE = False
UNIT_ID = 'RASP_PI_3'
#Image upload throttling - time between image sending (secs)
#Images trying to be send more than this are dropped
UPLOAD_THROTTLE = 10
MSG_THROTTLE = 10

FULL_BODY_CASCADE = cv2.CascadeClassifier('/usr/local/share/OpenCV/haarcascades/haarcascade_fullbody.xml')
UPPER_BODY_CASCADE = cv2.CascadeClassifier('/usr/local/share/OpenCV/haarcascades/haarcascade_upperbody.xml')
# initialize the camera and grab a reference to the raw camera capture
CAMERA = PiCamera()
CAMERA.resolution = (800, 600)
CAMERA.framerate = 10
RAW_CAPTURE = PiRGBArray(CAMERA, size=(800, 600))
SLACK_RESOLUTION = (320, 240)
IMAGES_SAVE_PATH = '/home/pi/home_recon/detections'
IMAGES_TEMP_PATH = '/home/pi/home_recon/temp'


SLACK_TOKEN = os.environ["SLACK_TOKEN"]
SLACK_CLI = SlackClient(SLACK_TOKEN)


LOG_PATH = '/home/pi/home_recon/logs/recon.log'
logging.basicConfig(format='%(asctime)s %(message)s',
                    filename=LOG_PATH,
                    level=logging.INFO)


def send_msg(text):
    try:
        res = SLACK_CLI.api_call(
            "chat.postMessage",
            channel="#general",
            text="{}".format(text)
        )
        logging.debug('Send message success: {}'.format(res))
    except:
        logging.error('Send message failed: {}'.format(res))



def post_image(fname, fpath):
    #Downsample

    try:
        dtg = datetime.now().isoformat()
        res = SLACK_CLI.api_call(
            #"chat.postMessage",
            "files.upload",
            channel="#general",
            text="{} uploaded on {}".format(fname, dtg),
            filename=fname,
            file=open(os.path.join(fpath, fname), 'rb')
        )
        logging.debug('Send message success: {}'.format(res))
    except Exception as exc:
        exc_info = (type(exc), exc, exc.__traceback__)
        logging.exception('Upload Image Failed: {}'.format(exc_info))


def gen_hash():
    return hashlib.sha224("repetition {}".format(random()).encode('utf-8')).hexdigest()


def downsample_image(frame):
    try:
        down_samp = cv2.resize(frame,
                               SLACK_RESOLUTION,
                               interpolation = cv2.INTER_CUBIC)
        temp_fname = gen_hash() + '.jpg'
        cv2.imwrite(os.path.join(IMAGES_TEMP_PATH, temp_fname), down_samp)
        logging.debug('Downsample Success: {}'.format(temp_fname))
        return temp_fname
    except Exception as exc:
        exc_info = (type(exc), exc, exc.__traceback__)
        logging.exception('Dowsample Image Failed: {}'.format(exc_info))
        return None


def save_image(frame, num_people):
    try:
        fname = '{}_{}.jpg'.format(datetime.now().isoformat(), num_people)
        cv2.imwrite(os.path.join(IMAGES_SAVE_PATH, fname), frame)
        logging.debug('Save image success: {}'.format(fname))
        return fname
    except Exception as exc:
        exc_info = (type(exc), exc, exc.__traceback__)
        logging.exception('Error in save_image: {}'.format(exc_info))
        return None



def detect_people(grey_frame, bgr_frame):
    #people = full_body_cascade.detectMultiScale(gray)
    people = UPPER_BODY_CASCADE.detectMultiScale(grey_frame)
    logging.debug('People Detected:{}'.format(len(people)))
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



def main():
    try:
        # allow the camera to warmup
        time.sleep(0.1)
        upload_start = time.time()
        msg_start = time.time()

        # capture frames from the camera
        for frame in CAMERA.capture_continuous(RAW_CAPTURE, format="bgr", use_video_port=True):
            try:
                # grab the raw NumPy array representing the image, then initialize the timestamp
                # and occupied/unoccupied text
                img = frame.array
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                num_people, out_img = detect_people(gray, img)

                if num_people > 0:
                    logging.debug('{} People Detected at {}'.format(num_people,
                                                                          datetime.now().isoformat()))
                    fname = save_image(out_img, num_people)
                    if time.time()-msg_start > MSG_THROTTLE:
                        send_msg('{} People Detected at {} by {}, fname: {}'.format(num_people,
                                                                                datetime.now().isoformat(),
                                                                                UNIT_ID,
                                                                                fname))
                        msg_start = time.time()
                    #Check throttle and upload
                    if time.time()-upload_start > UPLOAD_THROTTLE:
                        downsamp_fname = downsample_image(out_img)
                        if downsamp_fname:
                            post_image(downsamp_fname, IMAGES_TEMP_PATH)
                            os.remove(os.path.join(IMAGES_TEMP_PATH, downsamp_fname))
                            logging.exception('Completed detection upload: {}'.format(downsamp_fname))
                            upload_start = time.time()


                # clear the stream in preparation for the next frame
                RAW_CAPTURE.truncate(0)
            except KeyboardInterrupt:
                logging.debug('Exiting on keyboard interrupt')
                break
            except Exception as exc:
                exc_info = (type(exc), exc, exc.__traceback__)
                logging.exception('Error in main loop: %s', exc_info)

    except KeyboardInterrupt:
        logging.debug('Exiting on keyboard interrupt')

    logging.debug('Exited detection')


if __name__ == '__main__':
    main()
