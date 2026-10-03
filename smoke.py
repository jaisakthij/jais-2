from pulse_build import PulseEngine, Patient, PatientVisit

e = PulseEngine()
p = Patient(patient_id="P001", age=52, sex="F", ancestry="EUR", site="UKB",
            visits=[PatientVisit(date="2020-01-01", labs={"glucose":105,"ldl":140,"hdl":48,"crp":3.2,"hba1c":5.9}),
                    PatientVisit(date="2021-06-01", labs={"glucose":112,"ldl":155,"crp":4.1})])
r = e.impute(p)
print("visits:", len(r.visits))
for vr in r.visits:
    print(" ", vr.date, [(i.biomarker, round(i.imputed_raw,1), i.measured) for i in vr.imputations[:5]])
print("uncertainty:", e.uncertainty(p))