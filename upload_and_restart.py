"""
Upload updated downloader.py to VPS and restart the mass_indexer
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP   = "206.189.128.37"
VPS_USER = "root"
VPS_PASS = "A@ghaZ9431A"
VPS_DIR  = "/root/groovia"
LOCAL_DL = r"C:\ALL FINAL PROJECTS\BOTS\GROOVIA_BOT\vps_downloader.py"

def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    print("Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print("Uploading downloader.py...")
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_DL, f"{VPS_DIR}/downloader.py")
    sftp.close()

    print("Restarting tmux session...")
    run(ssh, "tmux kill-session -t groovia 2>/dev/null; sleep 2")
    
    # Reset failed songs
    reset_script = """
import sys, os
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')
from db import Database
db = Database()
r = db.col.update_many(
    {'status': {'$in': ['failed', 'downloading']}},
    {'$set': {'status': 'pending', 'error': None, 'retry_count': 0}}
)
s = db.get_stats()
print('Reset: %d | Pending: %d | Uploaded: %d' % (r.modified_count, s.get('pending',0), s.get('uploaded',0)))
db.close()
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/reset4.py", 'w') as f:
        f.write(reset_script)
    sftp.close()
    
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python reset4.py 2>&1 | tail -3")
    print(out)
    
    start = (
        f"tmux new-session -d -s groovia "
        f"'cd {VPS_DIR} && venv/bin/python run.py run --workers 5 "
        f"2>&1 | tee groovia_indexer.log'"
    )
    run(ssh, start)
    print("Tmux started! Checking logs...")
    import time
    time.sleep(10)
    logs = run(ssh, f"tail -20 {VPS_DIR}/groovia_indexer.log 2>/dev/null")
    print(logs)

    ssh.close()

if __name__ == '__main__':
    main()
