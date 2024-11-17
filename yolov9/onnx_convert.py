from ultralytics import YOLO
model = YOLO('best4.pt')
model.export(format = 'onnx')
