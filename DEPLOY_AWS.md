# Deploy to the Sparkathon AWS account (us-east-1, private, VPN-only)

Exact CLI to launch the demo on a single EC2 instance. All resources are tagged
`Owner=<your name>`, live in **us-east-1**, and have **no public IP** — you reach the app
over **FortiClient VPN** at the instance's private IP. Bedrock access comes from the
instance IAM role (no static keys).

> Prereqs: AWS CLI authenticated to the Sparkathon account via the Azure/AWS SAML SSO,
> and **Bedrock model access enabled** in us-east-1 for the model in `BEDROCK_MODEL_ID`
> (default `us.anthropic.claude-sonnet-4-5-20250929-v1:0`). Enable it in the Bedrock
> console → *Model access* if it isn't already.
>
> **DynamoDB:** the EC2 bootstrap runs `seed_ddb.py`, which **creates and seeds** the
> `dev-sparkathon-sem-rca-forecast` table with synthetic KPI history (idempotent, `Owner`-tagged).
> The app reads actuals from it and writes forecasts back; if DDB is unreachable it falls
> back to the same synthetic values in-memory. No manual DynamoDB step is required — the
> IAM policy in step 1 grants the needed permissions. (To change the tag owner/table name,
> edit the `OWNER` / `DDB_TABLE` exports in `deploy/user_data.sh`.)

## 0. Set variables (fill these in)

```bash
export AWS_DEFAULT_REGION=us-east-1
export OWNER="Swapnil Nile"                 # your name — REQUIRED tag
export VPC_ID=vpc-xxxxxxxx                   # a VPC reachable over the VPN
export SUBNET_ID=subnet-xxxxxxxx             # a PRIVATE subnet in that VPC (with NAT egress)
export VPN_CIDR=10.0.0.0/8                   # CIDR the VPN hands out / the VPC CIDR
export KEY_NAME=your-keypair                 # optional; for SSH via VPN. omit --key-name if none
export TAGS="ResourceType=instance,Tags=[{Key=Owner,Value=\"$OWNER\"}]"
```

## 1. IAM role + instance profile (grants Bedrock invoke)

```bash
cat > /tmp/trust.json <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
"Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
JSON

aws iam create-role --role-name sparkathon-kpi-role \
  --assume-role-policy-document file:///tmp/trust.json \
  --tags Key=Owner,Value="$OWNER"

cat > /tmp/policy.json <<'JSON'
{"Version":"2012-10-17","Statement":[
  {"Effect":"Allow",
   "Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream","bedrock:Converse","bedrock:ConverseStream"],
   "Resource":"*"},
  {"Effect":"Allow",
   "Action":["dynamodb:CreateTable","dynamodb:DescribeTable","dynamodb:TagResource",
             "dynamodb:PutItem","dynamodb:BatchWriteItem","dynamodb:Query","dynamodb:GetItem"],
   "Resource":"*"}
]}
JSON

aws iam put-role-policy --role-name sparkathon-kpi-role \
  --policy-name kpi-demo --policy-document file:///tmp/policy.json

aws iam create-instance-profile --instance-profile-name sparkathon-kpi-profile
aws iam add-role-to-instance-profile \
  --instance-profile-name sparkathon-kpi-profile --role-name sparkathon-kpi-role
```

> If the account restricts IAM `create-role`, ask the account admin for a pre-made
> instance profile with Bedrock invoke, and skip to step 2 using its name.

## 2. Security group — allow Streamlit (8501) from the VPN only

```bash
SG_ID=$(aws ec2 create-security-group \
  --group-name sparkathon-kpi-sg --description "KPI demo 8501 from VPN" \
  --vpc-id "$VPC_ID" --query GroupId --output text \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Owner,Value=\"$OWNER\"}]")

aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
  --protocol tcp --port 8501 --cidr "$VPN_CIDR"
# optional SSH over VPN:
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
  --protocol tcp --port 22 --cidr "$VPN_CIDR"
echo "SG_ID=$SG_ID"
```

## 3. Latest Amazon Linux 2023 AMI

```bash
AMI_ID=$(aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameter.Value' --output text)
echo "AMI_ID=$AMI_ID"
```

## 4. Launch the instance (no public IP, Owner-tagged, user-data bootstrap)

```bash
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" --instance-type t3.small \
  --subnet-id "$SUBNET_ID" --security-group-ids "$SG_ID" \
  --no-associate-public-ip-address \
  --iam-instance-profile Name=sparkathon-kpi-profile \
  ${KEY_NAME:+--key-name "$KEY_NAME"} \
  --user-data file://deploy/user_data.sh \
  --tag-specifications "$TAGS" \
  --query 'Instances[0].InstanceId' --output text)
echo "INSTANCE_ID=$INSTANCE_ID"
```

## 5. Get the private IP and open the app

```bash
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
PRIVATE_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
echo "Open (on VPN):  http://$PRIVATE_IP:8501"
```

Bootstrap (git clone + pip install + service start) takes ~2–3 minutes after the instance
is running. Then, connected to FortiClient VPN, open `http://<PRIVATE_IP>:8501`.

## 6. Submission

Put on the Sparkathon submission page:
- Repo: https://github.com/swapnilnile22/sparkathon-proactive-kpi-intelligence
- Live app: `http://<PRIVATE_IP>:8501` (note: requires Sparkathon VPN)

## Troubleshooting

- **App not up after 3 min:** SSH in over VPN and check `journalctl -u streamlit -n 50`.
- **Investigation shows "Demo brief" not "Live Bedrock agent":** model access isn't enabled
  for `BEDROCK_MODEL_ID` in us-east-1, or the role lacks Bedrock permissions. Enable model
  access / fix the policy; the app still works (it falls back automatically).
- **git clone fails in bootstrap:** the subnet has no outbound egress — use a subnet with a
  NAT gateway, or bake the code into a custom AMI.
- **DynamoDB not seeded / app uses fallback data:** check `journalctl -u streamlit` and re-run
  `sudo DDB_TABLE=dev-sparkathon-sem-rca-forecast OWNER="Swapnil Nile" python3.11 /opt/app/seed_ddb.py`.
  The demo still works on the synthetic fallback if the table is missing. Inspect rows with
  `aws dynamodb scan --table-name dev-sparkathon-sem-rca-forecast --max-items 10`.

## Teardown (account is short-lived, but to be tidy)

```bash
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-terminated --instance-ids "$INSTANCE_ID"
aws ec2 delete-security-group --group-id "$SG_ID"
```
