import serial
import torch
import time
from playsound import playsound
import cv2
from ultralytics import YOLO

# Initialize first_time variable to ensure the sound only plays once
first_time = True

# Function to play sound and ensure camera detection pauses while sound is playing
def play_sound_and_pause(file_path):
    playsound(file_path)  # Play the sound and wait for it to finish before resuming

# Read sensor data from ESP32
def read_sensors(port='/dev/ttyACM0', baudrate=115200):
    with serial.Serial(port, baudrate) as ser:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if ',' in line:  # Check if there's at least one comma
                if line.count(',') == 1:  # Check if there is exactly one comma
                    try:
                        distance, light = map(float, line.split(','))
                        return distance, light
                    except ValueError:
                        print(f"Error parsing line: {line}")
                        continue  # Continue to the next line if there's an error
                else:
                    print(f"Unexpected format: {line}")
                    continue  # Continue to the next line if format is unexpected
            else:
                print(f"No comma found in line: {line}")
                continue  # Continue to the next line if there's no comma

# Check the conditions for playing sounds based on distance and light sensor data
def check_conditions(distance, light):
    if distance > 30:
        play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/jarak anda terlalu jauh.mp3")
    elif light > 2400:
        play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Ruangan anda terlalu gelap.mp3")
    else:
        play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Tunggu 1 menit.mp3")
        return "Tunggu satu menit."

def wait_for_conditions():
    while True:
        distance, light = read_sensors()
        message = check_conditions(distance, light)
        if message == "Tunggu satu menit.":
            break
        time.sleep(0.5)  # Wait for 0.5 seconds before rechecking

# Load YOLO model and perform inference
def run_yolo_inference():
    global first_time  # Ensure first_time is referenced globally
    wait_for_conditions()
    model = YOLO("best.pt")  # Use YOLOv11 weights
    ser = serial.Serial('/dev/ttyACM0', 115200)  # Open serial communication with ESP32

    # Load video feed or webcam (you can adjust this to use a video file or other sources)
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model(frame)  # Run inference with YOLOv11
        
        # Play the sound only the first time the camera is active
        if first_time:
            play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/ready.mp3")  # Play sound once
            first_time = False  # Set to False to prevent sound from playing again

        for result in results:
            # Get class names and their corresponding IDs
            for class_id, confidence, bbox in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy):
                class_name = model.names[int(class_id)]
                print(f"Detected {class_name} with confidence {confidence}")
                
                # Send class name to ESP32 via serial
                ser.write(class_name.encode('utf-8')) 
                
                # Play corresponding sound and pause detection
                if class_name == 'Neozep Forte':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Neozep Forte.mp3")
                elif class_name == 'Intunal F':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Intunal F.mp3")
                elif class_name == 'Paramex':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Paramex.mp3")
                elif class_name == 'Biogesic Paracetamol':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Biolgesic paracetamol.mp3")
                elif class_name == 'Bodrex Extra':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Bodrex Extra.mp3")
                elif class_name == 'Bodrex Flu dan Batuk PE':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Bodrex Flu dan Batuk PE.mp3")
                elif class_name == 'Bodrex Migra':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Bodrex Migra.mp3")
                elif class_name == 'Decolgen':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Decolgen.mp3")
                elif class_name == 'Decolsin':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Decolsin.mp3")
                elif class_name == 'Dumin Paracetamol':
                    play_sound_and_pause("/home/jetson/Music/obat_sound/Dumin Paracetamol.mp3")
                elif class_name == 'Insana Flu':
                    play_sound_and_pause("/home/jetson/Music/obat_sound/Insana Flu.mp3")
                elif class_name == 'Intunal Kaplet':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Intunal Kaplet.mp3")
                elif class_name == 'Inza':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Inza.mp3")
                elif class_name == 'Mixagrip':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Mixagrip Flu.mp3")
                elif class_name == 'Mixagrip Flu dan Batuk':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Mixagrip Flu dan Batuk.mp3")
                elif class_name == 'Neo Rheumacyl':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Neorheumacyl.mp3")
                elif class_name == 'Paramex':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Paramex.mp3")
                elif class_name == 'Oskadon Sakit Kepala':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Oskadon Sakit Kepala.mp3")
                elif class_name == 'Oskadon SP':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Oskadon SP.mp3")
                elif class_name == 'Pamol Paracetamol':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Pamol Paracetamol.mp3")
                    continue
                elif class_name == 'Panadol Cold Flu':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Panadol Cold Flu.mp3")
                elif class_name == 'Panadol Extra Paracetamol':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Panadol Extra Paracetamol.mp3")
                elif class_name == 'Panadol Paracetamol':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Panadol Paracetamol.mp3")
                elif class_name == 'Paramex Flu dan Batuk PE':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Paramex Flu dan Batuk PE.mp3")
                elif class_name == 'Paramex Nyeri Otot':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Paramex Nyeri Otot.mp3")
                elif class_name == 'Poldan Mig':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Poldan MIG.mp3")
                elif class_name == 'Procold Flu':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Procold Flu.mp3")
                elif class_name == 'Procold Flu dan Batuk':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Procold Flu dan Batuk.mp3")
                elif class_name == 'Sanaflu':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Sanaflu.mp3")
                elif class_name == 'Sanmol':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Sanmol.mp3")
                elif class_name == 'Saridon':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Saridon.mp3")
                elif class_name == 'Saridon Extra':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Saridon Extra.mp3")
                elif class_name == 'Stop Cold':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Stop Cold.mp3")
                elif class_name == 'Ultraflu Extra':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Ultraflu Extra.mp3")
                elif class_name == 'Ultraflu':
                    play_sound_and_pause("/home/jetson/Documents/PKM/obat_sound/Ultraflu.mp3")
                # Add more conditions here for other medicines

        # Resume real-time frame capture right after sound finishes
        # This ensures that after playing the sound, we immediately capture the latest frame
        cap.grab()  # Skip grabbing outdated frames and move to the next real-time frame

        # Show result on screen (optional)
        cv2.imshow('YOLOv11 Detection', results[0].plot())
        
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    ser.close()

if __name__ == "__main__":
    run_yolo_inference()

