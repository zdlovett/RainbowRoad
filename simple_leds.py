import time
import serial
import noise
import numpy as np
import matplotlib
import psutil
from cpu_leds import LEDS, find_device

#LED colors are G R B order

NUM_LEDS = 390

def breath(seg_len=NUM_LEDS):
    colors = np.zeros( (seg_len, 3))
    while True:
        t = time.monotonic()
        v = (1 - abs( np.sin( t / 2 ) )) * 255
        colors[:] = (v,v,v)
        yield colors

def perlin(seg_len=NUM_LEDS, speed=1, size=200):
    while True:
        v = np.array([noise.pnoise2(x/size, time.monotonic() * speed , repeatx=seg_len) for x in range(seg_len)])
        v = (v-v.min()) / (v.max() - v.min())
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
    dev = find_device()
    leds = LEDS(dev, debug=False)
    done = False
    colors = np.zeros((NUM_LEDS, 3))
    while not done:
        try:
            for s1, s2, s3 in zip(cpu_race(seg_len=60, length=10), perlin(seg_len=60, size=50), breath(seg_len=60)):
                colors[:60] = (s1 + s2*(s3/255)) / 2
                leds.send( colors )
        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":
    run()