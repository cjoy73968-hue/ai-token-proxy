# AI Token 代理服务系统

一套功能完善的 AI Token 代理服务系统，支持多模型路由、精准配额计费、微信支付集成，适合个人或企业搭建 AI API 代理服务。

## 功能特性

- **多模型支持**：支持 DeepSeek、GPT-4、GLM-4、Kimi、MiniMax 等主流 AI 模型
- **智能路由**：根据请求模型自动路由到对应上游服务商
- **精准计费**：基于 Token 消耗的精确配额扣费
- **微信支付**：集成微信支付，支持套餐购买和自动充值
- **用户管理**：密钥生成、余额查询、暂停/恢复功能
- **订阅消息**：支付成功后自动推送微信订阅消息通知
- **套餐灵活**：支持多种套餐，不同套餐包含不同模型
- **数据导出**：支持余额和订单的 CSV 导出

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   微信小程序     │────▶│  小程序后端     │────▶│   Agent 后端    │
│   (用户端)      │     │   (端口 8080)   │     │   (端口 8000)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                       │
                               ▼                       ▼
                        微信支付商户               上游 AI 服务商
                        (收款)                      (API调用)
```

## 目录结构

```
ai-token-proxy/
├── LICENSE                    # GPL 3.0 开源协议
├── README.md                  # 本文件
├── DISCLAIMER.md              # 免责声明
├── docs/                      # 文档目录
│   ├── requirements/          # 需求规格说明
│   └── operations/            # 运营管理手册
├── agent-backend/             # Agent 后端（API代理服务）
│   ├── main.py                # 主程序
│   ├── requirements.txt       # Python 依赖
│   ├── data/                  # 数据存储
│   └── export/                # 导出文件
├── mini-program-backend/      # 小程序后端（支付/用户管理）
│   ├── main.py                # 主程序
│   ├── config.py              # 配置文件
│   ├── requirements.txt       # Python 依赖
│   └── data/                  # 数据存储
└── mini-program-frontend/     # 微信小程序前端
    ├── app.js                 # 小程序入口
    └── pages/                 # 页面目录
```

## 环境要求

- Python 3.10+
- Linux 服务器（推荐 Ubuntu/CentOS）
- 微信小程序账号（需支持微信支付）
- 微信支付商户号
- 上游 AI 服务商 API Key

## 快速部署

### 1. 克隆代码

```bash
git clone https://github.com/your-repo/ai-token-proxy.git
cd ai-token-proxy
```

### 2. 安装依赖

```bash
# Agent 后端
cd agent-backend
pip install -r requirements.txt

# 小程序后端
cd ../mini-program-backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# Agent 后端环境变量
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export MINIMAX_API_KEY="your-minimax-api-key"
export ADMIN_PWD="your-admin-password"
export INTERNAL_API_KEY="your-internal-key"

# 小程序后端环境变量
export WX_APP_ID="your-wx-app-id"
export WX_APP_SECRET="your-wx-app-secret"
export WX_MCH_ID="your-mch-id"
export WX_API_V3_KEY="your-api-v3-key"
export INTERNAL_API_KEY="your-internal-key"
```

### 4. 启动服务

```bash
# 启动 Agent 后端（端口 8000）
cd agent-backend
python main.py

# 启动小程序后端（端口 8080）
cd mini-program-backend
python main.py
```

### 5. Nginx 配置反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Agent 后端（端口 8000）
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 小程序后端（端口 8080）
    location /mini/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
    }
}
```

## 配置说明

### Agent 后端配置 (agent-backend/main.py)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API密钥 | 环境变量 |
| OPENAI_API_KEY | OpenAI API密钥 | 环境变量 |
| ZHIPU_API_KEY | 智谱 API密钥 | 环境变量 |
| MOONSHOT_API_KEY | Kimi API密钥 | 环境变量 |
| MINIMAX_API_KEY | MiniMax API密钥 | 环境变量 |
| ADMIN_PWD | 管理员密码 | 环境变量 |
| INTERNAL_API_KEY | 内部通信密钥 | 环境变量 |
| DEFAULT_MODEL | 默认模型 | MiniMax-M2.7 |
| LIMIT_PER_MIN | IP限流（次/分钟） | 80 |

### 小程序后端配置 (mini-program-backend/config.py)

| 配置项 | 说明 |
|--------|------|
| WX_APP_ID | 微信小程序 AppID |
| WX_APP_SECRET | 微信小程序 AppSecret |
| WX_MCH_ID | 微信支付商户号 |
| WX_API_V3_KEY | 微信支付 APIv3密钥 |
| WX_NOTIFY_URL | 支付回调地址（需HTTPS） |
| WX_SUB_MSG_TEMPLATE_ID | 订阅消息模板ID |
| AGENT_BACKEND_URL | Agent 后端地址 |
| INTERNAL_API_KEY | 与Agent后端通信密钥 |

### 套餐配置

| 价格 | 名称 | 配额 | 包含模型 |
|------|------|------|----------|
| 9.9 | 体验版 | 500万Token | MiniMax-M2.7 |
| 299 | 基础版 | 1000万Token | MiniMax-M2.7 |
| 499 | 标准版 | 3000万Token | MiniMax-M2.7, DeepSeek, GLM-4 |
| 899 | 企业版 | 10000万Token | 全部模型 |

## API 接口

### 用户 API

| 接口 | 方法 | 说明 |
|------|------|------|
| POST /v1/chat/completions | POST | AI 对话（需 Bearer Token） |
| GET /user/balance | GET | 查询余额 |
| GET /models/list | GET | 获取模型列表 |
| GET /user/model-usage | GET | 获取使用统计 |

### 管理 API

| 接口 | 方法 | 说明 |
|------|------|------|
| GET /admin/all-balance | GET | 查看所有余额 |
| GET /admin/all-order | GET | 查看所有订单 |
| POST /admin/pause-key | POST | 暂停密钥 |
| POST /admin/resume-key | POST | 恢复密钥 |
| POST /admin/reset-balance | POST | 重置余额 |
| GET /admin/export-balance | GET | 导出余额CSV |
| GET /admin/export-order | GET | 导出订单CSV |

## Token 计算规则

```
实际消耗配额 = (请求Token数 + 响应Token数) / 10000 × 模型比例
```

**模型消耗比例：**

| 模型 | 比例 |
|------|------|
| DeepSeek Chat | 1.0 |
| MiniMax M2.7 | 1.0 |
| GLM-4 | 1.2 |
| Kimi Moonshot | 1.5 |
| GPT-4 | 3.0 |

## 运营管理

详细的运营管理手册请参考：[docs/operations/OPS_MANUAL.md](docs/operations/OPS_MANUAL.md)

### 常用命令

```bash
# 查看用户余额
curl "http://localhost:8000/admin/all-balance?admin_pwd=你的密码"

# 暂停用户
curl -X POST "http://localhost:8000/admin/pause-key" \
  -d "admin_pwd=你的密码&user_key=用户密钥&reason=违规"

# 恢复用户
curl -X POST "http://localhost:8000/admin/resume-key" \
  -d "admin_pwd=你的密码&user_key=用户密钥"

# 重置余额
curl -X POST "http://localhost:8000/admin/reset-balance" \
  -d "admin_pwd=你的密码&token_key=用户密钥&new_balance=1000"
```

## 常见问题

### Q: 微信支付回调接收不到？
- 确保回调地址使用 HTTPS
- 检查防火墙是否开放 443 端口
- 查看服务日志确认请求是否到达

### Q: 用户API调用返回403？
- 检查用户余额是否充足
- 检查用户密钥是否被暂停
- 查看日志确认具体错误原因

### Q: 上游API返回错误？
- 检查上游服务商API Key是否正确
- 检查网络是否可达
- 查看日志获取详细错误信息

## 开源协议

本项目采用 **GNU General Public License v3.0** 开源协议。

详细内容请查看 [LICENSE](LICENSE) 文件。

## 免责声明

使用本软件请遵守当地法律法规，不得用于任何违规用途。

详细内容请查看 [DISCLAIMER.md](DISCLAIMER.md)。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请通过 GitHub Issues 联系。

![联系方式](docs/assets/image.png)