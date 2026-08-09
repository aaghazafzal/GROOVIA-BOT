"""
Upload test_sources.py to VPS and run it
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
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    # Upload and run source tester
    sftp = ssh.open_sftp()
    sftp.put("test_sources.py", f"{VPS_DIR}/test_sources.py")
    sftp.close()

    print("Testing all alternative sources (takes ~2 min)...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_sources.py 2>&1", timeout=180)
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
