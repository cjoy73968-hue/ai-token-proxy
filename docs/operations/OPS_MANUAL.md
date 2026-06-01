# AI Token 代理系统 - 运营管理手册

## 目录

1. [系统概述](#系统概述)
2. [日常运维操作](#日常运维操作)
3. [用户管理](#用户管理)
4. [财务管理](#财务管理)
5. [故障排查](#故障排查)
6. [安全风控](#安全风控)
7. [客服支持](#客服支持)

---

## 系统概述

### 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  小程序前端  │────▶│ 小程序后端  │────▶│ Agent 后端  │
│  (用户端)   │     │ (8080端口)  │     │ (8000端口)  │
└─────────────┘     └─────────────┘     └─────────────┘
                        │                     │
                        ▼                     ▼
                  微信支付商户           上游AI服务商
                  (收款)                 (DeepSeek/MiniMax等)
```

### 服务地址

| 服务 | 地址 | 用途 |
|------|------|------|
| Agent 后端 | http://localhost:8000 | AI API 代理服务 |
| 小程序后端 | http://localhost:8080 | 支付/订单/用户管理 |

### 关键文件路径

```
agent-backend/
├── main.py              # 主程序（含管理接口）
├── data/
│   ├── balance.json     # 用户余额/密钥数据
│   └── order.json       # 订单记录
└── export/              # 导出文件目录

mini-program-backend/
├── main.py              # 主程序
├── config.py            # 配置文件
└── data/
    ├── balance.json     # 小程序端用户余额
    └── order.json       # 小程序端订单
```

---

## 日常运维操作

### 启动/停止服务

```bash
# Agent 后端
cd /var/www/ai-service/agent-backend
python main.py                    # 启动
# 或使用 systemd
systemctl start ai-agent           # 启动
systemctl stop ai-agent            # 停止
systemctl restart ai-agent          # 重启

# 小程序后端
cd /var/www/ai-service/mini-program-backend
python main.py
# 或使用 systemd
systemctl start ai-mini
systemctl stop ai-mini
systemctl restart ai-mini
```

### 查看服务状态

```bash
# 查看服务状态
systemctl status ai-agent
systemctl status ai-mini

# 查看实时日志
journalctl -u ai-agent -f
journalctl -u ai-mini -f

# 查看 Python 进程
ps aux | grep python
```

### 查看用户数据

```bash
# 查看用户余额列表
curl "http://localhost:8000/admin/all-balance?admin_pwd=你的管理密码"

# 查看所有订单
curl "http://localhost:8000/admin/all-order?admin_pwd=你的管理密码"
```

---

## 用户管理

### 查询用户信息

```bash
# 查看单个密钥详情
curl "http://localhost:8000/admin/key-detail?admin_pwd=你的管理密码&user_key=用户密钥"

# 查看用户余额
curl "http://localhost:8000/api/balance?openid=用户openid"
```

### 手动添加/修改用户余额

```bash
# 重置用户余额
curl -X POST "http://localhost:8000/admin/reset-balance" \
  -d "admin_pwd=你的管理密码&token_key=用户密钥&new_balance=1000"

# 创建订单并手动充值
curl -X POST "http://localhost:8000/admin/create-order" \
  -d "admin_pwd=你的管理密码&nickname=用户名&money=299&bind_key=用户密钥"
```

### 暂停/恢复用户密钥

```bash
# 暂停用户密钥（限制使用）
curl -X POST "http://localhost:8000/admin/pause-key" \
  -d "admin_pwd=你的管理密码&user_key=用户密钥&reason=违规操作"

# 恢复用户密钥
curl -X POST "http://localhost:8000/admin/resume-key" \
  -d "admin_pwd=你的管理密码&user_key=用户密钥"
```

### 导出用户数据

```bash
# 导出用户余额数据
curl "http://localhost:8000/admin/export-balance?admin_pwd=你的管理密码"

# 导出订单数据
curl "http://localhost:8000/admin/export-order?admin_pwd=你的管理密码"
```

---

## 财务管理

### 查看营收数据

```bash
# 查看所有订单（按时间排序）
curl "http://localhost:8000/admin/all-order?admin_pwd=你的管理密码"

# 查看订单状态
curl "http://localhost:8000/admin/order-status?admin_pwd=你的管理密码&order_no=订单号"
```

### 微信支付对账

1. 登录微信支付商户平台：https://pay.weixin.qq.com
2. 进入「账户中心」→「交易账单」
3. 核对当日收入与系统订单

### 手动确认支付（异常情况处理）

如果用户支付成功但系统未到账：

```bash
# 查询订单状态
curl "http://localhost:8000/admin/order-status?admin_pwd=你的管理密码&order_no=订单号"

# 手动确认支付成功
curl -X POST "http://localhost:8000/admin/pay-success" \
  -d "admin_pwd=你的管理密码&order_no=订单号"
```

---

## 故障排查

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 8000
netstat -tlnp | grep 8080

# 检查端口被谁占用
lsof -i :8000

# 杀掉占用进程
kill -9 <PID>
```

### 用户无法使用 API

```bash
# 1. 检查服务是否运行
systemctl status ai-agent

# 2. 检查用户余额
curl "http://localhost:8000/admin/key-detail?admin_pwd=你的管理密码&user_key=用户密钥"

# 3. 检查用户状态是否被暂停
# 如果 status 为 suspended，需要恢复
curl -X POST "http://localhost:8000/admin/resume-key" \
  -d "admin_pwd=你的管理密码&user_key=用户密钥"
```

### 微信支付回调失败

```bash
# 1. 检查服务是否运行
systemctl status ai-mini

# 2. 检查回调地址是否可达
curl -X POST https://你的域名/admin/pay-notify -H "Content-Type: application/json" -d '{}'

# 3. 查看服务日志
journalctl -u ai-mini -f | grep pay
```

### 余额未同步到 Agent

```bash
# 1. 检查小程序后端是否配置了 Agent 后端地址
cat /var/www/ai-service/mini-program-backend/config.py | grep AGENT

# 2. 检查内部接口是否正常
curl -X POST "http://localhost:8000/internal/register-token" \
  -d "internal_key=internal_secret_key_12345&openid=test&token_key=test&flow=100"
```

### 数据库文件损坏

```bash
# 备份文件
cp data/balance.json data/balance.json.bak
cp data/order.json data/order.json.bak

# 检查 JSON 格式是否正确
python3 -c "import json; json.load(open('data/balance.json'))"

# 如果格式错误，可以从备份恢复
cp data/balance.json.bak data/balance.json
```

---

## 安全风控

### 修改管理员密码

编辑 `agent-backend/main.py`：

```python
# 找到以下行并修改
ADMIN_PWD = "新密码"
```

重启服务使配置生效：

```bash
systemctl restart ai-agent
```

### 修改内部通信密钥

1. 编辑 `agent-backend/main.py`：
```python
INTERNAL_API_KEY = "新内部密钥"
```

2. 编辑 `mini-program-backend/config.py`：
```python
INTERNAL_API_KEY = "新内部密钥"
```

3. 重启两个服务

### 限制接口访问

```python
# 修改网关模式为白名单
GATEWAY_ACCESS_MODE = "whitelist"
WHITELIST_APP_IDS = ["已授权的小程序AppID"]

# 或改为完全开放
GATEWAY_ACCESS_MODE = "open"
```

### 暂停可疑用户

```bash
# 暂停用户密钥
curl -X POST "http://localhost:8000/admin/pause-key" \
  -d "admin_pwd=你的管理密码&user_key=可疑密钥&reason=风控原因"
```

---

## 客服支持

### 常见用户问题

| 问题 | 解决方案 |
|------|----------|
| API 返回"服务配额已耗尽" | 用户余额不足，引导续费 |
| API 返回"无效代理密钥" | 检查密钥是否正确，联系客服 |
| API 返回"密钥已被暂停" | 联系客服，确认违规情况 |
| 支付后未到账 | 提供订单号，核查支付状态 |

### 用户密钥格式

密钥格式：`用户名_base64随机字符串`

例如：`zhangsan_a1b2c3d4e5f6`

用户可通过小程序「我的」页面查看密钥

### 套餐兑换流程

1. 用户在小程序购买套餐
2. 微信支付成功回调
3. 系统自动生成/更新用户密钥
4. 订阅消息通知用户密钥
5. 用户使用密钥调用 API

### 联系方式

- 技术支持：查看服务日志定位问题
- 商务咨询：查看订单和用户数据

---

## 快速命令参考

```bash
# 服务管理
systemctl start ai-agent ai-mini      # 启动
systemctl stop ai-agent ai-mini       # 停止
systemctl restart ai-agent ai-mini    # 重启
systemctl status ai-agent ai-mini     # 状态

# 查看数据
curl "http://localhost:8000/admin/all-balance?admin_pwd=密码"
curl "http://localhost:8000/admin/all-order?admin_pwd=密码"
curl "http://localhost:8000/admin/key-detail?admin_pwd=密码&user_key=密钥"

# 用户管理
curl -X POST "http://localhost:8000/admin/pause-key" -d "admin_pwd=密码&user_key=密钥&reason=原因"
curl -X POST "http://localhost:8000/admin/resume-key" -d "admin_pwd=密码&user_key=密钥"
curl -X POST "http://localhost:8000/admin/reset-balance" -d "admin_pwd=密码&token_key=密钥&new_balance=数量"

# 导出数据
curl "http://localhost:8000/admin/export-balance?admin_pwd=密码"
curl "http://localhost:8000/admin/export-order?admin_pwd=密码"
```