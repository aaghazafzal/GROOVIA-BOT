"""
Get OAuth2 Device Code from yt-dlp on VPS
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP   = "206.189.128.37"
VPS_USER = "root"
VPS_PASS = "A@ghaZ9431A"
VPS_DIR  = "/root/groovia"

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print("Requesting OAuth2 Device Code from YouTube...")
    
    # Run in background with timeout
    cmd = f"cd {VPS_DIR} && venv/bin/yt-dlp --username oauth2 --password '' 'https://www.youtube.com/watch?v=NJAv_7lHUIU' 2>&1"
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    
    # Read output line by line looking for the code
    code_found = False
    for line in stdout:
        print(f"DEBUG: {line.strip()}")
        if "google.com/device" in line:
            print(f"\n=========================================")
            print(f"FOUND OAUTH CODE:")
            print(line.strip())
            print(f"=========================================\n")
            code_found = True
            break
            
    if not code_found:
        print("Could not get OAuth code.")

    ssh.close()

if __name__ == '__main__':
    main()
