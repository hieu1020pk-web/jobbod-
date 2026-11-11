# Production HTTPS — jobbod.net

Frontend: https://jobbod.net/; API: https://api.jobbod.net/api/hello.
The API retains its `/api/` prefix. Frontend must use the API hostname when adding
browser fetch calls. CORS is owned by Nginx and permits only https://jobbod.net;
do not add a second CORS implementation in the application without replacing it.
Backend ports remain internal; FORWARDED_ALLOW_IPS=* trusts only callers on its
private Docker network. Nginx overwrites forwarding headers and accepts client
IP claims only from Cloudflare's published ranges (cloudflare-realip.conf).
Review that static range list when Cloudflare publishes changes.

Cloudflare DNS: proxied A @ and api -> 160.187.246.154. Do not add origin AAAA
unless the server has a configured and verified IPv6 path. Existing Cloudflare
edge AAAA answers are normal and do not imply an origin IPv6 record.
Use Full (strict), Universal SSL active, TLS minimum 1.2, TLS 1.3 enabled.
Enable Always Use HTTPS after origin HTTPS works. Bypass cache for API hostname;
do not apply Cache Everything to API or authenticated content. Keep ACME challenge
paths accessible on HTTP, without Cloudflare Access, bot challenge or custom
redirect rules intercepting them. Never use Flexible mode with origin redirects.
Zone SSL API permission was unavailable; owner confirmed Full (strict) manually.

Origin uses a free Let's Encrypt certificate with SANs jobbod.net and api.jobbod.net.
Certbot is installed on app host; renewal uses HTTP-01 webroot /var/lib/jobbod/acme.
Nginx mounts the entire /etc/letsencrypt directory read-only, preserving renewal
symlinks. Private key stays root-owned on server and is never committed or copied
to CI. certbot.timer is enabled; deploy hook runs nginx -t and reloads Nginx.
Renewal does not restart applications, run migrations, SSH, or build images.

Check: sudo certbot certificates; systemctl list-timers certbot.timer;
sudo journalctl -u certbot.service; sudo certbot renew --dry-run --run-deploy-hooks --no-random-sleep-on-renew.
The initial ACME account was registered without email; operators may add a real
address using `sudo certbot update_account --email <operator-address>`. Configure
external expiry monitoring before relying on this as the sole expiry control.

For a fresh host, first install certbot and provide an HTTP Nginx listener serving
/.well-known/acme-challenge/ from /var/www/acme, mounting
/var/lib/jobbod/acme:/var/www/acme:ro. Obtain certificate before starting final TLS
configuration:

    sudo certbot certonly --webroot -w /var/lib/jobbod/acme \
      -d jobbod.net -d api.jobbod.net --cert-name jobbod.net \
      --agree-tos --non-interactive --email <operator-address>

Then install canonical app config and renewal hook via scripts/bootstrap.sh app,
recreate Nginx with `docker compose --env-file /etc/jobbod/releases.env up -d --no-deps --force-recreate --wait nginx`, and enable certbot.timer. Recreate after replacing bind-mounted config files; a plain up/reload may retain the previous file inode. There is one final Nginx config;
the HTTP-only issuance listener is temporary provisioning, not an alternate runtime.

Nginx redirects known HTTP hosts to HTTPS, rejects unknown TLS hostnames and
provides an internal HTTP /health/gateway endpoint for container checks. Deploy
smoke checks connect to local HTTPS with --resolve and normal CA verification,
so application CI does not depend on Cloudflare reachability or cache. No curl -k.
HSTS starts at max-age=86400 without includeSubDomains/preload; increase only after
verifying all required hosts and long-term certificate renewal.

Origin 80/443 currently remain publicly reachable. Full (strict) validates TLS but
does not by itself prevent Cloudflare bypass; restricting Docker ingress to
Cloudflare ranges or adding authenticated origin pulls is a separate hardening
step. No infra/MinIO hostname or public DB/Redis port was added.

## Verification 2026-11-11

Certificate issued for both hosts, expires 2027-02-09. Direct origin TLS and
Cloudflare HTTPS return 200; HTTP redirects to HTTPS. Owner confirmed Full
(strict). nginx -t passed; all app containers healthy. Allowed-origin preflight
returns 204 + exact ACAO; foreign origin gets no ACAO. Backend redirects preserve
HTTPS. Simulated ACME renewal and deploy hook succeeded; certbot.timer enabled
and active. Backend CI run 42964207555 attempt 3 succeeded with local HTTPS smoke
checks. No certificates, private keys or Cloudflare token were copied to Git.
