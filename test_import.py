import sys
sys.path.insert(0, "C:\\Users\\jaisa\\OneDrive\\Desktop\\Soft skills music\\pulse-build\\LongitudinalGeneration")

import pulse
from pulse.model import PulseModel
print("IMPORT OK", pulse.__version__)

import torch
import numpy as np
from pulse.data.dataset import LongitudinalDataset, collate_visits, create_synthetic_data

def to_tensor(x):
    if x is None:
        return None
    if isinstance(x, torch.Tensor):
        return x
    return torch.as_tensor(np.asarray(x, dtype=np.float32))

modality_dims = {"modality_a": 61, "modality_b": 251}
model = PulseModel(modality_dims=modality_dims, latent_dim=16, hidden_dim=32, temporal_model="recurrent")
patient_ids, visits_data, missing_masks = create_synthetic_data(
    n_patients=1000, n_visits=3, modality_dims=modality_dims, missing_rate=0.3)
visits_data = [[{k: to_tensor(v) for k, v in visit.items()} for visit in visits] for visits in visits_data]

out = model.impute_missing(visits_data[0], missing_masks[0])
print("IMPUTE OK, n_visits:", len(out))
for i, visit in enumerate(out):
    print(" visit", i, {k: tuple(v.shape) for k, v in visit.items()})