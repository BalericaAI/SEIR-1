#!/bin/bash
set -euo pipefail

#Chewbacca: The node awakens. The ops panel must be beautiful.

sleep 5
apt update -y
apt install -y nginx curl jq

# --- Helpers ---
METADATA="http://metadata.google.internal/computeMetadata/v1"
HDR="Metadata-Flavor: Google"

md() { curl -fsS -H "$HDR" "${METADATA}/$1" || echo "unknown"; }

INSTANCE_NAME="$(md instance/name)"
HOSTNAME="$(hostname)"
PROJECT_ID="$(md project/project-id)"
ZONE_FULL="$(md instance/zone)"            # projects/<id>/zones/us-central1-a
ZONE="${ZONE_FULL##*/}"
REGION="${ZONE%-*}"                        # us-central1
MACHINE_TYPE_FULL="$(md instance/machine-type)"
MACHINE_TYPE="${MACHINE_TYPE_FULL##*/}"

# Network interface 0
INTERNAL_IP="$(md instance/network-interfaces/0/ip)"
EXTERNAL_IP="$(md instance/network-interfaces/0/access-configs/0/external-ip)"
VPC_FULL="$(md instance/network-interfaces/0/network)"       # projects/<id>/global/networks/default
SUBNET_FULL="$(md instance/network-interfaces/0/subnetwork)" # projects/<id>/regions/<r>/subnetworks/default
VPC="${VPC_FULL##*/}"
SUBNET="${SUBNET_FULL##*/}"

UPTIME="$(uptime -p || true)"
LOADAVG="$(cat /proc/loadavg 2>/dev/null | awk '{print $1" "$2" "$3}' || echo "unknown")"

# RAM
MEM_TOTAL_MB="$(free -m | awk '/Mem:/ {print $2}')"
MEM_USED_MB="$(free -m | awk '/Mem:/ {print $3}')"
MEM_FREE_MB="$(free -m | awk '/Mem:/ {print $4}')"

# Disk (root)
DISK_LINE="$(df -h / | tail -n 1)"
DISK_SIZE="$(echo "$DISK_LINE" | awk '{print $2}')"
DISK_USED="$(echo "$DISK_LINE" | awk '{print $3}')"
DISK_AVAIL="$(echo "$DISK_LINE" | awk '{print $4}')"
DISK_USEP="$(echo "$DISK_LINE" | awk '{print $5}')"

START_TIME_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Nginx status
systemctl enable nginx >/dev/null 2>&1 || true
systemctl restart nginx

NGINX_STATE="$(systemctl is-active nginx 2>/dev/null || echo "unknown")"

cat > /var/www/html/index.html <<EOF
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>SEIR-I Cloud Node — Ops Panel</title>
  <style>
    body { background:#0b0c10; color:#c5c6c7; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
    .wrap { max-width: 900px; margin: 40px auto; padding: 24px; }
    h1 { color:#66fcf1; margin:0 0 12px 0; }
    .sub { color:#45a29e; margin-bottom: 24px; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .card { border:1px solid #45a29e; border-radius: 10px; padding: 14px 16px; background: rgba(255,255,255,0.03); }
    .k { color:#66fcf1; }
    .v { color:#ffffff; }
    .footer { margin-top: 18px; color:#45a29e; font-size: 12px; }
    .status-ok { color:#00ff99; }
    .status-bad { color:#ff3366; }
    .big { font-size: 14px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>⚡ SEIR-I Ops Panel — Node Online ⚡</h1>
    <div class="sub">If you can see this, you have deployed infrastructure that serves traffic on port 80.</div>

    <div class="grid">
      <div class="card">
        <div class="k">Identity</div>
        <div class="big"><span class="k">Project:</span> <span class="v">${PROJECT_ID}</span></div>
        <div class="big"><span class="k">Instance:</span> <span class="v">${INSTANCE_NAME}</span></div>
        <div class="big"><span class="k">Hostname:</span> <span class="v">${HOSTNAME}</span></div>
        <div class="big"><span class="k">Machine:</span> <span class="v">${MACHINE_TYPE}</span></div>
      </div>

      <div class="card">
        <div class="k">Location</div>
        <div class="big"><span class="k">Region:</span> <span class="v">${REGION}</span></div>
        <div class="big"><span class="k">Zone:</span> <span class="v">${ZONE}</span></div>
        <div class="big"><span class="k">Startup UTC:</span> <span class="v">${START_TIME_UTC}</span></div>
        <div class="big"><span class="k">Uptime:</span> <span class="v">${UPTIME}</span></div>
      </div>

      <div class="card">
        <div class="k">Network</div>
        <div class="big"><span class="k">VPC:</span> <span class="v">${VPC}</span></div>
        <div class="big"><span class="k">Subnet:</span> <span class="v">${SUBNET}</span></div>
        <div class="big"><span class="k">Internal IP:</span> <span class="v">${INTERNAL_IP}</span></div>
        <div class="big"><span class="k">External IP:</span> <span class="v">${EXTERNAL_IP}</span></div>
      </div>

      <div class="card">
        <div class="k">Health</div>
        <div class="big"><span class="k">Nginx:</span>
          <span class="v ${NGINX_STATE == "active" ? "status-ok" : "status-bad"}">${NGINX_STATE}</span>
        </div>
        <div class="big"><span class="k">Load Avg:</span> <span class="v">${LOADAVG}</span></div>
        <div class="big"><span class="k">RAM (MB):</span> <span class="v">${MEM_USED_MB} used / ${MEM_FREE_MB} free / ${MEM_TOTAL_MB} total</span></div>
        <div class="big"><span class="k">Disk (/):</span> <span class="v">${DISK_USED} used / ${DISK_AVAIL} avail / ${DISK_SIZE} total (${DISK_USEP})</span></div>
      </div>
    </div>

    <div class="footer">
      #Chewbacca: This page is your proof-of-life. In the real world, evidence beats vibes.
    </div>
  </div>
</body>
</html>
EOF

#Chewbacca: Allow the first victory to be visible.
echo "OK: SEIR-I Ops Panel deployed. Visit http://EXTERNAL_IP/"
