'''Web server that displays a webpage used to view the data from the raspberry pi pico'''
# Impor the web-relevant server libraries
from flask import Flask, request, render_template, jsonify
import json

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


app = Flask(__name__)



# Global variable to store the 'start reading' signal
start_signal = False

def generate_plot():
    '''Function to generate the plot and save it as an image to the server folder'''
    readings, times = read_json_to_list('received_sensor_readings.json')

    t = [float(item) for item in times]
    a = [float(item) for item in readings]

    # Filter the noise of the accelerometer reading
    threshold = 0.8
    a = [0 if -threshold < x < threshold else x for x in a]
    a = signal.medfilt(a)
    a = signal.wiener(a)
    a = signal.medfilt(a)
    a = signal.detrend(a)

    # Integrate twice to find the position
    v = integrate.cumulative_trapezoid(a, x=times, initial=0)
    y = integrate.cumulative_trapezoid(v, x=times, initial=0)

    fig, (y_plot, v_plot, a_plot) = plt.subplots(3, 1, figsize=(12.8, 9.6),
                                                layout='constrained')  # a  figure with a 3x1 grid of Axes
    fig.suptitle('Lectura del sensor')

    y_plot.set_title('Posición y')
    y_plot.set_ylabel('Posición\n[mm]')
    y_plot.set_xlabel('Time [s]', loc='right')
    y_plot.plot(t, y)

    v_plot.set_title('Velocity')
    v_plot.set_ylabel('Velocity\n[mm/s]')
    v_plot.set_xlabel('Time [s]', loc='right')
    v_plot.plot(t, v)

    a_plot.set_title('Acceleration')
    a_plot.set_ylabel('Acceleration\n[m/s^2]')
    a_plot.set_xlabel('Time [s]', loc='right')
    a_plot.plot(t, a)

    # Save the plot in a static directory
    #plt.show()
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
    readings = []
    times = []

    try:
        with open(filename, 'r') as file:
            for line in file:
                try:
                    json_data = json.loads(line.strip())
                    readings.append(json_data.get('reading', 0))
                    times.append(json_data.get('time', 0))
                except ValueError:
                    # Handle JSON decoding error (ValueError in MicroPython)
                    print("JSON format error")
                    continue
    except IOError:
        print("Error reading the file")

    return readings, times

# A function to clear the file when the user is done
def clear_file(filename):
    with open(filename, 'w') as file:
        pass  # Opening in 'w' mode and writing nothing will clear the file

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
