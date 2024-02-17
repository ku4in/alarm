#!/usr/bin/env python3

def nat_traversal():
    from socket import socket, AF_INET, SOCK_DGRAM, timeout
    import stun
    import json
    import os
    import sys
    import subprocess
    import time

    LPORT = 65000
    LHOST = '0.0.0.0'

    nat = stun.get_ip_info(LHOST, LPORT)
    nat_json = json.dumps(nat)
    os.system("clear")
    os.system(f"echo '{nat_json}' | qrencode -t ansiutf8")
    print(f"Your host parameters: {nat}")

    # clean clipboard
    os.system("termux-clipboard-set '' ")
    # try to get remote nat info in one minute
    print("Please, copy remote host info to your clipboard ...")
    remote_nat = ''
    for i in range(12):
        cb = subprocess.getoutput('termux-clipboard-get')
        try:
            remote_nat = json.loads(cb)
            if remote_nat:
                break
        except json.decoder.JSONDecodeError:
            pass
        time.sleep(5)
    else:
        print("Error: can't get remote host info", file=sys.stderr)
        sys.exit(1)

    print(f"Got remote host parameters: {remote_nat}")
    fnat_type, rip, rport = remote_nat

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind((LHOST, LPORT))
    sock.settimeout(5)

    for i in range(12):
        try:
            sock.sendto(b'NAT\n', (rip, rport))
            sock.recv(1024)
        except timeout:
            pass
        else:
            sock.sendto(b'NAT\n', (rip, rport))
            break
    else:
        print(f"Error: can't connect to remote host {rip}:{rport}", file=sys.stderr)
        sys.exit(1)

    print(f"Connection established with {rip}:{rport}")
    sock.settimeout(None)
    return rip, rport, sock
