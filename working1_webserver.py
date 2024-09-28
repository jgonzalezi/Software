'''Web server that displays a webpage used to view the data from the raspberry pi pico'''
# Impor the web-relevant server libraries
from flask import Flask, request, render_template, jsonify
import json
import os


# Matplotlib handles data visualization
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# NumPy handles the different computations (speeds, positions, etc). It is imported as np by convention
# Note: Numpy handles numerical and array computations, similar to matlab. Be careful when operating with scalars
import numpy as np

# SciPy provides several signal processing and filtering capabilities
# it also provides cumulative integrals by trapezoidal rule
from scipy import integrate
from scipy import signal
from filterpy.kalman import KalmanFilter
from scipy.signal import savgol_filter


app = Flask(__name__)
start_signal = False

def generate_plot():
    '''Function to generate the plot and save it as an image to the server folder'''
    if not os.path.exists('static'):
        os.makedirs('static')

    Sharp_V_reading, CJMCU103_V_Reading, times = read_json_to_list('received_sensor_readings.json')
    
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.array([[0.], [0.]])  # estado inicial
    kf.F = np.array([[1., 1.], [0., 1.]])  # matriz de transición
    kf.H = np.array([[1., 0.]])  # matriz de observación
    kf.P *= 1000.  # incertidumbre inicial
    kf.R = 5  # incertidumbre de la medición
    kf.Q = np.eye(2)  # ruido del proceso

    # Aplicar el filtro de Kalman
    # Aplicar el filtro de Kalman y asegurar que el tiempo esté sincronizado
    datos_filtrados_Sharp = []
    datos_filtrados_CJMCU = []
    tiempos_filtrados = []  # Tiempo sincronizado
    for z,theta, t in zip(Sharp_V_reading,CJMCU103_V_Reading, times):
        kf.predict()
        kf.update(z)
        datos_filtrados_Sharp.append(kf.x[0])
        datos_filtrados_CJMCU.append(kf.x[0])
        tiempos_filtrados.append(t)  # Mantén el tiempo sincronizado con los datos filtrados
    '''
    for z in CJMCU103_V_Reading:
        kf.predict()
        kf.update(z)
        datos_filtrados_CJMCU.append(kf.x[0])
    '''
    r=[]
    theta =[]
    # Convertir a arrays de numpy
    for i in range(len(datos_filtrados_Sharp)):
        r.append(datos_filtrados_Sharp[i][0])
        theta.append(datos_filtrados_CJMCU[i][0])
    theta = (np.array(theta) / 3.33 * 333.3) 
    r = np.power(np.array(r),-1.19)* 20.1
    t = np.array(tiempos_filtrados)  # Usamos el tiempo filtrado
    r = savgol_filter(r, window_length=51, polyorder=3)
    theta = savgol_filter(theta, window_length=51, polyorder=3)

    '''threshold = 0.8
    # Filter the noise of the distance reading
    r = [0 if -threshold < x < threshold else x for x in r]
    r = signal.medfilt(r)
    r = signal.wiener(r)
    r = signal.detrend(r)

    # Filter the noise of the angle reading
    theta = [0 if -threshold < x < threshold else x for x in theta]
    theta = signal.medfilt(theta)
    theta = signal.wiener(theta)
    theta = signal.detrend(theta)
    
    '''
     # --- Derive velocity and acceleration using np.gradient (numerical differentiation) ---
    dt = np.gradient(t)

    # Linear velocity (dr/dt) and acceleration (d²r/dt²)
    r_dot = np.gradient(r, dt)  # First derivative: velocity
    r_ddot = np.gradient(r_dot, dt)  # Second derivative: acceleration

    # Angular velocity (dθ/dt) and angular acceleration (d²θ/dt²)
    theta_dot = np.gradient(theta, dt)  # Angular velocity
    theta_ddot = np.gradient(theta_dot, dt)  # Angular acceleration

    # --- Plot the results ---
    
    # Crear un solo gráfico con subplots
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))  # 2 filas, 3 columnas

    # Gráficos de r (Distancia)
    axs[0, 0].plot(t, r, label='Distance (r)')
    axs[0, 0].set_title('Distance vs Time')
    axs[0, 0].set_xlabel('Time (s)')
    axs[0, 0].set_ylabel('Distance (r)')
    axs[0, 0].legend()

    axs[0, 1].plot(t, r_dot, label='Linear Velocity (dr/dt)')
    axs[0, 1].set_title('Linear Velocity vs Time')
    axs[0, 1].set_xlabel('Time (s)')
    axs[0, 1].set_ylabel('Velocity (dr/dt)')
    axs[0, 1].legend()

    axs[0, 2].plot(t, r_ddot, label='Linear Acceleration (d²r/dt²)')
    axs[0, 2].set_title('Linear Acceleration vs Time')
    axs[0, 2].set_xlabel('Time (s)')
    axs[0, 2].set_ylabel('Acceleration (d²r/dt²)')
    axs[0, 2].legend()

    # Gráficos de theta (Ángulo)
    axs[1, 0].plot(t, theta, color='orange', label='Angle (θ)')
    axs[1, 0].set_title('Angle vs Time')
    axs[1, 0].set_xlabel('Time (s)')
    axs[1, 0].set_ylabel('Angle (θ)')
    axs[1, 0].legend()

    axs[1, 1].plot(t, theta_dot, color='orange', label='Angular Velocity (dθ/dt)')
    axs[1, 1].set_title('Angular Velocity vs Time')
    axs[1, 1].set_xlabel('Time (s)')
    axs[1, 1].set_ylabel('Velocity (dθ/dt)')
    axs[1, 1].legend()

    axs[1, 2].plot(t, theta_ddot, color='orange', label='Angular Acceleration (d²θ/dt²)')
    axs[1, 2].set_title('Angular Acceleration vs Time')
    axs[1, 2].set_xlabel('Time (s)')
    axs[1, 2].set_ylabel('Acceleration (d²θ/dt²)')
    axs[1, 2].legend()

    # Ajustar el layout y guardar la imagen
    plt.tight_layout()
    plt.savefig('static/plot.png')
    plt.close()


# When the user presses the 'start reading' button, JavaScript invokes
# this app route. It sets the start_signal flag to TRUE
@app.route('/start_reading')
def start_reading():
    global start_signal
    start_signal = True
    return "Start signal set"

# This route is polled continuously by the picoW to check if it should start reading
@app.route('/check_start_signal')
def check_start_signal():
    global start_signal
    # Respond to the request with the current value of the start_signal flag
    response = jsonify({'start': start_signal})
    # Reset the signal after it's checked
    start_signal = False
    return response

# Function to get the JSON data and put into a python list []
def read_json_to_list(filename):
    distance_readings = []
    angle_readings = []
    times = []

    try:
        with open(filename, 'r') as file:
            for line in file:
                try:
                    json_data = json.loads(line.strip())
                    distance_readings.append(json_data.get('distance_reading', 0))
                    angle_readings.append(json_data.get('angle_reading', 0))
                    times.append(json_data.get('time', 0))
                except ValueError:
                    # Handle JSON decoding error (ValueError in MicroPython)
                    print("JSON format error")
                    continue
    except IOError:
        print("Error reading the file")

    return distance_readings, angle_readings, times

# A function to clear the file when the user is done
def clear_file(filename):
    with open(filename, 'w') as file:
        pass  # Opening in 'w' mode and writing nothing will clear the file
    image_path = 'static/plot.png'  
    if os.path.exists(image_path):
        os.remove(image_path)

# Route for the button to invoke the clear_file function
# When the user presses the 'Clear Data' button, JavaScript invokes
# this app route.
@app.route('/clear_data')
def clear_data():
    clear_file('received_sensor_readings.json')
    return "Data cleared"


# Web route to receive the JSON data as a bit stream and write it onto the file
@app.route('/upload_json', methods=['POST'])
def upload_json():
    with open('received_sensor_readings.json', 'wb') as f:
        while True:
            chunk = request.stream.read(512)  # Adjust chunk size as needed
            if not chunk:
                break
            f.write(chunk)
    # Generate the new plot with the just uploaded data
    generate_plot()
    return 'JSON file received successfully'
    


# This app route of the server displays the webpage.
# It is the home route a web browser will access
@app.route('/')
def display_messages():
    #readings, times = read_json_to_list('received_sensor_readings.json')
    #readings_times = zip(times, readings)
    #return render_template('messages.html', readings_times=readings_times)
    return render_template('messages.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


#sensor_readings = read_json_to_list('received_sensor_readings.json')
#print(sensor_readings)
