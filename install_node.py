"""
Install Node.js on VPS and re-test yt-dlp.
yt-dlp needs a JavaScript runtime to solve YouTube's signature challenges.
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
    out = stdout.read().decode('utf-8', errors='replace').strip()
    return out

def main():
    print("=== FIXING JS RUNTIME ERROR ===")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)

    print("[1] Installing Node.js on VPS...")
    out = run(ssh, "apt-get update -qq && apt-get install -y nodejs 2>&1 | tail -5")
    print(f"    {out}")
    
    node_ver = run(ssh, "node -v || nodejs -v")
    print(f"    Node version installed: {node_ver}")

    print("\n[2] Re-testing Kesariya download...")
    test = r"""
import sys, os
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')
from downloader import download_song, delete_song
print('Downloading Kesariya...')
path, _ = download_song('NJAv_7lHUIU')
if path and os.path.exists(path):
    mb = os.path.getsize(path)/1024/1024
    print('SUCCESS: %.2f MB' % mb)
    delete_song(path)
else:
    print('FAILED')
"""
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/test_cookies.py", 'w') as f:
        f.write(test)
    sftp.close()

    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python test_cookies.py 2>&1 | grep -E '(SUCCESS|FAILED|Downloading)'", timeout=90)
    print(f"    {out}")

    if 'SUCCESS' in out:
        print("\n[3] It worked! Node.js fixed the signature issue. Restarting pipeline...")
        run(ssh, "tmux kill-session -t groovia 2>/dev/null; sleep 2")
        
        # Start pipeline
        start = (
            f"tmux new-session -d -s groovia "
            f"'cd {VPS_DIR} && venv/bin/python run.py run --workers 5 "
            f"2>&1 | tee groovia_indexer.log'"
        )
        run(ssh, start)
        print("    Pipeline restarted!")
    else:
        print("\n❌ Still failing. We might need a different workaround.")

    ssh.close()

if __name__ == '__main__':
    main()
