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

# Create + seed the DynamoDB KPI table with synthetic actuals (idempotent).
export AWS_REGION=us-east-1
export DDB_TABLE=dev-sparkathon-sem-rca-forecast
export OWNER="Swapnil Nile"
python3.11 seed_ddb.py || echo "seed failed (app falls back to synthetic history)"

cat >/etc/systemd/system/streamlit.service <<'UNIT'
[Unit]
Description=Proactive KPI Intelligence (Streamlit)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/app
Environment=AWS_REGION=us-east-1
Environment=BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
Environment=DDB_TABLE=dev-sparkathon-sem-rca-forecast
ExecStart=/usr/bin/python3.11 -m streamlit run app.py \
  --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
User=root

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now streamlit
