#!/bin/bash
# EC2 user-data bootstrap for Amazon Linux 2023.
# Installs the app and runs Streamlit on :8501 via systemd. Bedrock access comes
# from the instance IAM role (no static keys). Assumes the subnet has outbound
# egress (NAT) so git clone + pip install can reach the internet.
set -euxo pipefail

dnf install -y python3.11 python3.11-pip git

cd /opt
git clone https://github.com/swapnilnile22/sparkathon-proactive-kpi-intelligence.git app
cd app
python3.11 -m pip install -r requirements.txt

cat >/etc/systemd/system/streamlit.service <<'UNIT'
[Unit]
Description=Proactive KPI Intelligence (Streamlit)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/app
Environment=AWS_REGION=us-east-1
Environment=BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
ExecStart=/usr/bin/python3.11 -m streamlit run app.py \
  --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
User=root

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now streamlit
