#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Created by Ilja Grebel on 08.02.2016
    Version 1.000
    
    TODO:
    - Set recording to pause
    - Sys. configuration
    - Save Screenshots in different format
    - Save recording in differtent raw format. Currently only .h264
    - .h264 to .mp4 converter
    - Stream stop and start
    - Make Directory for save every screenshot and record
    - Correct timestamp
    - Logic
    '''

from flask import Flask
from dateutil.tz import tzutc
from flask import jsonify
from flask import request
import datetime
import io
import time
import logging
import sys
import os
from threading import Lock
import picamera
import errno
import traceback
import socket
if sys.version_info[0] == 2:
    from cStringIO import StringIO as bio
else:
    from io import BytesIO as bio


camera = None  # After starting, camera is offline
camlock = Lock()  # Needed to block access from multi responses

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
record_file = 'recording-%s.h264' % st
app = Flask(__name__)

# START RECORD
@app.route("/start_record", methods=['POST'])
def start_capture():
    global camera
    with camlock:
        if camera:
            return 'already recording ' + record_file
        camera = picamera.PiCamera()
        camera.resolution = (1920, 1080)
        camera.start_preview()
        camera.start_recording(record_file)
    return 'record ' + record_file

# PAUSE RECORD - NOT WORKING AT MOMENT
@app.route("/pause_record", methods=['POST'])
def pause_record():
    global camera
    with camlock:
        if camera:
            return 'already paused ' + record_file
        camera = picamera.PiCamera()
        wait_recording(900000)
    return 'recording ' + record_file + ' paused'


# STOP RECODING
@app.route("/stop_record", methods=['POST'])
def stop_capture():
    global camera
    with camlock:
        if not camera:
            return 'already stopped'
        camera.close()
        camera = None
    return 'ok'

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
        camera.capture('%d-image-%s.jpeg' % (screenshot.counter, st), use_video_port=True)
    return 'Saved to %d-image-%s.jpeg' % (screenshot.counter, st)

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port='8080')
        app.run(debug=True)
    finally:
        # After http-server work is finished, shut off the camera
        with camlock:
            if camera:
                camera.close()