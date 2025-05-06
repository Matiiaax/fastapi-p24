from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import hashlib, json, base64, uuid, requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 Wklej swoje dane z panelu Przelewy24
MERCHANT_ID = 343371
API_KEY = "78ea7ccbf4bb7035609fb6f79af424b0"
CRC = "3dd1ac86b0fdb027"

@app.get("/create-payment")
def create_payment(amount: int = Query(..., description="Kwota w groszach")):
    session_id = f"order-{uuid.uuid4().hex[:8]}"
    currency = "PLN"

    # 🧮 Generowanie podpisu
    sign_data = {
        "sessionId": session_id,
        "merchantId": MERCHANT_ID,
        "amount": amount,
        "currency": currency,
        "crc": CRC
    }
    json_string = json.dumps(sign_data, separators=(',', ':'))
    sign = hashlib.sha384(json_string.encode("utf-8")).hexdigest()

    # 📦 Payload
    payload = {
        "merchantId": MERCHANT_ID,
        "posId": MERCHANT_ID,
        "sessionId": session_id,
        "amount": amount,
        "currency": currency,
        "description": "Zakup produktu",
        "email": "klient@example.com",
        "country": "PL",
        "urlReturn": "https://twoja-nazwa.onrender.com/return",
        "urlStatus": "https://twoja-nazwa.onrender.com/status",
        "sign": sign
    }

    # 🔐 Nagłówek autoryzacji
    auth = base64.b64encode(f"{MERCHANT_ID}:{API_KEY}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    # 🔁 Wysyłanie żądania do Przelewy24
    response = requests.post(
        "https://secure.przelewy24.pl/api/v1/transaction/register",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        token = response.json().get("data", {}).get("token")
        return {"token": token, "sessionId": session_id}
    else:
        return {
            "status": response.status_code,
            "error": response.json().get("error", "Unknown error"),
            "response_text": response.text,
            "headers": dict(response.headers)
        }

@app.post("/status")
async def handle_status(request: Request):
    data = await request.json()
    print("📥 Odebrano webhook od P24:", data)
    return {"status": "OK"}

@app.get("/return")
async def return_page():
    return HTMLResponse("""
    <html>
        <head><title>Dziękujemy</title></head>
        <body style='text-align:center;padding-top:40px;font-family:sans-serif;'>
            <h1>✅ Płatność zakończona</h1>
            <p>Dziękujemy za Twoją darowiznę!</p>
        </body>
    </html>
    """)
