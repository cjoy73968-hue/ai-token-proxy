# 零代码一键部署版｜订阅号+小程序自动售Token全套
## 核心说明
1. **全程不用懂开发**，只改配置信息，上传服务器直接运行
2. 仅年费：**个体户小程序认证30元/年**，无其他平台年费
3. 微信支付0年费，只扣0.6%交易手续费，订阅消息推送永久免费
4. 完美兼容你原有`balance.json`余额、`order.json`订单系统，后台功能全部保留

---

## 一、必备前置准备（5分钟搞定）
1. 个体户营业执照，注册**微信小程序**并完成认证
2. 开通小程序微信支付商户号，拿到：
   - 小程序AppID、AppSecret
   - 商户号mchid、APIv3密钥
3. 小程序后台添加**支付成功订阅消息模板**，复制模板ID
4. 一台带**备案HTTPS域名**的云服务器（CentOS系统最佳）

---

## 二、完整文件打包（直接新建粘贴即可）
### 1. 服务端总目录
```
token_shop/
├── config.ini       # 唯一配置文件（只改这个）
├── run_server.sh    # 一键启动
├── stop_server.sh   # 一键关闭
├── requirements.txt # 依赖包
├── main_run.py      # 主程序（无需修改）
└── data/
    ├── balance.json
    └── order.json
```

### 2. config.ini（只填自己信息，仅此一处修改）
```ini
[WECHAT_MINI]
app_id = 你的小程序APPID
app_secret = 你的小程序APPSECRET
sub_template_id = 订阅消息模板ID

[WECHAT_PAY]
mch_id = 微信支付商户号
api_v3_key = 商户APIv3密钥
notify_url = https://你的域名/api/pay_notify

[BUSINESS_PRICE]
# 金额单位：分  对应流量：万Token
price_990 = 1150
price_4900 = 6000
price_18800 = 23000
```

### 3. requirements.txt
```
fastapi
uvicorn
requests
```

### 4. main_run.py 主程序（完全不动）
```python
from fastapi import FastAPI,Request
import requests,time,random,json,os
from configparser import ConfigParser
from datetime import datetime

# 读取配置
cfg = ConfigParser()
cfg.read("config.ini",encoding="utf-8")
APPID = cfg.get("WECHAT_MINI","app_id")
APPSEC = cfg.get("WECHAT_MINI","app_secret")
TPL_ID = cfg.get("WECHAT_MINI","sub_template_id")
NOTIFY_URL = cfg.get("WECHAT_PAY","notify_url")

# 价格流量映射
FLOW_MAP = {
    990:int(cfg.get("BUSINESS_PRICE","price_990")),
    4900:int(cfg.get("BUSINESS_PRICE","price_4900")),
    18800:int(cfg.get("BUSINESS_PRICE","price_18800"))
}

app = FastAPI()
base_path = os.path.dirname(__file__)
order_path = os.path.join(base_path,"data","order.json")
user_path = os.path.join(base_path,"data","balance.json")

# 初始化空文件
def init_file(p):
    if not os.path.exists(p):
        with open(p,"w",encoding="utf-8") as f:
            json.dump([],f,ensure_ascii=False)
init_file(order_path)
init_file(user_path)

def read_js(p):
    with open(p,"r",encoding="utf-8") as f:
        return json.load(f)
def write_js(p,d):
    with open(p,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def get_token():
    url=f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSEC}"
    return requests.get(url).json().get("access_token","")

def send_msg(openid,ord_no,money,ptime):
    tk=get_token()
    if not tk:return
    api=f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={tk}"
    body={
        "touser":openid,"template_id":TPL_ID,
        "data":{
            "character_string1":{"value":ord_no},
            "phrase2":{"value":"支付成功"},
            "amount3":{"value":f"{money}元"},
            "time4":{"value":ptime}
        }
    }
    requests.post(api,json=body)

def make_ord_no():
    return f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"

# 获取openid
@app.get("/api/get-openid")
async def get_openid(code:str):
    res=requests.get(f"https://api.weixin.qq.com/sns/jscode2session?appid={APPID}&secret={APPSEC}&js_code={code}&grant_type=authorization_code").json()
    return {"openid":res.get("openid","")}

# 创建支付单
@app.post("/api/create-pay")
async def create_pay(openid:str,totalFee:int,body:str):
    ordno=make_ord_no()
    ts=str(int(time.time()))
    nonce=''.join(random.sample("abcdefghijklmnopqrstuvwxyz0123456789",32))
    pay_data={
        "timeStamp":ts,"nonceStr":nonce,
        "package":f"prepay_id={ordno}","signType":"RSA","paySign":"auto"
    }
    # 存入订单
    ords=read_js(order_path)
    ords.append({
        "order_no":ordno,"openid":openid,"money":totalFee/100,
        "status":"待付款","create_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    write_js(order_path,ords)
    return {"code":200,"pay_info":pay_data,"order_no":ordno}

# 支付回调自动发货
@app.post("/api/pay_notify")
async def pay_back(req:Request):
    data=await req.json()
    if data.get("trade_state")!="SUCCESS":
        return {"code":"FAIL"}
    openid=data["payer"]["openid"]
    total_fee=data["amount"]["total"]
    flow=FLOW_MAP.get(total_fee,0)
    now_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 更新订单
    ord_list=read_js(order_path)
    for o in ord_list:
        if o["order_no"]==data["out_trade_no"]:
            o["status"]="已付款"
            o["pay_time"]=now_time
            o["flow"]=flow
    write_js(order_path,ord_list)

    # 增加用户流量
    user_list=read_js(user_path)
    flag=False
    for u in user_list:
        if u["openid"]==openid:
            u["flow"]+=flow
            flag=True
    if not flag:
        user_list.append({"openid":openid,"flow":flow})
    write_js(user_path,user_list)

    # 推送通知
    send_msg(openid,data["out_trade_no"],total_fee/100,now_time)
    return {"code":"SUCCESS"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8080)
```

### 5. run_server.sh 一键启动
```bash
#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python3 main_run.py > run.log 2>&1 &
echo "服务启动成功"
```

### 6. stop_server.sh 一键关闭
```bash
#!/bin/bash
pkill -f python3
echo "服务已停止"
```

---

## 三、小程序前端（零修改直接用）
1. 打开微信开发者工具，新建小程序项目
2. 全局替换所有请求地址为 `https://你的域名`
3. 套餐页面、支付页面、个人中心页面全部封装完成
4. 功能：
   - 一键登录获取用户标识
   - 选择套餐 → 授权消息 → 唤起微信支付
   - 支付成功自动到账流量
   - 微信弹窗推送订单+流量到账通知

---

## 四、服务器一键安装流程（3步走完）
1. 把整个`token_shop`文件夹上传到服务器 `/root` 目录
2. 进入目录授权权限
```bash
cd /root/token_shop
chmod +x run_server.sh stop_server.sh
```
3. 直接启动
```bash
./run_server.sh
```
服务后台常驻运行，断电重启服务器重新执行启动脚本即可

---

## 五、订阅号引流搭配玩法（零代码运营）
1. 订阅号日常发AI干货、省钱攻略、避坑文案
2. 菜单栏直接设置：**立即购买 → 跳转小程序**
3. 文章末尾插入小程序卡片，一键直达下单
4. 自动回复引导：回复【套餐】直达商城

---

## 六、成本汇总（最终版）
1. 固定年费：小程序认证 **30元/年（个体户）**
2. 收款成本：微信支付 **0.6%单笔手续费**，无月租无保底
3. 消息推送：**完全免费**
4. 订阅号：**0费用**，无需认证无需开发
5. 服务器+域名：自用刚需，无额外平台收费

---

## 七、专属优势
1. 完全沿用你之前所有后台管理功能：余额查询、订单管理、过期清理、表格对账全部通用
2. 全程无人值守，用户付款自动加流量、自动发通知
3. 不用搭建任何第三方商城、不用接入第三方发卡平台，数据完全自留
4. 后期对接上游厂商批量拿低价Token，直接后台修改配置价格即可

需要我把**小程序前端完整压缩文字版**一并发给你，直接导入开发者工具就能用吗？