"""
Test yt-dlp with a free proxy on VPS
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP   = "206.189.128.37"
VPS_USER = "root"
VPS_PASS = "A@ghaZ9431A"
VPS_DIR  = "/root/groovia"

def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace').strip() + "\n" + stderr.read().decode('utf-8', errors='replace').strip()

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    test = r"""
import requests
import subprocess
import os
import concurrent.futures

print("Fetching free proxies...")
try:
    r = requests.get('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all')
    proxies = r.text.strip().split('\r\n')
    print(f"Found {len(proxies)} proxies. Testing them with yt-dlp...")
except Exception as e:
    print(f"Failed to fetch proxies: {e}")
    sys.exit(1)

def test_proxy(proxy):
    try:
        # Use yt-dlp with proxy to just fetch the title to see if it works without error
        cmd = f"/root/groovia/venv/bin/yt-dlp --proxy http://{proxy} --get-title 'https://www.youtube.com/watch?v=NJAv_7lHUIU'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if "Kesariya" in res.stdout or "Kesariya" in res.stderr:
            return proxy
    except:
        pass
    return None

working_proxy = None
# Test first 20 proxies concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = executor.map(test_proxy, proxies[:40])
    for res in results:
        if res:
            working_proxy = res
            print(f"✅ FOUND WORKING PROXY: {working_proxy}")
            break

if working_proxy:
    print(f"\nTesting full download with proxy {working_proxy}...")
    cmd = f"/root/groovia/venv/bin/yt-dlp --proxy http://{working_proxy} -f bestaudio -o '/tmp/test_proxy.mp3' 'https://www.youtube.com/watch?v=NJAv_7lHUIU'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    if os.path.exists('/tmp/test_proxy.mp3'):
        sz = os.path.getsize('/tmp/test_proxy.mp3')
        print(f"SUCCESS! Downloaded {sz/1024/1024:.2f} MB")
    else:
        print("Download failed.")
        print(res.stderr)
else:
    print("❌ No working proxy found in the first 40.")
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_proxy.py", 'w') as f:
        f.write(test)
    sftp.close()

    print("Running proxy test on VPS...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_proxy.py 2>&1", timeout=180)
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
