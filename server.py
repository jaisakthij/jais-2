"""Minimal HTTP server: serves the HTML UI and handles /api/impute POST requests."""
import http.server
import json
import os
import socketserver
import sys
from urllib.parse import parse_qs, urlparse

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from pulse_build import PulseEngine, Patient, PatientVisit

PORT = 8765
engine = PulseEngine(device="cpu")


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = os.path.join(_HERE, "ui.html")
            with open(html_path, "rb") as fh:
                self.wfile.write(fh.read())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/impute":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            # Build patient from JSON
            p = Patient(
                patient_id=data.get("patient_id", "P001"),
                age=int(data.get("age", 50)),
                sex=data.get("sex", "F"),
                ancestry=data.get("ancestry", "unknown"),
                site=data.get("site", "demo"),
                visits=[
                    PatientVisit(date=v["date"], labs=dict(v.get("labs", {})))
                    for v in data.get("visits", [])
                ],
            )

            # Run imputation
            result = engine.impute(p)
            unc = engine.uncertainty(p, n_samples=4)

            # Serialize
            out = {
                "patient_id": result.patient_id,
                "visits": [
                    {
                        "date": vr.date,
                        "imputations": [
                            {
                                "biomarker": imp.biomarker,
                                "measured": imp.measured,
                                "imputed_raw": imp.imputed_raw,
                                "imputed_z": imp.imputed_z,
                                "unit": imp.unit,
                                "mean": imp.mean,
                                "sd": imp.sd,
                            }
                            for imp in vr.imputations
                        ],
                    }
                    for vr in result.visits
                ],
                "uncertainty": unc,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(out).encode("utf-8"))
        else:
            self.send_error(404)


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"PULSE app running at http://127.0.0.1:{PORT}")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()