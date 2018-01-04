import time
import serial
import noise
import numpy as np
import matplotlib
from cpu_leds import LEDS, find_device

NUM_LEDS = 390

def breath():
    colors = np.zeros( (NUM_LEDS, 3))
    while True:
        t = time.monotonic()
        v = (1 - abs( np.sin(t) )) * 255
        colors[:] = (v,v,v)
        yield colors

def perlin():
    while True:
        v = np.array([noise.pnoise2(x/200, time.monotonic()/2 , repeatx=NUM_LEDS) for x in range(NUM_LEDS)])
        v = (v-v.min()) / (v.max() - v.min())
        colors = np.array( matplotlib.cm.hsv(v)[:,:3]*255 ).astype('int')
        yield colors

def solid(color):
    colors = np.zeros( (NUM_LEDS, 3) )
    colors[:] = color
    while True:
        yield colors

def run():
    dev = find_device()
    leds = LEDS(dev, debug=True)

    done = False
    while not done:
        try:
            s = time.monotonic()
            colors = next( breath() )
            leds.send( colors )
            s = time.monotonic() - s
        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":
    run()