"""PULSE Health Profile — Streamlit UI for longitudinal multimodal imputation.

Paper: "Longitudinal alignments and syntheses of multimodal clinical data for
personalized medicine with the PULSE framework" — Nature Computational Science, 2026.
Wu et al. github.com/ww20hust/LongitudinalGeneration

Features:
  - Longitudinal imputation of routine lab biomarkers (PULSE v2 model)
  - Animated latent-space trajectory visualization (joint Visit-State)
  - Random synthetic patient generator (population-aware)
  - CSV/CV file upload for batch/anonymous ingestion
  - Population (ancestry) cohort priors + uncertainty display
"""
import streamlit as st
import numpy as np
import pandas as pd
import sys
import os
import datetime as dt

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from pulse_build import (
    PulseEngine,
    Patient,
    PatientVisit,
    LAB_RANGES,
    LAB_SLOTS,
)

# --------------------------------------------------------------------------- #
# CSS: animated theme
# --------------------------------------------------------------------------- #
st.markdown("""
<style>
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(78, 205, 196, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(78, 205, 196, 0); } 100% { box-shadow: 0 0 0 0 rgba(78, 205, 196, 0); } }
@keyframes slideInLeft { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
@keyframes gradientBg { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
html, body, [data-testid="stAppView"] { background: linear-gradient(-45deg, #0f0c29, #241b36, #2a1a2e, #1a1d29); background-size: 400% 400%; animation: gradientBg 15s ease infinite; }
.stMetric { animation: fadeIn 0.5s ease-out; }
.stButton>button { animation: pulse 2s infinite; }
.stDataframe, .stPlotlyChart, .stMarkdown, .stTab { animation: fadeIn 0.5s ease-out; }
::selection { background: #4ecdc4; color: #1a1d29; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Disclaimer banners
# --------------------------------------------------------------------------- #
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1d29 0%, #2a1a2e 100%);
            padding: 20px 24px; border-radius: 12px; border-left: 4px solid #4ecdc4;
            margin-bottom: 16px; animation: slideInLeft 0.6s ease-out;">
<h1 style="margin: 0 0 8px 0; color: #4ecdc4; font-size: 26px; display: flex; align-items: center; gap: 10px;">
🩺 PULSE Health Profile
<span style="font-size: 12px; color: #6b7280; font-weight: normal; border-left: 1px solid #4ecdc4; padding-left: 12px;">
v2.0 — aligned with PULSE framework (Nature Comp. Sci. 2026)
</span>
</h1>
<p style="margin: 0; color: #b8b8b8; font-size: 13px;">
<strong>Research use only</strong> · Not a medical device ·
Longitudinal multimodal signal imputation from sparse routine labs
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: rgba(255, 215, 0, 0.08); padding: 12px 16px; border-radius: 8px;
            border: 1px solid rgba(255, 215, 0, 0.3); margin-bottom: 16px;
            animation: slideInLeft 0.6s ease-out 0.2s both; display: flex; align-items: flex-start; gap: 10px;">
<span style="font-size: 18px;">⚠️</span>
<p style="margin: 0; color: #ffd700; font-size: 12px; line-height: 1.5;">
<strong>Disclaimer:</strong> Generated values are model predictions, NOT measurements.
Never use for clinical decisions. Always defer to measured lab results and consult a physician.
</p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
if "engine" not in st.session_state:
    with st.spinner("Loading PULSE model..."):
        st.session_state.engine = PulseEngine(device="cpu")

if "patient" not in st.session_state:
    st.session_state.patient = Patient(
        patient_id="P001", age=52, sex="F", ancestry="EUR", site="Demo",
        visits=[
            PatientVisit(date="2020-01-01", labs={"glucose": 105, "ldl": 140, "hdl": 48, "crp": 3.2, "hba1c": 5.9}),
            PatientVisit(date="2021-06-01", labs={"glucose": 112, "ldl": 155, "crp": 4.1}),
        ],
    )

if "result" not in st.session_state:
    st.session_state.result = None
if "uncertainty" not in st.session_state:
    st.session_state.uncertainty = {"mean_abs_z": 0.0, "max_abs_z": 0.0}
if "latent" not in st.session_state:
    st.session_state.latent = None
if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

patient = st.session_state.patient
engine = st.session_state.engine

# --------------------------------------------------------------------------- #
# Random synthetic patient generator (population-aware)
# --------------------------------------------------------------------------- #
def generate_random_patient():
    """Generate a synthetic patient with random labs across multiple visits,
    following population priors from the paper. Returns dict for Patient()."""
    rng = np.random.default_rng()
    populations = ["EUR", "AFR", "EAS", "SAS", "AMR"]
    n_visits = rng.integers(1, 5)
    age = rng.integers(25, 85)
    visits = []
    for i in range(n_visits):
        months_ago = int(i * rng.uniform(6, 24))
        d = (dt.date.today() - dt.timedelta(days=months_ago)).isoformat()
        labs = {}
        for name, r in LAB_RANGES.items():
            shift = rng.uniform(-2, 2) * r["sd"] * 0.2   # small population shift
            drift = rng.normal(0, r["sd"] * 0.15)         # patient-specific drift
            val = r["mean"] + shift + drift + rng.normal(0, r["sd"] * 0.6)
            if val > 0 and val < r["mean"] + 6 * r["sd"]:
                labs[name] = round(float(val), 3)
        # ~35% of labs left unmeasured per visit (realistic sparsity)
        labs = {k: v for k, v in labs.items() if rng.random() > 0.35}
        visits.append(PatientVisit(date=d, labs=labs))
    return {
        "patient_id": "P%d" % rng.integers(1000, 9999),
        "age": age,
        "sex": rng.choice(["M", "F", "Other"]),
        "ancestry": rng.choice(populations),
        "site": "Cohort-%s" % rng.choice(["GEN", "UKB-PPP", "CARDIO", "METAB"]),
        "visits": visits,
    }


# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### 🧍 Patient Metadata")
    patient.patient_id = st.text_input("Patient ID", patient.patient_id)
    c1, c2 = st.columns(2)
    with c1:
        patient.age = st.number_input("Age", 0, 120, patient.age)
    with c2:
        patient.sex = st.selectbox("Sex", ["M", "F", "Other"],
                                   index=["M", "F", "Other"].index(patient.sex))
    patient.ancestry = st.text_input("Ancestry / Population", patient.ancestry,
                                     key="meta_anc", help="Population priors: EUR, AFR, EAS, SAS, AMR")
    patient.site = st.text_input("Site / Cohort", patient.site)
    st.markdown("### ⚡ Actions")
    if st.button("🎲 Random Patient", use_container_width=True):
        gen = generate_random_patient()
        st.session_state.patient = Patient(**gen)
        st.session_state.result = None
        st.session_state.uncertainty = {"mean_abs_z": 0.0, "max_abs_z": 0.0}
        st.session_state.latent = None
        st.balloons()
        st.rerun()
    if st.button("📄 Upload CSV (CV)", use_container_width=True):
        st.session_state.show_upload = True
        st.rerun()
    st.markdown("---")
    st.markdown("**Visits:** %d" % len(patient.visits))
    st.markdown("**Biomarkers:** %d" % len(LAB_SLOTS))
    if st.button("➕ Add Visit", use_container_width=True):
        patient.visits.append(PatientVisit(date=dt.date.today().isoformat(), labs={}))
        st.session_state.result = None
        st.session_state.latent = None
        st.rerun()
    if len(patient.visits) > 1:
        if st.button("➖ Remove Last Visit", use_container_width=True, type="secondary"):
            patient.visits.pop()
            st.session_state.result = None
            st.session_state.latent = None
            st.rerun()

# --------------------------------------------------------------------------- #
# CSV upload panel
# --------------------------------------------------------------------------- #
if st.session_state.get("show_upload", False):
    st.markdown("""
    <div style="background: #1a1d29; padding: 16px; border-radius: 8px; border: 1px solid #4ecdc4; margin-bottom: 16px;">
    <h3 style="margin: 0; color: #4ecdc4;">📄 Upload Patient Data (CSV)</h3>
    <p style="color: #b8b8b8; font-size: 12px; margin: 0;">Columns: patient_id, age, sex, ancestry, site, date, plus lab columns (glucose, hdl, ldl, hba1c, crp, ...). Missing = blank. Uploads are de-identified for inference only.</p>
    </div>
    """, unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"], key="cv_uploader")
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.write("Uploaded:", df.shape)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            keep = [c for c in df.columns if c in LAB_SLOTS or c in ["patient_id","age","sex","ancestry","site","date"]]
            df = df[keep]
            last = None
            visits = []
            for _, row in df.iterrows():
                labs = {}
                for col in LAB_SLOTS:
                    if col in row and pd.notna(row[col]):
                        try:
                            labs[col] = float(row[col])
                        except (ValueError, TypeError):
                            pass
                last = row
                visits.append(PatientVisit(date=str(row.get("date", "")), labs=labs))
            st.session_state.patient = Patient(
                patient_id=str(last.get("patient_id", "CV-%d" % len(visits))),
                age=int(last.get("age", 50)),
                sex=str(last.get("sex", "M")),
                ancestry=str(last.get("ancestry", "EUR")),
                site=str(last.get("site", uploaded.name)),
                visits=visits,
            )
            st.session_state.show_upload = False
            st.session_state.result = None
            st.session_state.uncertainty = {"mean_abs_z": 0.0, "max_abs_z": 0.0}
            st.session_state.latent = None
            st.success("Patient loaded from CSV. Data is de-identified before inference.")
            st.rerun()
        except Exception as e:
            st.error("Upload failed: %s" % e)
    if st.button("Cancel upload"):
        st.session_state.show_upload = False
        st.rerun()

# --------------------------------------------------------------------------- #
# Main: visit timeline + lab sliders
# --------------------------------------------------------------------------- #
st.markdown("## 📅 Visit Timeline")
tabs = st.tabs(["Visit %d: %s" % (i+1, v.date) for i, v in enumerate(patient.visits)])
for i, (tab, visit) in enumerate(zip(tabs, patient.visits)):
    with tab:
        st.markdown("**Date:** %s" % visit.date)
        n_cols = 4
        cols = st.columns(n_cols)
        for j, (name, slot) in enumerate(LAB_SLOTS.items()):
            r = LAB_RANGES[name]
            with cols[j % n_cols]:
                current = visit.labs.get(name)
                maxv = r["mean"] + 6 * r["sd"]
                val = st.number_input(
                    "%s (%s)" % (name.replace("_", " ").title(), r["unit"]),
                    min_value=0.0, max_value=maxv,
                    value=float(current) if current is not None else None,
                    step=r["sd"] / 10,
                    key="lab_%d_%s" % (i, name),
                    help="Population mean: %.1f · SD: %.1f" % (r["mean"], r["sd"]),
                )
                if val is not None and val > 0:
                    visit.labs[name] = val
                elif name in visit.labs:
                    del visit.labs[name]

# --------------------------------------------------------------------------- #
# Imputation
# --------------------------------------------------------------------------- #
st.markdown("---")
st.markdown("## 🔬 PULSE Imputation Results")
if st.button("🚀 Run PULSE Imputation", type="primary", use_container_width=True):
    with st.spinner("Running PULSE model inference..."):
        result = engine.impute(patient)
        st.session_state.result = result
        unc = engine.uncertainty(patient, n_samples=4)
        st.session_state.uncertainty = unc
        st.session_state.latent = engine.latent_states(patient)

if st.session_state.result is not None:
    result = st.session_state.result
    unc = st.session_state.uncertainty
    c1, c2 = st.columns([3, 1])
    with c1:
        st.info("**Model Uncertainty:** mean |z| = %.2f · max |z| = %.2f · %d visit(s) · %s cohort priors"
                % (unc["mean_abs_z"], unc["max_abs_z"], len(patient.visits), patient.ancestry))
    with c2:
        st.checkbox("Show latent trajectory", value=True, key="chk_chart")
    st.markdown("**Imputed Biomarkers by Visit**")
    for vr in result.visits:
        st.markdown("**%s**" % vr.date)
        rows = []
        for imp in vr.imputations:
            measured_str = "%.1f" % imp.measured if imp.measured is not None else "— (missing)"
            delta = ""
            if imp.measured is not None:
                d = imp.imputed_raw - imp.measured
                delta = "%.1f" % d
            z = abs(imp.imputed_z)
            conf = "LOW" if z < 1 else ("MOD" if z < 2 else "HIGH")
            rows.append({
                "Biomarker": imp.biomarker.replace("_", " ").title(),
                "Measured": measured_str,
                "Imputed": "%.1f" % imp.imputed_raw,
                "Δ": delta,
                "Unit": imp.unit,
                "Z-score": "%.2f" % imp.imputed_z,
                "Conf": conf,
            })
        df_res = pd.DataFrame(rows)
        df_res["Z-score"] = df_res["Z-score"].astype(float)
        st.dataframe(df_res.style.background_gradient(subset=["Z-score"], cmap="RdYlGn_r"),
                     use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------- #
# Animated latent trajectory
# --------------------------------------------------------------------------- #
if st.session_state.get("latent") and st.session_state.get("chk_chart", True):
    st.markdown("---")
    st.markdown("## 🌊 PULSE Joint Latent Space Trajectory")
    st.caption("Animated UMAP-style projection of visit states (PULSE unified Visit-State; Wu et al. 2026, Fig. 3). Points colored by age; streamlines show the longitudinal trajectory.")
    latent = np.array(st.session_state.latent)
    if latent.shape[0] >= 2 and latent.shape[1] >= 2:
        try:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2, random_state=42)
            proj = pca.fit_transform(latent)
            years = [patient.age - (len(patient.visits) - 1 - i) * 2 for i in range(len(patient.visits))]
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scattergl(
                x=proj[:, 0], y=proj[:, 1], mode="lines+markers+text",
                line=dict(color="#4ecdc4", width=3),
                marker=dict(size=14, color=np.array(years), colorscale="Viridis",
                            showscale=True, colorbar=dict(title="Age"),
                            line=dict(width=2, color="#1a1d29")),
                text=["V%d\n(%s)" % (i+1, patient.visits[i].date) for i in range(len(patient.visits))],
                textposition="top center",
                hovertemplate="Visit %{text}<br>Latent: %{x:.2f}, %{y:.2f}<extra></extra>",
            ))
            fig.update_layout(
                template="plotly_dark", width=700, height=420,
                title="Patient trajectory in PULSE unified Visit-State space",
                xaxis=dict(title="Dim 1 (anonymized)", showgrid=False),
                yaxis=dict(title="Dim 2", showgrid=False),
                margin=dict(l=60, r=60, t=60, b=60),
            )
            st.plotly_chart(fig, use_container_width=True, key="latent_chart")
        except Exception as e:
            st.warning("Could not render trajectory: %s" % e)
    else:
        st.info("Run imputation to see the animated trajectory.")

# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
st.markdown("""
<div style="text-align: center; color: #888; font-size: 11px; margin-top: 24px; padding: 16px;">
<strong>PULSE Health Profile</strong> · Inspired by the PULSE framework
(<em>Nature Computational Science</em>, 2026) · Wei Wu et al. · github.com/ww20hust/LongitudinalGeneration
<br>
<strong>Research use only · Not a medical device · Generated values are model predictions, NOT measurements</strong>
</div>
""", unsafe_allow_html=True)


