import RPi.GPIO as GPIO
import os
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
import Adafruit_DHT
import threading


from adafruit_ads1x15.analog_in import AnalogIn
from Firebase.firebase import firebaseReadChild,firebaseUpdateChild


# ********************************************************* Strawberry Backend ********************************************************* #

# *********************** for soil moisture *********************** #

# Define calibration constants
VOLTAGE_MIN = 0.0  # minimum voltage reading from sensor
VOLTAGE_MAX = 3.3  # maximum voltage reading from sensor
MOISTURE_MIN = 0   # moisture value corresponding to VOLTAGE_MIN
MOISTURE_MAX = 100 # moisture value corresponding to VOLTAGE_MAX

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)

# ********************** Pin Configuration ********************** #

Moisture_1 = AnalogIn(ads, ADS.P0)  # A0
Moisture_2 = AnalogIn(ads, ADS.P1)  # A1
Humid = 4 							# GPIO4
Trigger = 17                    	# GPIO17
Echo = 27							# GPIO27
FloatSwitch = 23 					# GPIO23
WaterPump = 24                      # GPIO24
# *********************** for humidity *********************** #
sensor = Adafruit_DHT.DHT22
# ********************** setup functions ********************** # 
def setup():
    
    GPIO.setwarnings(False) 
    if GPIO.getmode() == -1:
        GPIO.setmode(GPIO.BOARD)
    
    # Ultrasonic Sensor
    GPIO.setup(Trigger,GPIO.OUT)
    GPIO.setup(Echo,GPIO.IN)
    
    # Floatswitch
    GPIO.setup(FloatSwitch,GPIO.IN)
    
    # WaterPump
    GPIO.setup(WaterPump,GPIO.OUT)

# ********************** functions ********************** #  

# Humidity / Temperature celcius
def Humidity():

    humidity, temperature = Adafruit_DHT.read_retry(sensor, Humid)

    if humidity is not None:
    
        temp = float('%.1f'%(temperature))
        firebaseUpdateChild("Humidity","data",str('%.1f'%((((temp - 32) * 5 )/ 9)*0.1)) + "°C")
    else:
        firebaseUpdateChild("Humidity","data","unable to read")

        
# soil moisture
def calcu_moisture(Moisture_,moisture_sensor):
    voltage = moisture_sensor.voltage

    # Convert the voltage to a moisture value using linear interpolation
    moisture = (voltage - VOLTAGE_MIN) * \
               (MOISTURE_MAX - MOISTURE_MIN) / \
               (VOLTAGE_MAX - VOLTAGE_MIN) + MOISTURE_MIN
               
    firebaseUpdateChild(Moisture_,"data",round(float(moisture), 2))


# water level
def waterLevel():
    GPIO.output(Trigger, GPIO.LOW)
    GPIO.output(Trigger, GPIO.HIGH)
    
    time.sleep(0.00001)
    
    GPIO.output(Trigger, GPIO.LOW)

    StartTime = time.time()
    StopTime = time.time()
     
    
    # save StartTime
    while GPIO.input(Echo) == 0:
        StartTime = time.time()
    
    
    # save time of arrival
    while GPIO.input(Echo) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    pulse_duration = StopTime - StartTime    
    
    cm = round(pulse_duration * 17150, 2)
    inches = int(cm / 2.54)
    percent = int(inches*100/8)
    percent = 100 - percent
    
    #print(inches)
    if (GPIO.input(FloatSwitch)):
        firebaseUpdateChild("waterLevel","data","100%")
    else:
        firebaseUpdateChild("waterLevel","data",str(inches) + " inch")
    
# water pump
def waterPump():
    GPIO.output(WaterPump,firebaseReadChild("waterPump","data"))

# ********************** loop function ********************** #
def loop():

    # Humidity
    threading.Thread(target=Humidity, args=()).start()
    
    # Moisture 1
    threading.Thread(target=calcu_moisture, args=("Moisture 1",Moisture_1)).start()
    
    # Moisture 2
    threading.Thread(target=calcu_moisture, args=("Moisture 2",Moisture_2)).start()
    
    # water level
    threading.Thread(target=waterLevel, args=()).start()
    
    # water pump
    threading.Thread(target=waterPump, args=()).start()
   
    return loop()



setup()
loop()

