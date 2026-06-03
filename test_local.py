"""
test_local.py — Test the chatbot locally WITHOUT deploying to AWS.

Usage:
  export ANTHROPIC_API_KEY="sk-ant-..."
  python test_local.py
"""

import json
import os
import sys

# Stub out AWS calls so we can run locally
import unittest.mock as mock

# Patch boto3 before importing handler
mock_table = mock.MagicMock()
mock_table.put_item = mock.MagicMock()
mock_dynamodb = mock.MagicMock()
mock_dynamodb.Table.return_value = mock_table
mock_sns = mock.MagicMock()
mock_sns.publish = mock.MagicMock()

os.environ.setdefault("ORDERS_TABLE",      "ecommerce-orders")
os.environ.setdefault("SNS_TOPIC_ARN",     "arn:aws:sns:us-east-1:000000000000:test")
os.environ.setdefault("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))

with mock.patch("boto3.resource", return_value=mock_dynamodb), \
     mock.patch("boto3.client",   return_value=mock_sns):
    from chatbot_lambda.handler import lambda_handler   # noqa: E402

if not os.environ["ANTHROPIC_API_KEY"]:
    print("❌  Set ANTHROPIC_API_KEY first:  export ANTHROPIC_API_KEY='sk-ant-...'")
    sys.exit(1)


def chat(message: str, history: list) -> dict:
    event = {"body": json.dumps({"message": message, "history": history})}
    result = lambda_handler(event, None)
    return json.loads(result["body"])


def main():
    print("🛒  E-Commerce Chatbot — Local Test")
    print("Type 'quit' to exit\n")
    history = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue
        response = chat(user_input, history)
        reply = response.get("reply", "")
        history = response.get("history", history)
        order = response.get("order_result")
        print(f"\nBot: {reply}")
        if order:
            if order.get("success"):
                print(f"  ✅ Order placed! ID: {order['order_id']}  Total: ${order['total']:.2f}")
            else:
                print(f"  ❌ Order failed: {order.get('error')}")
        print()


if __name__ == "__main__":
    main()
