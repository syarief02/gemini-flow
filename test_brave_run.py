import subprocess
import time
import urllib.request
import json

p = subprocess.Popen(
    [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "--remote-debugging-port=9222", "--remote-allow-origins=*"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print("Started Brave PID:", p.pid)

for i in range(15):
    ret = p.poll()
    if ret is not None:
        print(f"Brave EXITED at {i}s with code: {ret}")
        break
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1) as resp:
            data = json.loads(resp.read().decode())
            print(f"SUCCESS at {i}s! Debugger URL: {data.get('webSocketDebuggerUrl')}")
            break
    except Exception as e:
        print(f"Second {i} waiting: {e}")
    time.sleep(1)

# Keep it alive
print("Keeping Brave process alive for automation...")
while True:
    time.sleep(10)
