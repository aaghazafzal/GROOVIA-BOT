"""
Push Piped-based downloader to VPS, test it, restart pipeline
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP   = "206.189.128.37"
VPS_USER = "root"
VPS_PASS = "A@ghaZ9431A"
VPS_DIR  = "/root/groovia"

def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    return out

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print("[1] Installing requests on VPS...")
    run(ssh, f"{VPS_DIR}/venv/bin/pip install requests -q")
    print("    Done!")

    print("\n[2] Uploading new downloader.py (Piped API version)...")
    sftp = ssh.open_sftp()
    sftp.put("mass_indexer/downloader.py", f"{VPS_DIR}/downloader.py")
    sftp.close()
    print("    Uploaded!")

    # Write test script
    test_code = r"""
import sys, os
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

print("=== Testing Piped API Download ===")
print()

# Test Piped connectivity first
import requests
instances = [
    'https://pipedapi.kavin.rocks',
    'https://api.piped.yt',
    'https://pipedapi.moomoo.me',
]
working = []
for inst in instances:
    try:
        r = requests.get(f'{inst}/streams/NJAv_7lHUIU', timeout=10)
        if r.status_code == 200:
            data = r.json()
            streams = data.get('audioStreams', [])
            print(f"  OK  {inst} ({len(streams)} audio streams)")
            working.append(inst)
        else:
            print(f"  FAIL {inst}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  FAIL {inst}: {e}")

print()
if not working:
    print("ERROR: No Piped instances working!")
    sys.exit(1)

print(f"Working instances: {len(working)}")
print()
print("Now downloading Kesariya via Piped...")
from downloader import download_song, delete_song
path, info = download_song('NJAv_7lHUIU')
if path and os.path.exists(path):
    size = os.path.getsize(path) / 1024 / 1024
    print('SUCCESS! Downloaded %.2f MB via Piped!' % size)
    delete_song(path)
    print('Piped API works perfectly on this server!')
else:
    print('FAILED - Check Piped instances above')
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_piped.py", 'w') as f:
        f.write(test_code)
    sftp.close()

    print("\n[3] Testing Piped API on VPS...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_piped.py 2>&1", timeout=90)
    print(out)

    if 'SUCCESS' in out or 'works perfectly' in out:
        print("\n[4] Piped works! Restarting pipeline...")
        run(ssh, "tmux kill-session -t groovia 2>/dev/null; sleep 2")

        # Reset all failed/downloading songs
        reset_code = """
import sys, os
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')
from db import Database
db = Database()
r = db.col.update_many(
    {'status': {'$in': ['failed', 'downloading']}},
    {'$set': {'status': 'pending', 'error': None, 'retry_count': 0}}
)
print('Reset %d songs' % r.modified_count)
s = db.get_stats()
print('Pending: %d | Uploaded: %d' % (s.get('pending',0), s.get('uploaded',0)))
db.close()
"""
        sftp = ssh.open_sftp()
        with sftp.open(f"{VPS_DIR}/reset2.py", 'w') as f:
            f.write(reset_code)
        sftp.close()
        out2 = run(ssh, f"cd {VPS_DIR} && venv/bin/python reset2.py 2>&1 | tail -5")
        print(f"    {out2}")

        start = (
            f"tmux new-session -d -s groovia "
            f"'cd {VPS_DIR} && venv/bin/python run.py run --workers 5 "
            f"2>&1 | tee groovia_indexer.log'"
        )
        run(ssh, start)
        time.sleep(8)

        sessions = run(ssh, "tmux list-sessions 2>/dev/null")
        print(f"    tmux: {sessions}")

        print("\n[5] Checking logs in 45 seconds...")
        time.sleep(45)
        out3 = run(ssh, f"tail -20 {VPS_DIR}/groovia_indexer.log 2>/dev/null")
        print(out3)
    else:
        print("\nPiped failed too — manual cookies needed!")

    ssh.close()
    print("\n=== Done! ===")

if __name__ == '__main__':
    main()
