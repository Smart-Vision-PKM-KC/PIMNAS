from ultralytics import YOLO
import cv2
model = YOLO("best5.pt")

results = model.predict(source="0", show=True, half=True, conf=0.9)

print(results)
