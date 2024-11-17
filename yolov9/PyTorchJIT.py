import torch
import torch.nn.utils.prune as prune
import torch.nn.functional as F

# Load model dari file .pt
model = torch.load('best2.pt')
#model.eval()

# Misal kita ingin melakukan pruning pada convolutional layer tertentu
module_to_prune = model.layer[0]  # ganti sesuai layer yang kamu ingin prune

# Terapkan pruning pada weight dari layer tersebut
prune.l1_unstructured(module_to_prune, name='weight', amount=0.2)

# Opsional: Hapus mask agar layer benar-benar di-prune
prune.remove(module_to_prune, 'weight')

# Simpan model yang sudah di-prune
torch.save(model, 'best2_pruned.pt')

