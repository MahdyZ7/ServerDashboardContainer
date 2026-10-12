# Server pages

Every monitored server has its own page on the dashboard:

    http://ksrc7.kunet.ae/server/<name>

`<name>` can be the display name (`KSRC2`), the hostname (`ksrc2.kunet.ae`), the
short hostname (`ksrc2`) or the IP from `.env` (`SERVER{n}_NAME/_HOST/_IP`). The page
shows, from the latest collection (every 15 minutes):

- CPU cores and memory free for new work
- whether each required mount is mounted (`REQUIRED_MOUNTS`, default `KSRC_lab_share`)
- VNC desktops: owner, display, whether a viewer is connected and from where, and
  which users run more than one desktop
- SSH logins: terminal, source, last keyboard input (active = input in the last
  30 minutes), plus terminal-less connections (VS Code, sftp, tunnels)
- the accounts using the most CPU and memory

A tab strip links all servers; "All servers" goes back to the fleet dashboard.
On the fleet dashboard (`http://ksrc7.kunet.ae/`), the "Servers" menu at the right
end of the section tabs lists every server page.

## Opening a server's page from its own hostname

The dashboard runs on KSRC7, whose port 80 serves the fleet dashboard. For every
other server, make its port 80 redirect to its page.

With Apache httpd (RHEL 6 and 9), the same file works on every server, because the dashboard accepts
the hostname the browser used:

```apache
# /etc/httpd/conf.d/ksrc-status.conf
RewriteEngine On
RewriteRule ^/?$ http://ksrc7.kunet.ae/server/%{SERVER_NAME} [R=302,L]
```

`%{SERVER_NAME}` is the name the browser asked for (`UseCanonicalName Off`, the
default), so `http://ksrc2.kunet.ae/` lands on `/server/ksrc2.kunet.ae`. To pin one
server instead, use `RedirectMatch 302 ^/$ http://ksrc7.kunet.ae/server/KSRC2`.

Then enable it and open the port:

```bash
# RHEL 9
sudo dnf install -y httpd && sudo systemctl enable --now httpd
sudo firewall-cmd --permanent --add-service=http && sudo firewall-cmd --reload
# RHEL 6
sudo yum install -y httpd && sudo chkconfig httpd on && sudo service httpd start
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT && sudo service iptables save
```

Check: `curl -sI http://ksrc2.kunet.ae/ | grep -i location`.

## How sessions are detected (no root needed)

`mini_monitering.sh` collects them with the other host metrics:

- **SSH with a terminal**: `who -u` entries from a remote host; idle time is the
  terminal's last access time (as `w` reports it). tmux panes and terminals inside
  a VNC desktop (`:1`) are skipped.
- **SSH without a terminal**: `sshd: user@notty` processes. The collector's own
  connection is excluded.
- **VNC**: one `Xvnc` process per desktop; its port is `-rfbport` or 5900 + display.
  A viewer is connected when that port has an established TCP connection in
  `/proc/net/tcp`. `127.0.0.1` means the viewer comes through an SSH tunnel.
- **Mounts**: read from `/proc/mounts` (cannot hang), then `stat -f` with a 10 s
  kill timeout; a mount that does not answer is reported as not responding.
