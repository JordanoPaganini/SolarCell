from machine import Pin, I2C, SPI, ADC, RTC
from onewire import OneWire
from ds18x20 import DS18X20
from time import sleep, sleep_ms
from libs.bme280 import BME280
from dht import DHT11
from libs.sdcard import SDCard
from libs.max7219_8digit import Display
import uos

print('Init...')

ds_pin = Pin(4)
cs = Pin(15, Pin.OUT)
ss = Pin(5, Pin.OUT)

spi = SPI(1, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
I2C_bus = I2C(0, sda=Pin(21), scl=Pin(22), freq=10000)

rtc = RTC()
display = Display(spi, ss)
bme280 = BME280(i2c=I2C_bus)
ds_sensor = DS18X20(OneWire(ds_pin))
dht11 = DHT11(Pin(26))
voltage_sensor = ADC(Pin(34), atten=ADC.ATTN_11DB)
sd = SDCard(spi, cs)

adc_atten = 11

vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")
rom = bytearray(b'(\xff\xb13q\x17\x03.')

# with open("/sd/test01.csv", "w") as file:
#     file.write("Hello, SD World!\r\n")
#     file.write("This is a test\r\n")

def convert(leitura: float = None, R1: int = 1000, R2: int = 270):
    return (((leitura / 1000000) * (R1 + R2)) / R2)
        
def config_atten(read: float) -> bool:
    global adc_atten
    if read <= 149100 and adc_atten == 11:
        voltage_sensor.atten(ADC.ATTN_0DB)
        global adc_atten
        adc_atten = 0
        return True
    elif read >= 134900 and adc_atten == 0:
        voltage_sensor.atten(ADC.ATTN_11DB)
        global adc_atten
        adc_atten = 11
        return True
    else:
        return False

def read_voltage() -> float:
    read = voltage_sensor.read_uv()
    if config_atten(read):
        return voltage_sensor.read_uv() / 1000000
    else:
        return read
            
def ler_dados() -> dict:
    ds_sensor.convert_temp()
    sleep_ms(750)
    dht11.measure()
    data = {'temp': ds_sensor.read_temp(rom),
            'humidity': dht11.humidity(),
            'pressure': bme280.pressure,
            'date': rtc.datetime(),
            'voltage': convert(read_voltage())}
    return data

def display_voltage():
    for _ in range(30):
        res = convert(read_voltage())
        if len(str(res // 1)) > 3:
            display.write_to_buffer_with_dots(f'{res:.2f}Volt')
        else:
            display.write_to_buffer_with_dots(f'{res:.2f} Volt')
        display.display()
        sleep(0.975)
   
sleep(5)
print('Start...')

with open("/sd/test01.csv", "w") as file:
    file.write(f'Temperatura;Umidade;Pressão;Data;Hora;Tensão; \n')
    for _ in range(5):
        dados = ler_dados()
        file.write(f"""{dados["temp"]};
{dados["humidity"]};
{dados["pressure"]};
{dados["date"][2]}/{dados["date"][1]}/{dados["date"][0]};
{dados["date"][4]}:{dados["date"][5]}:{dados["date"][6]};
{dados["voltage"]}; \n""")
        display_voltage()
    file.close()
