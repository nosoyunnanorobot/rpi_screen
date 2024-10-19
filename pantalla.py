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
from datetime import datetime

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


# Create TFT LCD display class.
disp = TFT.ST7735(
    DC,
    rst=RST,
    spi=SPI.SpiDev(
        SPI_PORT,
        SPI_DEVICE,
        max_speed_hz=SPEED_HZ))


# Load default font.
font_20 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
font_25 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
font_30 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
font_35 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 35)
font_robo_35 = ImageFont.truetype("/home/pi/Python_ST7735/src/fonts/Roboto-Medium.ttf", 35)
font_mdi = ImageFont.truetype("/home/pi/Python_ST7735/src/fonts/materialdesignicons-webfont.ttf", 30)

temperature='\U000F10C2'

sd = 'df |grep mmcblk0p2  || echo "null: 0 0 0 0% null"'
sdb1 = 'df |grep d3682f49  || echo "null: 0 0 0 0% null"'
sda1 = 'df |grep 2351bf86  || echo "null: 0 0 0 0% null"'
screen_out = 'raspi-gpio set 18 op'
screen_on = 'raspi-gpio set 18 dh'
screen_off = 'raspi-gpio set 18 dl'
cmd = "cat /proc/uptime | cut -d\' \' -f1"

# Definir los rangos de tiempo
hora_inicio_noche = 22
hora_fin_noche = 8

# Initialize display.
disp.begin()

# Alternatively can clear to a black screen by calling:
disp.clear()

disp.display()

def draw_rotated_text(image, text, position, angle, font, fill=(255,255,255)):
    # Get rendered font width and height.
    x1, y1, x2, y2 = font.getbbox(text)
    width = x2 
    height = y2

   #print ("x1 " + str(x1))
   #print ("x2 " + str(x2))
   #print ("y1 " + str(y1))
   #print ("y2 " + str(y2))
            
    # Create a new image with transparent background to store the text.
    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    # Render the text.
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0,0), text, font=font, fill=fill)
    # Rotate the text image.
    rotated = textimage.rotate(angle, expand=1)
    # Paste the text into the image, using it as a mask for transparency.
    image.paste(rotated, position, rotated)

def get_cpu_temperature():
    cpu_temperature = psutil.sensors_temperatures().get('cpu_thermal', [])
    if cpu_temperature:
        return cpu_temperature[0].current
    else:
        return None    

def get_network_usage(interval=1):
    # Obtiene las estadísticas de red iniciales
    net_io_1 = psutil.net_io_counters()
    time.sleep(interval)
    # Obtiene las estadísticas de red después del intervalo
    net_io_2 = psutil.net_io_counters()
    
    # Calcula los bytes enviados y recibidos en el intervalo
    bytes_sent = net_io_2.bytes_sent - net_io_1.bytes_sent
    bytes_recv = net_io_2.bytes_recv - net_io_1.bytes_recv

    # Convierte los bytes a megabytes
    mb_sent = bytes_sent / (1024 * 1024)
    mb_recv = bytes_recv / (1024 * 1024)

    return mb_sent / interval, mb_recv / interval        
          
disp.clear()

while True:

    hora_actual = datetime.now().hour
    if hora_actual >= hora_inicio_noche or hora_actual < hora_fin_noche:
        print('Apagar pantalla')
        f_screen_off = subprocess.run(screen_off, shell=True, check=True, capture_output=True, encoding='utf-8')
        sleep(60)
    else:
        print('Encender pantalla')
        f_screen_out = subprocess.run(screen_out, shell=True, check=True, capture_output=True, encoding='utf-8')
        f_screen_on = subprocess.run(screen_on, shell=True, check=True, capture_output=True, encoding='utf-8')
    
        ### uptime    
        uptime = subprocess.check_output(cmd, shell = True, encoding='utf-8')
        uptime = uptime.strip()
        
        if float(uptime) < (120 * 60):
            uptimestr = str(round(float(uptime)/60)) + " minutes"
        elif float(uptime) < (48 * 60 * 60):
            uptimestr = str(round(float(uptime)/60/60)) + " hours"
        else:
            uptimestr = str(round(float(uptime)/60/60/24)) + " days"
            
        print(uptimestr)
        ### end uptime
        
        ### Calcul disk free
        result_sd = subprocess.run(sd, shell=True, check=True, capture_output=True, encoding='utf-8')
        result_sda1 = subprocess.run(sda1, shell=True, check=True, capture_output=True, encoding='utf-8')
        result_sdb1 = subprocess.run(sdb1, shell=True, check=True, capture_output=True, encoding='utf-8')
        ### Calcul disk free
        
        ### Display time  
        draw = disp.draw()        
        hora = time.strftime("%H:%M")
        cpu_temp = get_cpu_temperature()
        cpu_percent= psutil.cpu_percent()
        ram_available = psutil.virtual_memory().available / (1024 * 1024)
        mbps_sent, mbps_recv = get_network_usage()
        print ("Hora: " + str(hora))
        print ("Temp: " + str(round(cpu_temp,1)))
        print ("CPU: " + str(round(float(cpu_percent),2)))        
        print ("RAM: " + str(psutil.virtual_memory().percent))
        print(f"Enviado: {mbps_sent:.2f} MB/s, Recibido: {mbps_recv:.2f} MB/s")
        print(f"Enviado: {mbps_sent:04.1f} MB/s, Recibido: {mbps_recv:04.1f} MB/s")
        draw_rotated_text(disp.buffer, hora , (0, 20), 90, font_35, fill=(255,255,255))
        draw.rectangle((58, 0, 61, 168), outline=(255,255,0), fill=(255,255,0))
        draw_rotated_text(disp.buffer, str(round(cpu_temp,1))+ "°C", (70, 20), 90, font_30, fill=(255,255,255))         
        disp.display()
        
        ###
        time.sleep(5)
        draw.rectangle((63, 0, 128, 168), outline=(0,0,0), fill=(0,0,0))
        draw_rotated_text(disp.buffer, "CPU " + str(round(float(cpu_percent),2)) + "%", (75, 10), 90, font_25, fill=(255,255,255))
        disp.display()
        ###
        time.sleep(4)
        ###
        draw.rectangle((63, 0, 128, 168), outline=(0,0,0), fill=(0,0,0))
        
        if mbps_sent < 10:
            draw_rotated_text(disp.buffer, f"s: {mbps_sent:.1f}MB/s" , (70, 20), 90, font_20, fill=(255,255,255))
        else:
            draw_rotated_text(disp.buffer, f"s: {mbps_sent:.1f}MB/s" , (70, 10), 90, font_20, fill=(255,255,255))
           
        if mbps_recv < 10:
            draw_rotated_text(disp.buffer, f"r: {mbps_recv:.1f}MB/s" , (95, 20), 90, font_20, fill=(255,255,255))
        else:
            draw_rotated_text(disp.buffer, f"r: {mbps_recv:.1f}MB/s" , (95, 10), 90, font_20, fill=(255,255,255))
            
        disp.display()
        time.sleep(5)
        
        ### End display time
        
        # clear screen
        disp.clear((0, 0, 0)) 
        # end write
            
        ### draw rectangles SSD
        x1 = 0
        y1 = 0
        draw = disp.draw()
        
        draw_rotated_text(disp.buffer, "120G (" + str(result_sda1.stdout.split()[4]) + ")" , (0, 10), 90, font_20, fill=(173,216,230)) 
        draw.rectangle((x1+30, y1+0, x1+50, y1+158), outline="white", fill="black")
        draw.rectangle((x1+30, y1+(( 1- (float((result_sda1.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+50, y1+158),  outline=(173,216,230), fill=(173,216,230))

        draw_rotated_text(disp.buffer, "500G (" + str(result_sdb1.stdout.split()[4]) + ")" , (60, 10), 90, font_20, fill=(211,211,211))        
        draw.rectangle((x1+90, y1+0, x1+110, y1+158), outline="white", fill="black")
        draw.rectangle((x1+90, y1+(( 1- (float((result_sdb1.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+110, y1+158),  outline=(211,211,211), fill=(211,211,211))    
        
        print ("SD  : " + str(result_sd.stdout.split()[4]))
        print ("SDA1: " + str(result_sda1.stdout.split()[4]))
        print ("SDB1: " + str(result_sdb1.stdout.split()[4]))
        ### end draw rectangles sd
        
        # Write buffer to display hardware, must be called to make things visible on the display! 
        disp.display()
        time.sleep(7)
        disp.clear((0, 0, 0))
        # End Write 