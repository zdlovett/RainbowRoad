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
    #dev = find_device(hint='FT231X')
    dev = find_device(hint='USB Serial Port')
    leds = Leds(dev, debug=D, total_leds=NUM_LEDS)
    done = False

    updates = 0
    last_update = 0
    last_debug = time.monotonic()

    rate_period = 0.01

    # change speed=0.1 to speed=10 for PARTY MODE
    animation = iter(perlin(speed=0.1, size=100))
    #animation = iter(cpu_race())
    #animation = iter(breath())

    while not done:
        try:
            now = time.monotonic()
            colors = next( animation )
            
            # set the red channel to 0
            #colors[:, 0] = 0
            #colors[:, 1] //= 2 # set the green channel to half of what it would be

            # reduce the brigntness a bit (divide by 3 and multiply by 2)
            colors = (colors // 3) * 2

            leds.send(colors)
            updates += 1

            # rate limit
            send_time = time.monotonic() - now
            if send_time < rate_period:
                #print(f'sleeping:{rate_period - send_time}')
                time.sleep(rate_period - send_time)

            # print every second
            if now - last_debug > 1:
                #print(updates)
                updates = 0
                last_debug = now

        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":
    run()
