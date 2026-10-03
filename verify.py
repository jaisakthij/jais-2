import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "LongitudinalGeneration"))
from pulse_build.engine import PulseEngine
from pulse_build.io import LAB_SLOTS, LAB_RANGES
import json

eng = PulseEngine(ckpt_path="ckpt_small/checkpoint_epoch_60.pt")
print("Engine loaded from:", eng._ckpt_path)
cfg = json.load(open("ckpt_small/model_config.json"))
print("Config:", {k: cfg.get(k) for k in ["latent_dim","hidden_dim","modality_dims","temporal_model","seed","n_patients","n_visits","train_mask_rate"]})
print("Lab slots:", len(LAB_SLOTS))
print("Eng model latent dim:", eng._model.latent_dim, "hidden dim:", eng._model.hidden_dim)
