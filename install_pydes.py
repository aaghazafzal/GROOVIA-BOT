import paramiko
from paramiko import SSHClient, AutoAddPolicy

def main():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect("206.189.128.37", username="root", password="A@ghaZ9431A", timeout=10)
    
    cmd = "/root/groovia/venv/bin/pip install pyDes"
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("STDOUT:", out)
    print("STDERR:", err)
    
    ssh.close()

if __name__ == '__main__':
    main()
