import requests
def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php", data={"username": payload, "password": "x"})
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:35}] waf={waf}")

test("admin' SLEEP", "sleep-alone")
test("admin'CASE", "case-alone")
test("admin'WHEN", "when-alone")
test("admin'THEN", "then-alone")
test("admin'END", "end-alone")
test("admin'EXISTS", "exists-alone")
test("admin'HAVING", "having-alone")
test("admin'BETWEEN", "between-alone")
