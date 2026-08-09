"""
Push updated downloader to VPS and restart pipeline
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP   = "206.189.128.37"
VPS_USER = "root"
VPS_PASS = "A@ghaZ9431A"
VPS_DIR  = "/root/groovia"

def run(ssh, cmd, timeout=60):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out, err

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print("[1] Uploading fixed downloader.py to VPS...")
    sftp = ssh.open_sftp()
    sftp.put("mass_indexer/downloader.py", f"{VPS_DIR}/downloader.py")
    sftp.close()
    print("    Done!")

    # Write a test script to VPS
    test_script = """
import os, sys
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')
from downloader import download_song, delete_song
print('Testing Kesariya download with mweb client...')
path, info = download_song('NJAv_7lHUIU')
if path and os.path.exists(path):
    size = os.path.getsize(path) / 1024 / 1024
    print('SUCCESS: %.2f MB downloaded!' % size)
    delete_song(path)
    print('Test PASSED - mweb client works on this server!')
else:
    print('FAILED - bot block still happening')
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_dl.py", 'w') as f:
        f.write(test_script)
    sftp.close()

    print("\n[2] Quick download test on VPS (takes 30 sec)...")
    out, err = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_dl.py 2>&1 | grep -E '(SUCCESS|FAILED|ERROR|Testing)'", timeout=90)
    print(f"    Result: {out or err or '(no output)'}")

    print("\n[3] Stopping old pipeline...")
    run(ssh, "tmux kill-session -t groovia 2>/dev/null; sleep 2")
    print("    Stopped!")

    # Reset failed songs
    print("\n[4] Resetting failed songs for retry...")
    reset_script = """
import sys
sys.path.insert(0, '/root/groovia')
import os
os.chdir('/root/groovia')
from db import Database
db = Database()
result = db.col.update_many(
    {'status': {'$in': ['failed', 'downloading']}},
    {'$set': {'status': 'pending', 'error': None, 'retry_count': 0}}
)
print('Reset %d songs to pending' % result.modified_count)
stats = db.get_stats()
print('Pending: %d | Uploaded: %d' % (stats.get('pending',0), stats.get('uploaded',0)))
db.close()
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/reset_failed.py", 'w') as f:
        f.write(reset_script)
    sftp.close()

    out, _ = run(ssh, f"cd {VPS_DIR} && venv/bin/python reset_failed.py 2>&1 | tail -5")
    print(f"    {out}")

    print("\n[5] Starting fresh pipeline...")
    start_cmd = (
        f"tmux new-session -d -s groovia "
        f"'cd {VPS_DIR} && venv/bin/python run.py run --workers 5 "
        f"2>&1 | tee groovia_indexer.log'"
    )
    run(ssh, start_cmd)
    time.sleep(8)

    sessions, _ = run(ssh, "tmux list-sessions 2>/dev/null")
    print(f"    tmux: {sessions}")

    print("\n[6] Waiting 40s then showing logs...")
    time.sleep(40)
    out, _ = run(ssh, f"tail -25 {VPS_DIR}/groovia_indexer.log 2>/dev/null")
    print(out or "(log empty)")

    ssh.close()
    print("\n=== Done! Check 'song database' channel in 1-2 minutes ===")

if __name__ == '__main__':
    main()
