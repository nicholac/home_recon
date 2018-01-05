import logging
import os

#LOGPATH = os.path.expanduser('~')
LOGPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'logs')
LOGNAME = 'home_recon.log'

log = logging.getLogger('Home_Recon_Log')
log.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s %(threadName)-11s %(levelname)-10s %(message)s")

# Log to file
filehandler = logging.FileHandler(os.path.join(LOGPATH, LOGNAME), "a")
filehandler.setLevel(logging.DEBUG)
filehandler.setFormatter(formatter)
log.addHandler(filehandler)
print ('[+] Logger Initialised to: '+LOGPATH+'/'+LOGNAME)