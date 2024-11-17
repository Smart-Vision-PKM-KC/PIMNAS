import cv2
import time
import random
import argparse
import numpy as np
import onnxruntime as ort

def loadSource(source_file):
    img_formats = ['jpg', 'jpeg', 'png', 'tif', 'tiff', 'dng', 'webp', 'mpo']
    key = 1 # 1 = Video, 0 = Image
    frame = None
    cap = None

    # Source from webcam
    if(source_file == "0"):
        image_type = False
        source_file = 0    
    else:
        image_type = source_file.split('.')[-1].lower() in img_formats

    # Open Image or Video
    if(image_type):
        frame = cv2.imread(source_file)
        key = 0
    else:
        cap = cv2.VideoCapture(source_file)

    return image_type, key, frame, cap

def preprocess(img):
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(image_rgb, (640, 640))

    # Scale input pixel value to 0 to 1
    input_image = resized / 255.0
    input_image = input_image.transpose(2,0,1)
    input_tensor = input_image[np.newaxis, :, :, :].astype(np.float32)        

    return input_tensor

def xywh2xyxy(x):
    # Convert bounding box (x, y, w, h) to bounding box (x1, y1, x2, y2)    
    box = np.copy(x)

    box[..., 0] = x[..., 0] - x[..., 2] / 2
    box[..., 1] = x[..., 1] - x[..., 3] / 2
    box[..., 2] = x[..., 0] + x[..., 2] / 2
    box[..., 3] = x[..., 1] + x[..., 3] / 2
    
    return box 

def postprocess(outputs):
    conf_thresh = args.thresh
    iou_thresh = args.iou_thresh

    predictions = np.squeeze(outputs).T
    scores = np.max(predictions[:, 4:], axis=1)
    predictions = predictions[scores > conf_thresh, :]
    scores = scores[scores > conf_thresh]
    class_ids = np.argmax(predictions[:, 4:], axis=1)

    # Rescale box
    boxes = predictions[:, :4]
    
    input_shape = np.array([640, 640, 640, 640])
    boxes = np.divide(boxes, input_shape, dtype=np.float32)
    boxes *= np.array([w, h, w, h])
    boxes = boxes.astype(np.int32)
    indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=conf_thresh, nms_threshold=iou_thresh)

    detections = []
    for bbox, score, label in zip(xywh2xyxy(boxes[indices]), scores[indices], class_ids[indices]):
        detections.append({
            "class_index": label,
            "confidence": score,
            "box": bbox,
            "class_name": class_names[label] if label < len(class_names) else "Unknown"
        })    
    
    return detections

def drawBbox(image, detections):
    for detection in detections:        
        x1, y1, x2, y2 = detection['box'].astype(int)
        class_id = detection['class_index']
        confidence = round(detection['confidence'], 3)

        # Bounding box color
        color = colors[class_id] if class_id < len(colors) else (0, 255, 0)        

        # Class Name        
        class_name = detection['class_name']    
        class_name += f' {str(confidence)}'

        # Draw Bounding Box
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

        # Draw class name and confidence score
        thickness = 2
        font_size = thickness / 2.8
        margin = thickness * 2
        cv2.putText(image, class_name, (x1, y1 - margin), cv2.FONT_HERSHEY_SIMPLEX, font_size, color, thickness=thickness)        

if __name__ == '__main__':
    # Add Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default="data/videos/road.mp4", help="Video")
    parser.add_argument("--names", type=str, default="data/dataobat.names", help="Object Names")
    parser.add_argument("--weights", type=str, default="yolov9-c-converted.onnx", help="Pretrained Weights")
    parser.add_argument("--thresh", type=float, default=0.4, help="Confidence Threshold")
    parser.add_argument("--iou-thresh", type=float, default=0.5, help="IOU Threshold")
    args = parser.parse_args()    

    # ONNX Session
    providers = ['CPUExecutionProvider']
    session = ort.InferenceSession(args.weights, providers=providers)

    class_names = []
    with open(args.names, "r") as f:
        class_names = [cname.strip() for cname in f.readlines()]
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in class_names]

    source_file = args.source    
    # Load Source
    image_type, key, frame, cap = loadSource(source_file)
    grabbed = True

    while(1):
        if not image_type:
            (grabbed, frame) = cap.read()

        if not grabbed:
            exit()

        image = frame.copy()
        h, w = image.shape[:2]

        # Preprocess
        input_tensor = preprocess(image)        

        # Inference
        outname = [i.name for i in session.get_outputs()]        
        inname = [i.name for i in session.get_inputs()]        
        inp = {inname[0]:input_tensor}

        outputs = session.run(outname, inp)[0]

        # Postprocess
        detections = postprocess(outputs)

        # Draw Bounding Boxes                        
        drawBbox(image, detections)

        grabbed = False
        cv2.imshow("YOLOv9 Object Detection", image)
        if cv2.waitKey(key) ==  ord('q'):
            break        