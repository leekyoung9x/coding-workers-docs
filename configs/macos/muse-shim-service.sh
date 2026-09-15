#!/usr/bin/env bash
# Service manager for muse-shim on macOS (loopback daemon)

DIR="$HOME/.config/muse"
ENV_FILE="$DIR/env"
PID_FILE="$DIR/shim.pid"
LOG_FILE="$DIR/shim.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "muse-shim is already running (PID: $(cat "$PID_FILE"))."
        return 0
    fi

    if [ ! -f "$ENV_FILE" ]; then
        echo "Error: Config file not found at $ENV_FILE"
        echo "Please create it: cp $DIR/env.template $ENV_FILE and enter your API key."
        return 1
    fi

    echo "Starting muse-shim..."
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a

    if [ -z "$MUSE_SHIM_API_KEY" ] || [ "$MUSE_SHIM_API_KEY" = "sk-or-v1-YOUR_KEY_HERE" ]; then
        echo "Error: MUSE_SHIM_API_KEY is not configured in $ENV_FILE"
        return 1
    fi

    nohup muse-shim generic > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "$PID" > "$PID_FILE"
    
    # Wait up to 5s for health check
    for i in {1..5}; do
        sleep 1
        HEALTH=$(curl -s "http://127.0.0.1:${MUSE_SHIM_PORT:-8787}/health" 2>/dev/null || true)
        if [ -n "$HEALTH" ]; then
            echo "muse-shim started successfully (PID: $PID, port: ${MUSE_SHIM_PORT:-8787})."
            echo "Health status: $HEALTH"
            return 0
        fi
    done

    if kill -0 "$PID" 2>/dev/null; then
        echo "Warning: muse-shim process is alive (PID: $PID) but /health did not answer in 5s."
        return 0
    else
        echo "Error: muse-shim failed to start. Check logs at $LOG_FILE"
        cat "$LOG_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "muse-shim is not running (no PID file)."
        return 0
    fi
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping muse-shim (PID: $PID)..."
        kill "$PID"
        sleep 1
        kill -9 "$PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "muse-shim stopped."
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "muse-shim is RUNNING (PID: $PID)."
        curl -s "http://127.0.0.1:8787/health" || echo "Health check endpoint failed."
        echo ""
    else
        echo "muse-shim is STOPPED."
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    log|logs)
        tail -n 50 "$LOG_FILE"
        ;;
    *)
        echo "Usage: muse-shim-service.sh {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
