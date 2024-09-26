from machine import Pin, ADC
import time

# Configure the ADC pins for the sensors

sv03 = ADC(Pin(26)) #GPIO26, physical pin 31
#sharp = ADC(Pin(27)) #GPIO27, physical pin 32
sharp = ADC(Pin(28)) #GPIO28, physical pin 34
sv03_vmax = 3.3 # Volts


while True:
    # Read the ADC value
    sv03_value = sv03.read_u16()
    sharp_value = sharp.read_u16()
    #sharp2_value = sharp2.read_u16()

    # Convert the value to a voltage (0 a 3.3V)
    sv03_voltage = (sv03_value / 65535) * 3.3
    sharp_voltage = (sharp_value / 65535) * 5
    #sharp2_voltage = (sharp2_value / 65535) * 5

    # Print the voltage0
    print('sv_voltage: ' + str(sv03_voltage))
    print('sharp_voltage :' + str(sharp_voltage))
    #print(sharp2_voltage)

    # Calculate angle and distance values
    sv03_angle = ((sv03_voltage/sv03_vmax) * 333.3) #-160 # 160° es el ángulo max
    C = 1.19
    k = 20.1
    if sharp_voltage == 0:
        pass
    else:
        sharp_distance = k * sharp_voltage**(-C)
    print("angle " + str(sv03_angle))
    print("distance " + str(sharp_distance))

    # Pause between readings
    time.sleep(0.05)