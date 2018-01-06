import os
import json
import hashlib
from random import random

import cv2
import requests

from support_funcs.logger import log

#Temp path for temp saving data
TMP_PATH = '/tmp'

def submit_detection(endpoint, frame, unit_id, dtg, 
                     num_people, comments):
    '''
    Send detection to Cloud api.
    We have to save the iamge to local fs, then reload.
    ::param frame opencv numpy array of image
    '''
    try:
        fname = gen_hash()+'.jpg'
        cv2.imwrite(os.path.join(TMP_PATH, fname), frame)
        assert(os.path.exists(os.path.join(TMP_PATH, fname)))
    except Exception as exc:
        exc_info = (type(exc), exc, exc.__traceback__)
        log.debug('Failed to save image to temp %s/%s, %s', TMP_PATH, fname, exc_info)
        return 500
    #try:
    data = {'dtg': dtg, 'unit_id':unit_id, 
            'comments':comments, 'num_people':num_people}
    files = {'image':open(os.path.join(TMP_PATH, fname))}
    res = requests.post(endpoint, data=data, files=files)
    assert(res.status_code == 201)
    #Remove temp file
    os.remove(os.path.join(TMP_PATH, fname))
    log.debug('Submitted a detection, status:%s, result:%s', res.status_code, res.text)
    return res.status_code
    #except Exception:
    #    log.debug('Failed to submit a detection, status:%s, result:%s', res.status_code, res.text)
    #    return res.status_code
        

def gen_hash():
    return hashlib.sha224("repetition {}".format(random()).encode('utf-8')).hexdigest()


