import sys, os, torch
sys.path.insert(0, os.path.join(os.getcwd(), "LongitudinalGeneration"))
from pulse_build.engine import PulseEngine, LAB_SLOTS
from pulse_build.io import Patient, PatientVisit, build_visit_vector

# inspect raw weights
cp = torch.load("ckpt_small/checkpoint_epoch_60.pt", map_location="cpu", weights_only=False)
cfg = cp["model_config"]
print("cfg:", cfg)
sd = cp["model_state_dict"]
for name, state in sd.items():
    has_nan = bool(torch.isnan(state).any().item())
    has_inf = bool(torch.isinf(state).any().item())
    nonzero = bool((state != 0).sum().item())
    print(f"{name:60s} nan={has_nan} inf={has_inf} nonzero={nonzero} shape={state.shape}")
    if has_nan:
        break
