# Import libraries for wifi connection
import network, time

# This libraries handle connection to the web server
import urequests, ujson

# These libraries handle GPIO functions in general
from machine import Pin, ADC




####--- Boot Sequence ---#####

# Enable the LED
led = Pin("LED", Pin.OUT)
# Blink the LED 5 times quickly to indicate succesful boot
for i in range(0,5):   
    led.on()
    time.sleep(0.1)
    led.off() 
    time.sleep(0.1)
time.sleep(1)



####--- Function and Parameter Definitions ---###



def connect_to_wifi():
    '''Function that encapsulates instructions to connect to wifi. Returns False if the connection
    was not succesful and True if it was'''

    # Define the wifi parameters and a wlan object
    ssid = 'PROYDINAMICA'
    password = 'qwerty123'
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
        
## Instructions to read the sensor values
# It only reads for 9s because movement is not expected beyond that

# Configure the ADC pins for the sensors
sv03 = ADC(Pin(26)) #GPIO26, physical pin 31
sharp = ADC(Pin(28)) #GPIO28, physical pin 34
sv03_vmax = 3.3

def read_sensor():
    start_time = time.ticks_ms() #Time when we start measuring
    reading_duration = 9000 # Time to read in ms
    with open('sensor_readings.json', 'a') as file:
        while True:
            current_time = time.ticks_ms()
            elapsed_time = (current_time - start_time) / 1000 # Convert to seconds, it's better for the timestamps
            
            #Turn the LED On to indicate that the pico is measuring
            led.on()

            # Read the ADC value
            sv03_value = sv03.read_u16()
            sharp_value = sharp.read_u16()

            # Convert the value to a voltage (0 to 3.3V)
            sv03_voltage = (sv03_value / 65535) * sv03_vmax
            sharp_voltage = (sharp_value / 65535) * 5
            if sharp_voltage == 0:
                continue
            
            # Print the voltage
            #print(sv03_voltage)
            print(sharp_voltage)

            # Calculate angle and distance values
            #sv03_angle = ((sv03_voltage/sv03_vmax) * 333.3) #-160 # 160° es el ángulo max
            #C = 1.19
            #k = 20.1
            #sharp_distance = k * (sharp_voltage**(-C))
            #print(sv03_angle)
            #print(sharp_distance)

            # Create a value pair of reading and timestamp
            reading_data = {
                'angle_reading': sv03_voltage,  #Replace with actual sensor reading variable
                'distance_reading': sharp_voltage,
                'time': elapsed_time
            }
            #Add reading to file line by line
            file.write(ujson.dumps(reading_data) + '\n')
                
            #Print the readings (debugging purposes)
            print("")
            
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
server_ip = 'http://192.168.122.170'
port = ':5000'
upload_url = server_ip + port + '/upload_json'


# Create file for the readings if it doesn't exist
filename = 'sensor_readings.json'
with open(filename, 'a') as file:
        pass



####---- MAIN LOOP ----####

# First, try to connect to wifi
# We try infinitely until a connection is established    
while True:
    if connect_to_wifi():
        break

# Check for the START signal from the server. If present, read and send data
while True:
        '''Main Loop'''
        # Check for the start signal
        response = urequests.get(server_ip + port + '/check_start_signal')
        
        # If the server returns the response, we invoke the reading and data send functions
        if response.json().get('start'):
            read_sensor()
            send_file_in_chunks('sensor_readings.json', upload_url)
        
        time.sleep(1)  # Polling interval (can be adjusted, 1s seems to work well)