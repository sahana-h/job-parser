#!/bin/bash
# Stop the scheduler

if [ -f scheduler.pid ]; then
    PID=$(cat scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm scheduler.pid
        echo "✅ Scheduler stopped"
    else
        echo "⚠️  Scheduler not running (PID file exists but process not found)"
        rm scheduler.pid
    fi
else
    echo "⚠️  Scheduler PID file not found. Is it running?"
fi

