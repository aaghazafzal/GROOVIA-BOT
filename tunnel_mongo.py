"""
Setup SSH tunnel to VPS MongoDB so local bot can use VPS data.
Run this once in a separate terminal: python tunnel_mongo.py
Then the bot can connect to localhost:27017 which tunnels to VPS.
"""
import subprocess
import sys

print("🔗 Opening SSH tunnel to VPS MongoDB...")
print("   VPS port 27017 → localhost:27017")
print("   Keep this terminal open while using the bot!")
print("   Press Ctrl+C to close tunnel\n")

try:
    subprocess.run([
        "ssh",
        "-N",                      # no remote command
        "-L", "27017:localhost:27017",  # local 27017 → VPS 27017
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "root@206.189.128.37",
    ])
except KeyboardInterrupt:
    print("\n✅ Tunnel closed.")
