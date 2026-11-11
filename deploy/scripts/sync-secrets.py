#!/usr/bin/env python3
"""Operator command: private pipes only; requires temporary operator sudo on both hosts."""
import subprocess

def ssh(host, command, data=None):
    args = ['ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes']
    if host == '100.98.24.40':
        args += ['-o', 'HostKeyAlias=103.252.137.194']
    return subprocess.run(args + ['devops@' + host, command], input=data, capture_output=True, check=True).stdout

for name in ('backend_config', 'migration_config'):
    data = ssh('100.98.24.40', 'sudo -n cat /etc/jobbod/secrets/' + name)
    ssh('160.187.246.154', 'sudo -n install -o 10001 -g 10001 -m 600 /dev/stdin /etc/jobbod/secrets/' + name, data)
print('Backend and migration secrets synchronized without console output')
