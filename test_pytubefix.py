"""
Test pytubefix on VPS
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

    print("Installing pytubefix...")
    run(ssh, f"cd {VPS_DIR} && venv/bin/pip install pytubefix -q")

    test = r"""
import sys, os
from pytubefix import YouTube
from pytubefix.cli import on_progress

print("Testing pytubefix with WEB client...")
try:
    yt = YouTube('https://www.youtube.com/watch?v=NJAv_7lHUIU', client='WEB')
    print(yt.title)
    ys = yt.streams.get_audio_only()
    ys.download(output_path='/tmp', filename='test_pytubefix.m4a')
    sz = os.path.getsize('/tmp/test_pytubefix.m4a')
    print(f"SUCCESS (WEB)! Size: {sz/1024/1024:.2f} MB")
    sys.exit(0)
except Exception as e:
    print(f"WEB failed: {e}")

print("\nTesting pytubefix with ANDROID client...")
try:
    yt = YouTube('https://www.youtube.com/watch?v=NJAv_7lHUIU', client='ANDROID')
    print(yt.title)
    ys = yt.streams.get_audio_only()
    ys.download(output_path='/tmp', filename='test_pytubefix.m4a')
    sz = os.path.getsize('/tmp/test_pytubefix.m4a')
    print(f"SUCCESS (ANDROID)! Size: {sz/1024/1024:.2f} MB")
    sys.exit(0)
except Exception as e:
    print(f"ANDROID failed: {e}")
    
print("\nTesting pytubefix with ANDROID_MUSIC client...")
try:
    yt = YouTube('https://music.youtube.com/watch?v=NJAv_7lHUIU', client='ANDROID_MUSIC')
    print(yt.title)
    ys = yt.streams.get_audio_only()
    ys.download(output_path='/tmp', filename='test_pytubefix.m4a')
    sz = os.path.getsize('/tmp/test_pytubefix.m4a')
    print(f"SUCCESS (ANDROID_MUSIC)! Size: {sz/1024/1024:.2f} MB")
    sys.exit(0)
except Exception as e:
    print(f"ANDROID_MUSIC failed: {e}")
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_pytubefix.py", 'w') as f:
        f.write(test)
    sftp.close()

    print("Running pytubefix test...")
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_pytubefix.py 2>&1")
    print(out)

    ssh.close()

if __name__ == '__main__':
    main()
