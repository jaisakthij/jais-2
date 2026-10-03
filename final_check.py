import sys, os, json, time
sys.path.insert(0, os.path.join(os.getcwd(), "LongitudinalGeneration"))

from pulse_build.engine import PulseEngine, LAB_SLOTS
from pulse_build.io import LAB_RANGES
import numpy as np

eng = PulseEngine(ckpt_path="ckpt_small/checkpoint_epoch_60.pt")
cfg = json.load(open("ckpt_small/train_config.json"))
print("Engine:", eng.__class__.__name__, "| model type:", type(eng.model).__name__)
for attr in ["latent_dim","hidden_dim"]:
    v = getattr(eng.model, attr, "N/A")
    print(f"  model.{attr} = {v}")

# Realistic patient with only a few measured labs, others imputed
from pulse_build.io import Patient, PatientVisit
labs = {"glucose": 98.0, "hdl": 48.0, "ldl": 105.0, "creatinine": 0.95}
patient = Patient(patient_id="P-001", age=55, sex="M", ancestry="EUR", site="SITE-A",
                  visits=[PatientVisit(date="2024-01-15", labs=labs)])
start = time.time()
res = eng.impute(patient)
print(f"Impute time: {time.time()-start:.3f}s")
for vr in res.visits:
    for imp in vr.imputations:
        tag = "MEAS" if imp.measured is not None else "IMPT"
        print(f"  [{tag}] {imp.biomarker:12s} measured={imp.measured}  imputed_z={imp.imputed_z:7.3f}  imputed_raw={imp.imputed_raw:8.2f} ({imp.unit})")
