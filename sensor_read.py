from machine import Pin, ADC
import time

# Configure the ADC pins for the sensors

sv03 = ADC(Pin(26)) #GPIO26, physical pin 31
sharp = ADC(Pin(27)) #GPIO26, physical pin 32
sv03_vmax = 3.3 # Volts


while True:
    # Read the ADC value
    sv03_value = sv03.read_u16()
    sharp_value = sharp.read_u16()

    # Convert the value to a voltage (0 a 3.3V)
    sv03_voltage = (sv03_value / 65535) * 3.3
    sharp_voltage = (sharp_value / 65535) * 3.3

    # Print the voltage
    #print(sv03_voltage)
    print(sharp_voltage)

    # Calculate angle and distance values
    sv03_angle = ((sv03_voltage/sv03_vmax) * 333.3) #-160 # 160° es el ángulo max
    sharp_distance = 29.988 * (sharp_voltage**1.173)
    #print(sv03_angle)
    print(sharp_distance)

    # Pause between readings
    time.sleep(0.05)