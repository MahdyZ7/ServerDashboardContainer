# SSH key authentication

**Status:** supported by the collector; not yet rolled out (every server still uses a password)
**Replaces:** `SERVER{n}_PASSWORD` + `sshpass`

## Why

| Problem with passwords | With keys |
|---|---|
| `.env` holds every server's password in plain text | `.env` holds only key file paths |
| A leaked `.env` (or a password pasted into a doc) opens every server | A key can be limited to one unprivileged account and revoked on that server alone |
| Monitoring runs as `root` on several servers | A dedicated `monitoring` account is enough for most figures |

## What is already in place

- `srcs/DataCollection/BashGetInfo.sh` uses `SSH_KEY_FILE` when set (`ssh -i … -o BatchMode=yes`),
  otherwise `SSHPASS` with `sshpass -e`. Credentials travel in the environment, never on the
  command line or in logs.
- `srcs/DataCollection/backend.py` reads `SERVER{n}_KEY_FILE`; when it is set the password is ignored.
- `keys/` is in `.gitignore`.

## What is left

1. Mount the keys into the collector, read-only, in `docker-compose.yml`:
   ```yaml
   datacollection:
     volumes:
       - ./srcs/DataCollection:/app
       - ./keys:/keys:ro
   ```
2. Migrate servers one at a time (below). Keep `SERVER{n}_PASSWORD` until the key works.
3. When no server uses a password, remove `sshpass` from `srcs/DataCollection/Dockerfile` and
   delete every `SERVER{n}_PASSWORD` line from `.env`.

## Migrating one server

On the dashboard host (KSRC7):

```bash
mkdir -p keys && chmod 700 keys
ssh-keygen -t rsa -b 4096 -N "" -C "dashboard-monitoring" -f keys/ksrc2_monitoring
chmod 600 keys/ksrc2_monitoring
```

RSA is used because RHEL 6 (OpenSSH 5.3) has no ed25519.

On the monitored server, create an account for monitoring and authorise the key:

```bash
sudo useradd -m -s /bin/bash monitoring
sudo passwd -l monitoring                      # key-only
sudo -u monitoring mkdir -p -m 700 ~monitoring/.ssh
echo 'no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty <contents of ksrc2_monitoring.pub>' |
    sudo -u monitoring tee -a ~monitoring/.ssh/authorized_keys
sudo chmod 600 ~monitoring/.ssh/authorized_keys
```

Do **not** add `command="bash -s"` to the key: the collector runs `bash -s -- <arguments>`
(for example `--kv --services … --mounts …`), and a forced command drops the arguments, so
the scripts would print the wrong format and every collection would fail to parse.

What a non-root account can and cannot see:

| Figure | As `monitoring` |
|---|---|
| Host metrics, mounts, sessions (SSH idle, VNC viewers) | Complete |
| Per-user CPU and memory | Complete |
| Per-user I/O (`/proc/<pid>/io`) | Unknown for other users' processes (shown as unknown, not zero) |
| Nightly home / `/eda_work` disk scans | Only directories the account can read; the rest is unknown |

Test from the dashboard host before changing `.env`:

```bash
ssh -i keys/ksrc2_monitoring -o BatchMode=yes -o HostKeyAlgorithms=+ssh-rsa \
    -o PubkeyAcceptedKeyTypes=+ssh-rsa monitoring@10.10.19.74 'bash -s -- --kv' \
    < srcs/DataCollection/mini_monitering.sh | head -3
```

Expected: `format_version=2` followed by metric lines. Then in `.env`:

```env
SERVER2_USERNAME=monitoring
SERVER2_KEY_FILE=/keys/ksrc2_monitoring
```

```bash
make restart-service SERVICE=datacollection
make collect-once && make logs-DataCollection-tail
```

| Symptom | Fix |
|---|---|
| `Permission denied (publickey)` | `authorized_keys` must be `600`, `.ssh` `700`, and the key on one line |
| `authentication failed` in the collector log | `SERVER{n}_KEY_FILE` must be the path inside the container (`/keys/...`) |
| `Host key verification failed` | The server's host key changed; check before removing the old entry |

## Revoking access

Remove the line from `~monitoring/.ssh/authorized_keys` on the server. Collection from that
server stops at the next run.
