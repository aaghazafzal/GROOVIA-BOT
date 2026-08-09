"""
Fix Node.js path for yt-dlp
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
import subprocess
import os

print("PATH is:", os.environ.get("PATH"))
try:
    res = subprocess.run(["node", "-v"], capture_output=True, text=True)
    print("subprocess node -v:", res.stdout, res.stderr)
except Exception as e:
    print("subprocess node -v FAILED:", e)

# Force symlink node to /usr/bin and /usr/local/bin just in case
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_node_env.py", 'w') as f:
        f.write(test)
    sftp.close()

    print("Checking why yt-dlp can't see node.js...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_node_env.py 2>&1")
    print(out)

    # Let's explicitly tell yt-dlp to use node!
    # There's no argument for JS runtime path, it relies on PATH.
    # What if we install nodejs via nvm? Or what if we use python's QuickJS?
    # Wait, yt-dlp supports quickjs! `pip install quickjs`!
    print("\nInstalling QuickJS (Python native JS runtime) for yt-dlp...")
    run(ssh, f"cd {VPS_DIR} && venv/bin/pip install quickjs -q 2>&1")
    
    print("Testing yt-dlp with QuickJS...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/yt-dlp --cookies cookies.txt --format bestaudio -v 'https://www.youtube.com/watch?v=NJAv_7lHUIU' 2>&1 | grep -E '(ERROR|WARNING|JS runtimes|download|100%)'", timeout=90)
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
