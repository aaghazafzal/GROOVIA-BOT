"""
Quick VPS status checker
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP   = "206.189.128.37"
VPS_USER = "root"
VPS_PASS = "A@ghaZ9431A"
VPS_DIR  = "/root/groovia"

def run(ssh, cmd):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out, err

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print("\n=== VPS STATUS CHECK ===\n")

    # 1. Is tmux running?
    out, _ = run(ssh, "tmux list-sessions 2>/dev/null")
    print(f"[tmux sessions]: {out or 'NONE - pipeline stopped!'}")

    # 2. Last 50 lines of log
    print("\n[Last 50 log lines]:")
    out, _ = run(ssh, f"tail -50 {VPS_DIR}/groovia_indexer.log 2>/dev/null")
    print(out or "(log empty)")

    # 3. DB stats
    print("\n[DB Stats]:")
    out, err = run(ssh, f"cd {VPS_DIR} && venv/bin/python run.py stats 2>&1")
    print(out or err or "(no output)")

    # 4. Process check
    print("\n[Running processes]:")
    out, _ = run(ssh, "ps aux | grep 'run.py' | grep -v grep")
    print(out or "No run.py process found!")

    ssh.close()
    print("\n=== END ===")

if __name__ == '__main__':
    main()
