import torch
import torch.nn.utils.prune as prune
from utils.torch_utils import pruned
from ultralytics import YOLO

model= YOLO("best.pt")

model.prune(0.7)

model.save("best_pruned.pt")

