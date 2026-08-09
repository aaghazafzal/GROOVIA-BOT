"""
Groovia VPS Deployer — Uploads mass_indexer to VPS and starts the pipeline
"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path

# ── VPS Config ────────────────────────────────────────────────────────────────
VPS_IP       = "206.189.128.37"
VPS_USER     = "root"
VPS_PASS     = "A@ghaZ9431A"
VPS_DIR      = "/root/groovia"
LOCAL_DIR    = "mass_indexer"

# ── Files to upload ───────────────────────────────────────────────────────────
FILES = [
    "mass_indexer/config.py",
    "mass_indexer/db.py",
    "mass_indexer/discovery.py",
    "mass_indexer/downloader.py",
    "mass_indexer/uploader.py",
    "mass_indexer/pipeline.py",
    "mass_indexer/run.py",
    "mass_indexer/requirements.txt",
    "mass_indexer/setup.sh",
]

def run_cmd(ssh, cmd, show_output=True):
    """Run command on server and return output"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if show_output and out:
        print(f"    {out}")
    if err and 'warn' not in err.lower() and 'deprecat' not in err.lower():
        print(f"    [ERR] {err[:200]}")
    return out


def main():
    print("\n" + "="*60)
    print("  GROOVIA VPS DEPLOYER")
    print(f"  Target: {VPS_USER}@{VPS_IP}:{VPS_DIR}")
    print("="*60 + "\n")

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    print(f"[1] Connecting to VPS {VPS_IP}...")
    try:
        ssh.connect(
            VPS_IP,
            port=22,
            username=VPS_USER,
            password=VPS_PASS,
            timeout=30,
            look_for_keys=False,
            allow_agent=False,
            auth_timeout=30,
            banner_timeout=30,
            disabled_algorithms={
                'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']
            }
        )
        print("    Connected!")
    except paramiko.AuthenticationException:
        print("    Auth failed - trying keyboard-interactive...")
        try:
            transport = ssh.get_transport()
            transport.auth_interactive_dumb(VPS_USER, lambda title, instr, fields: [VPS_PASS] * len(fields))
            print("    Connected via keyboard-interactive!")
        except Exception as e2:
            print(f"    FAILED: {e2}")
            print(f"\n    Try manually: ssh root@{VPS_IP}")
            print(f"    Password: {VPS_PASS}")
            return
    except Exception as e:
        print(f"    FAILED: {e}")
        return

    # ── Step 2: Setup system ───────────────────────────────────────────────────
    print("\n[2] Installing system packages (ffmpeg, python3, tmux)...")
    run_cmd(ssh, "apt-get update -qq 2>&1 | tail -3")
    run_cmd(ssh, "apt-get install -y -qq ffmpeg python3 python3-pip python3-venv tmux htop 2>&1 | tail -5")
    ffmpeg_ver = run_cmd(ssh, "ffmpeg -version 2>&1 | head -1", show_output=False)
    print(f"    ffmpeg: {ffmpeg_ver[:60]}")
    python_ver = run_cmd(ssh, "python3 --version", show_output=False)
    print(f"    python: {python_ver}")

    # ── Step 3: Create directories ────────────────────────────────────────────
    print(f"\n[3] Creating directories...")
    run_cmd(ssh, f"mkdir -p {VPS_DIR} /tmp/groovia_dl")
    print(f"    {VPS_DIR} created")

    # ── Step 4: Upload files via SFTP ─────────────────────────────────────────
    print(f"\n[4] Uploading {len(FILES)} files to server...")
    sftp = ssh.open_sftp()
    for local_path in FILES:
        if not os.path.exists(local_path):
            print(f"    SKIP (not found): {local_path}")
            continue
        filename   = os.path.basename(local_path)
        remote_path = f"{VPS_DIR}/{filename}"
        sftp.put(local_path, remote_path)
        size = os.path.getsize(local_path)
        print(f"    Uploaded: {filename} ({size/1024:.1f} KB)")
    sftp.close()

    # ── Step 5: Setup Python venv ─────────────────────────────────────────────
    print(f"\n[5] Setting up Python virtual environment...")
    run_cmd(ssh, f"cd {VPS_DIR} && python3 -m venv venv 2>&1 | tail -3")
    print("    venv created")

    # ── Step 6: Install Python packages ───────────────────────────────────────
    print(f"\n[6] Installing Python packages (this takes 2-3 mins)...")
    install_cmd = (
        f"cd {VPS_DIR} && "
        f"venv/bin/pip install --upgrade pip -q && "
        f"venv/bin/pip install -r requirements.txt -q 2>&1 | tail -10"
    )
    run_cmd(ssh, install_cmd)
    yt_dlp_ver = run_cmd(ssh, f"{VPS_DIR}/venv/bin/yt-dlp --version 2>/dev/null", show_output=False)
    print(f"    yt-dlp: {yt_dlp_ver}")

    # ── Step 7: Test connections ───────────────────────────────────────────────
    print(f"\n[7] Testing all connections...")
    test_cmd = f"cd {VPS_DIR} && venv/bin/python run.py test 2>&1"
    run_cmd(ssh, test_cmd)

    # ── Step 8: Kill any existing session ────────────────────────────────────
    print(f"\n[8] Preparing tmux session...")
    run_cmd(ssh, "tmux kill-session -t groovia 2>/dev/null; sleep 1", show_output=False)

    # ── Step 9: Start the pipeline in tmux ────────────────────────────────────
    print(f"\n[9] Starting Groovia Mass Indexer in background (tmux)...")
    start_cmd = (
        f"tmux new-session -d -s groovia "
        f"'cd {VPS_DIR} && venv/bin/python run.py run --workers 5 "
        f"2>&1 | tee groovia_indexer.log'"
    )
    run_cmd(ssh, start_cmd)
    time.sleep(3)

    # Verify it started
    sessions = run_cmd(ssh, "tmux list-sessions 2>/dev/null", show_output=False)
    if 'groovia' in sessions:
        print("    Pipeline started in tmux session 'groovia'!")
    else:
        print("    WARNING: tmux session not found, trying again...")
        run_cmd(ssh, start_cmd)

    # Show first few lines of output
    time.sleep(5)
    print(f"\n[10] Live output (first 20 lines):")
    out = run_cmd(ssh, f"cat {VPS_DIR}/groovia_indexer.log 2>/dev/null | head -20", show_output=False)
    print(out if out else "    (log empty - pipeline just started)")

    ssh.close()

    print("\n" + "="*60)
    print("  DEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"""
  Pipeline is running 24/7 on your VPS!

  To check progress anytime:
    ssh root@{VPS_IP}
    password: A@ghaZ9431a
    tmux attach -t groovia    <- Live progress
    (Ctrl+B then D to detach)

  Quick stats check:
    ssh root@{VPS_IP} 'cd {VPS_DIR} && venv/bin/python run.py stats'

  If server reboots, restart with:
    tmux new-session -d -s groovia 'cd {VPS_DIR} && venv/bin/python run.py retry --workers 5'

  Target: 1,00,000 songs in 8 days
  Channel: song database (Telegram)
""")


if __name__ == '__main__':
    main()
