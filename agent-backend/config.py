# ===================== Agent Backend Configuration =====================

# 上游 API 配置
UPSTREAM_API_KEY = "sk-your-kimi-api-key"
# UPSTREAM_API_URL = "https://api.deepseek.com/v1/chat/completions"
UPSTREAM_API_URL = "https://api.minimaxi.com/anthropic"
TIMEOUT_SECONDS = 120

# 风控配置
LIMIT_PER_MIN = 80
AVG_CONSUME_WAN_TOKEN = 0.05

# 管理员配置
ADMIN_PWD = "123456"

# 订单配置
ORDER_EXPIRE_MIN = 60

# 套餐定价 (金额: 流量)
PRICE_PACKAGE = {
    9.9: 1150,
    49: 6000,
    188: 23000
}

# 服务配置
HOST = "0.0.0.0"
PORT = 8000