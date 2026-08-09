"""
Check logs on VPS safely
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
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print(run(ssh, f"tail -50 {VPS_DIR}/groovia_indexer.log"))
    
    # Check if any new songs were uploaded to telegram
    print("\n--- DB STATS ---")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python -c \"from db import Database; db=Database(); print(db.get_stats()); db.close()\"")
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
