import time
import serial
import numpy as np
from cpu_leds import LEDS, find_device

NUM_LEDS = 390

def run():
    dev = find_device()
    leds = LEDS(dev)

    colors = np.zeros( (NUM_LEDS, 3) )
    print(len(colors), colors.shape)
    colors[:] = ( 0, 255, 0 )

    done = False
    while not done:
        try:
            s = time.monotonic()

            t = s * 2 * np.pi / 10
            color = (0, (np.sin(t)*np.sin(t)*254), 0)

            colors[:] = color            
            leds.send(colors)
            s = time.monotonic() - s
            print(f"Sending at {round(1/s, 3)}Hz, color:{color}")
        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":
    run()