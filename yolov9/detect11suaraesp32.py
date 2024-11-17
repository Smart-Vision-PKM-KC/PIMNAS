import argparse
import os
import platform
import sys
from pathlib import Path
import serial
import torch
import time
from playsound import playsound
import cv2  # Make sure cv2 is imported

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLO root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode

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

def check_conditions(distance, light):
    if distance > 30:
        playsound("/home/jetson/Documents/PKM/obat_sound/jarak anda terlalu jauh.mp3")
    elif light > 2400:
        playsound("/home/jetson/Documents/PKM/obat_sound/Ruangan anda terlalu gelap.mp3")
    else:
        playsound("/home/jetson/Documents/PKM/obat_sound/Tunggu 1 menit.mp3")
        return "Tunggu satu menit."

def wait_for_conditions():
    #engine = pyttsx3.init()
    while True:
        distance, light = read_sensors()
        message = check_conditions(distance, light)
        #engine.setProperty('rate', 170)
        #engine.setProperty('voice', 'id+f2')
        #engine.say(message)
        #engine.runAndWait()
        if message == "Tunggu satu menit.":
            break
        time.sleep(0.05)  # Wait for 0.5 seconds before rechecking

@smart_inference_mode()
def run(
        weights=ROOT / 'yolo.pt',  # model path or triton URL
        source=ROOT / 'data/images',  # file/dir/URL/glob/screen/0(webcam)
        data=ROOT / 'data/coco.yaml',  # dataset.yaml path
        imgsz=(384, 640),  # inference size (height, width)
        conf_thres=0.5,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=True,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        flip_method=True,  # add flip_method parameter
):
    wait_for_conditions()
    time.sleep(0.05)  # Wait for 1 minute

    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
    screenshot = source.lower().startswith('screen')
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Initialize TTS engine
    #engine = pyttsx3.init()

    # Initialize serial communication
    ser = serial.Serial('/dev/ttyACM0', 115200)  # Adjust the port and baud rate as needed

    # Dataloader
    bs = 10 # batch_size
    if webcam:
        view_img = check_imshow(warn=True)
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        bs = len(dataset)
    elif screenshot:
        dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
    for path, im, im0s, vid_cap, s in dataset:
        with dt[0]:
            im = torch.from_numpy(im).to(model.device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

        # Inference
        with dt[1]:
            visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(im, augment=augment, visualize=visualize)

        # NMS
        with dt[2]:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Rotate the image by 180 degrees
                im0 = cv2.rotate(im0, cv2.ROTATE_180)

                # Print results
                class_counts = {}
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()  # detections per class
                    class_counts[int(c)] = n

                # Send detected class names to ESP32
                for c in det[:, 5].unique():
                    class_name = names[int(c)]
                    ser.write(class_name.encode('utf-8'))  # Send class name over serial

                # Text-to-Speech
                if names[int(c)] == 'Neozep Forte':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Neozep forte.mp3")
                elif names[int(c)] == 'Intunal F':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Intunal F.mp3")
                elif names[int(c)] == 'Paramex':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Paramex.mp3")
                elif names[int(c)] == 'Biogesic Paracetamol':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Biolgesic paracetamol.mp3")
                elif names[int(c)] == 'Bodrex Extra':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Bodrex Extra.mp3")
                elif names[int(c)] == 'Bodrex Flu dan Batuk PE':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Bodrex Flu dan Batuk PE.mp3")
                elif names[int(c)] == 'Bodrex Migra':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Bodrex Migra.mp3")
                elif names[int(c)] == 'Decolgen':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Decolgen.mp3")
                elif names[int(c)] == 'Decolsin':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Decolsin.mp3")
                elif names[int(c)] == 'Dumin Paracetamol':
                    playsound("/home/jetson/Music/obat_sound/Dumin Paracetamol.mp3")
                elif names[int(c)] == 'Insana Flu':
                    playsound("/home/jetson/Music/obat_sound/Insana Flu.mp3")
                elif names[int(c)] == 'Intunal Kaplet':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Intunal Kaplet.mp3")
                elif names[int(c)] == 'Inza':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Inza.mp3")
                elif names[int(c)] == 'Mixagrip Flu':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Mixagrip Flu.mp3")
                elif names[int(c)] == 'Mixagrip Flu dan Batuk':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Mixagrip Flu dan Batuk.mp3")
                elif names[int(c)] == 'Neo Rheumacyl':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Neorheumacyl.mp3")
                elif names[int(c)] == 'Neozap Forte':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Neozep forte.mp3")
                elif names[int(c)] == 'Oskadon Sakit Kepala':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Oskadon Sakit Kepala.mp3")
                elif names[int(c)] == 'Oskadon SP':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Oskadon SP.mp3")
                elif names[int(c)] == 'Pamol Paracetamol':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Pamol_Paracetamol.mp3")
                elif names[int(c)] == 'Panadol Cold Flu':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Panadol_Cold_Flu.mp3")
                elif names[int(c)] == 'Panadol Extra Paracetamol':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Panadol_Extra_Paracetamol.mp3")
                elif names[int(c)] == 'Panadol Paracetamol':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Panadol.mp3")
                elif names[int(c)] == 'Paramex Flu dan Batuk PE':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Paramex_Flu_dan_Batuk_PE.mp3")
                elif names[int(c)] == 'Paramex Nyeri Otot':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Paramex_Nyeri_Otot.mp3")
                elif names[int(c)] == 'Poldan MIG':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Poldan_MIG.mp3")
                elif names[int(c)] == 'Procold Flu':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Procold_Flu.mp3")
                elif names[int(c)] == 'Procold Flu dan Batuk':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Procold_Flu_dan_Batuk.mp3")
                elif names[int(c)] == 'Sanaflu':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Sanaflu.mp3")
                elif names[int(c)] == 'Sanmol':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Sanmol.mp3")
                elif names[int(c)] == 'Saridon':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Saridon.mp3")
                elif names[int(c)] == 'Saridon Extra':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Saridon_Extra.mp3")
                elif names[int(c)] == 'Stop Cold':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Stop_Cold.mp3")
                elif names[int(c)] == 'Ultraflu Extra':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Ultraflu_Extra.mp3")
                elif names[int(c)] == 'Ultraflu PE':
                    playsound("/home/jetson/Documents/PKM/obat_sound/Ultraflu_PE.mp3")

            # Stream results
            im0 = annotator.result()
            
            # Flip the image horizontally if flip_method is True
            if flip_method:
                im0 = cv2.flip(im0, -1)  # Flip the frame horizontally

            if view_img:
                if platform.system() == 'Linux' and p not in windows:
                    windows.append(p)
                    cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                    cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                cv2.imshow(str(p), im0)
                cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer[i].write(im0)

        # Print time (inference-only)
        LOGGER.info(f"{s}{names[int(c)]  if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

    # Print results
    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    if update:
        strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)

    # Close serial connection
    ser.close()

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolo.pt', help='model path or triton URL')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob/screen/0(webcam)')
    #parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[320], help='inference size h,w')  # Ubah default ukuran gambar ke 320
    parser.add_argument('--conf-thres', type=float, default=0.65, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
    parser.add_argument('--flip-method', default = 0, action='store_true', help='flip video horizontally')  # add flip-method argument
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt

def main(opt):
    # check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))

if __name__ == "__main__":
    opt = parse_opt()
    main(opt)

