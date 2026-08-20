#!/bin/bash
# 一键启动本地预览服务器 + 管理后台（macOS 双击即可运行）
cd "$(dirname "$0")"

PORT=8000
if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  if curl -s --max-time 2 -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" 2>/dev/null | grep -q "^200"; then
    echo "预览服务器已在运行，正在打开浏览器…"
    open "http://localhost:$PORT"
    echo "管理后台：http://localhost:$PORT/manage/"
    exit 0
  fi
  echo "端口 $PORT 被其他程序占用，改用端口 8001"
  PORT=8001
fi

echo "正在启动本地预览服务器（http://localhost:$PORT/）…"
python3 server.py $PORT &
SERVER_PID=$!
sleep 1
open "http://localhost:$PORT"
echo "管理后台：http://localhost:$PORT/manage/"
wait "$SERVER_PID"
