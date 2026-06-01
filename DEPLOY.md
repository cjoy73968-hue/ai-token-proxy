# AI 服务系统部署指南

## 目录

1. [系统架构](#系统架构)
2. [前置准备清单](#前置准备清单)
3. [域名申请与配置](#域名申请与配置)
4. [微信小程序注册](#微信小程序注册)
5. [微信支付商户号申请](#微信支付商户号申请)
6. [上游 AI 服务申请](#上游-ai-服务申请)
7. [服务器部署](#服务器部署)
8. [小程序前端配置](#小程序前端配置)
9. [系统配置详解](#系统配置详解)
10. [常见问题](#常见问题)

---

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   小程序前端     │────▶│   小程序后端     │────▶│   Agent 后端     │
│  (微信小程序)    │     │   (端口 8080)    │     │   (端口 8000)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
    用户界面              支付/订单处理              AI服务转发
                              │                       │
                              ▼                       ▼
                    ┌─────────────────┐       ┌─────────────────┐
                    │   微信支付      │       │   MiniMax/DeepSeek│
                    │   商户平台      │       │   等上游 API     │
                    └─────────────────┘       └─────────────────┘
```

---

## 前置准备清单

| 序号 | 项目 | 费用 | 预计时间 |
|------|------|------|----------|
| 1 | 域名（已备案） | 30-60元/年 | 1-7天 |
| 2 | 服务器 | 100-500元/月 | 即时 |
| 3 | 微信小程序 | 30元/年 | 1-3天 |
| 4 | 微信支付商户号 | 免费 | 3-7天 |
| 5 | 上游 AI API Key | 按量计费 | 即时 |

---

## 域名申请与配置

### 1.1 域名注册

1. **选择域名注册商**
   - 阿里云（万网）：https://www.aliyun.com
   - 腾讯云：https://cloud.tencent.com
   - 华为云：https://www.huaweicloud.com

2. **搜索并注册域名**
   ```
   推荐域名格式：
   - ai服务.中国 (xn--ai-hn0cn.xn--fiqs8s)
   - yourbrand.com
   - yourbrand.cn
   ```

3. **价格参考**
   - .com 域名：约 60元/年
   - .cn 域名：约 30元/年
   - 首次注册通常有优惠

### 1.2 域名备案

**必须备案才能使用国内服务器**

1. **备案入口**
   - 阿里云：https://beian.aliyun.com
   - 腾讯云：https://cloud.tencent.com/product/ba

2. **备案流程**
   ```
   1. 注册备案账号
   2. 填写网站信息
      - 网站名称：AI智能服务
      - 域名：yourdomain.com
      - 网站性质：企业/个人
   3. 上传证件
      - 企业：营业执照、法人身份证
      - 个人：身份证
   4. 真实性核验
      - 需拍照上传幕布照或本地核验
   5. 接入服务商审核（1-2天）
   6. 管局审核（5-20天）
   ```

3. **备案期间**
   - 可使用香港/海外服务器临时访问
   - 备案成功后需将网站迁移至国内服务器

### 1.3 DNS 解析配置

1. **添加域名解析**
   ```
   登录域名管理控制台 → DNS解析 → 添加记录
   
   记录类型：A记录
   主机记录：
   - @     → 服务器 IP（主域名）
   - www   → 服务器 IP
   - api   → 服务器 IP（小程序 API）
   - pay   → 服务器 IP（支付回调）
   
   记录类型：CNAME（可选）
   主机记录：
   - *     → 泛解析
   ```

2. **配置 SSL 证书（免费）**
   ```
   推荐使用 Let's Encrypt 免费证书
   或在阿里云/腾讯云申请免费 Symantecc 证书
   ```

### 1.4 申请 SSL 证书

**方法一：Let's Encrypt（推荐，免费）**

```bash
# 安装 certbot
yum install certbot python3-certbot-nginx  # CentOS
apt install certbot python3-certbot-nginx  # Ubuntu

# 申请证书（需要域名已解析到服务器）
certbot --nginx -d yourdomain.com -d api.yourdomain.com

# 自动续期
certbot renew --dry-run
```

**方法二：阿里云/腾讯云免费证书**

1. 登录云控制台
2. 搜索 "SSL 证书"
3. 选择 "免费型 DV SSL"
4. 填写域名信息
5. DNS 验证（自动添加 TXT 记录）
6. 审核通过后下载证书

---

## 微信小程序注册

### 2.1 注册小程序账号

1. **注册地址**：https://mp.weixin.qq.com/
2. **账号类型选择**：根据业务需求选择「个人」或「企业/个体户」

| 类型 | 费用 | 功能限制 |
|------|------|----------|
| 个人 | 免费 | 无法使用微信支付 |
| 企业/个体户 | 30元/年 | 可使用微信支付 |

**强烈建议注册「企业/个体户」小程序**，否则无法接入微信支付。

### 2.2 获取 AppID 和 AppSecret

1. 登录微信公众平台：https://mp.weixin.qq.com/
2. 进入「开发」→「开发管理」→「开发设置」
3. 获取以下信息：
   ```
   AppID（小程序 ID）：wxfxxxxxxxxxxxxxxxx
   AppSecret（小程序密钥）：xxxxxxxxxxxxxxxxxxxxxxxx
   ```

**注意**：
- AppSecret 只显示一次，请妥善保存
- 如忘记需重新生成

### 2.3 配置服务器域名

1. 进入「开发」→「开发管理」→「开发设置」
2. 找到「服务器域名」
3. 点击「修改」，添加以下合法域名：
   ```
   request 合法域名：https://api.yourdomain.com
   wss    合法域名：wss://api.yourdomain.com
   uploadFile 合法域名：https://api.yourdomain.com
   downloadFile合法域名：https://api.yourdomain.com
   ```

### 2.4 添加订阅消息模板

1. 进入「功能」→「订阅消息」
2. 点击「添加消息模板」
3. 搜索并添加「支付成功通知」模板
4. 获取模板 ID：
   ```
   模板标题：支付成功通知
   模板ID：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 微信支付商户号申请

### 3.1 申请入口

**地址**：https://pay.weixin.qq.com/

### 3.2 商户号类型

| 类型 | 费用 | 需要资质 |
|------|------|----------|
| 普通商户 | 免费 | 营业执照（企业/个体户） |
| 特约商户 | 免费 | 需要通过服务商 |

### 3.3 申请步骤

1. **提交商户信息**
   ```
   1. 登录微信支付商户平台
   2. 点击「成为商户」
   3. 填写企业/个体户信息
   4. 上传营业执照
   ```

2. **对公账户验证**
   ```
   微信支付会向你的对公账户打一笔几分钱的验证款项
   需要在系统中输入验证金额完成认证
   ```

3. **签署协议**
   阅读并签署《微信支付服务协议》

### 3.4 获取商户号配置信息

登录商户平台后，在「账户中心」→「商户信息」获取：

```
商户号（MCH_ID）：1xxxxxxxxxx
```

在「账户中心」→「API安全」设置：

```
APIv3 密钥：32位字符串（自行设置）
证书密钥：下载证书文件
```

### 3.5 配置支付回调地址

1. 进入「交易设置」→「Native 反馈消息」
2. 点击「支付回调」
3. 填写回调地址：
   ```
   https://api.yourdomain.com/admin/pay-notify
   ```

**注意**：回调地址必须使用 HTTPS

---

## 上游 AI 服务申请

### 4.1 MiniMax（推荐，已配置）

**官网**：https://www.minimax.chat/

1. 注册并登录 MiniMax 控制台
2. 进入「API keys」创建新的 API Key
3. 获取 API Key：
   ```
   sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 4.2 DeepSeek（备选）

**官网**：https://platform.deepseek.com/

1. 注册并登录 DeepSeek 开放平台
2. 进入「API keys」创建新的 Key
3. 获取 API Key

### 4.3 其他可选服务商

| 服务商 | 模型 | 价格 | 特点 |
|--------|------|------|------|
| 智谱 GLM | glm-4 | 中等 | 国内稳定 |
| 百度文心 | ernie-4.0 | 较高 | 强中文理解 |
| Kimi | moonshot-v1 | 中等 | 长上下文 |

---

## 服务器部署

### 5.1 服务器推荐配置

| 配置 | 适用场景 | 价格/月 |
|------|----------|---------|
| 1核2G | 测试/小规模 | 50-100元 |
| 2核4G | 生产环境 | 100-200元 |
| 4核8G | 大规模 | 200-400元 |

**推荐云服务商**：
- 阿里云 ECS
- 腾讯云 CVM
- 华为云 ECS

### 5.2 服务器环境准备

```bash
# 更新系统
yum update -y  # CentOS
apt update && apt upgrade -y  # Ubuntu

# 安装 Python 3.10+
yum install python3 python3-pip -y  # CentOS
apt install python3 python3-pip -y  # Ubuntu

# 创建项目目录
mkdir -p /var/www/ai-service
cd /var/www/ai-service

# 克隆代码（如果有 Git）
# git clone https://your-repo/ai-service.git .

# 或使用 FTP/SFTP 上传代码
```

### 5.3 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install fastapi uvicorn httpx tiktoken python-multipart

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 5.4 配置 Agent 后端（多模型配置）

编辑 `/var/www/ai-service/agent-backend/main.py`：

```python
# ===================== 多上游服务商配置 =====================

# 支持多模型配置，根据请求的 model 字段自动路由
UPSTREAM_PROVIDERS = {
    "deepseek-chat": {
        "name": "DeepSeek Chat",
        "api_key": "sk-your-deepseek-api-key",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "rate_limit": 100,
        "enabled": True
    },
    "gpt-4": {
        "name": "GPT-4",
        "api_key": "sk-your-openai-api-key",
        "url": "https://api.openai.com/v1/chat/completions",
        "rate_limit": 50,
        "enabled": False  # 启用需配置 API Key
    },
    "glm-4": {
        "name": "智谱 GLM-4",
        "api_key": "sk-your-zhipu-api-key",
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "rate_limit": 80,
        "enabled": False
    },
    "moonshot-v1-8k": {
        "name": "Kimi",
        "api_key": "sk-your-kimi-api-key",
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "rate_limit": 80,
        "enabled": False
    },
    "MiniMax-M2.7": {
        "name": "MiniMax M2.7",
        "api_key": "sk-your-minimax-api-key",
        "url": "https://api.minimax.chat/v1/chat/completions",
        "rate_limit": 100,
        "enabled": True
    }
}

# 默认模型
DEFAULT_MODEL = "MiniMax-M2.7"

# 模型配额消耗比例（不同模型消耗不同比例）
MODEL_RATIOS = {
    "deepseek-chat": 1.0,
    "MiniMax-M2.7": 1.0,
    "glm-4": 1.2,
    "moonshot-v1-8k": 1.5,
    "gpt-4": 3.0
}

# 管理员密码（修改默认密码！）
ADMIN_PWD = "your-secure-admin-password"

# 网关访问控制模式: "whitelist"=白名单模式, "open"=完全开放
GATEWAY_ACCESS_MODE = "whitelist"
WHITELIST_APP_IDS = ["你的小程序AppID"]  # 你的小程序 AppID

# 微信支付商户号配置
MCH_ID = "your-mch-id"
API_V3_KEY = "your-api-v3-key"
NOTIFY_URL = "https://api.yourdomain.com/admin/pay-notify"

# 套餐定价（包含模型列表）
PRICE_PACKAGE = {
    299: {
        "name": "基础版",
        "service_quota": 1000,
        "models": ["MiniMax-M2.7"],
        "default_model": "MiniMax-M2.7"
    },
    499: {
        "name": "标准版",
        "service_quota": 3000,
        "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4"],
        "default_model": "MiniMax-M2.7"
    },
    899: {
        "name": "企业版",
        "service_quota": 10000,
        "models": ["MiniMax-M2.7", "deepseek-chat", "glm-4", "moonshot-v1-8k", "gpt-4"],
        "default_model": "MiniMax-M2.7"
    }
}
```

**说明：**
- 不同模型有不同的配额消耗比例：GPT-4 消耗最高（3x），DeepSeek 和 MiniMax 消耗最低（1x）
- 可根据需要启用/禁用模型（设置 `enabled: True/False`）
- 套餐包含的模型数量决定用户可使用的模型范围

### 5.5 配置 Nginx 反向代理

```bash
# 安装 Nginx
yum install nginx -y  # CentOS
apt install nginx -y  # Ubuntu

# 启动 Nginx
systemctl start nginx
systemctl enable nginx
```

创建 Nginx 配置文件 `/etc/nginx/conf.d/ai-service.conf`：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # HTTP 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/yourdomain.com.pem;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Agent 后端（端口 8000）
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 小程序后端（端口 8080）
    location /mini/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# 测试配置
nginx -t

# 重载配置
systemctl reload nginx
```

### 5.6 配置 Systemd 服务

创建服务文件 `/etc/systemd/system/ai-agent.service`：

```ini
[Unit]
Description=AI Agent Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/ai-service/agent-backend
Environment="PATH=/var/www/ai-service/venv/bin"
ExecStart=/var/www/ai-service/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 重载 systemd
systemctl daemon-reload

# 启动服务
systemctl start ai-agent

# 设置开机启动
systemctl enable ai-agent

# 查看状态
systemctl status ai-agent

# 查看日志
journalctl -u ai-agent -f
```

### 5.7 配置小程序后端

编辑 `/var/www/ai-service/mini-program-backend/config.py`：

```python
# 微信小程序基础信息
APP_ID = "wxfxxxxxxxxxxxxxxxx"
APP_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxx"

# 微信支付商户信息
MCH_ID = "1xxxxxxxxxx"
API_V3_KEY = "your-api-v3-key"
NOTIFY_URL = "https://api.yourdomain.com/admin/pay-notify"

# 订阅消息模板ID
SUB_MSG_TEMPLATE_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 业务套餐配置
PRICE_PACKAGE = {
    299: {"name": "基础版", "service_quota": 1000},
    499: {"name": "标准版", "service_quota": 3000},
    899: {"name": "企业版", "service_quota": 10000}
}
```

创建小程序后端服务 `/etc/systemd/system/ai-mini.service`：

```ini
[Unit]
Description=AI Mini Program Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/ai-service/mini-program-backend
Environment="PATH=/var/www/ai-service/venv/bin"
ExecStart=/var/www/ai-service/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start ai-mini
systemctl enable ai-mini
```

---

## 小程序前端配置

### 6.1 修改后端地址

在微信开发者工具中打开小程序项目，找到 `app.js` 或 `app.json`：

```javascript
// app.js
App({
  globalData: {
    apiBase: 'https://api.yourdomain.com',  // 你的 API 域名
    templateId: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  // 订阅消息模板 ID
  }
})
```

### 6.2 配置服务器域名

确保已在微信公众平台「开发」→「开发设置」→「服务器域名」中添加：

```
request 合法域名：https://api.yourdomain.com
```

### 6.3 编译模式

在微信开发者工具中：
1. 点击「详情」
2. 选择「本地设置」
3. 勾选「不校验合法域名」（开发阶段）

**注意**：上线前必须关闭此选项

---

## 系统配置详解

### 7.1 配置文件位置

| 文件 | 说明 |
|------|------|
| `agent-backend/main.py` | Agent 后端主文件（包含配置） |
| `mini-program-backend/config.py` | 小程序后端配置 |

### 7.2 主要配置项说明

#### Agent 后端 (`main.py`)

```python
# 网关访问控制
GATEWAY_ACCESS_MODE = "whitelist"  # 白名单模式
WHITELIST_APP_IDS = ["小程序AppID"]  # 允许的小程序列表

# 改为 open 模式（完全开放，无需白名单）
GATEWAY_ACCESS_MODE = "open"

# 限流配置
LIMIT_PER_MIN = 80  # 每分钟最大请求数

# 订单过期时间（分钟）
ORDER_EXPIRE_MIN = 60
```

#### 小程序后端 (`config.py`)

```python
# 微信小程序信息
APP_ID = "小程序AppID"
APP_SECRET = "小程序AppSecret"

# 微信支付信息
MCH_ID = "商户号"
API_V3_KEY = "APIv3密钥"

# 回调地址（必须 HTTPS）
NOTIFY_URL = "https://你的域名/admin/pay-notify"

# 订阅消息模板
SUB_MSG_TEMPLATE_ID = "模板ID"
```

---

## 常见问题

### Q1: 微信支付回调接收不到

**可能原因**：
1. 回调地址无法公网访问
2. 回调地址不是 HTTPS
3. 防火墙未开放 443 端口

**解决方案**：
```bash
# 检查防火墙
firewall-cmd --list-ports
firewall-cmd --add-port=443/tcp --permanent
firewall-cmd --reload

# 测试回调地址是否可访问
curl -X POST https://api.yourdomain.com/admin/pay-notify
```

### Q2: 小程序调用 API 报 403 错误

**可能原因**：AppID 不在白名单中

**解决方案**：
```python
# 检查配置
GATEWAY_ACCESS_MODE = "whitelist"
WHITELIST_APP_IDS = ["你的小程序AppID"]
```

### Q3: 服务启动失败

**可能原因**：端口被占用

**解决方案**：
```bash
# 查看端口占用
netstat -tlnp | grep 8000
netstat -tlnp | grep 8080

# 杀死占用进程或修改端口
```

### Q4: 备案审核被拒绝

**常见原因**：
1. 网站名称不规范
2. 资料不清晰
3. 核验照不合格

**解决方案**：
- 网站名称使用「AI智能服务」等正式名称
- 重新拍摄核验照（白色背景，双手持身份证）
- 联系备案服务商客服

### Q5: SSL 证书申请失败

**可能原因**：域名未解析到服务器

**解决方案**：
```bash
# 确认域名已解析
ping api.yourdomain.com

# 确认 DNS 传播
dig api.yourdomain.com
```

---

## 费用汇总

| 项目 | 首次费用 | 续费/年 |
|------|----------|---------|
| 域名 | 30-60元 | 30-60元 |
| 服务器（2核4G） | - | 1200-2400元 |
| 小程序认证 | 30元 | 30元 |
| 微信支付 | 免费 | 免费 |
| SSL 证书 | 免费 | 免费 |
| 上游 API | 按量计费 | 按量计费 |

---

## 快速联系

如有部署问题，请检查：
1. 日志文件：`journalctl -u ai-agent -f`
2. Nginx 日志：`/var/log/nginx/error.log`
3. 微信商户平台交易账单
