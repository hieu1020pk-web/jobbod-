# JOBBOD — Tài liệu bàn giao server App, Infra và CI/CD

**Ngày chốt thông tin:** 11/11/2026. **Môi trường:** một cụm triển khai, chưa tách staging/production.
**Repo:** https://github.com/hieu1020pk-web/jobbod- . Tài liệu và cấu hình vận hành chuẩn nằm trên nhánh `backend/ci-cd`, thư mục `deploy/`.

Tài liệu dành cho người tiếp nhận vận hành. Không chứa mật khẩu, token, private key hoặc dữ liệu thật. Người mới phải được cấp quyền riêng; không dùng lại khóa cá nhân của người bàn giao.

## 1. Đọc nhanh trước khi thao tác

- Website: https://jobbod.net/ . API kiểm tra: https://api.jobbod.net/api/hello . API vẫn giữ prefix `/api/`.
- Source được build trên GitHub Actions; server chỉ pull image từ GHCR và chạy Docker Compose.
- App và Infra kết nối qua Tailscale, không kết nối database bằng IP public.
- `devops` chưa thuộc nhóm `docker`: dùng `sudo docker ...`, nhập mật khẩu quản trị khi được yêu cầu. Đây là phân quyền có chủ đích, không phải lỗi Docker.
- Quyền sudo toàn phần không tương tác tạm thời đã được gỡ. CI dùng khóa SSH riêng và script deploy được cấp quyền giới hạn.
- Không chạy `docker compose down -v`, `docker system prune --volumes`, xóa thư mục dữ liệu hoặc thay secrets tùy tiện.
- Không chạy `docker compose up` cho toàn bộ app khi chưa kiểm tra image state và profile migration. Dùng script deploy cho phát hành; dùng `--no-deps` cho bảo trì từng service.
- Hướng dẫn TLS chi tiết: [TLS.md](TLS.md). Bằng chứng kiểm thử: [VERIFICATION.md](VERIFICATION.md). Các số đo không phải cam kết SLA.

## 2. Kiến trúc và inventory

```text
Người dùng
    │ HTTPS
Cloudflare: DNS proxy + Edge TLS, Full (strict)
    │ HTTPS tới origin
App 160.187.246.154 / Tailscale 100.110.186.46
    └─ Nginx :80/:443
         ├─ jobbod.net          → frontend:3000 (Next.js)
         └─ api.jobbod.net      → backend:8000 (FastAPI)
                                   └─ AI nội bộ: ai:8000 (skeleton)
    │ Tailscale: DB / Redis / S3
Infra 103.252.137.194 / Tailscale 100.98.24.40
    ├─ PostgreSQL + pgvector :5432
    ├─ Redis                :6379
    └─ MinIO S3 :9000 / console :9001
```

Đường backend → AI là hướng tích hợp dự kiến; skeleton hiện chưa có nghiệp vụ gọi model hay inference.

| Thuộc tính | Server App | Server Infra |
|---|---|---|
| Hostname | `application` | `infra` |
| SSH user | `devops` | `devops` |
| IP public | `160.187.246.154` | `103.252.137.194` |
| IP Tailscale | `100.110.186.46` | `100.98.24.40` |
| RAM quan sát | 3.8 GiB, tương đương máy 4 GB | 5.8 GiB, tương đương máy 6 GB |
| Disk root | 40 GB, còn khoảng 32 GB khi bàn giao | 99 GB, còn khoảng 89 GB khi bàn giao |
| Swap quan sát | Chưa có | Chưa có |
| Nền tảng | Ubuntu 24.04 LTS, x86_64 | Ubuntu 24.04 LTS, x86_64 |
| Compose project | `jobbod-app` | `jobbod-infra` |
| Dịch vụ nền | Docker, Tailscale, Certbot timer | Docker, Tailscale, backup timer, firewall unit |

Số tài nguyên trống là snapshot; luôn chạy `free -h`, `df -h /` trước bảo trì. Docker và Tailscale trên cả hai máy được đọc lại là active lúc soạn tài liệu; chứng nhận container healthy dựa trên các lần kiểm tra triển khai, không phải hệ thống giám sát liên tục.

### Container và ngân sách tài nguyên

| Service | Runtime | RAM limit | Ghi chú |
|---|---|---|---|
| frontend | Next.js 16.4.6 / React 19.3.0, Node 24 image | 512 MiB | Standalone, user 10001 |
| backend | FastAPI, Python 3.12, uv lock | 640 MiB | Một worker; sở hữu schema/migration |
| ai | FastAPI CPU, Python 3.12, uv lock | 1536 MiB | Một worker; chưa chọn/tải model |
| nginx | Image stable-alpine, pin digest | 64 MiB | TLS, routing, CORS |
| migrate | Alembic trong image backend | 256 MiB | Chạy tạm; không phải daemon |
| postgres | PostgreSQL 17, pgvector 0.8.7 | 2 GiB | shared_buffers 512 MB; max_connections 60 |
| redis | Redis 7.4, AOF | 512 MiB | maxmemory 384 MB; allkeys-lru |
| minio | Build từ source commit cố định | 1536 MiB | Community upstream đã archive |

Image được pin bằng digest trong Compose hoặc state release. Phiên bản chính xác và giới hạn còn lại xem `app/compose.yaml`, `infra/compose.yaml`. App có cpus limit cho từng service Python/Next.js; đây không phải máy đủ cho mọi model CPU/RAM lớn.

## 3. Truy cập quản trị và nhận bàn giao quyền

Máy người quản trị phải có SSH key được cấp, tham gia đúng tailnet và được firewall cho phép.

```bash
# App, từ máy quản trị
ssh -F /dev/null devops@160.187.246.154

# Infra: đường public SSH từng timeout; dùng Tailscale
ssh -F /dev/null -o HostKeyAlias=103.252.137.194 devops@100.98.24.40
```

`-F /dev/null` bỏ cấu hình SSH cá nhân không liên quan. `HostKeyAlias` dùng host key Infra đã lưu dưới IP public. Người mới phải đối chiếu fingerprint qua kênh tin cậy trước khi thêm known_hosts; không tắt StrictHostKeyChecking để vượt lỗi host key.

Nhận bàn giao qua kênh riêng: tài khoản nhà cung cấp VPS/console cứu hộ, quyền sudo của `devops`, Cloudflare zone/DNS, quyền quản trị tailnet và GitHub repo/packages/Actions. Bàn giao quyền, không chép private key cũ vào tài liệu/chat. Thử phiên SSH mới trước khi thu hồi key cũ.

Nhóm `docker` tương đương quyền quản trị rộng. Nếu tổ chức chủ động chọn cho `devops` chạy Docker trực tiếp, đó là một thay đổi phân quyền cần được ghi nhận; cấu hình hiện tại không cấp nhóm này.

## 4. Mạng và các cổng

| Đích | Cổng | Truy cập hiện tại |
|---|---|---|
| App SSH | 22 | Public SSH phục vụ GitHub-hosted runner và quản trị bằng key |
| App web | 80, 443 | Public; DNS web đi qua Cloudflare |
| frontend / backend / AI | 3000 / 8000 / 8000 | Chỉ mạng Docker, không publish host |
| Infra PostgreSQL | 5432 | Bind `100.98.24.40`; app và máy quản trị được phép |
| Infra Redis | 6379 | Bind `100.98.24.40`; app và máy quản trị được phép |
| Infra MinIO S3 | 9000 | Bind `100.98.24.40`; app và máy quản trị được phép |
| Infra MinIO Console | 9001 | Bind `100.98.24.40`; chỉ máy quản trị được cấu hình |

Máy quản trị hiện được whitelist Tailscale `100.74.53.37`. Khi chuyển người/máy quản trị, cần cập nhật firewall và tailnet policy bằng quyền quản trị trước khi bỏ đường cũ. Không mặc định mọi thiết bị trong tailnet đều vào được Infra.

Infra dùng UFW và chain `JOBBOD-INFRA` trong `DOCKER-USER`. Script `/usr/local/sbin/jobbod-infra-firewall` được systemd unit `jobbod-infra-firewall.service` áp dụng lại theo vòng đời Docker. Kiểm tra trên Infra:

```bash
sudo iptables -L JOBBOD-INFRA -n -v
sudo iptables -C DOCKER-USER -j JOBBOD-INFRA
sudo ufw status
systemctl status jobbod-infra-firewall.service
```

Đã áp dụng firewall host; chưa sửa ACL quản trị tailnet. `infra/tailscale-policy.hujson` là đoạn gợi ý để admin tailnet tích hợp, không phải bằng chứng policy đã được apply. Origin App 80/443 còn nhận trực tiếp ngoài Cloudflare; Full (strict) không ngăn bypass CDN. Chưa triển khai Cloudflare Tunnel hoặc Authenticated Origin Pulls.

## 5. Đường dẫn cần biết

| Vị trí | Máy | Vai trò |
|---|---|---|
| `/opt/jobbod/app/compose.yaml` | App | Compose đang vận hành |
| `/opt/jobbod/app/nginx.conf`, `cloudflare-realip.conf` | App | Routing/TLS/CORS; danh sách IP Cloudflare tin cậy |
| `/etc/jobbod/releases.env` | App | Digest hiện tại: FRONTEND_IMAGE, BACKEND_IMAGE, AI_IMAGE |
| `/etc/jobbod/{service}.previous` | App | Digest rollback gần nhất được script giữ |
| `/usr/local/sbin/jobbod-deploy` | App | Script deploy root-owned |
| `/usr/local/bin/jobbod-ci-entry` | App | Forced command kiểm soát khóa SSH CI |
| `/etc/sudoers.d/50-jobbod-deploy` | App | Sudo giới hạn cho script deploy |
| `/var/lib/jobbod/next-cache` | App | Cache Next.js bền |
| `/var/lib/jobbod/models` | App | Model cache bền, mount `/models` |
| `/etc/letsencrypt` | App | Chứng chỉ, private key, cấu hình renewal |
| `/var/lib/jobbod/acme` | App | Webroot HTTP-01 |
| `/opt/jobbod/infra/{compose.yaml,.env}` | Infra | Compose và digest image MinIO/CLI |
| `/var/lib/jobbod/{postgres,redis,minio}` | Infra | Dữ liệu bền; tuyệt đối không xóa để “reset deploy” |
| `/var/backups/jobbod` | Infra | PostgreSQL dump cục bộ |
| `/etc/jobbod/secrets` | Cả hai | Secrets; chỉ admin và UID container cần dùng đọc được |
| `/opt/jobbod/bootstrap/deploy` | Cả hai | Bản sao dùng cài đặt; có thể cũ, không phải nguồn chuẩn thay Git |

## 6. Lệnh kiểm tra hằng ngày

**Trên App:**

```bash
cd /opt/jobbod/app
sudo docker compose --env-file /etc/jobbod/releases.env ps
sudo docker compose --env-file /etc/jobbod/releases.env logs --tail 100 nginx backend
sudo docker stats --no-stream
free -h
df -h /
```

**Trên Infra:**

```bash
cd /opt/jobbod/infra
sudo docker compose ps
sudo docker compose logs --tail 100 postgres redis minio
systemctl list-timers jobbod-backup.timer
sudo ls -lh /var/backups/jobbod
```

**Từ máy người quản trị:**

```bash
curl -fsS https://jobbod.net/ -o /dev/null
curl -fsS https://api.jobbod.net/api/hello
```

Backend readiness kiểm tra DB, Redis có auth và quyền truy cập bucket; liveness không thay thế readiness. Đọc qua mạng Docker trên App:

```bash
cd /opt/jobbod/app
sudo docker compose --env-file /etc/jobbod/releases.env exec -T backend \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=15).read().decode())"
```

Khi chia sẻ logs, kiểm tra và che dữ liệu nhạy cảm. Không chép `/etc/jobbod/secrets`, `docker inspect` toàn bộ hoặc cấu hình credentials vào ticket/chat.

## 7. CI/CD: phát hành, rollback và giới hạn hiện tại

Local workspace `/home/tawn/code/Jobbod/{frontend,backend,ai}` gồm ba checkout độc lập của cùng repo. Source từng service nằm ở root trên cặp nhánh riêng; không phải monorepo chứa cả ba ứng dụng trong mỗi nhánh. Không merge nhánh của service này vào service khác. `main` vẫn giữ Vite cũ trong lịch sử, không phải nhánh triển khai hiện tại.

| Service | Nhánh viết code | Nhánh triển khai | Workflow |
|---|---|---|---|
| frontend | frontend/develop | frontend/ci-cd | frontend-deploy.yml |
| backend | backend/develop | backend/ci-cd | backend-deploy.yml |
| ai | ai/develop | ai/ci-cd | ai-deploy.yml |

Ví dụ trên checkout backend, sau review và kiểm tra phù hợp:

```bash
git switch backend/develop
git pull --ff-only origin backend/develop
# Hoàn tất thay đổi source, kiểm tra và push backend/develop trước.
git switch backend/ci-cd
git pull --ff-only origin backend/ci-cd
git merge backend/develop
git push origin backend/ci-cd
```

Không mặc định dùng fast-forward ở các lần phát triển sau: nhánh ci-cd đã có commit vận hành riêng. Khi conflict phải resolve/review; không force-push để vượt conflict. Đổi cấu hình vận hành thực hiện trên backend/ci-cd; đổi source backend thực hiện trên backend/develop rồi merge sang.

Luồng hiện tại: checkout → Buildx → đăng nhập GHCR bằng GITHUB_TOKEN → build/push native amd64 có cache → một SSH gọi deploy/check. Quyền workflow `contents: read`, `packages: write`. Package public để server pull không cần GH token; public repo không tự thay thế việc đặt package public.

GitHub secrets gồm `JOBBOD_DEPLOY_KEY` và `JOBBOD_KNOWN_HOSTS`. Khóa CI trong authorized_keys bị `restrict` và forced command; chỉ nhận `deploy <service> <image@sha256>`. Script root-owned xác thực namespace/repository/digest. Không cấp arbitrary shell hoặc cho CI thay Compose/script sudo.

Script server: kiểm tra disk ≥3 GiB → pull timeout 600 giây → flock tối đa 900 giây → kiểm tra cache model ≤8 GiB → migration backend → thay container service → chờ readiness tối đa 150 giây → kiểm tra gateway HTTPS local bằng `--resolve`, xác minh CA bình thường. Không dùng `curl -k`. Migration lỗi giữ backend cũ; health/smoke lỗi thử phục hồi image trước và báo CI fail. Nếu phục hồi cũng lỗi, cần xử lý thủ công; không có cam kết tự cứu mọi tình huống.

Có restart ngắn; không blue-green/zero-downtime. Backend phải dùng migration expand/contract tương thích phiên bản ứng dụng trước. Không tự downgrade DB. Mỗi service giữ image hiện tại và trước đó; không prune volume/model. Pull ở ngoài lock, thao tác thay đổi được serialize bằng lock chung trên App.

Theo dõi/chạy lại từ máy có quyền repo:

```bash
gh run list --repo hieu1020pk-web/jobbod- --limit 10
gh run view <RUN_ID> --repo hieu1020pk-web/jobbod- --log-failed
gh run rerun <RUN_ID> --repo hieu1020pk-web/jobbod-
```

Rerun hiện chạy lại cả job build/push/deploy, không chỉ SSH. Nút Run workflow trên UI có thể không hiện khi file không có trên default branch; người bàn giao cần hiểu cấu trúc nhánh này, không tùy ý đổi default branch để sửa UI.

Rollback thủ công trên App, chỉ khi có digest trước hợp lệ và DB còn tương thích:

```bash
sudo cat /etc/jobbod/backend.previous
sudo /usr/local/sbin/jobbod-deploy backend 'ghcr.io/hieu1020pk-web/jobbod-backend@sha256:<DIGEST_DA_XAC_NHAN>'
```

Digest rollback sau bootstrap có thể trống nếu chưa có bản trước; luôn kiểm tra. Không đưa password vào command line. Git revert source và deploy lại cũng cần xem xét schema, không phải rollback database.

### Đánh giá cho phát triển nhanh

**Đủ dùng cho giai đoạn hiện tại**, một App nhỏ và nhóm phát triển chấp nhận restart ngắn. Có cache, pin digest, một SSH, migration có thứ tự, health, rollback và giới hạn log/RAM. Backend và AI từng có lượt warm-cache 26–28 giây; thay dependency, mạng chậm hoặc source Next.js thay đổi có thể lâu hơn nhiều. Không thêm job test/lint riêng theo yêu cầu; đội phát triển vẫn phải kiểm tra source trước phát hành.

**Những đề xuất dưới đây CHƯA triển khai:** deploy lại riêng theo digest; chặn nhánh manual dispatch; ConnectTimeout 30 giây (hiện 15); Job Summary; persist-credentials=false; health/smoke chỉ theo service; chặn release cũ; bỏ qua digest không đổi; lịch sử deployment bền; xử lý tiến trình bị ngắt; cleanup GHCR định kỳ. AI hiện vẫn chịu smoke-check của cả frontend/backend; cache model vượt ngân sách cũng chặn deploy service khác. Khóa concurrency không thay thế cơ chế chống deploy commit cũ.

Ưu tiên kế tiếp: (1) chống deploy nhầm/cũ và xử lý interruption, (2) retry deploy theo digest và kiểm tra đúng service, (3) lịch sử/summary/cảnh báo, (4) đo cache Next.js khi sửa source thật, (5) dọn registry có bảo vệ digest rollback. Không cần đưa Kubernetes hoặc runner tự host trên App 4 GB vào lúc này. Khi workload/model/người dùng tăng, cần đánh giá thêm RAM/disk, môi trường staging và chiến lược không gián đoạn.

## 8. Thay đổi cấu hình server

Git `backend/ci-cd:deploy/` là nguồn chuẩn. CI app chỉ thay image; sửa Compose, Nginx, script privileged trong Git không tự cập nhật server. Một số đường dẫn deploy/docs nằm trong paths-ignore nên commit đó có thể không chạy workflow app.

Người quản trị phải review, chuyển các file được duyệt đến server và cài root-owned bằng sudo. Đối chiếu bản sao bootstrap với Git trước khi sử dụng. Không chạy lại bootstrap toàn bộ chỉ để sửa một dòng Nginx. Trước thay đổi hãy lưu bản config đang chạy trong thư mục root-only và giữ phiên SSH hiện hữu để phục hồi.

Kiểm tra Compose không in giá trị nhạy cảm:

```bash
cd /opt/jobbod/app
sudo docker compose --env-file /etc/jobbod/releases.env config --quiet
sudo docker compose --env-file /etc/jobbod/releases.env run --rm --no-deps nginx nginx -t
```

Khi thay file bind mount bằng `install` có thể đổi inode; cần recreate container Nginx để nhận file mới:

```bash
sudo docker compose --env-file /etc/jobbod/releases.env up -d --no-deps --force-recreate --wait nginx
```

Kiểm tra HTTPS frontend/API sau thay đổi. Nếu chỉ gia hạn cert, renewal hook reload Nginx là đủ vì mount cả thư mục chứng chỉ. Không cập nhật image PostgreSQL major hoặc đổi persisted schema như một deploy app bình thường; phải có kế hoạch backup/restore/migration riêng.

## 9. TLS, DNS và Cloudflare

DNS proxied A `@` và `api` trỏ `160.187.246.154`. Cloudflare Edge TLS bảo vệ trình duyệt → Cloudflare; Let's Encrypt trên App bảo vệ Cloudflare → Nginx. Full (strict), Always Use HTTPS, Minimum TLS 1.2, TLS 1.3 và cấu hình cache API đã được chủ hệ thống báo cấu hình; quyền API hiện có không cho đọc SSL settings nên đây là xác nhận của chủ hệ thống, không phải audit API độc lập.

Chứng chỉ SAN cho hai domain được cấp 11/11/2026, hạn lần cấp này 09/02/2027. `certbot.timer` tự gia hạn qua HTTP-01, hook `/etc/letsencrypt/renewal-hooks/deploy/jobbod-nginx` kiểm tra và reload Nginx. Không đặt key trong repo/image/Actions. Giữ đường ACME trên HTTP/HTTPS không bị Access/WAF/challenge chặn. CORS do Nginx quản lý, chỉ cho origin `https://jobbod.net`; backend tin forwarding headers vì không publish ra host và Nginx ghi đè headers.

```bash
# Trên App
sudo certbot certificates
systemctl list-timers certbot.timer
sudo journalctl -u certbot.service --since '7 days ago'
sudo certbot renew --dry-run --run-deploy-hooks --no-random-sleep-on-renew
```

Tài khoản ACME khởi tạo chưa có email; người nhận nên bổ sung email vận hành qua `sudo certbot update_account --email <EMAIL_VAN_HANH>` và thiết lập cảnh báo expiry bên ngoài. HSTS hiện 1 ngày, chưa includeSubDomains/preload. IP Cloudflare tin cậy là danh sách tĩnh, cần cập nhật khi Cloudflare đổi dải. Chi tiết cấp lại khi mất máy: [TLS.md](TLS.md).

## 10. Secrets và phân quyền dữ liệu

`/etc/jobbod` và thư mục secrets có mode 0700; file mode 0600. UID 10001 đọc config app/MinIO; UID 999 đọc PostgreSQL/Redis. Compose secrets là file mount read-only, không phải encrypted vault. Admin host và Docker daemon nằm trong phạm vi tin cậy. Không có Vault/Infisical/KMS hay cơ chế đồng bộ secrets tự động qua CI.

| Secret/tài khoản | Vị trí và phạm vi |
|---|---|
| backend_config | Infra giữ bản gốc, App nhận bản runtime; gồm DB runtime, Redis, S3 bucket jobbod |
| migration_config | Infra giữ bản gốc, App mount riêng cho migrate; không mount vào backend runtime |
| db_admin_password | Chỉ Infra; PostgreSQL admin |
| db_runtime_password / jobbod_runtime | Infra; role không được tạo bảng/schema |
| db_migration_password / jobbod_migration | Infra; sở hữu DB/schema, không phải superuser |
| redis_password / redis_acl | Infra; user jobbod, prefix jobbod:*, mặc định không auth bị từ chối |
| minio_root_user / minio_root_password | Chỉ Infra; không đưa cho app |
| s3_access_key / s3_secret_key | Infra; service account backend có policy giới hạn bucket jobbod |

Trong Git chỉ có tên/path secrets, không có giá trị. Người nhận lấy quyền đọc qua quản trị server/kho bí mật được tổ chức chỉ định, không qua tài liệu này. Khi chuyển người vận hành, kiểm kê/revoke key cũ và quyết định rotation, không tự khẳng định mật khẩu cũ đã được thay chỉ vì sửa file.

### Rotation runtime có downtime bảo trì

Đã có script `/usr/local/sbin/jobbod-rotate-runtime` trên Infra: đổi DB runtime, Redis và S3 service-account secret; không đổi PostgreSQL admin/migration hoặc MinIO root. Không có transaction chung xuyên ba hệ thống; lỗi giữa chừng phải phục hồi đồng bộ, giữ backend dừng.

1. Đảm bảo có quyền admin cả hai máy, tạm dừng lịch phát hành và có backup phục hồi. `scripts/sync-secrets.py` chạy từ máy quản trị dùng `sudo -n` trên hai máy: cần cấp quyền tạm phù hợp; việc vừa nhập `sudo` ở một phiên khác không bảo đảm script dùng được quyền.
2. Trên App, mở phiên root được quản lý rồi giữ khóa:

```bash
sudo -i
flock /run/lock/jobbod-app.lock bash
cd /opt/jobbod/app
docker compose --env-file /etc/jobbod/releases.env stop backend
```

3. Giữ nguyên shell đang giữ lock. Trên Infra, chạy `sudo /usr/local/sbin/jobbod-rotate-runtime`.
4. Từ checkout backend/ci-cd trên máy quản trị, chạy `python3 deploy/scripts/sync-secrets.py`. Script truyền secrets qua pipe SSH, không in console; không sửa nó để echo credentials.
5. Trong shell App đang giữ lock:

```bash
docker compose --env-file /etc/jobbod/releases.env up -d --no-deps --force-recreate --wait --wait-timeout 120 backend
curl -fsS --resolve api.jobbod.net:443:127.0.0.1 https://api.jobbod.net/api/hello
# Chạy thêm readiness/integration trước khi đóng bảo trì.
exit
exit
```

6. Xóa đúng thư mục recovery `/etc/jobbod/rotation-<timestamp>` do script vừa tạo chỉ sau khi mọi kiểm tra qua; thu hồi quyền admin tạm. Nếu fail, không xóa recovery và không resume traffic với secrets lệch nhau.

Đổi password PostgreSQL persisted phải ALTER ROLE, không chỉ đổi POSTGRES_PASSWORD_FILE. Đổi admin/migration/MinIO root cần quy trình bảo trì riêng và kiểm tra no-op migration/IAM. Muốn giữ secrets khi mất Infra phải có backup mã hóa bên ngoài; hiện chưa cấu hình đích/recipient key.

## 11. Backup, restore và sự cố mất máy

Infra có `jobbod-backup.timer` chạy 03:15 UTC mỗi ngày (10:15 giờ Việt Nam); script `/usr/local/sbin/jobbod-backup` tạo `pg_dump -Fc`, ghi `.tmp` rồi rename khi thành công, dọn bản hơn khoảng 7 ngày. Backup nằm cùng Infra: không bảo vệ khi mất cả máy/disk. Chưa có backup MinIO object, off-host hoặc kiểm thử DR toàn hệ thống từ máy trắng.

```bash
# Trên Infra: tạo backup ngay và xem log
sudo /usr/local/sbin/jobbod-backup
sudo journalctl -u jobbod-backup.service --since '7 days ago'
sudo ls -lh /var/backups/jobbod
```

Restore là thao tác phá dữ liệu hiện tại: phải chốt bản dump, có bản sao hiện trạng và dừng mọi writer trước. Với hệ thống hiện tại, giữ App deployment lock như quy trình bảo trì và stop backend; nếu sau này có worker/client khác ghi DB cũng phải dừng chúng.

```bash
# Trên Infra, chỉ trong cửa sổ bảo trì đã xác nhận
sudo /usr/local/sbin/jobbod-restore /var/backups/jobbod/postgres-<TIMESTAMP>.dump
```

Script dùng pg_restore --clean --if-exists --exit-on-error vào DB jobbod. Dump không chứa cluster roles hay secrets. Khi khôi phục sang cluster mới, phải tạo đúng role/extension/quyền trước, rồi restore; xác minh pgvector, Alembic revision và readiness trước mở writer. Không xóa volume để thử restore.

Đã thử restore vào DB riêng `jobbod_restore_probe`, xác nhận vector 0.8.7 và Alembic 0001, rồi xóa DB kiểm tra. Mục tiêu khoảng cách backup lý thuyết khoảng 24 giờ nếu timer luôn thành công; chưa có RPO/RTO cam kết hoặc failover tự động.

Nếu mất App: lấy canonical deploy tree, khôi phục quyền SSH/Tailscale, cấp lại TLS theo TLS.md, nhận secrets qua kênh quản trị, lấy digest hợp lệ từ lịch sử/registry và dựng lại app. Image không chứa model weights; model phải phục hồi/tải riêng.
Nếu mất Infra: khôi phục cluster/roles/secrets và dump từ nguồn ngoài máy, MinIO objects và các dữ liệu cần giữ. **Hiện thiếu bản sao ngoài máy nên chưa có quy trình DR khả thi cho mất toàn bộ Infra**; phải xử lý khoảng trống này trước khi lưu dữ liệu người dùng quan trọng.

## 12. Disk, model và bảo trì định kỳ

Model cache là bind mount bền; HF_HOME và SENTENCE_TRANSFORMERS_HOME trỏ `/models`. Không có model, GPU hoặc inference engine được triển khai. Không nhét weights vào Git/image/release. Chọn CPU model theo RAM thực tế; model nhỏ trên disk vẫn có thể vượt RAM lúc load.

Deploy chặn cache trên 8 GiB và disk trống dưới 3 GiB; đây là check lúc deploy, không phải quota filesystem hoặc cảnh báo sớm. Container log json-file giới hạn 10 MB × 3 file/container; chưa ship sang hệ thống tập trung. Backup/dữ liệu object tăng vẫn có thể lấp disk.

```bash
sudo docker system df
sudo du -sh /var/lib/jobbod/* /var/backups/jobbod
sudo docker stats --no-stream
```

Chỉ dọn image/revision model đã xác nhận không dùng. Không xóa current/rollback digest, không prune toàn bộ Docker volume. Chưa có workflow dọn GHCR; registry vẫn tích lũy phiên bản dù server đã dọn. Cần theo dõi disk, RAM/OOM, backup fail, cert expiry và HTTP errors; hiện chưa cài dashboard/alerting tập trung.

## 13. Tra cứu sự cố

| Dấu hiệu | Kiểm tra đầu tiên / hướng xử lý |
|---|---|
| devops chạy docker ps bị permission denied | Dùng sudo docker ps; không chmod 666 docker.sock |
| SSH Infra public timeout | Tailscale online, đúng private IP, tailnet/firewall và host key alias |
| Cloudflare 521/522 | App/nginx có chạy, cổng 443/listener/firewall và DNS origin đúng |
| Cloudflare 525/526 | Certificate chain/SAN/hạn, nginx -t, Full (strict); không hạ Flexible để che lỗi |
| 502/504 | Container upstream healthy, logs, RAM/OOM, mạng Docker; resolver Nginx dùng Docker DNS |
| Backend readiness 503 | DB/Redis/S3 qua Tailscale, ACL/auth, bucket, secrets có đồng bộ |
| CORS lỗi | Origin đúng https://jobbod.net; preflight và header; không bật '*' cùng credentials |
| CI SSH timeout | Kiểm tra SSH từ operator, trạng thái server/runner; rerun hiện chạy lại cả job |
| CI migration fail | Không retry mù; đọc logs, lock/quyền/schema/revision; backend cũ thường được giữ |
| CI rollback fail | So container thực tế với releases.env; xác nhận digest, dependency và DB tương thích |
| Deploy bị ngắt giữa chừng | Kiểm tra container/digest/state trước khi rerun; chưa có phục hồi interruption đầy đủ |
| Certbot renew fail | Timer/journal, DNS, HTTP/HTTPS challenge có bị WAF/cache/redirect chặn |
| Nginx sửa file nhưng không đổi | Kiểm tra bind mount inode; recreate Nginx sau kiểm tra syntax |
| Backup timer enabled nhưng không có dump mới | Kiểm tra service exit/log và dung lượng; enabled không có nghĩa backup thành công |
| Redis dữ liệu bị evict | maxmemory/allkeys-lru: hiện Redis là cache, chưa phải durable job queue |

## 14. Checklist tiếp nhận và việc còn lại

- [ ] Người nhận có SSH key riêng, sudo bằng tài khoản quản trị, quyền tailnet, GitHub, Cloudflare và console VPS cứu hộ.
- [ ] Đã thử SSH App/Infra, cập nhật whitelist operator nếu đổi IP Tailscale; chưa thu hồi key cũ trước khi thử key mới.
- [ ] Đã xem canonical config, image state, container health, logs và lịch sử CI; không coi bootstrap copy là source mới nhất.
- [ ] Xác nhận DNS/TLS, tự chạy renewal dry-run trong cửa sổ phù hợp; bổ sung email và cảnh báo expiry.
- [ ] Thiết lập backup DB/MinIO/secrets mã hóa ngoài Infra; thử phục hồi và thống nhất RPO/RTO.
- [ ] Chốt owner/on-call thực tế, kênh báo sự cố, lịch rotation và bảo trì; tài liệu không tự gán SLA hoặc người chịu trách nhiệm chưa được xác nhận.
- [ ] Lập kế hoạch giới hạn web origin chỉ nhận Cloudflare hoặc authenticated origin pulls; không chặn SSH runner hay ACME ngoài ý muốn.
- [ ] Quyết định duy trì MinIO archive/fork hoặc sản phẩm thay thế, có kế hoạch security update rõ ràng.
- [ ] Ưu tiên CI/CD theo mục 7; phân biệt đề xuất với tính năng đã có.
- [ ] Trước khi có dữ liệu/thanh toán thật: bổ sung nghiệp vụ/auth, staging, monitoring và DR; skeleton hiện không đồng nghĩa sản phẩm production đã hoàn thiện.

## 15. Bằng chứng và giới hạn kiểm tra

Ngày soạn lại tài liệu: public frontend HTTP 200 qua HTTPS, hello API trả đúng; Docker/Tailscale active; App certbot.timer enabled; Infra backup.timer enabled; backend CI run [42964207555](https://github.com/hieu1020pk-web/jobbod-/actions/runs/42964207555) attempt 4 success. Kiểm tra read-only, không thay server hay mở lại sudo trong tác vụ bàn giao.

Các kiểm thử đã thực thi trong đợt dựng hệ thống: unit backend/AI, bộ rules agent, Docker/Next build, integration DB/vector/Redis/S3 và quyền bị từ chối, persistence sau recreate, restore DB riêng, rotation runtime, migration lỗi giữ backend cũ, image AI lỗi rollback thành công, deploy đồng thời/idempotency, TLS và renewal hook. Chi tiết và links ở VERIFICATION.md, TLS.md. Không chạy lại toàn bộ test suite hoặc restore/rotation chỉ để viết tài liệu.

Thông số runtime chi tiết và image digest lấy từ file cấu hình/state thực tế, không sao chép secrets vào bàn giao. Người nhận phải đối chiếu lại nếu server/repo đã đổi sau ngày chốt này.
