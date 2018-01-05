#Builtins
import sys
import os
from time import sleep, time
import logging as log
import traceback
import threading
from threading import Thread

#Home Recon
from support_funcs.logger import log
from actions.thread_detect import Detect

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
    def __init__(self, initParams):
        '''
        Hub provides:
        '''
        threading.Thread.__init__(self)
        self.running = False
        self._stopper = threading.Event()
        self._stopped = threading.Event()
        #Store Initialisation parameters
        self.initParams = initParams
        
        #Load config path
        try:
            if initParams['baseConfigPath'] == '':
                self.baseConfigPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'configs')
            else:
                self.baseConfigPath = initParams['baseConfigPath']
        except KeyError:
            self.baseConfigPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'configs')
        
        #PI Camera 
        self.CAMERA = PiCamera()
        self.detect_port = 2
        self.stream_port = 1

        #Threads
        self.detection_thread = Detect(self.CAMERA, self.detect_port)
        self.stream_thread = None
        
        log.info( '[+] Finished setting up modules, ready to start')
    
    
    
    def run(self):
        '''
        The main controller loop
        '''
        #Init various threads
        self.detection_thread.start()

        log.info( '[+] Main controller running')
            
    
    def stopit(self):
        '''
        Main controller shutdown sequence
        '''
        #Shutdown various threads...
        #Shutdown main controller loop
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