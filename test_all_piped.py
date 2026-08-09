"""
Test ALL available Piped API instances to find a working one.
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
import concurrent.futures

print("Fetching all Piped instances...")
try:
    r = requests.get('https://raw.githubusercontent.com/TeamPiped/Piped-Instances/main/instances.json')
    instances = r.json()
    apis = [i['api_url'] for i in instances if i.get('api_url') and i.get('up', True)]
except Exception as e:
    print(f"Error fetching instances list: {e}")
    sys.exit(1)

print(f"Found {len(apis)} API instances. Testing them for downloads...")
working = []

def test_api(api):
    try:
        r = requests.get(f"{api}/streams/NJAv_7lHUIU", timeout=5)
        if r.status_code == 200:
            data = r.json()
            audio = [s for s in data.get('audioStreams', []) if s.get('url')]
            if audio:
                # Try small download
                url = audio[0]['url']
                r2 = requests.get(url, stream=True, timeout=5)
                # Read just 1KB to confirm it streams
                chunk = next(r2.iter_content(chunk_size=1024))
                if len(chunk) > 0:
                    return api
    except:
        pass
    return None

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(test_api, apis)
    for res in results:
        if res:
            print(f"✅ WORKING API: {res}")
            working.append(res)
            if len(working) >= 5:
                break # Just need 5 good ones

if not working:
    print("❌ No working Piped APIs found!")
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_all_piped.py", 'w') as f:
        f.write(test)
    sftp.close()

    print("Testing ALL Piped instances on VPS...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_all_piped.py 2>&1")
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
