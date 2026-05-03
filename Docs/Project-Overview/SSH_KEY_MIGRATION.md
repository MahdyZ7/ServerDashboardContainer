# SSH Key-Based Auth Migration Plan

**Status:** Planned — not yet implemented
**Replaces:** `sshpass` + `SERVER{n}_PASSWORD` in `.env`
**Goal:** Remove password exposure from admin; allow users to self-register without sharing credentials

---

## Why Migrate

| Problem | Current state |
|---|---|
| Admin holds every user's password | All passwords in `.env` |
| `.env` leak = all servers compromised | Single file, plaintext |
| Adding a server = sharing password with admin | No alternative |
| `sshpass` is a security anti-pattern | Flagged by audits |

With SSH key auth: the admin never sees a password. Users control their own access and can revoke it themselves at any time.

---

## Files to Change

### 1. `srcs/DataCollection/BashGetInfo.sh`
Replace `sshpass -p "$3"` with `ssh -i "$3"`. The third argument changes from a password string to a key file path.

```bash
# REMOVE:
sshpass -p "$3" ssh -o "StrictHostKeyChecking accept-new" \
  -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedKeyTypes=+ssh-rsa \
  "$2"@"$1" "bash -s" < "$4" -- "${@:5}"

# REPLACE WITH:
ssh -i "$3" \
  -o StrictHostKeyChecking=accept-new \
  -o BatchMode=yes \
  -o ConnectTimeout=10 \
  -oHostKeyAlgorithms=+ssh-rsa \
  -oPubkeyAcceptedKeyTypes=+ssh-rsa \
  "$2"@"$1" "bash -s" < "$4" -- "${@:5}"
```

`BatchMode=yes` makes SSH fail immediately if key auth fails instead of prompting for a password.

---

### 2. `srcs/DataCollection/backend.py`

**`readServerList()`** — replace `password` with `key_file`:
```python
# REMOVE:
"password": os.getenv(f"SERVER{i}_PASSWORD"),
# ADD:
"key_file": os.getenv(f"SERVER{i}_KEY_FILE"),
```

**`run_monitoring_script()` and `get_top_users()`** — replace `server["password"]` with `server["key_file"]` in both `command_string` lists.

Optionally add startup validation:
```python
import stat
key = server.get("key_file")
if not key or not os.path.exists(key):
    logger.error(f"Key file missing for {server['name']}: {key}")
    raise FileNotFoundError(f"Key file not found: {key}")
file_mode = oct(stat.S_IMODE(os.stat(key).st_mode))
if file_mode != '0o600':
    logger.warning(f"Key file {key} has insecure permissions {file_mode} — SSH may reject it")
```

---

### 3. `docker-compose.yml`

Add a read-only `keys/` volume mount to the `datacollection` service:
```yaml
datacollection:
  volumes:
    - ./srcs/DataCollection:/app
    - ./keys:/keys:ro          # ← add this line
```

---

### 4. `srcs/DataCollection/Dockerfile`

Remove `sshpass` — it is no longer needed:
```dockerfile
# REMOVE this line from apt-get install:
    sshpass \
```

---

### 5. `.env`

Replace `SERVER{n}_PASSWORD` with `SERVER{n}_KEY_FILE` for each server:
```env
# BEFORE:
SERVER1_USERNAME=root
SERVER1_PASSWORD="tolba#1970"

# AFTER:
SERVER1_USERNAME=monitoring
SERVER1_KEY_FILE=/keys/ksrc1_monitoring_key
```

---

### 6. `.gitignore`

Add the keys directory so private keys are never committed:
```
keys/
```

---

### 7. New: `keys/` directory (at project root, not in git)

```
keys/
    ksrc1_monitoring_key        # RSA 4096 private key for KSRC1
    ksrc2_monitoring_key        # RSA 4096 private key for KSRC2
    ksrc3_monitoring_key        # ... etc
```

```bash
mkdir -p keys
chmod 700 keys
chmod 600 keys/*
```

---

### 8. `CLAUDE.md`

Update the "Environment Variables" section to document `SERVER{n}_KEY_FILE` replacing `SERVER{n}_PASSWORD`, and note the `keys/` directory convention.

---

### 9. `Docs/INDEX.md`

Add an entry for this document under Project Overview.

---

## Migration Sequence for Existing Servers

The 9 current servers all use password auth. Migrate each one without downtime:

```
For each server (can do in batches):
1. Generate RSA key pair locally
2. SSH in once with the existing password to add the public key
3. Test key auth works before changing anything in the codebase
4. Move private key into keys/ with correct permissions
5. Update .env — add KEY_FILE line, keep PASSWORD line for now
```

Once all servers are tested:
```
6. Update all 4 files listed above
7. make rebuild-service SERVICE=datacollection
8. make collect-once && make logs-DataCollection-tail
9. Confirm data flows correctly
10. Remove all SERVER{n}_PASSWORD lines from .env
```

---

## Verification

```bash
# 1. Rebuild container (sshpass removed from image)
make rebuild-service SERVICE=datacollection

# 2. Confirm sshpass is gone
docker exec DataCollection which sshpass   # should return nothing

# 3. Run a single collection cycle
make collect-once

# 4. Check logs for success
make logs-DataCollection-tail

# 5. Confirm key permissions inside container
docker exec DataCollection ls -la /keys/

# 6. Check database received new data
make db-stats
```

---

## User Tutorial: Adding a New Server with SSH Key Auth

This section is for server owners who want to register their machine with the monitoring system.

### Overview

You generate a key pair on your own machine. Your private key never leaves your control. You give the admin only your public key and server details. The admin cannot log in as you interactively — the key is restricted to run only the monitoring scripts.

---

### Step 1 — Generate a dedicated monitoring key pair

Run this **on your own machine** (or on the server itself):

```bash
ssh-keygen -t rsa -b 4096 \
  -f ~/.ssh/monitoring_key \
  -N "" \
  -C "monitoring-$(hostname)-$(date +%Y)"
```

This creates:
- `~/.ssh/monitoring_key` — **private key** (never share this)
- `~/.ssh/monitoring_key.pub` — **public key** (safe to share)

> **RHEL 6 compatibility:** RSA 4096 is used instead of ed25519 because RHEL 6 ships OpenSSH 5.3, which does not support ed25519. RSA 4096 works on all RHEL versions.

---

### Step 2 — Create a dedicated monitoring user (recommended)

Run this **on the server being monitored**. Using a dedicated non-privileged user is better than monitoring under a personal account:

```bash
sudo useradd -m -s /bin/bash monitoring
sudo passwd -l monitoring          # lock password — key-only access
```

If you prefer to use your existing user account, skip this step.

---

### Step 3 — Authorize the key on the server

Log into the server as the user that will run monitoring (either `monitoring` or your own account), then:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Append the public key with command restriction
# Replace PASTE_PUBLIC_KEY_HERE with the full contents of monitoring_key.pub
echo 'command="bash -s",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty PASTE_PUBLIC_KEY_HERE' \
  >> ~/.ssh/authorized_keys

chmod 600 ~/.ssh/authorized_keys
```

To get your public key:
```bash
cat ~/.ssh/monitoring_key.pub
```

> **What `command="bash -s"` does:** This key can **only** run bash scripts piped to it via SSH. It cannot open an interactive shell, forward ports, or do anything else. Even if someone stole this private key, they could only run monitoring scripts on your server.

> **RHEL 6:** The `authorized_keys` restriction syntax is fully supported on OpenSSH 5.3.

---

### Step 4 — Verify sshd allows public key auth

On RHEL 6/7, confirm the SSH daemon is configured correctly:

```bash
grep -E "PubkeyAuthentication|AuthorizedKeysFile" /etc/ssh/sshd_config
```

Expected output:
```
PubkeyAuthentication yes
AuthorizedKeysFile     .ssh/authorized_keys
```

If `PubkeyAuthentication` is `no` or missing, edit `/etc/ssh/sshd_config` and restart sshd:
```bash
sudo sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo service sshd restart    # RHEL 6
# or
sudo systemctl restart sshd  # RHEL 7+
```

---

### Step 5 — Test key auth works

From the machine where the private key lives:

```bash
ssh -i ~/.ssh/monitoring_key \
    -o BatchMode=yes \
    -oHostKeyAlgorithms=+ssh-rsa \
    -oPubkeyAcceptedKeyTypes=+ssh-rsa \
    monitoring@YOUR_SERVER_IP \
    "bash -s" <<< "echo hello"
```

Expected output: `hello`

**Troubleshooting if it fails:**

| Symptom | Fix |
|---|---|
| `Permission denied (publickey)` | Check `authorized_keys` permissions (`chmod 600`) and that the key was pasted as a single line |
| `Host key verification failed` | Add `-o StrictHostKeyChecking=accept-new` to accept the host key on first connect |
| `ssh_exchange_identification` | RHEL 6 — add `-oHostKeyAlgorithms=+ssh-rsa` flag |
| `Bad permissions` on key file | `chmod 600 ~/.ssh/monitoring_key` |

---

### Step 6 — Send the admin what they need

Email or message the admin **only these three things**:

1. Your server's IP address
2. The username the key is authorized for (e.g. `monitoring`)
3. The contents of `~/.ssh/monitoring_key.pub`

**Do not send the private key** (`monitoring_key` without `.pub`).

---

### Step 7 — What the admin does

The admin saves the private key to the `keys/` directory and adds to `.env`:

```env
SERVER_N_NAME=your-server-name
SERVER_N_HOST=your.server.hostname
SERVER_N_IP=10.x.x.x
SERVER_N_USERNAME=monitoring
SERVER_N_KEY_FILE=/keys/your-server-name_monitoring_key
```

Then:
```bash
chmod 600 keys/your-server-name_monitoring_key
make restart-service SERVICE=datacollection
make collect-once   # verify it works
```

---

### Revoking access

To remove monitoring access at any time, remove your key from `~/.ssh/authorized_keys` on your server. No need to contact the admin — access stops immediately on the next collection cycle. The admin cannot re-add access without a new public key from you.

---

**Last Updated:** 2026-02-18
**Related:** `srcs/DataCollection/BashGetInfo.sh`, `srcs/DataCollection/backend.py`, `docker-compose.yml`
