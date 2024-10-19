import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import subprocess
import psutil
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import ST7735 as TFT
from PIL import Image, ImageDraw, ImageFont

# Configuración del servidor HTTP
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global override_end_time
        if self.path == "/toggle_screen":
            override_end_time = datetime.now() + timedelta(minutes=10)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Screen override activated for 10 minutes')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Not found')

def run_server():
    server_address = ('', 8080)  # Puerto en el que escuchará el servidor HTTP
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()

# Inicialización del servidor en un hilo separado
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# Configuración de la pantalla OLED
WIDTH = 128
HEIGHT = 160
SPEED_HZ = 4000000

DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

disp = TFT.ST7735(
    DC,
    rst=RST,
    spi=SPI.SpiDev(
        SPI_PORT,
        SPI_DEVICE,
        max_speed_hz=SPEED_HZ))

# Fuente predeterminada
font_20 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
font_25 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
font_30 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
font_35 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 35)

# Comandos para controlar la pantalla
screen_out = 'raspi-gpio set 18 op'
screen_on = 'raspi-gpio set 18 dh'
screen_off = 'raspi-gpio set 18 dl'
cmd = "cat /proc/uptime | cut -d\' \' -f1"

# Definir los rangos de tiempo
hora_inicio_noche = 22
hora_fin_noche = 8
override_end_time = None

# Inicializa la pantalla
disp.begin()
disp.clear()

def draw_rotated_text(image, text, position, angle, font, fill=(255,255,255)):
    x1, y1, x2, y2 = font.getbbox(text)
    width = x2
    height = y2

    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0,0), text, font=font, fill=fill)
    rotated = textimage.rotate(angle, expand=1)
    image.paste(rotated, position, rotated)

def get_cpu_temperature():
    cpu_temperature = psutil.sensors_temperatures().get('cpu_thermal', [])
    if cpu_temperature:
        return cpu_temperature[0].current
    else:
        return None    

def get_network_usage(interval=1):
    net_io_1 = psutil.net_io_counters()
    time.sleep(interval)
    net_io_2 = psutil.net_io_counters()
    
    bytes_sent = net_io_2.bytes_sent - net_io_1.bytes_sent
    bytes_recv = net_io_2.bytes_recv - net_io_1.bytes_recv

    mb_sent = bytes_sent / (1024 * 1024)
    mb_recv = bytes_recv / (1024 * 1024)

    return mb_sent / interval, mb_recv / interval        

while True:
    hora_actual = datetime.now().hour
    now = datetime.now()
    
    if override_end_time and now < override_end_time:
        # El modo de interrupción está activo
        print('Modo de interrupción activo')
        subprocess.run(screen_out, shell=True, check=True, capture_output=True, encoding='utf-8')
        subprocess.run(screen_on, shell=True, check=True, capture_output=True, encoding='utf-8')
    elif hora_actual >= hora_inicio_noche or hora_actual < hora_fin_noche:
        print('Apagar pantalla')
        subprocess.run(screen_off, shell=True, check=True, capture_output=True, encoding='utf-8')
    else:
        print('Encender pantalla')
        subprocess.run(screen_out, shell=True, check=True, capture_output=True, encoding='utf-8')
        subprocess.run(screen_on, shell=True, check=True, capture_output=True, encoding='utf-8')
        
        uptime = subprocess.check_output(cmd, shell=True, encoding='utf-8').strip()
        if float(uptime) < (120 * 60):
            uptimestr = str(round(float(uptime)/60)) + " minutes"
        elif float(uptime) < (48 * 60 * 60):
            uptimestr = str(round(float(uptime)/60/60)) + " hours"
        else:
            uptimestr = str(round(float(uptime)/60/60/24)) + " days"
            
        print(uptimestr)

        draw = disp.draw()
        hora = time.strftime("%H:%M")
        cpu_temp = get_cpu_temperature()
        cpu_percent = psutil.cpu_percent()
        ram_available = psutil.virtual_memory().available / (1024 * 1024)
        mbps_sent, mbps_recv = get_network_usage()
        print("Hora: " + str(hora))
        print("Temp: " + str(round(cpu_temp,1)))
        print("CPU: " + str(round(float(cpu_percent),2)))
        print("RAM: " + str(psutil.virtual_memory().percent))
        print(f"Enviado: {mbps_sent:.2f} MB/s, Recibido: {mbps_recv:.2f} MB/s")

        draw_rotated_text(disp.buffer, hora , (0, 20), 90, font_35, fill=(255,255,255))
        draw.rectangle((58, 0, 61, 168), outline=(255,255,0), fill=(255,255,0))
        draw_rotated_text(disp.buffer, str(round(cpu_temp,1))+ "°C", (70, 20), 90, font_30, fill=(255,255,255))         
        disp.display()
        
        time.sleep(5)
        draw.rectangle((63, 0, 128, 168), outline=(0,0,0), fill=(0,0,0))
        draw_rotated_text(disp.buffer, "CPU " + str(round(float(cpu_percent),2)) + "%", (75, 10), 90, font_25, fill=(255,255,255))
        disp.display()
        
        time.sleep(4)
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
        disp.clear((0, 0, 0)) 
        
        x1 = 0
        y1 = 0
        draw = disp.draw()
        
        result_sda1 = subprocess.run('df |grep 2351bf86  || echo "null: 0 0 0 0% null"', shell=True, check=True, capture_output=True, encoding='utf-8')
        draw_rotated_text(disp.buffer, "120G (" + str(result_sda1.stdout.split()[4]) + ")" , (0, 10), 90, font_20, fill=(173,216,230)) 
        draw.rectangle((x1+30, y1+0, x1+50, y1+158), outline="white", fill="black")
        draw.rectangle((x1+30, y1+(( 1- (float((result_sda1.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+50, y1+158),  outline=(173,216,230), fill=(173,216,230))

        draw_rotated_text(disp.buffer, "500G (" + str(result_sdb1.stdout.split()[4]) + ")" , (60, 10), 90, font_20, fill=(211,211,211))        
        draw.rectangle((x1+90, y1+0, x1+110, y1+158), outline="white", fill="black")
        draw.rectangle((x1+90, y1+(( 1- (float((result_sdb1.stdout.split()[4]).replace('%', 'e-2')))) * 158 ), x1+110, y1+158),  outline=(211,211,211), fill=(211,211,211))    
        
        disp.display()
        time.sleep(7)
        disp.clear((0, 0, 0))
