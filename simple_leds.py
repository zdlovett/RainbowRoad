import time
import serial
import noise
import numpy as np
import matplotlib
import psutil
from cpu_leds import LEDS, find_device

#LED colors are G R B order

NUM_LEDS = 60

def breath():
    colors = np.zeros( (NUM_LEDS, 3))
    while True:
        t = time.monotonic()
        v = (1 - abs( np.sin( t / 2 ) )) * 255
        colors[:] = (v,v,v)
        yield colors

def perlin(speed=1):
    while True:
        v = np.array([noise.pnoise2(x/200, time.monotonic() * speed , repeatx=NUM_LEDS) for x in range(NUM_LEDS)])
        v = (v-v.min()) / (v.max() - v.min())
        colors = np.array( matplotlib.cm.hsv(v)[:,:3]*255 ).astype('int')
        yield colors

def solid(color=(255,0,200)):
    colors = np.zeros( (NUM_LEDS, 3) )
    colors[:] = color
    while True:
        yield colors

def cpu_race(length=30):
    i = 0
    while True:
        colors = np.zeros( (NUM_LEDS, 3) )

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
    while not done:
        try:
            for c1, c2 in zip( perlin(0.25), cpu_race(10) ):
                colors = (c1 + c2) / 2
                leds.send( colors )
        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":
    run()