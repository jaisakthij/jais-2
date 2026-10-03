import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "LongitudinalGeneration"))
from pulse_build.engine import PulseEngine
from pulse_build.io import Patient, PatientVisit, build_visit_vector
import torch

eng = PulseEngine(ckpt_path="ckpt_small/checkpoint_epoch_60.pt")

vec = build_visit_vector(PatientVisit(date="2024-01-15", labs={"glucose": 98.0, "hdl": 48.0, "ldl": 105.0, "creatinine": 0.95}))
print("input vec nonzero count:", (vec != 0).sum(), "of", len(vec))
tvec = torch.as_tensor(vec.reshape(1, -1))
enc_mu, _ = eng.model.encoders["modality_a"](tvec)
print("encoder mu norm:", enc_mu.norm().item(), "mean:", enc_mu.mean().item())
hs = eng.model.temporal_module.init_context(1, "cpu")
vis_state = eng.model.compute_visit_state_dynamic({"modality_a": enc_mu}, z_past_mu=hs, include_history=True)
print("visit_state:", vis_state, "mean:", vis_state.mean().item())
recon = eng.model.decoders["modality_a"](vis_state)
print("recon nonzero:", (recon != 0).sum().item(), "of", recon.shape[1], "mean:", recon.mean().item())
