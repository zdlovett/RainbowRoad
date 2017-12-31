import os
import sys
import time
import serial
from serial.tools import list_ports
import psutil
import matplotlib.cm
import numpy as np
import noise
import colr

# core segments
segs = {
        'fr': np.arange(  0,  50), # moving up
        'fl': np.arange( 50, 100), # moving down
        'sf': np.arange(100, 150),
        'st': np.arange(150, 194),
        'sr': np.arange(194, 243),
        'sb': np.arange(243, 284),
        'br': np.arange(284, 317),
        'bl': np.arange(317, 354)
        }

total_leds = sum([len(v) for v in segs.values()])
print(total_leds)

# segment regions
segs['all'] = np.hstack([s for s in segs.values()])
segs['side'] = np.hstack( [segs['st'], segs['sr'], segs['sb'], segs['sf']] )
segs['front'] = np.hstack( [ segs['fl'], segs['fr'] ] ) 
segs['bottom'] = np.hstack( [ segs['br'], segs['bl'] ] )

def find_device(hint="Arduino"):
    device = None
    ports = list_ports.comports()
    for p in ports:
        if hint in p.description:
            device = p
            print(f"Found {p}")
            break
    return device

def mix(a, x, y):
    return x*(1-a)+y*a

class LEDS:
    def __init__(self, device=None, debug=False):
        self.debug = debug
        self.device = device
        if device is not None:
            self.device = serial.Serial(device.device, 2500000)

        self.gamma8 = [#adjusted to remove 0 from the colors
            1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
            1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
            1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
            2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
            5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
            10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
            17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
            25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
            37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
            51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
            69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
            90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
            115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
            144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
            177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
            215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255]

        self.vgam = np.vectorize(lambda c: self.gamma8[c])

    def send(self, colors):
        colors = np.clip(colors, 1, 255)
        colors = np.array(colors, dtype='uint8').flatten()
        colors = self.vgam(colors)
        while len(colors) < 251*3:
            colors = np.append(colors, 1)

        if self.debug:
            out = ""
            for i in range(0,len(colors),3):
                out += colr.color('x', fore=tuple(colors[i:i+3]))
            print(out)

        if self.device is not None:
            colors = bytes([0]+list(colors))
            self.device.write(colors)
            self.device.flush()

class WhiteRoll:
    """
    single white pixel going around
    """
    def __init__(self, indices):
        self.indices = indices
        self.colors = [0,0,0]*len(indices)
        self.colors[:3] = [255,255,255]
        self.colors = np.array(self.colors).reshape(-1,3)

    def update(self, dt):
        self.colors = np.roll(self.colors, 1, axis=0)
        return self.colors

class WhiteRollTail:
    """
    single white pixel going around with dim tail
    """
    def __init__(self, indices, length=50, decay=8):
        self.indices = indices
        length = min(len(indices), length)

        self._colors = np.zeros(len(indices))
        self._colors[:length] = np.power(np.arange(length) / length, decay) * 255
        self.colors = np.zeros(len(indices)*3)
        self.colors[0::3] = self._colors
        self.colors[1::3] = self._colors
        self.colors[2::3] = self._colors

    def update(self, dt):
        self.colors = np.roll(self.colors, 3)
        return self.colors.reshape(-1,3)

class CpuRollTail:
    """
    single white pixel going around with dim tail color and speed by cpu percent
    """
    def __init__(self, indices, length=50, speed=1):
        self.indices = indices
        self.num_leds = len(indices)
        self.length = length
        self.speed = speed
        self.i = 0

    def update(self, dt):
        cpu = psutil.cpu_percent() / 100
        self.speed = int(cpu * 4+ 1)
        _colors = np.zeros(self.num_leds)
        _colors[:self.length] = np.arange(self.length) / self.length * 255
        colors = np.zeros(self.num_leds*3)
        colors[0::3] = _colors
        colors[1::3] = _colors * (1-cpu)
        colors[2::3] = _colors * (1-cpu)
        colors = np.roll(colors, self.i*3)
        self.i += self.speed
        return colors.reshape(-1,3)

class RainbowRoll:
    def __init__(self, indices):
        self.indices = indices
        colors = np.arange(len(indices)) / len(indices)
        self.colors = (matplotlib.cm.jet(colors)[:,:3] * 255).astype('int')

    def update(self, dt):
        self.colors = np.roll(self.colors, 3)
        return self.colors

class WhiteBreath:
    def __init__(self, indices):
        self.indices = indices
        self.num_leds = len(indices)
        self.t = time.time()

    def update(self, dt):
        millis = (time.time() - self.t) * 1000
        value = (np.exp(np.sin(millis/2000.0*np.pi)) - 0.36787944)*108.0;
        colors = [value] * self.num_leds * 3
        return np.array(colors).reshape(-1,3)

class Perlin:
    def __init__(self, indices, mode='rgb'):
        self.indices = indices
        self.speed = 0.5
        self.t = 0
        self.mode = mode

    def update(self, dt):
        speed = (psutil.cpu_percent() / 100) * 0.9 + 0.25
        v = np.array([noise.pnoise2(x/100, self.t, repeatx=len(self.indices)) for x in range(len(self.indices))])
        v = (v-v.min()) / (v.max() - v.min())
        
        if self.mode == 'rgb':
            colors = np.array( matplotlib.cm.hsv(v)[:,:3]*255 ).astype('int')
        elif self.mode == 'murrica':
            colors = np.array( matplotlib.cm.seismic(v)[:,:3]*255 ).astype('int')

        self.t += dt * speed
        return colors

class Sparkle:
    def __init__(self, indices):
        self.indices = indices
        self.num_leds = len(indices)
        self.t = time.monotonic()
        self.speed = 2

    def update(self, dt):
        v = np.array([noise.pnoise2(x/60, self.t, repeatx=self.num_leds) for x in range(self.num_leds*3)])
        #print(np.shape(v))
        #print(v.min(), v.max())

        v = (v-v.min()) / (v.max() - v.min())
        v = v**6

        #v = (v+1) / 2
        colors = np.array(v * 255).astype('uint8')
        self.t += dt * self.speed
        return colors.reshape(-1,3)

class Life:
    def __init__(self, indices):
        self.indices = indices
        self.num_leds = len(indices)
        #seed the board with random cells
        #self.c1 = np.array([np.random.randint(0,2) for i in range(self.num_leds)])
        #alt seed for a Sierpinksi Triangle
        self.c1 = np.zeros(self.num_leds, dtype=float)
        self.c1[self.num_leds // 2] = 1

        self.last_t = 0
        self.t = time.monotonic()
        self.step_time = 0.5#1.5

        self.c0 = np.array(self.c1, dtype=float)
        self.fade_time = 0.15
        self.fade = 1

    def update(self, dt):
        #update the simulation (or not if not enough time has passed)
        cpu_factor = psutil.cpu_percent() / 100
        fade_time = self.fade_time * (1.01 - cpu_factor)
        step_time = self.step_time * (1.01 - cpu_factor)

        #print(fade_time, step_time, cpu_factor)

        self.t += dt
        if (self.t - self.last_t) > step_time:
            self.last_t = self.t

            c1 = []
            for i, c0 in enumerate(self.c1):
                a = self.c0[i - 1]
                b = self.c0[i + 1] if i+1 < len(self.c0) else self.c0[-1]
                c1i = not a != (not b)
                c1.append( c1i )
            c1 = np.array(c1)
            self.c0 = self.c1
            if np.array_equal(self.c0, c1):#then the game has become static, we need to mix it up.
                #self.c1 = np.array([np.random.randint(0,2) for i in range(self.num_leds)])
                self.c1 = c1
            else:
                self.c1 = c1
            self.fade = 0 #reset the change tracker since we just changed

        #calculate the fade levels
        self.fade += dt / fade_time
        if self.fade > 1:
            self.fade = 1

        x = self.fade*6 - 3
        f = ( 1 / ( 1 + np.e**(-x) ) )

        #print(f"fade:{self.fade}, f:{f}")

        colors = self.c1 * f + self.c0 * (1 - f)

        colors = np.array([colors, colors, colors]).T
        colors = colors*255
        return colors

"""
Generate a wave that will move through the leds
and fade over time. Output should be smoothly ramped
in time to make sure that the wave looks smooth as
it moves
"""
class Wave:
    def __init__(self, indices, start=0, width=10, speed=30): #TODO: Add some color selection for the wave
        self.indices = indices
        self.start = start
        self.num_steps = len(indices)
        self.speed = speed
        self.ts = 0

        wave = np.sin(np.linspace(0, np.pi, width)) * 255
        wave = np.append(wave, np.zeros(self.num_steps - width))
        peak = np.argmax(wave)
        wave = np.roll(wave, start - peak)
        self.buffer = wave

        self.rf = np.random.rand() + 0.5
        self.gf = np.random.rand() + 0.5
        self.bf = np.random.rand() + 0.5

    def update(self, dt):
        if self.ts > 2 * self.num_steps:
            self.ts = 0

        self.ts += dt * self.speed
        step = int(self.ts)
        fade = 1 + (self.ts**2 / (self.num_steps*10))
        rf = fade * self.rf
        gf = fade * self.gf
        bf = fade * self.bf

        wave1 = np.roll(self.buffer, self.start - step)
        wave2 = np.roll(self.buffer, self.start + step)
        wave = wave1 + wave2

        return np.array([wave / rf, wave / gf, wave / bf]).T

class Pond:
    def __init__(self, indices, speed=30, num_waves=5, max_width=50):
        self.indices = indices
        self.num_steps = len(indices)
        self.num_waves = num_waves
        self.max_width = max_width
        self.waves = []
        self.add_wave()

    def add_wave(self):
        start = np.random.randint(0, self.num_steps)
        width = np.random.randint(10, self.max_width)
        wave = Wave(self.indices, width=width, start=start)
        self.waves.append(wave)

    def update(self, dt):
        output = np.zeros((self.num_steps,3))
        waves1 = []
        for w in self.waves:
            output = np.add(output, w.update(dt))
            if w.ts < 1*w.num_steps:
                waves1.append(w)

        self.waves = waves1
        if len(self.waves) < self.num_waves:
            high = (100 - psutil.cpu_percent()) + 1
            if np.random.randint(0, high) == 0:
                self.add_wave()

        return output

class Rain:
    def __init__(self, indices, reverse=False):
        pass
    
    def update(self, dt):
        pass

class Raindrop:
    def __init__(self, indices, start=0, width=10, speed=30, reverse=False):
        self.indices = indices
        self.start = start
        self.num_steps = len(indices)
        self.speed = speed
        self.ts = 0
        self.reversed = reverse

        drop = np.sin(np.linspace(0, np.pi/2, width)) * 255
        drop = np.append(drop, np.zeros(self.num_steps - width))
        
        self.buffer = np.zeros( (self.num_steps, 3) )
        self.buffer[:,2] = drop

    def update(self, dt):
        self.ts += dt
        shift = int(self.ts * self.speed) + self.start
        
        if self.reversed:
            shift = 0 - shift

        return np.roll( self.buffer, shift, 0 ) 

class CPUTimes:
    def __init__(self, indices, percpu=False):
        self.indices = indices
        self.percpu = percpu

    def update(self, dt):
        if self.percpu:
            p = psutil.cpu_times_percent(percpu=True)
            leds_per_cpu = int(len(self.indices) / len(p))
            assert leds_per_cpu >= 1.0
            colors = []
            for pp in p:
                colors += [pp.system, pp.user, pp.idle]*leds_per_cpu
            while len(colors) < len(self.indices)*3:
                colors += colors[-3:]
            return np.array(colors).reshape(-1,3)
        else:
            p = psutil.cpu_times_percent()
            r = p.system
            g = p.user
            b = p.idle
            colors = np.array([r,g,b]*len(self.indices)).reshape(-1,3)
        return colors

psutil.cpu_times_percent().user

if __name__ == '__main__':
    debug = len(sys.argv) > 1

    device = find_device()

    debug = device is None
    leds = LEDS(device, debug=debug)

    anims = [
            #Life(segs['all']),
            #Pond(segs['all'], num_waves=15),
            #Sparkle(segs['st']),
            #WhiteBreath(segs['all']),
            #CPUTimes(segs['all'], percpu=True),
            #CpuRollTail(segs['all'], length=15),
            #WhiteRollTail(segs['all'][::-1]),
            #Perlin(segs['all']),
            #RainbowRoll(segs['side']),
            #RainbowPulse(segs['side']),
            Raindrop(segs['side'])
            ]

    blend = True

    t = time.monotonic()

    while True:
        dt = time.monotonic() - t
        t  = time.monotonic()
        colors = np.zeros((total_leds,3), dtype='float64')
        for a in anims:
            c = a.update(dt)
            if blend:
                colors[a.indices] += c
            else:
                has_color = (c > 0).sum(axis=1) > 0
                colors[a.indices[has_color]] = c[has_color]
        leds.send(colors)

        e = time.monotonic()
        if e-t < 0.01:
            time.sleep( 0.01 - (e-t))
