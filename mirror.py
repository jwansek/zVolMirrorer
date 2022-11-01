import datetime
import fabric
import subprocess
import configparser
import time
import os

CONFIG = configparser.ConfigParser()

def get_nas_ssh_conn():
    return fabric.Connection(
        host = CONFIG.get("host", "ip"),
        user = CONFIG.get("host", "ssh_user"),
        connect_kwargs = {
            "key_filename": CONFIG.get("host", "ssh_key"),
        }
    )

def get_active_iscsi_connections():
    connections = get_nas_ssh_conn().run("ctladm islist", hide=True, pty=True).stdout.split("\n")[1:-1]
    return [i.split() for i in connections]

def get_drives():
    proc = subprocess.Popen(["lsblk"], stdout = subprocess.PIPE)
    blocks = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        blocks.append(line.decode().rstrip())
    return {i.split()[0] for i in blocks[1:]}

def connect_iscsi(host, iqn, target):
    for id_, initiator_ip, initiator_iqn, active_target in get_active_iscsi_connections():
        if active_target == "%s:%s" % (iqn, target):
            raise ConnectionError("Cannot connect to target '%s', initiator '%s' is connected at '%s'" % (active_target, initiator_iqn, initiator_ip))

    before_drives = get_drives()
    subprocess.run(["iscsiadm", "--mode", "node", "--targetname", "%s:%s" % (iqn, target), "--portal", host, "--login"])
    time.sleep(2)
    new_drives = get_drives().difference(before_drives)
    if len(new_drives) != 1:
        raise ConnectionError("Could not connect to iSCSI target, or could not ascertain new drive letter")
    
    return list(new_drives)[0]

def disconnect_iscsi(host, iqn, target):
    subprocess.run(["iscsiadm", "--mode", "node", "--targetname", "%s:%s" % (iqn, target), "--portal", host, "-u"])

def mirror_dd(source, target):
    cmd = ["time", "dd", "if=/dev/%s" % source, "of=/dev/%s" % target, "status=progress"]
    print(" ".join(cmd))
    subprocess.run(cmd)

def main():
    source_drive = connect_iscsi(CONFIG.get("host", "ip"), CONFIG.get("host", "target_iqn"), CONFIG.get("host", "source_target"))
    print("Source: %s:%s --> %s" % (CONFIG.get("host", "target_iqn"), CONFIG.get("host", "source_target"), source_drive))

    target_drive = connect_iscsi(CONFIG.get("host", "ip"), CONFIG.get("host", "target_iqn"), CONFIG.get("host", "target_target"))
    print("Target: %s:%s --> %s" % (CONFIG.get("host", "target_iqn"), CONFIG.get("host", "target_target"), target_drive))

    mirror_dd(source_drive, target_drive)

    disconnect_iscsi(CONFIG.get("host", "ip"), CONFIG.get("host", "target_iqn"), CONFIG.get("host", "source_target"))
    disconnect_iscsi(CONFIG.get("host", "ip"), CONFIG.get("host", "target_iqn"), CONFIG.get("host", "target_target"))

if __name__ ==  "__main__":
    cwd = os.getcwd()

    os.chdir(os.path.dirname(__file__))
    CONFIG.read("mirrorer.conf")
    main()
    print("Finished at %s\n\n\n" % datetime.datetime.now())
    os.chdir(cwd)

    
