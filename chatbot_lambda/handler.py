"""
E-Commerce Chatbot — AWS Lambda Handler
Handles conversational product queries and autonomous order placement
using the Claude API, DynamoDB, and SNS.
"""

import json
import os
import uuid
from datetime import datetime

import boto3
import anthropic

# ── AWS clients ────────────────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
ses = boto3.client("ses", region_name="us-east-1")

ORDERS_TABLE      = os.environ["ORDERS_TABLE"]
SNS_TOPIC_ARN     = os.environ["SNS_TOPIC_ARN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SENDER_EMAIL      = os.environ["SENDER_EMAIL"]

# ── Product catalogue (50+ SKUs) ───────────────────────────────────────────────
PRODUCTS = {
    "P001": {"name": "Wireless Noise-Cancelling Headphones", "price": 79.99,  "category": "Electronics", "stock": 45},
    "P002": {"name": "Bluetooth Speaker",                   "price": 34.99,  "category": "Electronics", "stock": 80},
    "P003": {"name": "USB-C Charging Cable (2m)",           "price": 12.99,  "category": "Electronics", "stock": 200},
    "P004": {"name": "Laptop Stand (Aluminium)",            "price": 29.99,  "category": "Electronics", "stock": 60},
    "P005": {"name": "Mechanical Keyboard",                 "price": 59.99,  "category": "Electronics", "stock": 30},
    "P006": {"name": "Ergonomic Mouse",                     "price": 44.99,  "category": "Electronics", "stock": 55},
    "P007": {"name": "27-inch Monitor",                     "price": 249.99, "category": "Electronics", "stock": 20},
    "P008": {"name": "Webcam 1080p",                        "price": 49.99,  "category": "Electronics", "stock": 35},
    "P009": {"name": "Ring Light (10 inch)",                "price": 22.99,  "category": "Electronics", "stock": 70},
    "P010": {"name": "HDMI Cable (3m)",                     "price": 9.99,   "category": "Electronics", "stock": 150},
    "P011": {"name": "Running Shoes – Men's Size 10",       "price": 89.99,  "category": "Footwear",    "stock": 25},
    "P012": {"name": "Running Shoes – Women's Size 7",      "price": 89.99,  "category": "Footwear",    "stock": 25},
    "P013": {"name": "Casual Sneakers – White",             "price": 54.99,  "category": "Footwear",    "stock": 40},
    "P014": {"name": "Sandals – Unisex",                    "price": 24.99,  "category": "Footwear",    "stock": 60},
    "P015": {"name": "Hiking Boots",                        "price": 119.99, "category": "Footwear",    "stock": 15},
    "P016": {"name": "Yoga Mat",                            "price": 19.99,  "category": "Fitness",     "stock": 90},
    "P017": {"name": "Resistance Bands Set",                "price": 14.99,  "category": "Fitness",     "stock": 100},
    "P018": {"name": "Dumbbell Set (5–25 kg)",              "price": 149.99, "category": "Fitness",     "stock": 10},
    "P019": {"name": "Jump Rope",                           "price": 8.99,   "category": "Fitness",     "stock": 120},
    "P020": {"name": "Foam Roller",                         "price": 17.99,  "category": "Fitness",     "stock": 75},
    "P021": {"name": "Stainless Steel Water Bottle (1L)",   "price": 16.99,  "category": "Kitchen",     "stock": 110},
    "P022": {"name": "French Press Coffee Maker",           "price": 27.99,  "category": "Kitchen",     "stock": 50},
    "P023": {"name": "Non-Stick Frying Pan (28 cm)",        "price": 34.99,  "category": "Kitchen",     "stock": 40},
    "P024": {"name": "Chef's Knife",                        "price": 39.99,  "category": "Kitchen",     "stock": 30},
    "P025": {"name": "Cutting Board (Bamboo)",              "price": 13.99,  "category": "Kitchen",     "stock": 85},
    "P026": {"name": "Air Fryer (3.5L)",                    "price": 69.99,  "category": "Kitchen",     "stock": 22},
    "P027": {"name": "Electric Kettle",                     "price": 24.99,  "category": "Kitchen",     "stock": 65},
    "P028": {"name": "Meal Prep Containers (10-pack)",      "price": 18.99,  "category": "Kitchen",     "stock": 95},
    "P029": {"name": "Blender",                             "price": 54.99,  "category": "Kitchen",     "stock": 28},
    "P030": {"name": "Toaster (2-slice)",                   "price": 21.99,  "category": "Kitchen",     "stock": 50},
    "P031": {"name": "Cotton T-Shirt – Black (M)",          "price": 14.99,  "category": "Clothing",    "stock": 100},
    "P032": {"name": "Cotton T-Shirt – White (M)",          "price": 14.99,  "category": "Clothing",    "stock": 100},
    "P033": {"name": "Slim-Fit Jeans – 32x32",             "price": 44.99,  "category": "Clothing",    "stock": 30},
    "P034": {"name": "Hoodie – Grey (L)",                   "price": 34.99,  "category": "Clothing",    "stock": 55},
    "P035": {"name": "Shorts – Navy (M)",                   "price": 19.99,  "category": "Clothing",    "stock": 70},
    "P036": {"name": "Backpack (30L)",                      "price": 49.99,  "category": "Bags",        "stock": 40},
    "P037": {"name": "Laptop Bag (15 inch)",                "price": 37.99,  "category": "Bags",        "stock": 35},
    "P038": {"name": "Tote Bag – Canvas",                   "price": 12.99,  "category": "Bags",        "stock": 80},
    "P039": {"name": "Travel Wallet",                       "price": 22.99,  "category": "Bags",        "stock": 60},
    "P040": {"name": "Gym Bag",                             "price": 29.99,  "category": "Bags",        "stock": 45},
    "P041": {"name": "Novel: 'The Midnight Library'",       "price": 11.99,  "category": "Books",       "stock": 90},
    "P042": {"name": "Novel: 'Atomic Habits'",              "price": 13.99,  "category": "Books",       "stock": 85},
    "P043": {"name": "Novel: 'Deep Work'",                  "price": 13.99,  "category": "Books",       "stock": 70},
    "P044": {"name": "Notebook – A5 Dotted",               "price": 7.99,   "category": "Stationery",  "stock": 150},
    "P045": {"name": "Ballpoint Pens (12-pack)",            "price": 5.99,   "category": "Stationery",  "stock": 200},
    "P046": {"name": "Desk Organiser",                      "price": 18.99,  "category": "Stationery",  "stock": 55},
    "P047": {"name": "Sticky Notes (5-pack)",               "price": 4.99,   "category": "Stationery",  "stock": 180},
    "P048": {"name": "Sunscreen SPF 50 (100ml)",            "price": 9.99,   "category": "Health",      "stock": 120},
    "P049": {"name": "Vitamin C Supplements (60 tabs)",     "price": 12.99,  "category": "Health",      "stock": 95},
    "P050": {"name": "Hand Sanitiser (500ml)",              "price": 5.99,   "category": "Health",      "stock": 160},
    "P051": {"name": "Face Moisturiser (50ml)",             "price": 17.99,  "category": "Health",      "stock": 75},
    "P052": {"name": "Scented Candle – Vanilla",            "price": 14.99,  "category": "Home",        "stock": 80},
    "P053": {"name": "Indoor Plant Pot (20 cm)",            "price": 11.99,  "category": "Home",        "stock": 60},
    "P054": {"name": "LED Desk Lamp",                       "price": 24.99,  "category": "Home",        "stock": 50},
    "P055": {"name": "Throw Blanket – Fleece",              "price": 22.99,  "category": "Home",        "stock": 65},
}

# ── System prompt for the chatbot ──────────────────────────────────────────────
def build_system_prompt():
    catalogue_lines = "\n".join(
        f"  {pid}: {info['name']} — ${info['price']:.2f} ({info['category']}) — Stock: {info['stock']}"
        for pid, info in PRODUCTS.items()
    )
    return f"""You are a friendly and helpful e-commerce shopping assistant.
You help customers find products, answer questions, and place orders.

PRODUCT CATALOGUE:
{catalogue_lines}

CAPABILITIES:
- Answer questions about products (price, category, stock availability)
- Recommend products based on customer needs or budget
- Place an order when the customer explicitly asks to buy / order something
- Confirm order details before placing

ORDERING RULES:
- Always confirm the product name and price before placing an order
- Ask for the customer's name and email before placing an order if not already known
- After collecting name, email, product ID, and quantity, respond with EXACTLY this JSON block (nothing else on that line):
  ORDER_JSON: {{"customer_name":"<name>","customer_email":"<email>","product_id":"<pid>","quantity":<int>}}
- After the JSON, continue the conversation naturally confirming the order

TONE: Friendly, concise, helpful. No jargon.
"""

# ── Tool: place order ──────────────────────────────────────────────────────────
def place_order(customer_name: str, customer_email: str, product_id: str, quantity: int):
    """Write order to DynamoDB and publish SNS notification."""
    product = PRODUCTS.get(product_id)
    if not product:
        return {"success": False, "error": f"Product {product_id} not found."}
    if product["stock"] < quantity:
        return {"success": False, "error": f"Only {product['stock']} units in stock."}

    order_id = str(uuid.uuid4())[:8].upper()
    total = round(product["price"] * quantity, 2)
    timestamp = datetime.utcnow().isoformat()

    # Write to DynamoDB
    table = dynamodb.Table(ORDERS_TABLE)
    table.put_item(Item={
        "order_id":       order_id,
        "timestamp":      timestamp,
        "customer_name":  customer_name,
        "customer_email": customer_email,
        "product_id":     product_id,
        "product_name":   product["name"],
        "quantity":       quantity,
        "total_price":    str(total),
        "status":         "confirmed",
    })

    # Publish SNS notification (admin)
    admin_message = (
        f"New Order #{order_id}\n"
        f"Customer: {customer_name} <{customer_email}>\n"
        f"Product:  {product['name']} (x{quantity})\n"
        f"Total:    ${total:.2f}\n"
        f"Time:     {timestamp}"
    )
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=f"Order #{order_id} Confirmed", Message=admin_message)

    # Send confirmation email to customer via SES
    customer_html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;color:#1a1a1a">
      <h2 style="font-size:1.3rem;margin-bottom:4px">Thanks for your order, {customer_name.split()[0]}!</h2>
      <p style="color:#666;font-size:0.9rem;margin-bottom:24px">Here's your order summary.</p>
      <div style="background:#f9f9f7;border-radius:12px;padding:20px;margin-bottom:24px">
        <p style="margin:0 0 8px"><strong>Order ID:</strong> #{order_id}</p>
        <p style="margin:0 0 8px"><strong>Product:</strong> {product['name']}</p>
        <p style="margin:0 0 8px"><strong>Quantity:</strong> {quantity}</p>
        <p style="margin:0"><strong>Total:</strong> ${total:.2f}</p>
      </div>
      <p style="color:#666;font-size:0.82rem">We'll be in touch with shipping details soon.</p>
      <p style="color:#aaa;font-size:0.78rem;margin-top:32px">Pixi &mdash; Your personal shopping assistant</p>
    </div>
    """
    try:
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [customer_email]},
            Message={
                "Subject": {"Data": f"Your Pixi Order #{order_id} is confirmed!"},
                "Body": {
                    "Html": {"Data": customer_html},
                    "Text": {"Data": f"Thanks {customer_name}! Your order #{order_id} for {product['name']} (x{quantity}) totalling ${total:.2f} is confirmed."},
                },
            },
        )
        print(f"SES email sent successfully. MessageId: {response['MessageId']} To: {customer_email}")
    except Exception as e:
        print(f"SES email failed: {e}")  # don't block the order if email fails

    return {"success": True, "order_id": order_id, "total": total}


# ── Lambda entry point ─────────────────────────────────────────────────────────
def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        user_message = body.get("message", "").strip()
        conversation_history = body.get("history", [])   # list of {role, content}

        if not user_message:
            return _response(400, {"error": "No message provided."})

        # Build messages list
        messages = conversation_history + [{"role": "user", "content": user_message}]

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        result = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=build_system_prompt(),
            messages=messages,
        )

        assistant_text = result.content[0].text

        # Check if Claude decided to place an order
        order_result = None
        if "ORDER_JSON:" in assistant_text:
            for line in assistant_text.splitlines():
                if line.strip().startswith("ORDER_JSON:"):
                    try:
                        json_str = line.split("ORDER_JSON:", 1)[1].strip()
                        order_data = json.loads(json_str)
                        order_result = place_order(**order_data)
                    except Exception as e:
                        order_result = {"success": False, "error": str(e)}
                    break

        return _response(200, {
            "reply":        assistant_text,
            "order_result": order_result,
            "history":      messages + [{"role": "assistant", "content": assistant_text}],
        })

    except Exception as e:
        return _response(500, {"error": str(e)})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
