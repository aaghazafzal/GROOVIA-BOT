"""
Fetch downloader.py from VPS to local file
"""
import sys
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

    sftp = ssh.open_sftp()
    sftp.get(f"{VPS_DIR}/downloader.py", r"C:\ALL FINAL PROJECTS\BOTS\GROOVIA_BOT\vps_downloader.py")
    sftp.close()
    ssh.close()
    print("Done downloading!")

if __name__ == '__main__':
    main()
