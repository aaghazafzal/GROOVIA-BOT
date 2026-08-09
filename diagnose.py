"""
Diagnose exactly why cookies aren't working
"""
import sys, io
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
    return out + "\n" + err if err else out

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    # 1. Show cookies content (masked)
    print("=== COOKIES FILE CONTENTS ===")
    out = run(ssh, f"cat {VPS_DIR}/cookies.txt | head -5")
    print(out)
    print("...")
    print()

    # 2. Check key auth cookies are present
    print("=== KEY AUTH COOKIES CHECK ===")
    important = ['SID', 'HSID', 'SSID', 'SAPISID', 'LOGIN_INFO', '__Secure-1PSID', '__Secure-3PSID', 'VISITOR_INFO']
    for cookie in important:
        out = run(ssh, f"grep -c '{cookie}' {VPS_DIR}/cookies.txt 2>/dev/null || echo '0'")
        status = "✅" if out.strip() != "0" else "❌"
        print(f"  {status} {cookie}: {'found' if out.strip() != '0' else 'MISSING'}")

    print()

    # 3. Verbose yt-dlp test
    print("=== VERBOSE YT-DLP TEST ===")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/yt-dlp --cookies {VPS_DIR}/cookies.txt --skip-download -v 'https://music.youtube.com/watch?v=NJAv_7lHUIU' 2>&1 | head -40", timeout=45)
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
