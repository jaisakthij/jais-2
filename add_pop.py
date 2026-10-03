p = "ui.html"
t = open(p).read()

pop_css = """
/* Population comparison panel */
.pop-panel { display: grid; grid-template-columns: 1fr 2.2fr; gap: 24px; }
.pop-aside { padding: 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; }
.pop-aside h4 { font-size: 13px; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
.pop-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding: 8px; background: rgba(255,255,255,0.02); border-radius: 8px; }
.pop-btn { flex: 1; padding: 10px; font-size: 13px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.03); color: var(--text-secondary); border-radius: 8px; cursor: pointer; }
.pop-btn.active { background: var(--primary); color: #0a0d1f; font-weight: 700; border-color: var(--primary); }
.pop-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 20px; }
.pop-table th { padding: 12px 16px; font-size: 12px; color: var(--primary); text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1); }
.pop-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
.pop-table tr:hover { background: rgba(255,255,255,0.03); }
.pop-label { font-size: 12px; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 6px; }
.pop-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
.diff-high { color: var(--error); }
.diff-mid { color: var(--warning); }
.diff-low { color: var(--success); }
@media (max-width: 1024px) { .pop-panel { grid-template-columns: 1fr; } }
"""
t = t.replace("</style>", pop_css + "</style>")

new_section = """
  <div id="population" style="display: none;" class="fade-in">
    <section class="section glass">
      <div class="section-header">
        <span class="icon">🌍</span>
        <h2>Between-Population Comparison</h2>
      </div>
      <p style="color: var(--text-secondary); margin-bottom: 16px;">
        Compare one patient's imputed profile against reference distributions from other ancestry
        populations. Population means/SD are bootstrapped from cohort data (or loaded reference priors).
      </p>
      <div class="pop-panel">
        <div class="pop-aside">
          <h4>Reference populations</h4>
          <div class="pop-row"><label><input type="checkbox" onchange="toggleCohort('EUR', this.checked)"> </label><span style="flex:1">🇪🇺 EUR (European) — n=</span><span id="pop-n-EUR" class="pop-val">—</span></div>
          <div class="pop-row"><label><input type="checkbox" onchange="toggleCohort('AFR', this.checked)"> </label><span style="flex:1">🌍 AFR (African) — n=</span><span id="pop-n-AFR" class="pop-val">—</span></div>
          <div class="pop-row"><label><input type="checkbox" onchange="toggleCohort('EAS', this.checked)"> </label><span style="flex:1">🇨🇳 EAS (East Asian) — n=</span><span id="pop-n-EAS" class="pop-val">—</span></div>
          <div class="pop-row"><label><input type="checkbox" onchange="toggleCohort('SAS', this.checked)"> </label><span style="flex:1">🇮🇳 SAS (South Asian) — n=</span><span id="pop-n-SAS" class="pop-val">—</span></div>
          <div class="pop-row"><label><input type="checkbox" onchange="toggleCohort('AMR', this.checked)"> </label><span style="flex:1">🌎 AMR (Latin American) — n=</span><span id="pop-n-AMR" class="pop-val">—</span></div>
          <div class="pop-row"><button class="pop-btn" style="width:100%" onclick="loadPopulationStats()">🔄 Refresh reference</button></div>
          <div class="pop-row"><button class="pop-btn" style="width:100%" onclick="compareCurrentPatient()">⚡ Compare current patient</button></div>
        </div>
        <div class="pop-main">
          <div class="pop-label">Imputation z-scores by reference population</div>
          <table class="pop-table"><thead><tr>
            <th>Biomarker</th><th style="text-align:right">Patient (z)</th>
            <th style="text-align:right">EUR</th><th style="text-align:right">AFR</th>
            <th style="text-align:right">EAS</th><th style="text-align:right">SAS</th>
            <th style="text-align:right">AMR</th>
          </tr></thead>
          <tbody id="pop-table-body"><tr><td colspan="7" style="text-align:center;color:var(--text-tertiary)">Load reference populations and compare a patient.</td></tr></tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
"""
t = t.replace('<div id="results" style="display: none;" class="fade-in">',
              '<button class="btn btn-secondary" onclick="document.getElementById(\\"results\\").style.display=\\"none\\";document.getElementById(\\"population\\").style.display=\\"block\\";window.scrollTo(0,document.body.scrollHeight)">🌍 View Population Comparison</button>' + new_section +
              '<div id="results" style="display: none;" class="fade-in">')
open(p, "w").write(t)
print("ui.html patched:", "population" in t)
