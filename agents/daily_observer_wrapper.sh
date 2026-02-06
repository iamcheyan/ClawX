#!/bin/bash
# Daily Timeline Observer Wrapper
# 在18:00启动，随机延迟0-120分钟后执行

# 随机延迟0-7200秒（0-120分钟）
DELAY=$((RANDOM % 7200))
MINUTES=$((DELAY / 60))

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daily Timeline Observer scheduled"
echo "Delay: ${MINUTES} minutes (${DELAY} seconds)"
echo "Estimated execution: $(date -d "+${DELAY} seconds" '+%H:%M:%S')"

# 等待
sleep $DELAY

# 执行观察脚本
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting observation..."
cd /home/tetsuya/mini-twitter
python3 agents/daily_timeline_observer.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done"
