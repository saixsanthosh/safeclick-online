# safeclick/backend/main.py
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3, os, datetime, random, string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ensure selfies dir exists
os.makedirs("selfies", exist_ok=True)

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        city TEXT,
        pincode TEXT,
        items TEXT,
        total TEXT,
        selfie_path TEXT,
        ip TEXT,
        device TEXT,
        browser TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# serve selfie files
app.mount("/selfies", StaticFiles(directory="selfies"), name="selfies")

@app.post("/save_order")
async def save_order(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    items: str = Form(...),
    total: str = Form(...),
    selfie: UploadFile = File(None),
    request: Request = None,
):
    selfie_path = None
    if selfie:
        content = await selfie.read()
        filename = f"{int(datetime.datetime.now().timestamp()*1000)}.png"
        path = os.path.join("selfies", filename)
        with open(path, "wb") as f:
            f.write(content)
        selfie_path = "/selfies/" + filename

    client_host = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders 
        (order_id, name, email, phone, address, city, pincode, items, total, selfie_path, ip, device, browser, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        name,
        email,
        phone,
        address,
        city,
        pincode,
        items,
        total,
        selfie_path,
        client_host,
        user_agent,
        user_agent,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    last_id = c.lastrowid
    conn.close()

    return {"status": "success", "order_id": order_id, "id": last_id}

@app.get("/orders")
def get_orders():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, order_id, name, email, phone, address, city, pincode, items, total, selfie_path, ip, device, browser, created_at FROM orders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    orders = []
    for r in rows:
        orders.append({
            "id": r[0],
            "order_id": r[1],
            "name": r[2],
            "email": r[3],
            "phone": r[4],
            "address": r[5],
            "city": r[6],
            "pincode": r[7],
            "items": r[8],
            "total": r[9],
            "selfie_path": r[10] or "",
            "ip": r[11],
            "device": r[12],
            "browser": r[13],
            "timestamp": r[14]
        })
    return {"orders": orders}

@app.get("/order/{order_id}")
def get_order_by_id(order_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, order_id, name, email, phone, address, city, pincode, items, total, selfie_path, ip, device, browser, created_at FROM orders WHERE id = ?", (order_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return {"error": "not found"}
    return {
        "id": r[0],
        "order_id": r[1],
        "name": r[2],
        "email": r[3],
        "phone": r[4],
        "address": r[5],
        "city": r[6],
        "pincode": r[7],
        "items": r[8],
        "total": r[9],
        "selfie_path": r[10] or "",
        "ip": r[11],
        "device": r[12],
        "browser": r[13],
        "timestamp": r[14]
    }
