import numpy as np

class PiCamera():
    def __init__(self):
        self.resolution = None
        self.framerate = None
    
    def capture_continuous(self, raw_cap, format, 
                           use_video_port, splitter_port):
        while True:
            yield Frame()


class Frame():
    def __init__(self):
        self.array = np.zeros((10, 10))


class PiRGBArray():
    def __init__(self, CAMERA, size):
        self.size = size
        self.CAMERA = CAMERA



    