from PIL import Image, ImageDraw, ImageFont
import paho.mqtt.client as mqtt
from threading import Thread
from time import sleep
from sys import stdout
from math import floor
import numpy as np
import requests

class Display:
    def __init__(self):
        self.state = {
            'title': 'Je Mama',
            'artist': '- Wiebe',
            'status': 'play',
            'seek': (69 * 60) * 1000,
            'duration': (69 * 60) * 2,
            'volume': 100
        }

        self.show_volume = None
        self.next_frame = True

        self.font = './font/TerminusTTF-4.49.1.ttf'
        self.big_font = ImageFont.truetype(self.font, size=16)
        self.small_font = ImageFont.truetype(self.font, size=12)

        self.t_scroll = 0
        self.a_scroll = 0

        # subscribe to player mqtt
        self.client = mqtt.Client()
        self.client.on_message = self.mqtt_handle

    def start(self):
        self.client.connect('mqtt.bitlair.nl')
        self.client.loop_start()

        self.client.subscribe('djo/player/#')

        self.thread = Thread(target=self.loop)
        self.thread.start()

    def loop(self):
        while True:
            if self.show_volume:
                self.show_volume = False
                self.volume()
            else:
                self.frame()
            
            # sleep(.05)

    def mqtt_handle(self, _c, _u, msg):
        topic = msg.topic.split('/')[-1]
        self.state[topic] = msg.payload.decode()

        if topic == 'volume':
            if self.show_volume is None:
                self.show_volume = False
            else:
                self.show_volume = True

    def volume(self):
        image = Image.new('RGB', (120, 48), 'black')

        draw = ImageDraw.Draw(image)

        progress = int(self.state['volume']) / 100
        draw.line([(0, 0), (int(120 * progress), 0)], fill='red', width=92)

        self.output(image)
        sleep(2)

    def frame(self):
        image = Image.new('RGB', (120, 48), 'black')

        draw = ImageDraw.Draw(image)

        title = self.state['title']
        artist = self.state['artist']

        t_width = self.big_font.getsize(title)[0]
        a_width = self.big_font.getsize(artist)[0]

        p_text = '- paused -'
        if self.state['status'] == 'play':
            seconds = int(int(self.state['seek']) / 1000)
            minutes = floor(seconds / 60)
            seconds -= minutes * 60

            p_text = str(minutes)
            p_text += ':' + ('0' if seconds < 10 else '')
            p_text += str(seconds)

        draw.text((60, 46), p_text, fill='green', anchor='mb', font=self.small_font)

        progress = (int(self.state['seek']) / 1000) / int(self.state['duration'])
        draw.line([(0, 46), (int(119 * progress), 46)], fill='green', width=2)

        if t_width >= 120:
            self.t_scroll += 2.5
            if self.t_scroll >= t_width + 150:
                self.t_scroll = 0
            
            draw.text((120 - self.t_scroll, 8), title, fill='orange', anchor='lm', font=self.big_font)
        else:
            draw.text((60, 8), title, fill='orange', anchor='mm', font=self.big_font)

        if a_width >= 120:
            self.a_scroll += 2.5
            if self.a_scroll >= a_width + 150:
                self.a_scroll = 0
            
            draw.text((120 - self.a_scroll, 22), artist, fill='orange', anchor='lm', font=self.big_font)
        else:
            draw.text((60, 22), artist, fill='orange', anchor='mm', font=self.big_font)

        self.output(image)
    
    def output(self, image):
        # [[r, g, b], [r, g, b]] -> [r, g, b, r, g, b]
        data = np.asarray(image, dtype='uint8').flatten()
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

# class Output:
#     def __init__(self):
        # self.font = './font/TerminusTTF-4.49.1.ttf'
        # self.big_font = ImageFont.truetype(self.font, size=16)
        # self.small_font = ImageFont.truetype(self.font, size=12)

        # self.t_scroll = 0
        # self.a_scroll = 0
    


if __name__ == '__main__':
    disp = Display()
    disp.start()