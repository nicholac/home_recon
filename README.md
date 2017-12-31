# home_recon

### Simple script to turn PiCamera into person detector with notification through Slack.

* Samples PiCamera and detects people using OpenCV Haarcascade (upper body)
* Posts messages to given Slack channel on detection
* Uploads down-sampled image files to slack on detection


### Install:

* Build / install OpenCV 3 on Raspberry Pi (qudos to PyImageSearch - https://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/)
* Install other python libs - picamera, slackclient
* Setup Slack channel and add bot user with scopes for chat.message and file.upload
* Add oAuth Token to Pi Environment variable SLACK_TOKEN
* Run python main.py


#### Its not optimised very well and does throw plenty of false detections.
