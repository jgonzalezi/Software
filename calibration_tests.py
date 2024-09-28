from machine import Pin, ADC
import time

l298_in1 = Pin(11, Pin.OUT) 
l298_in2 = Pin(12, Pin.OUT)
l298_enA = Pin(10, Pin.OUT)

def motor_forward():
    l298_in1.on() 
    l298_in2.off()
    l298_enA.on()

def motor_backward():
    l298_in1.off()
    l298_in2.on()
    l298_enA.on()

def motor_stop():
    l298_enA.off()
    
# Pulsadores para captura de ángulos
start_button = Pin(14, Pin.IN, Pin.PULL_UP)  # GPIO14
end_button = Pin(15, Pin.IN, Pin.PULL_UP)    # GPIO15

# Configuración del sensor SV03 para lectura de voltajes del sv_03
sv03 = ADC(Pin(26)) # GPIO26, physical pin 31

# Habilitar el LED integrado
led = Pin("LED", Pin.OUT)

start_angle = None
end_angle = None

def capture_start_angle():
    global start_angle
    led.on()
    while True:
        if not start_button.value():
            time.sleep(0.05)
            start_angle = sv03.read_u16()
            led.off()
            break
        

def capture_end_angle():
    global end_angle
    led.off()
    while True:
        if not end_button.value():
            motor_stop()
            led.on()
            time.sleep(0.5)
            end_angle = sv03.read_u16()
            time.sleep(0.2)
            led.off()
            break


# Función para regresar al ángulo inicial
def return_to_start():
    global start_angle
    tolerance = 50  # Ajusta este valor según la precisión que necesites
    print(f"Moviendo motor hacia el ángulo inicial: {start_angle} con tolerancia de {tolerance}")
    motor_backward()
    while True:
        current_angle = sv03.read_u16()
        if abs(current_angle - start_angle) <= tolerance:  # Verifica si está dentro del margen
            motor_stop()
            time.sleep(0.4)
            print(f"Motor detenido en ángulo inicial. Valor actual: {current_angle}")
            break
        time.sleep(0.01)

capture_start_angle()
motor_forward()
capture_end_angle()
return_to_start()

