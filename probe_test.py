import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "LongitudinalGeneration"))
from pulse_build.engine import PulseEngine
from pulse_build.io import Patient, PatientVisit
import time

eng = PulseEngine(ckpt_path="ckpt_small/checkpoint_epoch_60.pt")

def show(desc, labs):
    patient = Patient(patient_id="P-001", age=55, sex="M", ancestry="EUR", site="A",
                      visits=[PatientVisit(date="2024-01-15", labs=labs)])
    t0 = time.time()
    res = eng.impute(patient)
    print(f"--- {desc} ({time.time()-t0*1000:.1f}ms) ---")
    for vr in res.visits:
        for imp in vr.imputations:
            tag = "MEAS" if imp.measured is not None else "IMPT"
            print(f"  {tag} {imp.biomarker:12s} meas={imp.measured:7}  im_z={imp.imputed_z:6.3f}  raw={imp.imputed_raw:7.2f}")

show("glucose=200 (far)", {"glucose": 200.0, "hdl": 50.0})
show("glucose=60  (low)", {"glucose": 60.0, "hdl": 50.0})
show("all four", {"glucose": 98.0, "hdl": 48.0, "ldl": 105.0, "creatinine": 0.95})
