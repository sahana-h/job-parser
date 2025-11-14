#!/bin/bash
# Start the scheduler in the background

cd "$(dirname "$0")"
nohup python3 scheduler.py > scheduler.log 2>&1 &
echo $! > scheduler.pid
echo "✅ Scheduler started in background (PID: $(cat scheduler.pid))"
echo "📋 Logs: tail -f scheduler.log"
echo "🛑 Stop: kill $(cat scheduler.pid)"

