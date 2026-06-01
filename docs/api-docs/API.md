# API 接口文档

## Agent 后端接口 (端口 8000)

### 模型相关接口

#### 获取可用模型列表
```
GET /models/available?token_key=xxx
```

**响应：**
```json
{
  "code": 200,
  "models": [
    {
      "id": "MiniMax-M2.7",
      "name": "MiniMax M2.7",
      "ratio": 1.0,
      "enabled": true
    },
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "ratio": 1.0,
      "enabled": true
    }
  ]
}
```

#### 获取所有模型列表
```
GET /models/list
```

**响应：**
```json
{
  "code": 200,
  "models": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "ratio": 1.0,
      "enabled": true
    },
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "ratio": 3.0,
      "enabled": false
    }
  ]
}
```

#### 获取用户模型使用统计
```
GET /user/model-usage?token_key=xxx
```

**响应：**
```json
{
  "code": 200,
  "model_usage": {
    "deepseek-chat": 45,
    "gpt-4": 12,
    "glm-4": 28
  }
}
```

#### 查询用户余额
```
GET /user/balance?token_key=xxx
```

**响应：**
```json
{
  "code": 200,
  "user_key": "xxx",
  "remain_wan_token": 850.5,
  "status": "active",
  "tip": "服务配额充足",
  "model_usage": {
    "deepseek-chat": 45,
    "gpt-4": 12
  }
}
```

### Chat 转发接口

#### AI 对话转发
```
POST /v1/chat/completions
Authorization: Bearer <token_key>
Content-Type: application/json

{
  "model": "deepseek-chat",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "stream": false
}
```

**说明：**
- `model` 字段可选，不填则使用默认模型
- 支持的模型：`deepseek-chat`, `gpt-4`, `glm-4`, `moonshot-v1-8k`, `MiniMax-M2.7`
- 不同模型有不同的配额消耗比例（见下方）

**配额消耗比例：**
| 模型 | 比例 |
|------|------|
| deepseek-chat | 1.0x |
| MiniMax-M2.7 | 1.0x |
| glm-4 | 1.2x |
| moonshot-v1-8k | 1.5x |
| gpt-4 | 3.0x |

### 管理接口

#### 暂停密钥
```
POST /admin/pause-key?admin_pwd=xxx&user_key=xxx&reason=xxx
```

#### 恢复密钥
```
POST /admin/resume-key?admin_pwd=xxx&user_key=xxx
```

#### 密钥详情
```
GET /admin/key-detail?admin_pwd=xxx&user_key=xxx
```

#### 重置余额
```
POST /admin/reset-balance?admin_pwd=xxx&token_key=xxx&new_balance=1000
```

#### 订单状态查询
```
GET /admin/order-status?admin_pwd=xxx&order_no=xxx
```

---

## 小程序后端接口 (端口 8080)

### 用户接口

#### 获取 OpenID
```
GET /api/get-openid?code=xxx
```

**响应：**
```json
{
  "openid": "oxxxxxxxx"
}
```

#### 创建支付订单
```
POST /api/create-pay-order
Content-Type: application/json

{
  "openid": "oxxxxxxxx",
  "goodsId": 299,
  "totalFee": 29900,
  "body": "基础版"
}
```

#### 查询订单列表
```
GET /api/order-list?openid=xxx
```

#### 查询余额
```
GET /api/balance?openid=xxx
```

**响应：**
```json
{
  "code": 200,
  "flow": 850
}
```

#### 获取套餐列表（包含模型）
```
GET /api/packages
```

**响应：**
```json
{
  "code": 200,
  "packages": [
    {
      "price": 299,
      "name": "基础版",
      "service_quota": 1000,
      "models": ["MiniMax-M2.7"],
      "default_model": "MiniMax-M2.7",
      "description": "智能咨询+文案辅助（个人/自媒体）"
    },
    {
      "price": 499,
      "name": "标准版",
      "service_quota": 3000,
      "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4"],
      "default_model": "MiniMax-M2.7",
      "description": "营销文案+活动策划+日常咨询"
    },
    {
      "price": 899,
      "name": "企业版",
      "service_quota": 10000,
      "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4", "moonshot-v1-8k", "gpt-4"],
      "default_model": "MiniMax-M2.7",
      "description": "全场景智能服务+技术支持"
    }
  ]
}
```

#### 获取模型列表
```
GET /api/models
```

**响应：**
```json
{
  "code": 200,
  "models": [
    {
      "id": "MiniMax-M2.7",
      "name": "MiniMax M2.7",
      "ratio": 1.0
    },
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "ratio": 1.0
    }
  ]
}
```

#### 获取用户套餐信息
```
GET /api/user-package?openid=xxx
```

**响应：**
```json
{
  "code": 200,
  "package_price": 499,
  "package_name": "标准版",
  "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4"],
  "default_model": "MiniMax-M2.7",
  "service_quota": 3000
}
```

#### 获取用户模型使用统计
```
GET /api/model-usage?openid=xxx
```

**响应：**
```json
{
  "code": 200,
  "model_usage": {
    "deepseek-chat": 45,
    "gpt-4": 12
  }
}
```

### 支付回调
```
POST /api/pay-notify
Content-Type: application/json

{
  "trade_state": "SUCCESS",
  "out_trade_no": "XCxxxxxx",
  "payer": {"openid": "oxxxxxxxx"},
  "amount": {"total": 29900}
}
```

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 无效密钥 |
| 403 | 拒绝访问（密钥暂停/无权限） |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 模型不可用 |