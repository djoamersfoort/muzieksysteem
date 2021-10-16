from PIL import Image, ImageDraw, ImageFont
import paho.mqtt.client as mqtt

from time import sleep
from sys import stdout
import numpy as np
import json

class Display:
    def __init__(self):
        # assign pil image
        self.font = './font/NotoSansMono-Regular.ttf'
        self.state = None
        self.scroll = 0
        
        # subscribe to player mqtt
        self.client = mqtt.Client()
        self.client.on_message = self.mqtt_handle

    def start(self):
        self.client.connect('mqtt.bitlair.nl')
        self.client.loop_start()
        self.client.subscribe('djo/player/state')

        while True:
            if self.state is not None:
                self.frame()
            
            sleep(0.25)

    def mqtt_handle(self, _c, _u, msg):
        state = msg.payload.decode('utf-8')
        self.state = json.loads(state)

        self.frame()

    def frame(self):
        image = Image.new('RGB', (120, 48), 'black')

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font, size=16)

        txt = self.state['title'] + ' | '
        
        self.scroll += 1
        if self.scroll >= len(txt):
            self.scroll = 0

        txt = txt[self.scroll:] + txt[:self.scroll]
        
        draw.text((60, 24), txt, fill='green', anchor='mm', font=font)

        self.output(image)
    
    def output(self, image):
        # [[r, g, b], [r, g, b]] -> [r, g, b, r, g, b]
        data = np.asarray(image).flatten()
        # [r, g, b, r, g, b] -> [r, g, r, g]
        data = np.delete(data, np.arange(2, data.size, 3))

        # [0, 255, 255, 0] -> '0110'
        b = ''.join(map(lambda l: str(min(l, 1)), data))
        # '0110110011011001' -> ['01101100', '11011001']
        b = [b[i:i+8] for i in range(0, len(b), 8)]

        barr = bytearray(b':00')
        barr.extend(map(lambda l: int(l, 2), b))
        barr.append(0)

        stdout.buffer.write(barr)

if __name__ == '__main__':
    disp = Display()
    disp.start()