from PIL import Image
from sys import stdin
from time import sleep
import numpy as np
import timg

class Visualize:
    def __init__(self):
        self.bufsize = int(120 * 48 / 4 + 1)

    def start(self):
        while True:
            read = stdin.buffer.read(3)

            if read == b':00':
                read = stdin.buffer.read(self.bufsize)

                if len(read) >= self.bufsize and read.endswith(b'\x00'):
                    self.read(read[:-1])

    def read(self, read):
        # b':00' + [... bytes ...] + b'\x00'
        barr = bytearray(read)

        # [... bytes ...] -> '... 11001010101 ...'
        bits = "".join(["{0:b}".format(l) for l in barr])
        bits = [bits[i:i+2] for i in range(0, len(bits), 2)]
        arr = [[int(l[0]) * 255, int(l[1]) * 255, 0] for l in bits]
        arr = np.asarray(arr, dtype='uint8').reshape((48, 120, 3))

        # arr = np.ones((120, 48, 3))
        img = Image.fromarray(arr, mode='RGB')
        img.save('test.png')

        rend = timg.Renderer()
        rend.load_image(img)

        print('\x1b[2J\x1b[H', end='')
        rend.render(timg.Ansi8FblockMethod)

if __name__ == '__main__':
    vis = Visualize()
    vis.start()