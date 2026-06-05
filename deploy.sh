#!/bin/bash
# ─────────────────────────────────────────────────────────────
# deploy.sh  —  Build Lambda package and deploy via Terraform
# Run this from the project root folder:  bash deploy.sh
# ─────────────────────────────────────────────────────────────
set -e

echo "🔧 Step 1: Installing Python dependencies into lambda_package/ ..."
rm -rf lambda_package venv_deploy
mkdir lambda_package
pip install -r chatbot_lambda/requirements.txt \
  -t lambda_package/ \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --quiet
cp chatbot_lambda/handler.py lambda_package/

echo "🏗️  Step 2: Running Terraform ..."
cd terraform
terraform init -input=false
terraform apply -input=false -auto-approve \
  -var="anthropic_api_key=$ANTHROPIC_API_KEY" \
  -var="admin_email=$ADMIN_EMAIL" \
  -var="sender_email=$SENDER_EMAIL"

echo ""
echo "✅ Deployment complete! Your API endpoint is shown above as 'api_endpoint'."
