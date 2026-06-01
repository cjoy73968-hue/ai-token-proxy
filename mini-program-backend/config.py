# AI Token 代理服务系统
# Copyright (C) 2026
# License: GNU General Public License v3.0
# https://www.gnu.org/licenses/

import os

# ===================== 微信小程序配置 =====================
# 请通过环境变量配置敏感信息，或参考部署文档

# 微信小程序基础信息（请在部署时配置）
APP_ID = os.getenv("WX_APP_ID", "YOUR_WX_APP_ID")
APP_SECRET = os.getenv("WX_APP_SECRET", "YOUR_WX_APP_SECRET")

# 微信支付商户信息（请在部署时配置）
MCH_ID = os.getenv("WX_MCH_ID", "YOUR_WX_MCH_ID")
API_V3_KEY = os.getenv("WX_API_V3_KEY", "YOUR_WX_API_V3_KEY")
NOTIFY_URL = os.getenv("WX_NOTIFY_URL", "https://your-domain.com/admin/pay-notify")

# 订阅消息模板ID
SUB_MSG_TEMPLATE_ID = os.getenv("WX_SUB_MSG_TEMPLATE_ID", "YOUR_SUB_MSG_TEMPLATE_ID")

# 业务套餐配置 (金额: 服务配额+模型列表)
PRICE_PACKAGE = {
    9.9: {
        "name": "体验版",
        "service_quota": 500,  # 500万Token
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

# 兼容性别名（用于价格到配额的映射）
PRICE_TO_FLOW = {
    9.9: 500,
    299: 1000,
    499: 3000,
    899: 10000
}

# 模型消耗比例
MODEL_RATIOS = {
    "deepseek-chat": 1.0,
    "MiniMax-M2.7": 1.0,
    "glm-4": 1.2,
    "moonshot-v1-8k": 1.5,
    "gpt-4": 3.0
}

# 可用模型列表
UPSTREAM_PROVIDERS = {
    "deepseek-chat": {"name": "DeepSeek Chat", "enabled": True},
    "gpt-4": {"name": "GPT-4", "enabled": False},
    "glm-4": {"name": "智谱 GLM-4", "enabled": False},
    "moonshot-v1-8k": {"name": "Kimi", "enabled": False},
    "MiniMax-M2.7": {"name": "MiniMax M2.7", "enabled": True}
}

# 服务配置
HOST = "0.0.0.0"
PORT = 8080

# Agent Backend配置
AGENT_BACKEND_URL = os.getenv("AGENT_BACKEND_URL", "http://localhost:8000")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "CHANGE_ME_INTERNAL_KEY")