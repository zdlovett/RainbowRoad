import time
import socket
import numpy as np
from leds import Leds, LISTEN_PORT
from animations import perlin, solid



soc = socket.create_connection((socket.gethostname(), LISTEN_PORT))
animation = iter(perlin(speed=0.1, size=200))
#animation = solid( color=(220, 200, 10))

rate = 1 / 100
done = False
while not done:
    try:
        start_time = time.monotonic()
        
        colors = next(animation)
        
        colors = np.array(colors, dtype='uint8')
        buffer = colors.tobytes()
        soc.send(buffer)
        duration = time.monotonic() - start_time
        if duration < rate:
            time.sleep(rate - duration)
            print(time.time())
    except KeyboardInterrupt:
        done = True
         
soc.close()