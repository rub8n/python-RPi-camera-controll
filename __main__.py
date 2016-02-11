#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Python-Raspberry-Contoll-Managment
    #######################################################
    
    Created by Ilja Grebel on 08.02.2016
    Version 1.005
    
    :| Copyright |: 2016, Ilja Grebel - igrebel@icloud.com
    :| license   |: Not licensed now
    
    #######################################################
    
    -TODO:
    - Set recording to pause
    - Sys. configuration
    - Save Screenshots in different format. At moment you can change format in python script
    - Save recording in differtent raw format. Currently only .h264. At moment you can change format in python script
    - Logic
    - Stop and start streaming | not FFmpeg udp streaming
    - Image effects + params
    '''
# Set default encoding to UTF-8
from flask import Flask
import datetime
import io
import time
import sys
import os
from threading import Lock
import picamera
# Not needed at moment - Streaming
#import socket
if sys.version_info[0] == 2:
    from cStringIO import StringIO as bio
else:
    from io import BytesIO as bio


camera = None  # After starting, camera is offline
camlock = Lock()  # Needed to block access from multi responses
record_dir = ''
img_dir = ''
record_file = 'video'
img_file = 'image'

app = Flask(__name__)

#################
# CONFIGURATION #
video_fmt = '.h264'
img_fmt = '.jpeg'
# resolution = ''
# img_effect = ''


# Timestamp
def timestamp():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
    return st

# Make directory
def mkdir():
    now = timestamp()
    global record_dir
    global img_dir
    record_dir = './record-%s/' % now
    img_dir = record_dir + '/images/'
    os.mkdir(record_dir)
    os.mkdir(img_dir)


# START RECORD
@app.route("/start_record", methods=['POST'])
def start_capture():
    global camera
    with camlock:
        if camera:
            return 'already recording ' + record_file + video_fmt
        mkdir()
        camera = picamera.PiCamera()
        camera.resolution = (1920, 1080)
        camera.start_preview()
        camera.start_recording(record_dir + record_file + video_fmt)
    return 'Recording to ' + record_file + video_fmt

# PAUSE RECORD - NOT WORKING AT MOMENT
@app.route("/pause_record", methods=['POST'])
def pause_record():
    global camera
    with camlock:
        if camera:
            return 'already paused ' + record_file + video_fmt
        camera = picamera.PiCamera()
        wait_recording(900000)
    return 'Recording to ' + record_file + video_fmt + ' paused'

# STOP RECODING
@app.route("/stop_record", methods=['POST'])
def stop_capture():
    global camera
    with camlock:
        if not camera:
            return 'already stopped'
        camera.stop_recording()
        h264_to_mp4()
        camera = None
    return 'Record Stopped, converting .h264 to .mp4'

# START STREAM
@app.route("/start_stream", methods=['POST'])
def start_stream():
    global camera
    with camlock:
        os.system('raspivid -t 0 -fps 25 -hf -b 2000000 -o - | ffmpeg -i - -vcodec copy -an -r 30 -g 30 -bufsize 2000000 -pix_fmt yuv420p -f mpegts udp://@239.239.2.1:1234')
    return 'UPD Stream is started at udp://@239.239.2.1:1234'

# STOP STREAM
@app.route("/stop_stream", methods=['POST'])
def stop_stream():
    os.kill(ffmpeg)

# MP4
def h264_to_mp4():
    cmd = ('ffmpeg -i %s -vcodec copy -an -f mp4 %s.mp4') % (record_dir + record_file + video_fmt, record_dir + record_file)
    os.system(cmd)
    return 'Creating .MP4 File'
    #os.remove(record_dir + record_file + ".h264")
    #return '.h264 File deleted'

# FOR COUNTER
def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

# SCREENSHOT
@app.route("/screenshot", methods=['POST'])
@static_var("counter", 0)
def screenshot():
    with camlock:
        screenshot.counter += 1
        if not camera:
            return 'Camera is not started'
        camera.capture((img_dir + '%s-' + img_file + img_fmt) % (screenshot.counter), use_video_port=True)
    return 'Saved to %d-image.jpeg' % (screenshot.counter)


if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port='8080')
    finally:
        # After http-server work is finished, shut off the camera
        with camlock:
            if camera:
                camera.close()