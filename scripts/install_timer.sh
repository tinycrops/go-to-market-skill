#!/usr/bin/env bash
# install_timer.sh <slug> <product-dir> : refresh <dir>/STATS.md every 30 min (systemd user timer on 7a72)
set -euo pipefail
slug=$1; dir=$(realpath "$2"); u=~/.config/systemd/user
mkdir -p "$u"
cat > "$u/$slug-stats.service" <<UNIT
[Unit]
Description=Refresh $slug STATS.md from its Modal event log
[Service]
Type=oneshot
ExecStart=$dir/stats.py
UNIT
cat > "$u/$slug-stats.timer" <<UNIT
[Unit]
Description=Refresh $slug stats every 30 minutes
[Timer]
OnCalendar=*:0/30
Persistent=true
[Install]
WantedBy=timers.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now "$slug-stats.timer"
systemctl --user start "$slug-stats.service"
echo "timer on: $dir/STATS.md"
