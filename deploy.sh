#!/bin/bash
# ─────────────────────────────────────────────────────────────
# deploy.sh  —  Build Lambda package and deploy via Terraform
# Run this from the project root folder:  bash deploy.sh
# ─────────────────────────────────────────────────────────────
set -e

echo "🔧 Step 1: Installing Python dependencies into lambda_package/ ..."
rm -rf lambda_package venv_deploy
mkdir lambda_package
python3 -m venv venv_deploy
source venv_deploy/bin/activate
pip install -r chatbot_lambda/requirements.txt -t lambda_package/ --quiet
deactivate
cp chatbot_lambda/handler.py lambda_package/

echo "🏗️  Step 2: Running Terraform ..."
cd terraform
terraform init -input=false
terraform apply -input=false -auto-approve \
  -var="anthropic_api_key=$ANTHROPIC_API_KEY" \
  -var="admin_email=$ADMIN_EMAIL"

echo ""
echo "✅ Deployment complete! Your API endpoint is shown above as 'api_endpoint'."
