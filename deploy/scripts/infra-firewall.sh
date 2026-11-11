#!/bin/bash
set -euo pipefail
iptables -w -N JOBBOD-INFRA 2>/dev/null || iptables -w -F JOBBOD-INFRA
iptables -w -A JOBBOD-INFRA -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
iptables -w -A JOBBOD-INFRA -i tailscale0 -s 100.110.186.46 -p tcp -m multiport --dports 5432,6379,9000 -j RETURN
iptables -w -A JOBBOD-INFRA -i tailscale0 -s 100.74.53.37 -p tcp -m multiport --dports 5432,6379,9000,9001 -j RETURN
iptables -w -A JOBBOD-INFRA -p tcp -m multiport --dports 5432,6379,9000,9001 -j REJECT
iptables -w -A JOBBOD-INFRA -j RETURN
if ! iptables -w -C DOCKER-USER -j JOBBOD-INFRA 2>/dev/null; then
    iptables -w -I DOCKER-USER 1 -j JOBBOD-INFRA
fi
