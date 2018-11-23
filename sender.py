import sys
import time
import socket
import select
import numpy as np
from leds import Leds, LISTEN_PORT
import animations
import skratch



soc = socket.create_connection(('192.168.2.3', LISTEN_PORT))

# sleep to let the leds clear from the last buffers
time.sleep(2)

#animation = iter(animations.perlin(speed=1, size=50))
#animation = solid( color=(220, 10, 200))
#animation = single
#nimation = iter(animations.per_seg())
#animation = iter(animations.cylon(seg_len=37, length=11, rate=10, color=(0,255,255)) )
#front_1 = iter(animations.cylon(seg_len=159-105, length=15, rate=20, color=(255,10,200)) )
#front_2 = iter(animations.cylon(seg_len=213-160, length=15, rate=20, color=(255,10,200), forward=False) )

#cpu_fan = iter(animations.cpu_race(seg_len=12, length=4, speed=0.1))

pond = skratch.Pond([a for a in range(419)], speed=1, num_waves=10)

rate = 1 / 100
done = False

offset = 390


colors = np.zeros( (419, 3) )

while not done:
    try:
        start_time = time.monotonic()

        #colors = single(419, offset)
        #colors[0:37, :] = next(animation)
        #colors[105:159, :] = next(front_1)
        #colors[160:213, :] = next(front_2)
        #colors[407:419, :] = next(cpu_fan)

        colors = pond.update(0.01)

        colors = np.array(colors, dtype='uint8')
        buffer = colors.tobytes()
        soc.send(buffer)

        duration = time.monotonic() - start_time
        if duration < rate:
            time.sleep(rate - duration)

    except KeyboardInterrupt:
        done = True

soc.close()