# Pixi — LLM-Powered E-Commerce Chatbot

A serverless e-commerce chatbot that lets users browse products and place orders through natural conversation. Built with the Claude API on a fully serverless AWS backend.

## What it does

- Understands natural language queries like "show me something under $50" or "I want to order the blue hoodie"
- Handles a 55-product catalogue across categories (electronics, fitness, clothing, kitchen, etc.)
- Places orders autonomously — writes to DynamoDB and fires an email notification via SNS
- Maintains conversation history across multiple turns

## Tech stack

- **Claude API** — conversational AI and order intent detection
- **AWS Lambda** — serverless compute, only runs when a message is sent
- **API Gateway** — HTTP endpoint that the frontend talks to
- **DynamoDB** — stores every order with customer details and timestamp
- **SNS** — triggers email notifications to the admin on each order
- **Terraform** — all infrastructure defined as code, one command to deploy or tear down

## Architecture

```
User → pixi.html → API Gateway → Lambda → Claude API
                                    ↓
                               DynamoDB (orders)
                                    ↓
                               SNS → Email notification
```

## Project structure

```
├── chatbot_lambda/
│   ├── handler.py        # Lambda function — chat logic, order placement
│   └── requirements.txt
├── terraform/
│   └── main.tf           # All AWS infrastructure
├── pixi.html             # Frontend chat UI
├── deploy.sh             # Build and deploy script
└── test_local.py         # Local testing without AWS
```

## Running locally

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pip install anthropic boto3
python test_local.py
```

## Deploying to AWS

You'll need the AWS CLI configured and Terraform installed.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export ADMIN_EMAIL="you@email.com"
bash deploy.sh
```

Terraform will output the API Gateway URL. Paste that into `pixi.html` and it's live.

## Tearing down

```bash
cd terraform
terraform destroy -var="anthropic_api_key=$ANTHROPIC_API_KEY" -var="admin_email=$ADMIN_EMAIL"
```
