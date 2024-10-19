#############################################################################
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import ST7735 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import subprocess
import time
import psutil
import socket

WIDTH = 128
HEIGHT = 160
SPEED_HZ = 4000000


# Raspberry Pi configuration.
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# BeagleBone Black configuration.
# DC = 'P9_15'
# RST = 'P9_12'
# SPI_PORT = 1
# SPI_DEVICE = 0

# Create TFT LCD display class.
disp = TFT.ST7735(
    DC,
    rst=RST,
    spi=SPI.SpiDev(
        SPI_PORT,
        SPI_DEVICE,
        max_speed_hz=SPEED_HZ))

# Initialize display.
disp.begin()

# Alternatively can clear to a black screen by calling:
disp.clear()

# Load default font.
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
font_25 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
font_30 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
font_25_2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 25)
font_20 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
font_35 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 35)
font_15 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
font_mdi = ImageFont.truetype("/home/pi/Python_ST7735/src/fonts/materialdesignicons-webfont.ttf", 30)

sd='df |grep mmcblk0p2  || echo "null: 0 0 0 0% null"'
sdb1='df |grep sdb1  || echo "null: 0 0 0 0% null"'
sda1='df |grep sda1  || echo "null: 0 0 0 0% null"'

disp.display()


# Define a function to create rotated text.  Unfortunately PIL doesn't have good
# native support for rotated fonts, but this function can be used to make a
# text image and rotate it so it's easy to paste in the buffer.
def draw_rotated_text(image, text, position, angle, font, fill=(255,255,255)):
    # Get rendered font width and height.
    draw = ImageDraw.Draw(image)
    #width, height = draw.textsize(text, font=font) -- Se eliminar por estar deprecada.
    bbox = draw.textbbox((0, 0), text, font=font)
    
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1] + 4
        
    # Create a new image with transparent background to store the text.
    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    # Render the text.
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0,0), text, font=font, fill=fill)
    # Rotate the text image.
    rotated = textimage.rotate(angle, expand=1)
    # Paste the text into the image, using it as a mask for transparency.
    image.paste(rotated, position, rotated)

def get_ip_address():
    # Obtener todas las interfaces de red
    interfaces = psutil.net_if_addrs()
    
    # Iterar sobre las interfaces y encontrar la dirección IP de la interfaz de red activa
    for interface_name, interface_addresses in interfaces.items():
        for address in interface_addresses:
            if address.family == socket.AF_INET:  # IPv4
                if not address.address.startswith("127."):  # Ignorar la dirección IP local
                    return address.address
    return None
       

def get_cpu_temperature():
    cpu_temperature = psutil.sensors_temperatures().get('cpu_thermal', [])
    if cpu_temperature:
        return cpu_temperature[0].current
    else:
        return None    
    
disp.clear()

while True:
    # Write two lines of white text on the buffer, rotated 90 degrees counter clockwise.
    
    hora = time.strftime("%H:%M")
    print (hora)
    draw_rotated_text(disp.buffer, hora , (50, 30), 90, font_35, fill=(255,255,255))
    
    # Write buffer to display hardware, must be called to make things visible on the display!
    disp.display()
    time.sleep(3)
    disp.clear((0, 0, 0))
    
    result_sd = subprocess.run(sd, shell=True, check=True, capture_output=True, encoding='utf-8')
    result_sda1 = subprocess.run(sda1, shell=True, check=True, capture_output=True, encoding='utf-8')
    result_sdb1 = subprocess.run(sdb1, shell=True, check=True, capture_output=True, encoding='utf-8')
    
    
    cpu_temp = get_cpu_temperature()

    draw_rotated_text(disp.buffer, f"CPU: {cpu_temp}°C", (0, 0), 90, font_15, fill=(255,255,255))   
 ## draw_rotated_text(disp.buffer, f"CPU Tem: {cpu_temp}°C", (0, 0), 90, font_15, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, 'SD', (60, 20), 90, font, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, str((result_sd.stdout.split()[4]))  , (60, 50), 90, font, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, 'Media', (90, 20), 90, font, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, str((result_sda1.stdout.split()[4]))  , (90, 50), 90, font, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, str((result_sdb1.stdout.split()[4]))  , (120, 50), 90, font, fill=(255,255,255))
 
    x1 = 0
    y1 = 0
    draw = disp.draw()

    
    draw.rectangle((x1+20, y1+0, x1+40, y1+158), outline="red", fill="black")
    draw.rectangle((x1+20, y1+(( 1- (float((result_sda1.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+40, y1+158),  outline="red", fill="red")
    
    draw.rectangle((x1+60, y1+0, x1+80, y1+158), outline="blue", fill="black")
    draw.rectangle((x1+60, y1+(( 1- (float((result_sdb1.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+80, y1+158),  outline="blue", fill="blue")    

    draw.rectangle((x1+100, y1+0, x1+120, y1+158), outline="green", fill="black")
    draw.rectangle((x1+100, y1+(( 1- (float((result_sd.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+120, y1+158),  outline="green", fill="green")

    print ("Temp: " + str(round(cpu_temp,1)))
    print ("SD  : " + str(result_sd.stdout.split()[4]))
    print ("SDA1: " + str(result_sda1.stdout.split()[4]))
    print ("SDB1: " + str(result_sdb1.stdout.split()[4]))
    
    print (result_sd.stdout.split()[4])
    print(float((result_sd.stdout.split()[4]).replace('%', 'e-2')))

    
    disp.display()
    time.sleep(3)
    disp.clear((0, 0, 0))
    
    ram_available = psutil.virtual_memory().available / (1024 * 1024)    
    cpu_percent= psutil.cpu_percent()
        
    ip_address = get_ip_address()
    
 ## draw_rotated_text(disp.buffer, 'RAM Available:', (0, 35), 90, font_15, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, f"{ram_available:.2f} MB", (30, 60), 90, font_15, fill=(255,255,255))
 ## draw_rotated_text(disp.buffer, f"{cpu_percent:.2f} %", (60, 60), 90, font_15, fill=(255,255,255))    
 ## draw_rotated_text(disp.buffer, str(ip_address), (90, 30), 90, font_15, fill=(255,255,255))    

    print ("CPU: " + str(round(float(cpu_percent),2)))
    print ("IP : " + str(ip_address))
    print ("RAM: " + str(psutil.virtual_memory().percent))
    
    cmd = "cat /proc/uptime | cut -d\' \' -f1"
    uptime = subprocess.check_output(cmd, shell = True, encoding='utf-8')
    uptime = uptime.strip()

    # Less than 2 hours?
    if float(uptime) < (120 * 60):
        uptimestr = str(round(float(uptime)/60)) + " minutes"
    # Less than 48 hours?
    elif float(uptime) < (48 * 60 * 60):
        uptimestr = str(round(float(uptime)/60/60)) + " hours"
    # More than 2 days
    else:
        uptimestr = str(round(float(uptime)/60/60/24)) + " days"
        
    print(uptimestr)
    
   # disp.display()
   # time.sleep(3)
   # disp.clear((0, 0, 0))
    
    disp.reset
    time.sleep(3)

    #image = Image.open('raspberry-pi-logo-6328.png')    
    #image = image.rotate(90).resize((WIDTH, HEIGHT))
    #disp.display(image)
    #time.sleep(1)
    #disp.clear((0, 0, 0))
