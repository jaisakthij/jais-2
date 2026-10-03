t = open("ui.html").read()
js = r"""
// Population comparison
let referenceStats = {};

function toggleCohort(cohort, checked) {
  if (checked) referenceStats[cohort] = referenceStats[cohort] || { mean: {}, sd: {}, n: 0 };
  else delete referenceStats[cohort];
  renderPopulationStats();
}

function loadPopulationStats() {
  fetch("/api/populations").then(r => r.json()).then(data => {
    referenceStats = {};
    let total = 0;
    for (const [cohort, v] of Object.entries(data.cohorts || {})) {
      referenceStats[cohort] = { mean: v.means || {}, sd: v.sds || {}, n: v.n || 0, labels: v.labels || {} };
      total += v.n || 0;
    }
    renderPopulationStats();
    alert("Reference populations loaded: " + total + " patient-visits across " + Object.keys(referenceStats).length + " cohorts");
  }).catch(e => alert("Failed to load reference populations: " + e.message));
}

function renderPopulationStats() {
  for (const cohort of ["EUR", "AFR", "EAS", "SAS", "AMR"]) {
    const el = document.getElementById("pop-n-" + cohort);
    if (el) el.textContent = referenceStats[cohort] ? referenceStats[cohort].n : "—";
  }
}

function compareCurrentPatient() {
  if (Object.keys(referenceStats).length === 0) { alert("Load reference populations first (Refresh reference)"); return; }
  const patient_id = document.getElementById("patient_id").value;
  const age = parseInt(document.getElementById("age").value) || 50;
  const sex = document.getElementById("sex").value;
  const site = document.getElementById("site").value;
  const visits = visits.map(v => ({
    date: v.date,
    labs: Object.fromEntries(Object.entries(v.labs).filter(([k, val]) => val != null && val !== undefined && !isNaN(val)))
  }));
  if (visits.length === 0) { alert("Enter a patient with lab values first"); return; }
  document.getElementById("population").style.display = "block";
  document.getElementById("results").style.display = "none";
  fetch("/api/impute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id, age, sex, ancestry: "EUR", site, visits })
  }).then(r => r.json()).then(data => {
    const biomarkerZ = {};
    for (const vr of data.visits) {
      for (const imp of vr.imputations) {
        if (!(imp.biomarker in biomarkerZ)) biomarkerZ[imp.biomarker] = { measured: [], imputed: [] };
        biomarkerZ[imp.biomarker].imputed.push(imp.imputed_z);
        if (imp.measured !== null) biomarkerZ[imp.biomarker].measured.push(imp.measured);
      }
    }
    const zForPatient = Object.keys(biomarkerZ).map(name => {
      const zList = biomarkerZ[name].imputed;
      return { name, z: zList.length ? (zList.reduce((a, b) => a + b, 0) / zList.length).toFixed(2) : "—" };
    });
    const rows = zForPatient.map(({ name, z }) => {
      const cells = [{ name, z }];
      for (const cohortRef of ["EUR", "AFR", "EAS", "SAS", "AMR"]) {
        const ref = referenceStats[cohortRef];
        let cell = "—", cssClass = "pop-val";
        if (ref && ref.mean[name] !== undefined) {
          const refMean = parseFloat(ref.mean[name]);
          const refSd = parseFloat(ref.sd[name]) || 1;
          const zvs = ((parseFloat(z) || 0) - refMean) / refSd;
          cell = zvs.toFixed(2);
          if (Math.abs(zvs) >= 2) cssClass = "diff-high";
          else if (Math.abs(zvs) >= 1) cssClass = "diff-mid";
          else cssClass = "diff-low";
        }
        cells.push({ text: cell, cssClass });
      }
      return cells;
    });
    const tbody = document.getElementById("pop-table-body");
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-tertiary)">No imputed biomarkers to compare.</td></tr>';
    } else {
      tbody.innerHTML = rows.map(row =>
        "<tr><td style=\"font-weight:600\">" + row[0].name +
          (biomarkerZ[row[0].name].measured.length > 0 ? " <small style=\"color:var(--text-tertiary)\">(" + biomarkerZ[row[0].name].measured.length + " measured)</small>" : "") +
          "</td>" +
          row.slice(1).map(c => "<td style=\"text-align:right\">" + c.text + "</td>").join("") +
          "</tr>"
      ).join("");
    }
    document.getElementById("population").scrollIntoView({ behavior: "smooth" });
  }).catch(e => alert("Error: " + e.message));
}
"""
anchor = "renderVisits();\n"
assert anchor in t, "anchor not found"
t = t.replace(anchor, js + "\n" + anchor)
open("ui.html", "w").write(t)
print("ui.html + population JS patched")
