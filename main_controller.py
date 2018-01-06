#Builtins
import sys
import os
from time import sleep, time
import logging as log
import traceback
import threading
from threading import Thread
import json

#Home Recon
from support_funcs.logger import log
from actions.thread_detect import Detect
from actions.thread_stream import Stream

#Switch for dev / testing beyond Pi
if sys.platform.find('linux') != -1:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
else:
    from tests.pi_camera_mock import PiCamera, PiRGBArray


class hub(threading.Thread):
    '''
    Hub of the System
    '''
    def __init__(self):
        '''
        Hub provides:
        '''
        threading.Thread.__init__(self)
        self.running = False
        self._stopper = threading.Event()
        self._stopped = threading.Event()
        #Load config path
        try:
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json'), 'rb') as fp:
                self.config = json.load(fp)
        except Exception:
            print ('Fatal Error - Failed to load config.json')
            return None
        
        #PI Camera 
        self.CAMERA = PiCamera()
        self.CAMERA.resolution = self.config["global"]["resolution"]
        self.CAMERA.framerate = self.config["global"]["framerate"]
        #Camera Warmup
        print ('Warming Camera up...')
        sleep(2.0)
        print ('Camera Ready')

        #Threads - detect and stream
        self.detection_thread = Detect(self.CAMERA, 
                                       self.config)

        self.stream_thread = Stream(self.CAMERA, 
                                    self.config["stream"]["port"], 
                                    self.config["stream"]["host"])
        self.stream_thread.isDaemon()
        
        log.info( '[+] Finished setting up modules, ready to start')
    
    
    
    def run(self):
        '''
        The main controller loop
        '''
        #Init various threads
        log.info( '[+] Starting streaming thread...')
        self.stream_thread.start()
        while not self.stream_thread._started.isSet():
            sleep(0.1)
        log.info( '[+] Streaming thread running')

        log.info( '[+] Starting detection thread...')
        self.detection_thread.start()
        log.info( '[+] Detection thread running')

        log.info( '[+] Main controller completed startup')
            
    
    def stopit(self):
        '''
        Main controller shutdown sequence
        '''
        #Shutdown various threads...
        #Shutdown main controller loop
        log.info( '[+] Shutting down threads...)')
        self.detection_thread.stopit()
        while not self.detection_thread.stopped:
            sleep(0.1)
        log.info( '[+] Completed Shutdown')
        self._stopped.set()
        return True
    
    
    def stopped(self):
        return self._stopped.isSet()


if __name__ == '__main__':
    try:
        initParams = {'config':'testing'}
        mainThread = hub(initParams)
        #Run a while and stop
        print ('[+] Starting Home Recon in '+str.upper(initParams['config'])+' mode...')
        start = time()
        #Startup the main thread
        mainThread.start()
        while True: sleep(0.25)
    
    except KeyboardInterrupt:
        print ('[+] Caught Ctrl-C - Stopping')
        mainThread.stopit()
        print ('[+] Shutdown Complete.')

    #except Exception:
    #    exc_type, exc_value, exc_traceback = sys.exc_info()
    #    log.error('[-]  Fatal Error: %s', exc_traceback)
    #    print ('[-]  Fatal Error:%s', exc_traceback)
    #    sys.exit()