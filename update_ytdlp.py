"""
Update yt-dlp to nightly build on VPS and test cookies again
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

    print("[1] Updating yt-dlp to latest nightly build on VPS...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python -m pip install -U --pre yt-dlp 2>&1")
    print(out)
    
    version = run(ssh, f"{VPS_DIR}/venv/bin/yt-dlp --version")
    print(f"New yt-dlp version: {version}")

    print("\n[2] Testing download with cookies on nightly yt-dlp...")
    test_cmd = f"cd {VPS_DIR} && venv/bin/yt-dlp --cookies cookies.txt --format bestaudio -v 'https://www.youtube.com/watch?v=NJAv_7lHUIU' 2>&1 | grep -E '(ERROR|WARNING|download|100%)'"
    out = run(ssh, test_cmd, timeout=90)
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
