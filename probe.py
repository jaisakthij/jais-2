import urllib.request, json, sys
url = "https://pypi.org/pypi/python-dateutil/json"
d = json.load(urllib.request.urlopen(url, timeout=30))
rel = d["releases"]["2.9.0"]
for f in rel:
    if "py3-none-any" in f["filename"]:
        print(f["url"], f["filename"])