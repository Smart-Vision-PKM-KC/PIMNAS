import torch
import time
from models.common import DetectMultiBackend
from utils.torch_utils import select_device

device = select_device('cuda:0')

model = DetectMultiBackend('best4.pt', device=device)
model.model.eval()

dummy_input = torch.randn(3,3,640,640).to(device)

with torch.no_grad():
	print ('Memulai warm-up run...')
	start_time = time.time()
	output = model(dummy_input)
	end_time = time.time()
	print(f'warm-up run selesai dalam {end_time - start_time:.2f} detik')
