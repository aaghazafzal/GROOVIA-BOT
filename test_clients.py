"""
Test various yt-dlp player clients with cookies on VPS to find the working combination.
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
    print("=== TESTING YT-DLP CLIENTS ON VPS ===")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    test_script = """
import yt_dlp
import os

TEST_ID = 'NJAv_7lHUIU'
URL = f"https://music.youtube.com/watch?v={TEST_ID}"

clients = [
    ['web'],
    ['android'],
    ['ios'],
    ['mweb'],
    ['web_music'],
    ['android_music'],
    ['web', 'ios'],
    ['mweb', 'android'],
    ['tv'],
]

print("Testing different player clients with cookies...")

for client in clients:
    print(f"\\n--- Testing client: {client} ---")
    
    mp3 = f'/tmp/test_{client[0]}.mp3'
    if os.path.exists(mp3):
        os.remove(mp3)
        
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': mp3,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': '/root/groovia/cookies.txt',
        'extractor_args': {
            'youtube': {
                'player_client': client,
                'player_skip': ['webpage', 'configs']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(URL, download=True)
            
        if os.path.exists(mp3) and os.path.getsize(mp3) > 10000:
            print(f"✅ SUCCESS: {client}")
            os.remove(mp3)
        else:
            print(f"❌ FAILED (no file or too small)")
    except Exception as e:
        err = str(e).lower()
        if 'sign in' in err or 'bot' in err:
            print(f"❌ FAILED: Bot Blocked (Sign in required)")
        else:
            print(f"❌ FAILED: {str(e)[:80]}")
"""
    
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_clients.py", 'w') as f:
        f.write(test_script)
    sftp.close()

    print("[*] Running exhaustive client tests (this will take a minute)...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_clients.py 2>&1")
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
