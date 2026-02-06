#!/bin/bash
# Daily Best/Worst Picker Wrapper
# 每天在随机时间段执行（00:00-23:59之间）

# 生成今天的随机执行时间（0-86399秒 = 0-23:59）
TARGET_SECONDS=$((RANDOM % 86400))
TARGET_HOUR=$((TARGET_SECONDS / 3600))
TARGET_MIN=$(((TARGET_SECONDS % 3600) / 60))
TARGET_SEC=$((TARGET_SECONDS % 60))

# 计算当前时间到目标时间的秒数
CURRENT_SECONDS=$(($(date +%H) * 3600 + $(date +%M) * 60 + $(date +%S)))

if [ $CURRENT_SECONDS -lt $TARGET_SECONDS ]; then
    # 目标时间在今天晚些时候
    DELAY=$((TARGET_SECONDS - CURRENT_SECONDS))
else
    # 目标时间已过，推迟到明天同一时间
    DELAY=$((86400 - CURRENT_SECONDS + TARGET_SECONDS))
fi

DELAY_HOUR=$((DELAY / 3600))
DELAY_MIN=$(((DELAY % 3600) / 60))

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daily Best/Worst Picker scheduled"
echo "Target time today: $(printf '%02d:%02d:%02d' $TARGET_HOUR $TARGET_MIN $TARGET_SEC)"
echo "Will execute in: ${DELAY_HOUR}h ${DELAY_MIN}m (${DELAY}s)"
echo "Estimated execution: $(date -d "+${DELAY} seconds" '+%Y-%m-%d %H:%M:%S')"

# 保存下次运行时间供前端显示
NEXT_RUN=$(date -d "+${DELAY} seconds" '+%Y-%m-%d %H:%M:%S')
python3 -c "
import json
with open('/home/tetsuya/mini-twitter/next_schedule.json', 'w') as f:
    json.dump({
        'next_run': '$NEXT_RUN',
        'delay_minutes': $((DELAY / 60)),
        'status': 'waiting'
    }, f)
"

# 等待
sleep $DELAY

# 执行
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting..."
cd /home/tetsuya/mini-twitter
python3 agents/daily_best_worst_picker.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done"
