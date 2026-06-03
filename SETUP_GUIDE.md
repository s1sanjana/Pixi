# 🛒 E-Commerce Chatbot — Complete Setup Guide

Think of this project like a vending machine connected to the internet.
- **Claude** is the smart brain that understands what you're saying.
- **AWS Lambda** is the machine that runs the code (only when needed, so it's cheap).
- **DynamoDB** is the filing cabinet that stores all orders.
- **SNS** is the notification bell that emails you when an order is placed.
- **Terraform** is the instruction manual that builds all of AWS for you automatically.

---

## ✋ Part 1 — Things Only YOU Can Do (takes ~30 min)

### Step 1: Create a Free AWS Account
AWS (Amazon Web Services) is where your chatbot will live on the internet.

1. Go to **https://aws.amazon.com** and click **"Create an AWS Account"**
2. Enter your email, choose a password, and pick an account name (anything, e.g. "my-chatbot")
3. Enter a credit card — **don't worry, the free tier covers everything in this project** (you'll pay $0 unless you make thousands of orders)
4. Verify your phone number
5. Choose the **Basic (Free)** support plan
6. You're in! Log into the AWS Console.

### Step 2: Create an AWS Access Key (so your laptop can talk to AWS)
This is like creating a password specifically for your terminal.

1. In the AWS Console, click your name in the top-right corner → **"Security credentials"**
2. Scroll down to **"Access keys"** → click **"Create access key"**
3. Choose **"Command Line Interface (CLI)"** → tick the checkbox → **Next** → **Create**
4. You'll see an **Access Key ID** and a **Secret Access Key** — **copy both, you won't see the secret again**
5. Keep these private — treat them like a password

### Step 3: Get an Anthropic API Key (the Claude "brain")
1. Go to **https://console.anthropic.com**
2. Sign up / Log in
3. Click **"API Keys"** in the left sidebar → **"Create Key"**
4. Give it a name like "chatbot-key" → copy the key (starts with `sk-ant-`)
5. Keep this private too

### Step 4: Subscribe to your order notification emails
After you deploy (Step in Part 2), AWS will send you a confirmation email to the address you provide. **You must click the confirmation link in that email** or you won't receive order notifications.

---

## 💻 Part 2 — Install Tools (I'll walk you through each one)

Open your **Terminal** app (search "Terminal" in Spotlight).

### Install Homebrew (Mac's app store for developer tools)
Paste this and press Enter:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Install AWS CLI (lets your laptop talk to AWS)
```bash
brew install awscli
```

Then configure it with your keys from Step 2:
```bash
aws configure
```
It will ask four questions — answer like this:
```
AWS Access Key ID:     → paste your Access Key ID
AWS Secret Access Key: → paste your Secret Access Key
Default region name:   → us-east-1
Default output format: → json
```

### Install Terraform (builds your cloud infrastructure)
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

### Install Python 3.12
```bash
brew install python@3.12
```

---

## 🚀 Part 3 — Deploy the Project

Open Terminal, navigate to the project folder:
```bash
cd ~/Desktop/Claude\ Project/LLM-Powered\ E-Commerce\ Chatbot
```

Set your secret keys as environment variables (replace the values with yours):
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export ADMIN_EMAIL="your@email.com"
```

Run the deploy script:
```bash
bash deploy.sh
```

This will:
1. Install Python libraries into a package folder
2. Zip everything up
3. Upload to AWS and create all the infrastructure automatically

At the end you'll see something like:
```
api_endpoint = "https://abc123.execute-api.us-east-1.amazonaws.com/chat"
```
**That URL is your chatbot!**

---

## 💬 Part 4 — Test It!

### Option A: Test locally first (no AWS needed)
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
python test_local.py
```
Then type things like:
- "What headphones do you have under $100?"
- "I'd like to order the Bluetooth Speaker"

### Option B: Test the live deployed version
```bash
curl -X POST https://YOUR-API-URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me your fitness products", "history": []}'
```

---

## 🧹 Cleaning Up (to avoid any charges)

When you're done with the project, destroy the AWS resources:
```bash
cd terraform
terraform destroy \
  -var="anthropic_api_key=$ANTHROPIC_API_KEY" \
  -var="admin_email=$ADMIN_EMAIL"
```
Type `yes` when prompted. This deletes everything.

---

## 📁 Project File Map

```
LLM-Powered E-Commerce Chatbot/
├── lambda/
│   ├── handler.py          ← The chatbot brain (Python code)
│   └── requirements.txt    ← Python library list
├── terraform/
│   └── main.tf             ← AWS infrastructure blueprint
├── deploy.sh               ← One-click deploy script
├── test_local.py           ← Test without AWS
└── SETUP_GUIDE.md          ← This file
```

---

## ❓ What does each AWS service cost?

| Service       | Free Tier          | Your usage           | Cost    |
|---------------|--------------------|----------------------|---------|
| Lambda        | 1M calls/month     | A few hundred        | **$0**  |
| DynamoDB      | 25 GB storage       | A few KB             | **$0**  |
| SNS           | 1M publishes/month  | One per order        | **$0**  |
| API Gateway   | 1M calls/month     | Testing only         | **$0**  |

You only pay for the Anthropic API usage (~$0.01–0.05 per conversation).
