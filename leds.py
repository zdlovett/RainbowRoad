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

LISTEN_PORT = 8765

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

class Leds:
    def __init__(self, device=None, debug=False, total_leds=419 ):
        self.debug = debug
        self.total_leds = total_leds
        self.device = device
        if device is not None:
            self.device = serial.Serial(device.device, 3000000)
            print(self.device)

        self.gamma8 = [
            0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
            0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
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


        while len(colors) < self.total_leds*3:
            colors = np.append(colors, 1)

        if self.debug:
            out = ""
            for i in range(0,len(colors),3):
                out += colr.color('x', fore=tuple(colors[i:i+3]))

        if self.device is not None:
            colors = bytes(list(colors))
            self.device.write(colors)
            self.device.flush()


def service(soc, leds):
    color_len = leds.total_leds*3
    buffer = bytearray()
    done = False
    while not done:
        try:
            incoming = con.recv(1024)
            if len(incoming) == 0:
                done = True
            buffer += incoming
        except socket.timeout:
            pass
        else:
            if len(buffer) >= color_len:
                colors = np.frombuffer(buffer[:color_len], dtype='uint8')
                colors = np.reshape(colors, (-1, 3))
                leds.send(colors)
            
                buffer = buffer[color_len:]
    print("finished service")
         
         
if __name__ == "__main__":
    import socket
    from animations import perlin
    
    dev = find_device(hint='USB Serial Port')
    leds = Leds(dev)

    soc = socket.socket()
    soc.bind((socket.gethostname(), LISTEN_PORT))
    soc.settimeout(0.01)
    soc.listen()

    animation = iter(perlin(speed=0.1, size=200))
    
    done = False
    while not done:
        try:
            con, addr = soc.accept()
            print(f"connected to {addr}")
            service(con, leds)
        except KeyboardInterrupt:
            done = True
        except socket.timeout:
            leds.send(next(animation) * 2 / 3)
            

    
            
            