"""
Upload YouTube cookies to VPS and restart pipeline with cookies
"""
import sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy

VPS_IP        = "206.189.128.37"
VPS_USER      = "root"
VPS_PASS      = "A@ghaZ9431A"
VPS_DIR       = "/root/groovia"
LOCAL_COOKIES = r"C:\ALL FINAL PROJECTS\BOTS\GROOVIA_BOT\www.youtube.com_cookies.txt"

def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    print("\n=== GROOVIA COOKIE UPLOAD & RESTART ===\n")

    # Check cookies file exists
    if not os.path.exists(LOCAL_COOKIES):
        print(f"ERROR: Cookies file not found: {LOCAL_COOKIES}")
        return
    size = os.path.getsize(LOCAL_COOKIES)
    print(f"[1] Cookies file found: {size} bytes")

    # Quick peek - count lines
    with open(LOCAL_COOKIES, 'r', encoding='utf-8', errors='replace') as f:
        lines = [l for l in f.readlines() if not l.startswith('#') and l.strip()]
    print(f"    Contains {len(lines)} cookie entries")

    # Connect to VPS
    print("\n[2] Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS,
                timeout=20, look_for_keys=False, allow_agent=False)
    print("    Connected!")

    # Upload cookies
    print("\n[3] Uploading cookies.txt to VPS...")
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_COOKIES, f"{VPS_DIR}/cookies.txt")
    sftp.close()
    print(f"    Uploaded: {size} bytes → {VPS_DIR}/cookies.txt")

    # Update downloader.py to use cookies
    print("\n[4] Updating downloader to use cookies...")
    patch = f"""
import sys
sys.path.insert(0, '{VPS_DIR}')
content = open('{VPS_DIR}/downloader.py').read()

# Add cookiefile to yt-dlp opts (if not already there)
if 'cookiefile' not in content:
    old = "'nopart': True,"
    new = "'nopart': True,\\n        'cookiefile': '{VPS_DIR}/cookies.txt',"
    content = content.replace(old, new, 1)
    open('{VPS_DIR}/downloader.py', 'w').write(content)
    print('Added cookiefile to downloader.py')
else:
    print('cookiefile already present in downloader.py')
"""
    # Write patch script
    sftp = ssh.open_sftp()
    with sftp.open(f"{VPS_DIR}/patch_cookies.py", 'w') as f:
        f.write(patch)
    sftp.close()
    out = run(ssh, f"cd {VPS_DIR} && venv/bin/python patch_cookies.py 2>&1")
    print(f"    {out}")

    # Test download with cookies
    print("\n[5] Testing download with cookies (Kesariya)...")
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
        print("\n[6] Cookies work! Restarting pipeline...")
        run(ssh, "tmux kill-session -t groovia 2>/dev/null; sleep 2")

        # Reset all failed/stuck songs
        reset = r"""
import sys, os
sys.path.insert(0, '/root/groovia')
os.chdir('/root/groovia')
from db import Database
db = Database()
r = db.col.update_many(
    {'status': {'$in': ['failed', 'downloading']}},
    {'$set': {'status': 'pending', 'error': None, 'retry_count': 0}}
)
s = db.get_stats()
print('Reset: %d | Pending: %d | Uploaded: %d' % (r.modified_count, s.get('pending',0), s.get('uploaded',0)))
db.close()
"""
        sftp = ssh.open_sftp()
        with sftp.open(f"{VPS_DIR}/reset3.py", 'w') as f:
            f.write(reset)
        sftp.close()
        out2 = run(ssh, f"cd {VPS_DIR} && venv/bin/python reset3.py 2>&1 | tail -3")
        print(f"    {out2}")

        # Start pipeline
        start = (
            f"tmux new-session -d -s groovia "
            f"'cd {VPS_DIR} && venv/bin/python run.py run --workers 5 "
            f"2>&1 | tee groovia_indexer.log'"
        )
        run(ssh, start)
        time.sleep(8)
        sess = run(ssh, "tmux list-sessions 2>/dev/null")
        print(f"    tmux: {sess}")

        # Wait and check logs
        print("\n[7] Checking logs in 60 seconds...")
        time.sleep(60)
        logs = run(ssh, f"tail -20 {VPS_DIR}/groovia_indexer.log 2>/dev/null")
        print(logs)

        # Check if any song downloaded
        uploads = run(ssh, f"cd {VPS_DIR} && venv/bin/python -c \"from db import Database; db=Database(); s=db.get_stats(); print('Uploaded:',s.get('uploaded',0)); db.close()\" 2>/dev/null")
        print(f"\n    DB check: {uploads}")

        print("\n✅ DONE! Songs should now appear in 'song database' channel!")
        print("   Check Telegram — first new song should come within 1-2 minutes!")
    else:
        print("\n❌ Cookies also didn't work. Try re-exporting from YouTube.")

    ssh.close()

if __name__ == '__main__':
    main()
