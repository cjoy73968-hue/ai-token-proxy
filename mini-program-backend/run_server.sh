#!/bin/bash
cd "$(dirname "$0")"

# 使用虚拟环境 (如果存在)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 安装依赖
pip install fastapi uvicorn requests -q

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8080 --reload