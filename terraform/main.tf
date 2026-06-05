###############################################################################
# LLM-Powered E-Commerce Chatbot — Terraform Infrastructure
###############################################################################

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

###############################################################################
# Variables
###############################################################################

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "anthropic_api_key" {
  description = "Anthropic API key (stored as a secret, never in state)"
  type        = string
  sensitive   = true
}

variable "admin_email" {
  description = "Admin email to receive order notifications"
  type        = string
}

variable "sender_email" {
  description = "Verified SES email address used to send order confirmations to customers"
  type        = string
}

###############################################################################
# DynamoDB — Orders Table
###############################################################################

resource "aws_dynamodb_table" "orders" {
  name         = "ecommerce-orders"
  billing_mode = "PAY_PER_REQUEST"   # no capacity planning needed
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }

  tags = { Project = "ecommerce-chatbot" }
}

###############################################################################
# SNS — Order Notifications Topic
###############################################################################

resource "aws_sns_topic" "order_notifications" {
  name = "ecommerce-order-notifications"
  tags = { Project = "ecommerce-chatbot" }
}

# Subscribe the admin email to the topic
resource "aws_sns_topic_subscription" "admin_email" {
  topic_arn = aws_sns_topic.order_notifications.arn
  protocol  = "email"
  endpoint  = var.admin_email
}

###############################################################################
# IAM — Lambda Execution Role
###############################################################################

resource "aws_iam_role" "lambda_exec" {
  name = "ecommerce-chatbot-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "ecommerce-chatbot-lambda-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # CloudWatch Logs
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # DynamoDB access
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"]
        Resource = aws_dynamodb_table.orders.arn
      },
      {
        # SNS publish
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.order_notifications.arn
      },
      {
        # SES send email
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      }
    ]
  })
}

###############################################################################
# Lambda — Package & Deploy
###############################################################################

# Build the deployment zip from the lambda/ directory
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_package"
  output_path = "${path.module}/lambda_package.zip"
}

resource "aws_lambda_function" "chatbot" {
  function_name    = "ecommerce-chatbot"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      ORDERS_TABLE      = aws_dynamodb_table.orders.name
      SNS_TOPIC_ARN     = aws_sns_topic.order_notifications.arn
      ANTHROPIC_API_KEY = var.anthropic_api_key
      SENDER_EMAIL      = var.sender_email
    }
  }

  tags = { Project = "ecommerce-chatbot" }
}

###############################################################################
# API Gateway — HTTP API (v2, cheaper & simpler than REST API)
###############################################################################

resource "aws_apigatewayv2_api" "chatbot_api" {
  name          = "ecommerce-chatbot-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.chatbot_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.chatbot.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "chat_route" {
  api_id    = aws_apigatewayv2_api.chatbot_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.chatbot_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatbot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.chatbot_api.execution_arn}/*/*"
}

###############################################################################
# Outputs
###############################################################################

output "api_endpoint" {
  description = "Send POST requests to this URL"
  value       = "${aws_apigatewayv2_stage.default.invoke_url}/chat"
}

output "dynamodb_table" {
  value = aws_dynamodb_table.orders.name
}

output "sns_topic_arn" {
  value = aws_sns_topic.order_notifications.arn
}
