# Agent Backend 部署与使用指南

## 一、系统概述

Agent Backend 是 Token 代理系统的核心后端服务，负责：
- API 请求转发（OpenAI 格式）
- 用户密钥鉴权与余额管理
- 自动流量扣减
- IP 限流保护
- 订单管理与导出

---

## 二、目录结构

```
agent-backend/
├── main.py              # 主程序
├── config.py            # 配置文件
├── run.sh               # 启动脚本
├── requirements.txt     # Python 依赖
├── tokenproxy.service   # systemd 服务文件
├── data/               # 数据目录（自动创建）
│   ├── balance.json     # 用户余额数据
│   └── order.json       # 订单数据
└── export/              # 导出目录（自动创建）
    └── *.csv           # 导出的表格
```

---

## 三、配置说明

编辑 `main.py` 或 `config.py` 中的以下配置项：

### 必填配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `UPSTREAM_API_KEY` | 上游 API 密钥 | `sk-xxxxxx` |
| `UPSTREAM_API_URL` | 上游 API 地址 | `https://api.deepseek.com/v1/chat/completions` |
| `ADMIN_PWD` | 管理员密码 | 环境变量 `ADMIN_PWD`（请修改）|

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `TIMEOUT_SECONDS` | 请求超时时间（秒） | `120` |
| `LIMIT_PER_MIN` | 单 IP 每分钟最大请求数 | `80` |
| `AVG_CONSUME_WAN_TOKEN` | 单次请求扣减流量（万Token） | `0.05` |
| `ORDER_EXPIRE_MIN` | 订单过期时间（分钟） | `60` |
| `PRICE_PACKAGE` | 套餐定价 {金额: 流量} | `{9.9: 500, 49: 4000, 188: 15000}` |

---

## 四、部署步骤

### 方式一：直接运行

```bash
# 1. 安装依赖
pip install fastapi uvicorn httpx

# 2. 创建数据目录
mkdir -p data export

# 3. 编辑配置
vim main.py  # 修改 UPSTREAM_API_KEY 等

# 4. 启动服务
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 方式二：使用脚本

```bash
chmod +x run.sh
./run.sh
```

### 方式三：systemd 服务（推荐生产环境）

```bash
# 1. 复制服务文件
cp tokenproxy.service /etc/systemd/system/

# 2. 重载 systemd
systemctl daemon-reload

# 3. 启动服务
systemctl start tokenproxy

# 4. 设置开机自启
systemctl enable tokenproxy

# 5. 查看状态
systemctl status tokenproxy
```

## 五、Nginx反向代理+HTTPS配置
### 1. Nginx站点配置 `/etc/nginx/sites-available/proxy.conf`
```nginx
server {
    listen 80;
    server_name 你的域名.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name 你的域名.com;

    ssl_certificate /etc/letsencrypt/live/你的域名.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/你的域名.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```
启用站点：
```bash
ln -s /etc/nginx/sites-available/proxy.conf /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 2. 免费SSL证书申请
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d 你的域名.com
```

---

## 六、接口说明

### 1. 核心转发接口（用户调用）

**请求**
```
POST /v1/chat/completions
Authorization: Bearer <用户密钥>
Content-Type: application/json

{
  "model": "gpt-3.5-turbo",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

**响应**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "choices": [...]
}
```

### 2. 用户查余额

```
GET /user/balance?token_key=<用户密钥>
```

**响应**
```json
{
  "code": 200,
  "user_key": "tk20240101001",
  "remain_wan_token": 500.0,
  "tip": "流量充足"
}
```

### 3. 管理员接口

| 接口 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/admin/create-order` | POST | admin_pwd, nickname, money, bind_key | 创建订单 |
| `/admin/pay-success` | POST | admin_pwd, order_no | 确认付款充值 |
| `/admin/all-order` | GET | admin_pwd | 查看全部订单 |
| `/admin/export-balance` | GET | admin_pwd | 导出余额 CSV |
| `/admin/export-order` | GET | admin_pwd | 导出订单 CSV |
| `/` | GET | 无 | 健康检测 |

---

## 七、使用流程

### 1. 初始化用户

首次使用需要在 `balance.json` 中添加用户密钥和初始流量：

```json
{
  "tk20240101001": 500,
  "tk20240101002": 4000,
  "tk20240101003": 15000
}
```

### 2. 客户下单流程

1. **创建订单**（管理员操作）
   ```
   POST /admin/create-order?admin_pwd=密码&nickname=客户昵称&money=49&bind_key=tk20240101001
   ```
   返回：
   ```json
   {
     "code": 200,
     "order_info": {
       "order_no": "ORD20240101120000",
       "nickname": "张三",
       "money": 49,
       "init_flow": 4000,
       "bind_key": "tk20240101001",
       "status": "待付款",
       "create_time": "2024-01-01 12:00:00"
     }
   }
   ```

2. **客户付款**

3. **确认到账**（管理员操作）
   ```
   POST /admin/pay-success?admin_pwd=密码&order_no=ORD20240101120000
   ```
   系统自动给对应密钥加流量

### 3. 客户使用

客户使用自己的密钥调用接口：
```
curl -X POST https://你的域名/v1/chat/completions \
  -H "Authorization: Bearer tk20240101001" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

每次调用自动扣减 0.05 万Token

### 4. 导出数据

```
GET /admin/export-balance?admin_pwd=密码
GET /admin/export-order?admin_pwd=密码
```

---

## 八、数据文件格式

### balance.json（用户余额）
```json
{
  "密钥": 剩余流量(万Token)
}
```

### order.json（订单记录）
```json
[
  {
    "order_no": "ORD20240101120000",
    "nickname": "张三",
    "money": 49,
    "init_flow": 4000,
    "bind_key": "tk20240101001",
    "status": "已付款已发货",
    "create_time": "2024-01-01 12:00:00"
  }
]
```

---

## 九、注意事项

1. **安全修改密码**：请务必将 `ADMIN_PWD` 修改为强密码
2. **数据备份**：定期备份 `data/` 目录下的 JSON 文件
3. **流量监控**：余额低于 100 万Token 时会自动预警
4. **订单过期**：未付款订单 60 分钟后自动过期
5. **IP 限流**：单个 IP 每分钟超过 80 次请求会被拒绝

---

## 十、故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 401 无效密钥 | 密钥不在 balance.json 中 | 添加密钥 |
| 403 流量耗尽 | 余额不足 | 管理员充值 |
| 500 上游异常 | API Key 无效或网络问题 | 检查 UPSTREAM_API_KEY |
| 无法启动 | 端口被占用 | 检查端口或改端口 |
| 导出失败 | export 目录无权限 | chmod 777 export |