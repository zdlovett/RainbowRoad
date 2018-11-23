import os
import time
import serial
import noise
import numpy as np
import matplotlib
import psutil
from collections import namedtuple
from leds import Leds, find_device

#LED colors are G R B order

D = False
Z = False
if os.path.exists('zachs_computer'):
    Z = True
    print("on zach's computer")

if os.path.exists('debug'):
    D = True
    print("turning on debug mode")

NUM_LEDS = 100 if Z else 419


# looking at the case from the front
SEGS ={
    'gpu'           : (0, 36),  # front to back
    'bottom_right'  : (37, 70), # front to back
    'bottom_left'   : (71, 104), # front to back
    'front_left'    : (105, 159), # bottom to top
    'front_right'   : (160, 213), # top to bottom
    'front_bottom'  : (214, 230), # right to left
    'side_front'    : (231, 257), # middle to top?
    'side_top'      : (258, 296), # front to back
    'side_back'     : (297, 343), # top to bottom
    'side_bottom'   : (344, 384), # back to front
    'side_front_2'  : (385, 402), # bottom to middle
    'fan_center'    : (403, 406), # counter clockwise
    'fan_rim'       : (407, 419) # counter clockwise
}


def breath(seg_len=NUM_LEDS):
    colors = np.zeros( (seg_len, 3))
    while True:
        t = time.monotonic()
        v = (1 - abs( np.sin( t / 2 ) )) * 255
        colors[:] = (v,v,v)
        yield colors

def perlin(seg_len=NUM_LEDS, speed=0.5, size=200):
    while True:
        v = np.array([noise.pnoise2(x/size, time.monotonic() * speed , repeatx=seg_len) for x in range(seg_len)])
        v = ( v-v.min() ) / (v.max() - v.min())
        colors = np.array( matplotlib.cm.hsv(v)[:,:3]*255 ).astype('int')

		# reduce the brigntness a bit (divide by 3 and multiply by 2)
        colors = (colors // 3) * 2

        yield colors

def solid(seg_len=NUM_LEDS, color=(255,0,200)):
    colors = np.zeros( (seg_len, 3) )
    colors[:] = color
    while True:
        yield colors

def per_seg(color=(220, 10, 200), delay=1):
    colors = np.zeros( (NUM_LEDS, 3) )
    last_time = time.monotonic()

    seg = 0
    segs = [s for s in SEGS.values()]

    while True:
        csg = segs[seg]
        colors[ csg[0]:csg[1], : ] = color

        now = time.monotonic()
        if now - last_time > delay:
            last_time = now
            colors[ csg[0]:csg[1], : ] = (0, 0, 0)

            # advance the seg
            seg += 1
            if seg >= len(segs):
                seg = 0
        yield colors


def cylon(seg_len=NUM_LEDS, length=10, rate=10, color=(255, 0, 0), forward=True):
    "oscilate back and forth"
    rate = 1/rate # leds per second

    colors = np.zeros( (seg_len, 3) )
    colors[0:length, :] = color
    colors[0:length, 0] *= np.sin(np.linspace(0, np.pi, length))
    colors[0:length, 1] *= np.sin(np.linspace(0, np.pi, length))
    colors[0:length, 2] *= np.sin(np.linspace(0, np.pi, length))

    center = length // 2

    last_time = time.monotonic()

    while True:
        now = time.monotonic()
        if now - last_time > rate:
            last_time = now
            if center > seg_len - length:
                forward = False
            elif center < 0:
                forward = True

            if forward:
                center += 1
            else:
                center -= 1

        yield np.roll(colors, center, 0)

def cpu_race(seg_len=NUM_LEDS, length=30, speed=0.1):
    i = 0
    while True:
        colors = np.zeros( (seg_len, 3) )

        cpu = psutil.cpu_percent() / 100
        cpu = int(cpu * speed + 1)

        #set the pulse
        colors[:length, 0] = (np.arange(length) / length * 255) * (1-cpu)   # G
        colors[:length, 1] = (np.arange(length) / length * 255)             # R
        colors[:length, 2] = (np.arange(length) / length * 255) * (1-cpu)   # B

        colors = np.roll(colors, i, 0)
        i += cpu
        yield colors

def single(seg_len=NUM_LEDS, offset=0):
    colors = np.zeros( (seg_len, 3) )
    colors[0, :] = (220, 10, 200)
    colors = np.roll(colors, offset, 0)
    return colors

