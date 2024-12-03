# PIMNAS Object Detection Project

## Project Overview
This project implements object detection using two state-of-the-art YOLO (You Only Look Once) models: YOLOv9 and YOLO11 for advanced computer vision tasks.

## Prerequisites
- Anaconda/Miniconda
- CUDA-compatible NVIDIA GPU
- Git
- Python 3.8+

## Repository Structure
```
project-root/
│
├── yolov9/
├── ultralytics/
├── datasets/
└── README.md
```

## Setup Instructions

### 1. Clone Repositories
```bash
# Clone YOLOv9
git clone https://github.com/WongKinYiu/yolov9.git

# Clone YOLO11 (Ultralytics)
git clone https://github.com/ultralytics/ultralytics.git
```

### 2. Environment Setup
Use the provided Anaconda environment:
- Download environment file from: https://terabox.com/s/1q3O5f3KA7qdQ4SZEY8Xq4w
- Create and activate the environment:
```bash
conda env create -f environment.yml
conda activate yolov8-gpu-env
```

### 3. Model Weights
Download pre-trained weights:
- YOLOv9: https://terabox.com/s/1cRqWd_LtmPUKyH-_34jw0Q
- YOLO11: https://terabox.com/s/1rG76qBh3Ggs4lPS0PoXGLA

## Training

### YOLO11 Training
```bash
# Activate environment
conda activate yolov8-gpu-env

# Navigate to ultralytics directory
cd path/to/ultralytics

# Run training
yolo detect train \
    model=yolo11m.pt \
    epochs=300 \
    patience=50 \
    batch=-1 \
    workers=8 \
    data=path/to/data.yaml \
    device=0
```

### YOLOv9 Training
```bash
# Activate environment
conda activate yolov8-gpu-env

# Navigate to YOLOv9 directory
cd path/to/yolov9

# Run training
python train_dual.py \
    --workers 8 \
    --batch 4 \
    --img 384 \
    --epochs 300 \
    --patience 50 \
    --data path/to/data.yaml \
    --weights path/to/yolov9-c-converted.pt \
    --device 0 \
    --cfg models/detect/yolov9_custom.yaml \
    --hyp data/hyps/hyp.scratch-high.yaml
```

## Configuration
- Modify `data.yaml` to specify your dataset paths and classes
- Adjust hyperparameters in respective YAML configuration files

## Troubleshooting
- Ensure CUDA and GPU drivers are up to date
- Check conda environment compatibility
- Verify dataset format and annotations

## Acknowledgments
- YOLOv9 Repository: https://github.com/WongKinYiu/yolov9
- Ultralytics Repository: https://github.com/ultralytics/ultralytics

## Additional Notes
- This README provides a comprehensive guide for setting up and training YOLOv9 and YOLO11 models
- Customize paths and parameters according to your specific project requirements
- For detailed model-specific configurations, refer to the original repositories

