# Import libraries for wifi connection
import network, time
# This libraries handle connection to the web server
import urequests, ujson
# These libraries handle GPIO functions in general, the second one
# handles the sensor
from machine import Pin, I2C
from micropython_bmi160 import bmi160


# Enable the LED
led = Pin("LED", Pin.OUT)

# Blink the LED 5 times quickly to indicate succesful boot
for i in range(0,5):   
    led.on()
    time.sleep(0.1)
    led.off() 
    time.sleep(0.1)
time.sleep(1)


# Function definitions first
def connect_to_wifi():
    '''Function that encapsulates instructions to connect to wifi. Returns False if the connection
    was not succesful and True if it was'''

    # Define the wifi parameters and a wlan object
    ssid = 'GONZALEZ_2.4G'
    password = 'Ufx970max405'
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Connect to wifi
    wlan.connect(ssid, password)

    # Wait for connection with a timeout
    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        timeout -= 1
        time.sleep(1)

    # Check and output True if the wifi is connected
    if wlan.isconnected():
        print("Connected to Wi-Fi")
        print(wlan.ifconfig())
        # Blink the LED twice to indicate succesful connection
        for i in range(0,2):   
            led.on()
            time.sleep(0.4)
            led.off() 
            time.sleep(0.4)
            return True
        else:
            print("Failed to connect to Wi-Fi")
            return False

# Instructions to read the sensor values
# It only reads for 6s because movement is not expected beyond that
def read_sensor():
    start_time = time.ticks_ms() #Time when we start measuring
    reading_duration = 6000 # Time to read in ms
    with open('sensor_readings.json', 'a') as file:
        while True:
            current_time = time.ticks_ms()
            elapsed_time = (current_time - start_time) / 1000 # Convert to seconds, it's better for the timestamps
            
            #Turn the LED On to indicate that the pico is measuring
            led.on()

            # This conversion is done here because the conversion in the library is badly implemented
            # Since the BMI 160 is a 16-Bit sensor, it outputs data in the +/- 32768 range (2^16)
            accx, accy, accz = bmi.acceleration

            # Since we set it up in the +-4G range, we divide the range by four.
            # Then, the raw value is divided by this factor and thus is expressed in Gs (multiples of gravity)
            accz = accz / 81912
            # Finally multiply by the value of gravity to get data in "raw" m/s^2
            accz = accz * 9.8065
            accz = accz - 9.8065
            accy = accy / 81912
            accy = accy * 9.8065
            accx = accx / 81912
            accx = accx * 9.8065
            accx = accx - 9.8065

            # Create a value pair of reading and timestamp
            reading_data = {
                'reading': accx,  # Replace with actual sensor reading
                'time': elapsed_time
            }
            #Add reading to file line by line
            file.write(ujson.dumps(reading_data) + '\n')
            
            #Print the readings (debugging purposes)
            print(f"x:{accx:.2f}m/s2, y:{accy:.2f}m/s2, z{accz:.2f}m/s2")
            
            # Check if the total reading duration is over
            if current_time - start_time >= reading_duration:
                led.off()
                break

def clear_file(filename):
    '''Function to empty the JSON file and avoid appending data to the old reading'''
    with open(filename, 'w') as file:
        pass  # Opening in 'w' mode and writing nothing will clear the file


def send_file_in_chunks(filename, url):
    '''Function to send the file to the server. It breaks the data down
    into a stream of bytes, because the Pi Pico has limited RAM and thus
    cannot open the full readings file in RAM to send it to the server'''

    headers = {'Content-Type': 'application/json'}

    # Function to generate file data in chunks (to avoid hogging RAM)
    def generate_file_data():
        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(1024)  # 1kB seems to work well in wifi LAN
                if not chunk:
                    break
                yield chunk

    # Post the data to the server
    response = urequests.post(url, data=generate_file_data(), headers=headers)
    # Delete the data from the pico if the server received it succesfully
    if response.text == 'JSON file received successfully':
        clear_file('sensor_readings.json')
    print(response.text)
    response.close()


# Set parameters to send data over the web
server_ip = 'http://192.168.0.8'
port = '5000'
url = 'http://192.168.0.8/upload_json'

# Create file for the readings if it doesn't exist
filename = 'sensor_readings.json'
with open(filename, 'a') as file:
        pass

# Establish sensor parameters and connect to the sensor
i2c = I2C(1, sda=Pin(26), scl=Pin(27))  # Correct I2C pins for RP2040
i2c.scan() # Find I2C devices
bmi = bmi160.BMI160(i2c, 0x68) # Connect to the sensor
bmi.acceleration_range = bmi160.ACCEL_RANGE_4G
bmi.acceleration_output_data_rate = bmi160.BANDWIDTH_400
# Blink the LED for half a second to indicate succesful sensor connection   
# If there is an error, the code will stop execution here and the LED won't turn on again
led.on()
time.sleep(1)
led.off() 
time.sleep(1)


# First, try to connect to wifi
# We try infinitely until a connection is established    
while True:
    if connect_to_wifi():
        break

# Check for the START signal from the server.
# If present, read and send data
while True:
        '''Main Loop'''
        # Check for the start signal
        response = urequests.get('http://192.168.0.8:5000/check_start_signal')
        
        # If the server returns the response, we invoke the reading and data send functions
        if response.json().get('start'):
            read_sensor()
            send_file_in_chunks('sensor_readings.json', 'http://192.168.0.8:5000/upload_json')
        
        time.sleep(1)  # Polling interval (can be adjusted, 1s seems to work well)

#read_sensor()
#send_file_in_chunks('sensor_readings.json', 'http://192.168.0.8:5000/upload_json')
