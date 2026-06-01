# AI Token 代理服务系统
# Copyright (C) 2026
# License: GNU General Public License v3.0
# https://www.gnu.org/licenses/

from fastapi import FastAPI, Request, HTTPException
import requests
import time
import random
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import config

app = FastAPI(title="AI Token商城后端")

BASE_DIR = Path(__file__).parent
ORDER_FILE = BASE_DIR / "data" / "order.json"
BALANCE_FILE = BASE_DIR / "data" / "balance.json"
USER_KEY_FILE = BASE_DIR / "data" / "user_keys.json"  # openid -> token_key 映射

for f in [ORDER_FILE, BALANCE_FILE, USER_KEY_FILE]:
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text("[]" if "order" in str(f) else "{}", encoding="utf-8")

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_token_key():
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(32))

def get_or_create_token_key(openid: str) -> str:
    user_keys = read_json(USER_KEY_FILE)
    for item in user_keys:
        if item.get("openid") == openid:
            return item.get("token_key")
    token_key = generate_token_key()
    user_keys.append({"openid": openid, "token_key": token_key})
    write_json(USER_KEY_FILE, user_keys)
    return token_key

def get_token_key_by_openid(openid: str) -> str:
    user_keys = read_json(USER_KEY_FILE)
    for item in user_keys:
        if item.get("openid") == openid:
            return item.get("token_key", "")
    return ""

def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={config.APP_ID}&secret={config.APP_SECRET}"
    res = requests.get(url).json()
    return res.get("access_token", "")

def send_subscribe_msg(openid, order_no, money, pay_time, token_key=""):
    token = get_access_token()
    if not token:
        return
    send_url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"
    body = {
        "touser": openid,
        "template_id": config.SUB_MSG_TEMPLATE_ID,
        "data": {
            "character_string1": {"value": order_no},
            "phrase2": {"value": "支付成功"},
            "amount3": {"value": f"{money}元"},
            "time4": {"value": pay_time}
        }
    }
    if token_key:
        body["data"]["character_string5"] = {"value": f"密钥:{token_key}"}
    requests.post(send_url, json=body)

def gen_order_no():
    return f"XC{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"

# 1. 获取用户openid
@app.get("/api/get-openid")
async def get_openid(code: str):
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={config.APP_ID}&secret={config.APP_SECRET}&js_code={code}&grant_type=authorization_code"
    res = requests.get(url).json()
    return {"openid": res.get("openid", "")}

# 2. 创建支付订单
@app.post("/api/create-pay-order")
async def create_order(openid: str, goodsId: int, totalFee: int, body: str):
    order_no = gen_order_no()
    timestamp = str(int(time.time()))
    nonce_str = ''.join(random.sample("abcdefghijklmnopqrstuvwxyz0123456789", 32))

    pay_info = {
        "appId": config.APP_ID,
        "timeStamp": timestamp,
        "nonceStr": nonce_str,
        "package": f"prepay_id={order_no}",
        "signType": "RSA"
    }
    sign_str = f"{config.APP_ID}\n{timestamp}\n{nonce_str}\n{pay_info['package']}\n"
    pay_info["paySign"] = hashlib.md5((sign_str + config.API_V3_KEY).encode()).hexdigest().upper()

    order_list = read_json(ORDER_FILE)
    order_list.append({
        "order_no": order_no,
        "openid": openid,
        "goods_id": goodsId,
        "total_fee": totalFee,
        "status": "pending",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    write_json(ORDER_FILE, order_list)
    return {"code": 200, "data": pay_info}

# 3. 支付异步回调
@app.post("/api/pay-notify")
async def pay_callback(req: Request):
    try:
        data = await req.json()
    except:
        return {"code": "FAIL"}
    if data.get("trade_state") != "SUCCESS":
        return {"code": "FAIL"}

    openid = data.get("payer", {}).get("openid", "")
    order_no = data.get("out_trade_no", "")
    total_fee = data.get("amount", {}).get("total", 0)
    pay_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price_yuan = total_fee / 100  # 微信支付返回的是分，转成元
    flow = config.PRICE_TO_FLOW.get(price_yuan, 0)

    orders = read_json(ORDER_FILE)
    for item in orders:
        if item["order_no"] == order_no:
            item["status"] = "paid"
            item["pay_time"] = pay_time
            item["flow_num"] = flow
    write_json(ORDER_FILE, orders)

    balance_data = read_json(BALANCE_FILE)
    token_key = get_or_create_token_key(openid)
    exist = False
    for user in balance_data:
        if user.get("openid") == openid:
            user["flow"] = user.get("flow", 0) + flow
            user["package_price"] = price_yuan
            user["token_key"] = token_key
            exist = True
    if not exist:
        balance_data.append({"openid": openid, "flow": flow, "package_price": price_yuan, "token_key": token_key})
    write_json(BALANCE_FILE, balance_data)

    try:
        requests.post(
            f"{config.AGENT_BACKEND_URL}/internal/register-token",
            params={
                "internal_key": config.INTERNAL_API_KEY,
                "openid": openid,
                "token_key": token_key,
                "flow": flow
            },
            timeout=5
        )
    except Exception as e:
        print(f"[ERROR] 同步Token到Agent失败: {e}")

    send_subscribe_msg(openid, order_no, total_fee/100, pay_time, token_key)
    return {"code": "SUCCESS", "token_key": token_key}

# 4. 查询订单
@app.get("/api/order-list")
async def get_orders(openid: str):
    orders = read_json(ORDER_FILE)
    user_orders = [o for o in orders if o.get("openid") == openid]
    return {"code": 200, "data": user_orders}

# 5. 查询余额
@app.get("/api/balance")
async def get_balance(openid: str):
    balance_data = read_json(BALANCE_FILE)
    for user in balance_data:
        if user.get("openid") == openid:
            return {"code": 200, "flow": user.get("flow", 0), "token_key": user.get("token_key", "")}
    return {"code": 200, "flow": 0, "token_key": ""}

# 5.1 获取用户TokenKey
@app.get("/api/token-key")
async def get_user_token_key(openid: str):
    token_key = get_or_create_token_key(openid)
    return {"code": 200, "token_key": token_key}

# 6. 获取套餐列表（包含模型）
@app.get("/api/packages")
async def get_packages():
    packages = []
    for price, pkg in config.PRICE_PACKAGE.items():
        packages.append({
            "price": price,
            "name": pkg["name"],
            "service_quota": pkg["service_quota"],
            "models": pkg["models"],
            "default_model": pkg.get("default_model", "MiniMax-M2.7"),
            "description": pkg.get("description", "")
        })
    return {"code": 200, "packages": packages}

# 7. 获取模型列表
@app.get("/api/models")
async def get_models():
    models = []
    for model_id, cfg in config.UPSTREAM_PROVIDERS.items():
        if cfg.get("enabled", False):
            models.append({
                "id": model_id,
                "name": cfg["name"],
                "ratio": config.MODEL_RATIOS.get(model_id, 1.0)
            })
    return {"code": 200, "models": models}

# 8. 获取用户套餐信息
@app.get("/api/user-package")
async def get_user_package(openid: str):
    balance_data = read_json(BALANCE_FILE)
    for user in balance_data:
        if user.get("openid") == openid:
            package_price = user.get("package_price", 299)
            pkg = config.PRICE_PACKAGE.get(package_price, config.PRICE_PACKAGE[299])
            return {
                "code": 200,
                "package_price": package_price,
                "package_name": pkg["name"],
                "models": pkg["models"],
                "default_model": pkg.get("default_model", "MiniMax-M2.7"),
                "service_quota": pkg["service_quota"]
            }
    return {"code": 200, "package_price": 299, "package_name": "基础版", "models": ["MiniMax-M2.7"], "default_model": "MiniMax-M2.7", "service_quota": 1000}

# 9. 获取用户模型使用统计
@app.get("/api/model-usage")
async def get_model_usage(openid: str):
    balance_data = read_json(BALANCE_FILE)
    for user in balance_data:
        if user.get("openid") == openid:
            model_usage = user.get("model_usage", {})
            return {"code": 200, "model_usage": model_usage}
    return {"code": 200, "model_usage": {}}

# 健康检测
@app.get("/")
async def health():
    return {"status": "running", "note": "AI Token商城后端"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)