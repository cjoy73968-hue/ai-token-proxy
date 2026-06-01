# AI Token 代理服务系统
# Copyright (C) 2026
# License: GNU General Public License v3.0
# https://www.gnu.org/licenses/

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx
import time
import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
import csv
from typing import Optional
import tiktoken

app = FastAPI(title="AI Token代理服务 完整版")

try:
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
except:
    encoding = None

def calculate_tokens(messages: list, model: str = "deepseek-chat") -> int:
    """计算对话消息的Token数量"""
    global encoding
    if encoding is None:
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            return 50
    try:
        tokens_per_message = 3
        tokens_per_name = 1
        total_tokens = 0
        for msg in messages:
            total_tokens += tokens_per_message
            for key, value in msg.items():
                try:
                    total_tokens += len(encoding.encode(value))
                except:
                    total_tokens += len(value) // 4
                if key == "name":
                    total_tokens += tokens_per_name
        total_tokens += 3
        return total_tokens
    except Exception as e:
        print(f"Token计算失败：{e}")
        return 50

# ===================== 全局配置区 自行修改 =====================

# ===================== 多上游服务商配置 =====================
# 请在下方填入你的API密钥，或通过环境变量方式配置

UPSTREAM_PROVIDERS = {
    "deepseek-chat": {
        "name": "DeepSeek Chat",
        "api_key": os.getenv("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY"),
        "url": "https://api.deepseek.com/v1/chat/completions",
        "rate_limit": 100,
        "enabled": True
    },
    "gpt-4": {
        "name": "GPT-4",
        "api_key": os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"),
        "url": "https://api.openai.com/v1/chat/completions",
        "rate_limit": 50,
        "enabled": False
    },
    "glm-4": {
        "name": "智谱 GLM-4",
        "api_key": os.getenv("ZHIPU_API_KEY", "YOUR_ZHIPU_API_KEY"),
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "rate_limit": 80,
        "enabled": False
    },
    "moonshot-v1-8k": {
        "name": "Kimi",
        "api_key": os.getenv("MOONSHOT_API_KEY", "YOUR_MOONSHOT_API_KEY"),
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "rate_limit": 80,
        "enabled": False
    },
    "MiniMax-M2.7": {
        "name": "MiniMax M2.7",
        "api_key": os.getenv("MINIMAX_API_KEY", "YOUR_MINIMAX_API_KEY"),
        "url": "https://api.minimax.chat/v1/chat/completions",
        "rate_limit": 100,
        "enabled": True
    }
}

DEFAULT_MODEL = "MiniMax-M2.7"

# 模型配额消耗比例
MODEL_RATIOS = {
    "deepseek-chat": 1.0,
    "MiniMax-M2.7": 1.0,
    "glm-4": 1.2,
    "moonshot-v1-8k": 1.5,
    "gpt-4": 3.0
}

def route_to_provider(model: str) -> dict:
    """根据模型名称路由到对应提供商"""
    if model not in UPSTREAM_PROVIDERS:
        model = DEFAULT_MODEL
    provider = UPSTREAM_PROVIDERS.get(model, UPSTREAM_PROVIDERS[DEFAULT_MODEL])
    if not provider.get("enabled", False):
        return None
    return provider

def calculate_quota(tokens: int, model: str) -> float:
    """根据模型比例计算配额消耗"""
    ratio = MODEL_RATIOS.get(model, 1.0)
    return round(tokens / 10000 * ratio, 4)

def get_model_ratio(model: str) -> float:
    """获取模型配额比例"""
    return MODEL_RATIOS.get(model, 1.0)

def get_enabled_models() -> list:
    """获取所有已启用的模型列表"""
    return [model for model, cfg in UPSTREAM_PROVIDERS.items() if cfg.get("enabled", False)]

def get_all_models() -> dict:
    """获取所有模型及其信息"""
    return {
        model: {
            "name": cfg["name"],
            "enabled": cfg.get("enabled", False),
            "ratio": MODEL_RATIOS.get(model, 1.0)
        }
        for model, cfg in UPSTREAM_PROVIDERS.items()
    }

TIMEOUT_SECONDS = 120

# 风控扣量
LIMIT_PER_MIN = 80
AVG_CONSUME_WAN_TOKEN = 0.05  # 单次请求扣万Token

# 管理员密码（请在部署时修改，或使用环境变量ADMIN_PWD）
ADMIN_PWD = os.getenv("ADMIN_PWD", "CHANGE_ME_ADMIN_PASSWORD")

# 内部API密钥（用于服务间通信，请使用复杂随机字符串）
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "CHANGE_ME_INTERNAL_KEY")

# 订单过期时长 单位：分钟
ORDER_EXPIRE_MIN = 60

# 网关访问控制模式: "whitelist"=白名单模式, "open"=完全开放
GATEWAY_ACCESS_MODE = "open"
WHITELIST_APP_IDS = ["xxxxxxxx"]  # 允许调用的小程序AppId列表

# 微信支付商户号配置
MCH_ID = ""  # 商户号
API_V3_KEY = ""  # APIv3密钥
NOTIFY_URL = "https://你的域名/admin/pay-notify"  # 回调地址

# 套餐定价（包含模型列表和Token配额）
PRICE_PACKAGE = {
    9.9: {
        "name": "体验版",
        "service_quota": 100,  # 500万Token (500 = 500万/1万)
        "models": ["MiniMax-M2.7"],
        "default_model": "MiniMax-M2.7",
        "description": "新人专享，100万Token"
    },
    19.9: {
        "name": "体验版2",
        "service_quota": 500,  # 500万Token (500 = 500万/1万)
        "models": ["MiniMax-M2.7"],
        "default_model": "MiniMax-M2.7",
        "description": "新人专享，500万Token"
    },
    299: {
        "name": "基础版",
        "service_quota": 1000,  # 1000万Token
        "models": ["MiniMax-M2.7"],
        "default_model": "MiniMax-M2.7",
        "description": "智能咨询+文案辅助（个人/自媒体）"
    },
    499: {
        "name": "标准版",
        "service_quota": 3000,  # 3000万Token
        "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4"],
        "default_model": "MiniMax-M2.7",
        "description": "营销文案+活动策划+日常咨询"
    },
    899: {
        "name": "企业版",
        "service_quota": 10000,  # 10000万Token
        "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4", "moonshot-v1-8k", "gpt-4"],
        "default_model": "MiniMax-M2.7",
        "description": "全场景智能服务+技术支持"
    }
}

def get_package_models(package_price: int) -> list:
    """获取套餐包含的模型列表"""
    pkg = PRICE_PACKAGE.get(package_price, {})
    return pkg.get("models", [DEFAULT_MODEL])

def get_package_default_model(package_price: int) -> str:
    """获取套餐默认模型"""
    pkg = PRICE_PACKAGE.get(package_price, {})
    return pkg.get("default_model", DEFAULT_MODEL)

def check_model_access(package_price: int, model: str) -> bool:
    """检查模型是否在套餐范围内"""
    pkg = PRICE_PACKAGE.get(package_price, {})
    models = pkg.get("models", [])
    return model in models

# 数据文件路径
DATA_DIR = Path("./data")
BALANCE_FILE = DATA_DIR / "balance.json"
ORDER_FILE = DATA_DIR / "order.json"
EXPORT_DIR = Path("./export")

# 线程锁
lock = threading.Lock()

# 限流容器
ip_request_record = {}
# 提供商限流记录 {model: {"count": int, "window_start": int}}
provider_rate_limit = {}
# =================================================================

# 初始化目录文件
def init_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)
    if not BALANCE_FILE.exists():
        with open(BALANCE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    if not ORDER_FILE.exists():
        with open(ORDER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def migrate_balance_data(data: dict) -> dict:
    new_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            if "model_usage" not in value:
                value["model_usage"] = {}
            new_data[key] = value
        else:
            new_data[key] = {
                "balance": value,
                "status": "active",
                "create_date": datetime.now().strftime("%Y-%m-%d"),
                "model_usage": {}
            }
    return new_data

# 数据读写工具
def load_balance() -> dict:
    with lock:
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_balance(data: dict):
    with lock:
        with open(BALANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_orders() -> list:
    with lock:
        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_orders(data: list):
    with lock:
        with open(ORDER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def track_model_usage(user_key: str, model: str, tokens: int):
    """追踪用户各模型使用量"""
    if user_key not in USER_BALANCE:
        return
    if isinstance(USER_BALANCE[user_key], dict):
        if "model_usage" not in USER_BALANCE[user_key]:
            USER_BALANCE[user_key]["model_usage"] = {}
        usage = USER_BALANCE[user_key]["model_usage"]
        usage[model] = usage.get(model, 0) + 1
        USER_BALANCE[user_key]["model_usage"] = usage

def check_provider_rate_limit(model: str) -> bool:
    """检查提供商是否超过限流，返回True表示允许，False表示被限流"""
    now = int(time.time())
    window = 60
    if model not in provider_rate_limit:
        provider_rate_limit[model] = {"count": 0, "window_start": now}
    record = provider_rate_limit[model]
    if now - record["window_start"] > window:
        record["count"] = 0
        record["window_start"] = now
    rate_limit = UPSTREAM_PROVIDERS.get(model, {}).get("rate_limit", 100)
    if record["count"] >= rate_limit:
        return False
    record["count"] += 1
    return True

# 校验管理员密码
def check_admin_pwd(pwd: str) -> bool:
    return pwd == ADMIN_PWD

# 定时清理过期订单
def clean_expire_orders(order_list: list) -> list:
    now = datetime.now()
    valid_list = []
    for item in order_list:
        if item["status"] != "待付款":
            valid_list.append(item)
            continue
        try:
            create_dt = datetime.strptime(item["create_time"], "%Y-%m-%d %H:%M:%S")
            if now - create_dt <= timedelta(minutes=ORDER_EXPIRE_MIN):
                valid_list.append(item)
            else:
                item["status"] = "已过期"
                valid_list.append(item)
        except:
            valid_list.append(item)
    return valid_list

# 初始化加载
init_data_files()
raw_balance = load_balance()
if raw_balance and isinstance(list(raw_balance.values())[0], (int, float)):
    USER_BALANCE = migrate_balance_data(raw_balance)
    save_balance(USER_BALANCE)
else:
    USER_BALANCE = raw_balance
PAY_ORDER_LIST = load_orders()
PAY_ORDER_LIST = clean_expire_orders(PAY_ORDER_LIST)
save_orders(PAY_ORDER_LIST)

# IP限流中间件
@app.middleware("http")
async def ip_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now_ts = int(time.time())
    if client_ip not in ip_request_record or now_ts - ip_request_record[client_ip]["ts"] > 60:
        ip_request_record[client_ip] = {"cnt": 1, "ts": now_ts}
    else:
        ip_request_record[client_ip]["cnt"] += 1
        if ip_request_record[client_ip]["cnt"] > LIMIT_PER_MIN:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试")
    return await call_next(request)

# 模型列表（OpenAI 兼容）
@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 1677610602,
                "owned_by": "system"
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "system"
            },
            {
                "id": "text-embedding-3-large",
                "object": "model",
                "created": 1700000000,
                "owned_by": "system"
            }
        ]
    }

# OpenAI 兼容端点 - 有些工具用这个路径（非 chat 格式）
@app.post("/v1/completions")
async def chat_completions_compat(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="授权格式错误")
    user_key = auth_header.replace("Bearer ", "").strip()

    if user_key not in USER_BALANCE:
        raise HTTPException(status_code=401, detail="无效代理密钥")
    if USER_BALANCE[user_key] <= 0:
        raise HTTPException(status_code=403, detail="流量已耗尽，请续费后使用")

    req_body = await request.json()
    prompt = req_body.get("prompt", "")
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = [{"role": "user", "content": str(prompt)}]

    chat_req = {"model": req_body.get("model", MODEL_NAME), "messages": messages}

    headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(UPSTREAM_API_URL, json=chat_req, headers=headers)
            resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上游接口异常: {str(e)}")

    USER_BALANCE[user_key] -= AVG_CONSUME_WAN_TOKEN
    save_balance(USER_BALANCE)
    return resp.json()

# Embeddings 端点（透传）
@app.post("/v1/embeddings")
async def embeddings_proxy(request: Request):
    req_body = await request.json()
    headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(
                UPSTREAM_API_URL.replace("/chat/completions", "/embeddings"),
                json=req_body,
                headers=headers
            )
            resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=500, detail="上游接口异常")
    return resp.json()

# 核心转发接口
@app.post("/v1/chat/completions")
async def chat_proxy(request: Request, req_body_override: dict = None):
    app_id = request.headers.get("X-App-Id", "")
    if GATEWAY_ACCESS_MODE == "whitelist" and app_id not in WHITELIST_APP_IDS:
        raise HTTPException(status_code=403, detail="未授权的访问来源")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="授权格式错误")
    user_key = auth_header.replace("Bearer ", "").strip()

    if user_key not in USER_BALANCE:
        raise HTTPException(status_code=401, detail="无效代理密钥")

    user_balance_data = USER_BALANCE[user_key]
    if isinstance(user_balance_data, dict):
        if user_balance_data.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="密钥已被暂停，请联系管理员")
        balance = user_balance_data.get("balance", 0)
    else:
        balance = user_balance_data

    if balance <= 0:
        raise HTTPException(status_code=403, detail="服务配额已耗尽，请续费后使用")

    if req_body_override:
        req_body = req_body_override
    else:
        req_body = await request.json()

    stream_mode = req_body.get("stream", False)

    model = req_body.get("model", DEFAULT_MODEL)
    if not model:
        model = DEFAULT_MODEL

    provider = route_to_provider(model)
    if provider is None:
        raise HTTPException(status_code=503, detail=f"模型 {model} 暂不可用，请稍后重试或联系管理员")

    if not check_provider_rate_limit(model):
        raise HTTPException(status_code=429, detail=f"请求过于频繁，请稍后重试")

    req_tokens = calculate_tokens(req_body.get("messages", []), model)

    headers = {
        "Authorization": f"Bearer {provider['api_key']}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            upstream_resp = await client.post(provider["url"], json=req_body, headers=headers)
            print(f"[DEBUG] {provider['name']} status: {upstream_resp.status_code}")
            upstream_resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] 上游API错误: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"上游API错误: {e.response.status_code}")
    except Exception as e:
        print(f"[ERROR] 上游接口异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上游接口异常: {str(e)}")

    resp_tokens = 0
    if not stream_mode:
        try:
            resp_json = upstream_resp.json()
            resp_content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            try:
                resp_tokens = len(encoding.encode(resp_content)) if encoding else len(resp_content) // 4
            except:
                resp_tokens = len(resp_content) // 4
        except:
            pass

    total_tokens = req_tokens + resp_tokens
    consume_quota = calculate_quota(total_tokens, model)

    if isinstance(user_balance_data, dict):
        USER_BALANCE[user_key]["balance"] = round(balance - consume_quota, 4)
    else:
        USER_BALANCE[user_key] = {"balance": round(balance - consume_quota, 4), "status": "active", "model_usage": {}}
    save_balance(USER_BALANCE)
    track_model_usage(user_key, model, total_tokens)

    if stream_mode:
        print(f"[DEBUG] 进入流式模式")
        async def stream_generator():
            async for chunk in upstream_resp.aiter_bytes():
                print(f"[DEBUG] 流式块: {chunk[:100]}")
                yield chunk
        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    print(f"[DEBUG] 进入非流式模式")
    try:
        return upstream_resp.json()
    except:
        print(f"[ERROR] JSON解析失败，原始响应: {upstream_resp.text[:200]}")
        raise HTTPException(status_code=500, detail=f"上游返回非JSON")

# 用户自助查余额
@app.get("/user/balance")
async def query_balance(token_key: str):
    if token_key not in USER_BALANCE:
        return {"code": 401, "msg": "密钥不存在", "balance": 0, "model_usage": {}}
    data = USER_BALANCE[token_key]
    if isinstance(data, dict):
        remain = round(data.get("balance", 0), 2)
        status = data.get("status", "active")
        model_usage = data.get("model_usage", {})
    else:
        remain = round(data, 2)
        status = "active"
        model_usage = {}
    tip = "服务配额充足" if remain >= 100 else "【预警】服务配额不足，请续费"
    return {
        "code": 200,
        "user_key": token_key,
        "remain_wan_token": remain,
        "status": status,
        "tip": tip,
        "model_usage": model_usage
    }

# 获取用户可用模型列表
@app.get("/models/available")
async def get_available_models(token_key: str):
    if token_key not in USER_BALANCE:
        return {"code": 401, "msg": "密钥不存在", "models": []}
    data = USER_BALANCE[token_key]
    pkg_price = data.get("package_price", 299)
    models = get_package_models(pkg_price)
    enabled_models = get_all_models()
    return {
        "code": 200,
        "models": [
            {
                "id": mid,
                "name": enabled_models.get(mid, {}).get("name", mid),
                "ratio": enabled_models.get(mid, {}).get("ratio", 1.0),
                "enabled": enabled_models.get(mid, {}).get("enabled", False)
            }
            for mid in models
        ]
    }

# 获取模型列表（所有模型）
@app.get("/models/list")
async def get_models_list():
    models = get_all_models()
    return {
        "code": 200,
        "models": [
            {
                "id": mid,
                "name": cfg["name"],
                "ratio": MODEL_RATIOS.get(mid, 1.0),
                "enabled": cfg.get("enabled", False)
            }
            for mid, cfg in UPSTREAM_PROVIDERS.items()
        ]
    }

# 获取用户模型使用统计
@app.get("/user/model-usage")
async def get_model_usage(token_key: str):
    if token_key not in USER_BALANCE:
        return {"code": 401, "msg": "密钥不存在", "model_usage": {}}
    data = USER_BALANCE[token_key]
    if isinstance(data, dict):
        model_usage = data.get("model_usage", {})
    else:
        model_usage = {}
    return {
        "code": 200,
        "model_usage": model_usage
    }

# 设置用户模型偏好
@app.post("/user/model-preference")
async def set_model_preference(token_key: str, model: str):
    if token_key not in USER_BALANCE:
        return {"code": 401, "msg": "密钥不存在"}
    if model not in UPSTREAM_PROVIDERS:
        return {"code": 400, "msg": "无效的模型"}
    provider = UPSTREAM_PROVIDERS.get(model, {})
    if not provider.get("enabled", False):
        return {"code": 400, "msg": "该模型暂不可用"}
    user_data = USER_BALANCE.get(token_key, {})
    if isinstance(user_data, dict):
        user_data["preferred_model"] = model
        USER_BALANCE[token_key] = user_data
    else:
        USER_BALANCE[token_key] = {"balance": user_data, "status": "active", "preferred_model": model}
    save_balance(USER_BALANCE)
    return {"code": 200, "msg": "偏好已设置", "model": model}

# 获取用户模型偏好
@app.get("/user/model-preference")
async def get_model_preference(token_key: str):
    if token_key not in USER_BALANCE:
        return {"code": 401, "msg": "密钥不存在", "model": ""}
    user_data = USER_BALANCE.get(token_key, {})
    if isinstance(user_data, dict):
        preferred = user_data.get("preferred_model", "")
        return {"code": 200, "model": preferred}
    return {"code": 200, "model": ""}

# ========== 管理员加密接口 ==========
# 创建订单
@app.post("/admin/create-order")
async def create_order(
    admin_pwd: str,
    nickname: str,
    money: float,
    bind_key: str
):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    if money not in PRICE_PACKAGE:
        return {"code": 400, "msg": "无此套餐"}
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    pkg = PRICE_PACKAGE[money]
    init_flow = pkg["service_quota"]
    new_order = {
        "order_no": order_no,
        "nickname": nickname,
        "money": money,
        "init_flow": init_flow,
        "bind_key": bind_key,
        "package_name": pkg["name"],
        "models": pkg["models"],
        "status": "待付款",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    PAY_ORDER_LIST.append(new_order)
    save_orders(PAY_ORDER_LIST)
    return {"code": 200, "order_info": new_order}

# 确认付款充值
@app.post("/admin/pay-success")
async def pay_success(admin_pwd: str, order_no: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    with lock:
        global PAY_ORDER_LIST
        PAY_ORDER_LIST = clean_expire_orders(PAY_ORDER_LIST)

        for order in PAY_ORDER_LIST:
            if order["order_no"] == order_no:
                if order["status"] != "待付款":
                    return {"code": 400, "msg": "订单已付款/已过期"}
                order["status"] = "已付款已发货"
                key = order["bind_key"]
                add_num = order["init_flow"]
                if key in USER_BALANCE:
                    bal = USER_BALANCE[key]
                    if isinstance(bal, dict):
                        bal["balance"] += add_num
                    else:
                        USER_BALANCE[key] = {"balance": bal + add_num, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d")}
                else:
                    USER_BALANCE[key] = {"balance": add_num, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d")}
                save_balance(USER_BALANCE)
                save_orders(PAY_ORDER_LIST)
                return {"code": 200, "msg": "充值成功", "order": order}
        return {"code": 400, "msg": "未找到该订单"}

# 创建微信支付订单
@app.post("/admin/create-pay-order")
async def create_pay_order(admin_pwd: str, nickname: str, money: float, bind_key: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    if money not in PRICE_PACKAGE:
        return {"code": 400, "msg": "无此套餐"}
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    pkg = PRICE_PACKAGE[money]
    new_order = {
        "order_no": order_no,
        "nickname": nickname,
        "money": money,
        "init_flow": pkg["service_quota"],
        "package_name": pkg["name"],
        "bind_key": bind_key,
        "status": "待付款",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    PAY_ORDER_LIST.append(new_order)
    save_orders(PAY_ORDER_LIST)
    return {"code": 200, "order_info": new_order}

# 微信支付回调通知
@app.post("/admin/pay-notify")
async def pay_notify(request: Request):
    try:
        body = await request.json()
        event_type = body.get("event_type", "")
        if event_type != "TRANSACTION.SUCCESS":
            return {"code": 400, "msg": "非成功事件"}
        resource = body.get("resource", {})
        original_data = resource.get("original_data", {})
        order_no = original_data.get("out_trade_no", "")
        amount = original_data.get("amount", {}).get("total", 0)
    except:
        return {"code": 400, "msg": "解析失败"}

    with lock:
        global PAY_ORDER_LIST
        PAY_ORDER_LIST = clean_expire_orders(PAY_ORDER_LIST)
        for order in PAY_ORDER_LIST:
            if order["order_no"] == order_no:
                if order["status"] != "待付款":
                    return {"code": 200, "msg": "订单已处理"}
                order["status"] = "已付款已发货"
                key = order["bind_key"]
                add_num = order["init_flow"]
                if key in USER_BALANCE:
                    bal = USER_BALANCE[key]
                    if isinstance(bal, dict):
                        bal["balance"] += add_num
                    else:
                        USER_BALANCE[key] = {"balance": bal + add_num, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d")}
                else:
                    USER_BALANCE[key] = {"balance": add_num, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d")}
                save_balance(USER_BALANCE)
                save_orders(PAY_ORDER_LIST)
                return {"code": 200, "msg": "处理成功"}
        return {"code": 400, "msg": "未找到订单"}

# 暂停密钥
@app.post("/admin/pause-key")
async def pause_key(admin_pwd: str, user_key: str, reason: str = ""):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    with lock:
        if user_key not in USER_BALANCE:
            return {"code": 400, "msg": "密钥不存在"}
        if isinstance(USER_BALANCE[user_key], dict):
            USER_BALANCE[user_key]["status"] = "suspended"
            USER_BALANCE[user_key]["suspended_reason"] = reason
            USER_BALANCE[user_key]["suspended_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            USER_BALANCE[user_key] = {"balance": USER_BALANCE[user_key], "status": "suspended", "suspended_reason": reason, "suspended_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_balance(USER_BALANCE)
        return {"code": 200, "msg": "密钥已暂停", "user_key": user_key}

# 启用密钥
@app.post("/admin/resume-key")
async def resume_key(admin_pwd: str, user_key: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    with lock:
        if user_key not in USER_BALANCE:
            return {"code": 400, "msg": "密钥不存在"}
        if isinstance(USER_BALANCE[user_key], dict):
            USER_BALANCE[user_key]["status"] = "active"
            USER_BALANCE[user_key].pop("suspended_reason", None)
            USER_BALANCE[user_key].pop("suspended_at", None)
        else:
            USER_BALANCE[user_key] = {"balance": USER_BALANCE[user_key], "status": "active"}
        save_balance(USER_BALANCE)
        return {"code": 200, "msg": "密钥已启用", "user_key": user_key}

# 查看密钥详情
@app.get("/admin/key-detail")
async def key_detail(admin_pwd: str, user_key: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    if user_key not in USER_BALANCE:
        return {"code": 400, "msg": "密钥不存在"}
    data = USER_BALANCE[user_key]
    if isinstance(data, dict):
        return {"code": 200, "user_key": user_key, "balance": data.get("balance", 0), "status": data.get("status", "active"), "suspended_reason": data.get("suspended_reason", ""), "suspended_at": data.get("suspended_at", ""), "create_date": data.get("create_date", "")}
    return {"code": 200, "user_key": user_key, "balance": data, "status": "active", "suspended_reason": "", "suspended_at": "", "create_date": ""}

# 查看全部订单
@app.get("/admin/all-order")
async def get_all_order(admin_pwd: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    global PAY_ORDER_LIST
    PAY_ORDER_LIST = clean_expire_orders(PAY_ORDER_LIST)
    save_orders(PAY_ORDER_LIST)
    return {"code": 200, "data": PAY_ORDER_LIST}

# 导出余额CSV（Excel可直接打开）
@app.get("/admin/export-balance")
async def export_balance(admin_pwd: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = EXPORT_DIR / f"余额数据表_{now_str}.csv"
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["客户密钥","剩余流量(万Token)"])
        for k,v in USER_BALANCE.items():
            writer.writerow([k, round(v,2)])
    return {"code":200,"msg":"余额导出成功","file_path":str(file_path)}

# 导出订单CSV
@app.get("/admin/export-order")
async def export_order(admin_pwd: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = EXPORT_DIR / f"订单数据表_{now_str}.csv"
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["订单号","客户昵称","金额","赠送流量","绑定密钥","订单状态","创建时间"])
        for item in PAY_ORDER_LIST:
            writer.writerow([
                item["order_no"],
                item["nickname"],
                item["money"],
                item["init_flow"],
                item["bind_key"],
                item["status"],
                item["create_time"]
            ])
    return {"code":200,"msg":"订单导出成功","file_path":str(file_path)}

# 重置用户余额
@app.post("/admin/reset-balance")
async def reset_balance(admin_pwd: str, token_key: str, new_balance: float):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    with lock:
        old_balance = USER_BALANCE.get(token_key, 0)
        USER_BALANCE[token_key] = {"balance": new_balance, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d")} if not isinstance(USER_BALANCE.get(token_key), dict) else {**USER_BALANCE[token_key], "balance": new_balance}
        save_balance(USER_BALANCE)
        return {"code":200,"msg":"余额重置成功","token_key":token_key,"old_balance":old_balance,"new_balance":new_balance}

# 查询订单状态
@app.get("/admin/order-status")
async def order_status(admin_pwd: str, order_no: str):
    if not check_admin_pwd(admin_pwd):
        raise HTTPException(status_code=403, detail="管理员密码错误")
    for order in PAY_ORDER_LIST:
        if order["order_no"] == order_no:
            return {"code": 200, "order": order}
    return {"code": 400, "msg": "订单不存在"}

# 内部接口 - 注册Token密钥（供其他服务调用）
@app.post("/internal/register-token")
async def register_token(internal_key: str, openid: str, token_key: str, flow: float = 0):
    if internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="内部密钥验证失败")
    with lock:
        if token_key in USER_BALANCE:
            bal = USER_BALANCE[token_key]
            if isinstance(bal, dict):
                bal["balance"] += flow
            else:
                USER_BALANCE[token_key] = {"balance": bal + flow, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d"), "openid": openid}
        else:
            USER_BALANCE[token_key] = {"balance": flow, "status": "active", "create_date": datetime.now().strftime("%Y-%m-%d"), "openid": openid}
        save_balance(USER_BALANCE)
        return {"code": 200, "msg": "注册成功", "token_key": token_key, "balance": flow}

# 健康检测
@app.get("/")
async def health_check():
    return {
        "status":"running",
        "note":"合规AI服务系统-包月套餐+精准扣费+密钥管控"
    }

# 调试路由 - 捕获所有未匹配的请求（放在最后，只捕获未匹配业务路由的请求）
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def debug_route(path: str, request: Request):
    print(f"[DEBUG] 收到请求: {request.method} /{path}")
    print(f"[DEBUG] Headers: {dict(request.headers)}")
    try:
        body = await request.body()
        print(f"[DEBUG] Body: {body.decode()}")
    except:
        pass
    return {"error": "not_found", "path": f"/{path}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)