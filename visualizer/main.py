from PIL import Image, ImageDraw, ImageFont
import paho.mqtt.client as mqtt
from sys import stdout
from math import floor
import numpy as np
import time

# Render scrolling text
class TextRender:
    def __init__(self, uri, size, color):
        self.color = color
        self.font = ImageFont.truetype(uri, size=size)
        self.value = ''
        self.x = 0

    def text(self, text):
        self.value = text
        self.x = 0

        w, h = self.font.getsize(text)
        self.scroll = w >= 120
        self.width = 120

        if self.scroll:
            text += '    '
            w, h = self.font.getsize(text)
            self.width += w

        self.height = h

        self.image = Image.new('RGB', (self.width, h), 'black')
        draw = ImageDraw.Draw(self.image)
        
        if self.scroll:
            # draw left half
            draw.text((0, 0), text, fill=self.color, anchor='lt', font=self.font)
            # draw right half
            draw.text((w, 0), text, fill=self.color, anchor='lt', font=self.font)
        else:
            # draw middle
            draw.text((60, 0), text, fill=self.color, anchor='mt', font=self.font)

    # draws image on line y onwards
    def draw(self, image, y):
        area = self.image.crop((self.x, 0, self.width, self.height))
        image.paste(area, (0, y))

        # scroll forward if applicable        
        if self.scroll:
            self.x += 1
            if self.x >= self.width - 120:
                self.x = 0

# Bar renderer
def time_text(seek):
    seconds = seek
    minutes = floor(seconds / 60)
    seconds -= minutes * 60

    p_text = str(minutes)
    p_text += ':' + ('0' if seconds < 10 else '')
    p_text += str(seconds)
    
    return p_text

class Progress:
    def __init__(self, uri, color):
        self.font = ImageFont.truetype(uri, size=12)
        self.color = color

        self.seek = 0
        self.duration = 0
    
    def set(self, seek=None, duration=None):
        self.seek = seek or self.seek
        self.duration = duration or self.duration

        self.image = Image.new('RGB', (120, 12), 'black')
        draw = ImageDraw.Draw(self.image)

        # draw "bar"
        if self.duration > 0:
            progress = (self.seek / self.duration)
        else:
            progress = 0

        width = int(120 * progress)
        draw.line(((0, 10), (width, 10)), width=2, fill=self.color)

        # draw start and end
        draw.text((1, 11), time_text(self.seek), fill=self.color, font=self.font, anchor='lb')
        draw.text((120, 11), time_text(self.duration), fill=self.color, font=self.font, anchor='rb')

    def draw(self, image, y):
        area = self.image.crop((0, 0, 120, 12))
        image.paste(area, (0, y))      

# MQTT Connection
class Volumio:
    def __init__(self, handle):
        self.client = mqtt.Client()
        self.client.on_message = handle

    def connect(self, host):
        self.client.connect(host)
        self.client.loop_start()

        self.client.subscribe('djo/player/title')
        self.client.subscribe('djo/player/artist')
        self.client.subscribe('djo/player/album')
        self.client.subscribe('djo/player/seek')
        self.client.subscribe('djo/player/duration')
        self.client.subscribe('bitlair/state/djo')

# Decoder
class Encode:
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

# Main Display class
terminus = './font/TerminusTTF-4.49.1.ttf'

class Display:
    def __init__(self):
        self.image = Image.new('RGB', (120, 48))

        self.encoder = Encode()
        self.mqtt = Volumio(self.message)
        self.has_drawn = False
        self.state = None

        self.title = TextRender(terminus, 12, 'orange')
        self.artist = TextRender(terminus, 12, 'green')
        self.album = TextRender(terminus, 12, 'green')
        self.progress = Progress(terminus, 'red')

    def message(self, _c, _u, msg):
        topic = msg.topic.split('/')[-1]
        payload = msg.payload.decode()

        if topic in ['title', 'artist', 'album']:
            getattr(self, topic).text(payload)

        if topic == 'seek':
            self.progress.set(seek=int(int(payload) / 1000))
        if topic == 'duration':
            self.progress.set(duration=int(payload))
        if topic == 'djo':
            self.state = payload == 'open'
    
    def exiting(self):
        font = ImageFont.truetype(terminus, size=18)
        image = Image.new('RGB', (120, 48), 'black')
        draw = ImageDraw.Draw(image)

        draw.text((60, 24), 'DOEI!', fill='orange', font=font, anchor='mm')
        self.encoder.output(image)

    def start(self):
        self.mqtt.connect('mqtt.bitlair.nl')

        self.title.text('Verbinden')
        self.artist.text('met Volumio')
        self.album.text('')
        self.progress.set(seek=69, duration=420)

        while True:
            if self.state == True:
                self.frame()
                self.has_drawn = True
            elif self.state == False:
                if self.has_drawn:
                    self.exiting()
                exit(0)
            # time.sleep(0.05)
        
    def frame(self):
        self.title.draw(self.image, 0)
        self.artist.draw(self.image, 12)
        self.album.draw(self.image, 24)
        self.progress.draw(self.image, 36)

        self.encoder.output(self.image)

if __name__ == '__main__':
    disp = Display()
    disp.start()