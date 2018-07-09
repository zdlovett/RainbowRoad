import os
import time
import serial
import noise
import numpy as np
import matplotlib
import psutil
from collections import namedtuple
from cpu_leds import LEDS, find_device

#LED colors are G R B order

D = False
Z = False
if os.path.exists('zachs_computer'):
    Z = True

if os.path.exists('debug'):
    D = True

NUM_LEDS = 60 if Z else 419


SEGS = [

]


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
        yield colors

def solid(seg_len=NUM_LEDS, color=(255,0,200)):
    colors = np.zeros( (seg_len, 3) )
    colors[:] = color
    while True:
        yield colors

def cpu_race(seg_len=NUM_LEDS, length=30):
    i = 0
    while True:
        colors = np.zeros( (seg_len, 3) )

        cpu = psutil.cpu_percent() / 100
        speed = int(cpu * 4 + 1)

        #set the pulse
        colors[:length, 0] = (np.arange(length) / length * 255) * (1-cpu)   # G
        colors[:length, 1] = (np.arange(length) / length * 255)             # R
        colors[:length, 2] = (np.arange(length) / length * 255) * (1-cpu)   # B

        colors = np.roll(colors, i, 0)
        i += speed
        yield colors

def run():
    dev = find_device(hint='FT231X')
    leds = LEDS(dev, debug=D)
    done = False

    updates = 0
    last_update = 0
    last_debug = time.monotonic()

    rate_period = 0.01

    #animation = iter(perlin(size=50))
    animation = iter(cpu_race())
    #animation = iter(breath())

    while not done:
        try:
            now = time.monotonic()
            colors = next( animation )
            leds.send(colors)
            updates += 1

            # rate limit
            send_time = time.monotonic() - now
            if send_time < rate_period:
                #print(f'sleeping:{rate_period - send_time}')
                time.sleep(rate_period - send_time)

            # print every second
            if now - last_debug > 1:
                print(updates)
                updates = 0
                last_debug = now

        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":
    run()
