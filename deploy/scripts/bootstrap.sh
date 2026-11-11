#!/bin/bash
set -euo pipefail
[[ $EUID == 0 && $# == 1 ]] || { echo 'Run as root: bootstrap.sh app|infra'; exit 2; }
role=$1
source_dir=$(cd "$(dirname "$0")/.." && pwd)
install -d -m 700 /etc/jobbod /etc/jobbod/secrets
install -d -m 755 /var/lib/jobbod /opt/jobbod
case "$role" in
app)
    install -d -m 755 /opt/jobbod/app
    install -m 644 "$source_dir/app/compose.yaml" "$source_dir/app/nginx.conf" "$source_dir/app/cloudflare-realip.conf" /opt/jobbod/app/
    install -d -m 755 /var/lib/jobbod/acme
    if [[ -d /etc/letsencrypt/renewal-hooks/deploy ]]; then
        install -m 755 "$source_dir/scripts/renew-tls.sh" /etc/letsencrypt/renewal-hooks/deploy/jobbod-nginx
    fi
    install -d -o 10001 -g 10001 -m 700 /var/lib/jobbod/models /var/lib/jobbod/next-cache
    install -m 755 "$source_dir/scripts/deploy.py" /usr/local/sbin/jobbod-deploy
    install -m 755 "$source_dir/scripts/ci-entry.sh" /usr/local/bin/jobbod-ci-entry
    printf 'devops ALL=(root) NOPASSWD: /usr/local/sbin/jobbod-deploy *\n' > /etc/sudoers.d/50-jobbod-deploy
    chmod 440 /etc/sudoers.d/50-jobbod-deploy
    visudo -cf /etc/sudoers.d/50-jobbod-deploy
    ;;
infra)
    install -d -m 755 /opt/jobbod/infra
    install -m 644 "$source_dir/infra/compose.yaml" "$source_dir/infra/redis.conf" "$source_dir/infra/minio-admin.py" "$source_dir/infra/admin-requirements.txt" /opt/jobbod/infra/
    install -m 755 "$source_dir/scripts/minio-admin.sh" /usr/local/sbin/jobbod-minio-admin
    install -m 755 "$source_dir/scripts/rotate-runtime.py" /usr/local/sbin/jobbod-rotate-runtime
    python3 "$source_dir/scripts/init-secrets.py"
    if [[ ! -f /opt/jobbod/infra/.env ]]; then install -m 600 "$source_dir/infra/.env.example" /opt/jobbod/infra/.env; fi
    install -m 755 "$source_dir/infra/init-db.sh" /opt/jobbod/infra/
    install -d -o 999 -g 999 -m 700 /var/lib/jobbod/postgres /var/lib/jobbod/redis
    install -d -o 10001 -g 10001 -m 700 /var/lib/jobbod/minio
    install -m 755 "$source_dir/scripts/infra-firewall.sh" /usr/local/sbin/jobbod-infra-firewall
    printf '[Unit]\nDescription=Jobbod Docker ingress firewall\nAfter=docker.service tailscaled.service\nRequires=docker.service\nPartOf=docker.service\n[Service]\nType=oneshot\nRemainAfterExit=yes\nExecStart=/usr/local/sbin/jobbod-infra-firewall\n[Install]\nWantedBy=docker.service\n' > /etc/systemd/system/jobbod-infra-firewall.service
    systemctl daemon-reload
    systemctl enable --now jobbod-infra-firewall.service
    install -m 755 "$source_dir/scripts/backup.sh" /usr/local/sbin/jobbod-backup
    install -m 755 "$source_dir/scripts/restore.sh" /usr/local/sbin/jobbod-restore
    install -d -m 700 /var/backups/jobbod
    printf '[Unit]\nDescription=Jobbod PostgreSQL backup\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/jobbod-backup\n' > /etc/systemd/system/jobbod-backup.service
    printf '[Unit]\nDescription=Daily Jobbod backup\n[Timer]\nOnCalendar=*-*-* 03:15:00\nPersistent=true\n[Install]\nWantedBy=timers.target\n' > /etc/systemd/system/jobbod-backup.timer
    systemctl daemon-reload
    systemctl enable --now jobbod-backup.timer
    ;;
*) exit 2;;
esac
