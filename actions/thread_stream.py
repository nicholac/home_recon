import os
import sys
import subprocess
from time import sleep, time
import threading
from threading import Thread, Condition
import io
import socketserver
from http import server

import numpy as np
import cv2

from support_funcs.logger import log

#Switch for dev / testing beyond Pi
if sys.platform.find('linux') != -1:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
else:
    from tests.pi_camera_mock import PiRGBArray, PiCamera


PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="1296" height="972" />
</body>
</html>
"""

output = None
        

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                log.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

#Rename this class to what your shell script does - no spaces, special chars - use CaMaL casing
class Stream(Thread):
    '''
    What does it do?
    '''

    def __init__(self, CAMERA, config):
        '''
        '''
        #Rename the super(THIS Classname) to the name of your class
        super(Stream, self).__init__()
        #This signal is set when the machine wants your class to stop
        self._stopper = threading.Event()
        self._started = threading.Event()
        #This signal says when the stop command has completed
        self._stop_complete = threading.Event()
        #Parsed data - see above
        self.CAMERA = CAMERA
        self.config = config
        self.stream_port = self.config["stream"]["port"]
        self.stream_host = self.config["stream"]["host"]
        log.info('[+] Streaming thread initialised')


    def stopit(self):
        self._stopper.set()
    
    
    def stopped(self):
        return self._stop_complete.is_set()


    def run(self):
        '''
        '''
        log.info( '[+] Stream Thread starting')
        #Linux testing 
        if sys.platform.find('linux') == -1:
            return
        global output
        output = StreamingOutput()
        self.CAMERA.start_recording(output, format='mjpeg')
        try:
            address = (self.stream_host, self.stream_port)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
            self._started.set()
            log.info( '[+] Stream Thread started')
        finally:
            self.CAMERA.stop_recording()