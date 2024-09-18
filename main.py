# Import libraries for wifi connection
import network, time

# This libraries handle connection to the web server
import urequests, ujson

# These libraries handle GPIO functions in general
from machine import Pin




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



####--- Function Definitions ---###

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

            # Create a value pair of reading and timestamp
            reading_data = {
                'reading': accx,  # Replace with actual sensor reading
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
        response = urequests.get('http://192.168.0.8:5000/check_start_signal')
        
        # If the server returns the response, we invoke the reading and data send functions
        if response.json().get('start'):
            read_sensor()
            send_file_in_chunks('sensor_readings.json', 'http://192.168.0.8:5000/upload_json')
        
        time.sleep(1)  # Polling interval (can be adjusted, 1s seems to work well)