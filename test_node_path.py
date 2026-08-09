"""
Run yt-dlp test with node in PATH explicitly
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

    print("Checking Node PATH...")
    out = run(ssh, "which node || which nodejs")
    node_path = out.strip().split('\n')[0]
    print(f"Node path: {node_path}")

    print("\nTesting yt-dlp with explicit PATH...")
    test_cmd = f"cd {VPS_DIR} && export PATH=$PATH:$(dirname {node_path}) && venv/bin/yt-dlp --cookies cookies.txt --format bestaudio -v 'https://www.youtube.com/watch?v=NJAv_7lHUIU' 2>&1"
    out2 = run(ssh, test_cmd, timeout=90)
    print("Output includes 'JS runtimes: node'? " + str("JS runtimes: node" in out2))
    print(out2[:500] + "\n...\n" + out2[-1000:])

    ssh.close()

if __name__ == '__main__':
    main()
