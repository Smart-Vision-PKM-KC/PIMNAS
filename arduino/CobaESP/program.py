import serial
import time

# Initialize serial connection to the ESP32
arduino = serial.Serial(
    port='COM6',
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=5,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False,
    writeTimeout=2
)

def parse_data(data_line):
    try:
        # Strip any extraneous whitespace and split the data by comma
        data_parts = data_line.strip().decode().split(',')
        if len(data_parts) == 2:
            # Convert the parts to float values
            ultrasonic_value = float(data_parts[0])
            ldr_value = float(data_parts[1])
            return ultrasonic_value, ldr_value
        else:
            print("Data format error: ", data_line)
            return None, None
    except ValueError as e:
        print("ValueError: ", e)
        return None, None

try:
    while True:
        # Read a line of data from the serial connection
        data = arduino.readline()
        if data:
            ultrasonic, ldr = parse_data(data)
            if ultrasonic is not None and ldr is not None:
                print(f"Ultrasonic Distance: {ultrasonic} cm, LDR Value: {ldr}")
        time.sleep(1)
except Exception as e:
    print("Exception: ", e)
finally:
    arduino.close()
