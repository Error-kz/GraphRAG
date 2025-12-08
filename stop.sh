#!/bin/bash

# ============================================================================
# GraphRAG 服务停止脚本
# 停止所有运行中的服务
# ============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

PID_DIR="$PROJECT_ROOT/storage/pids"

echo ""
echo "正在停止 GraphRAG 服务..."
echo ""

# 停止 Agent 服务
if [ -f "$PID_DIR/agent_service.pid" ]; then
    AGENT_PID=$(cat "$PID_DIR/agent_service.pid")
    if ps -p "$AGENT_PID" > /dev/null 2>&1; then
        echo "停止 Agent 服务 (PID: $AGENT_PID)..."
        kill "$AGENT_PID" 2>/dev/null || true
        sleep 1
        # 强制杀死（如果还在运行）
        if ps -p "$AGENT_PID" > /dev/null 2>&1; then
            kill -9 "$AGENT_PID" 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Agent 服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  Agent 服务进程不存在${NC}"
    fi
    rm -f "$PID_DIR/agent_service.pid"
else
    # 尝试通过端口查找并停止
    AGENT_PID=$(lsof -ti:8103 2>/dev/null || true)
    if [ -n "$AGENT_PID" ]; then
        echo "通过端口停止 Agent 服务 (PID: $AGENT_PID)..."
        kill "$AGENT_PID" 2>/dev/null || true
        sleep 1
        if ps -p "$AGENT_PID" > /dev/null 2>&1; then
            kill -9 "$AGENT_PID" 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Agent 服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  Agent 服务未运行${NC}"
    fi
fi

# 停止 Graph 服务
if [ -f "$PID_DIR/graph_service.pid" ]; then
    GRAPH_PID=$(cat "$PID_DIR/graph_service.pid")
    if ps -p "$GRAPH_PID" > /dev/null 2>&1; then
        echo "停止 Graph 服务 (PID: $GRAPH_PID)..."
        kill "$GRAPH_PID" 2>/dev/null || true
        sleep 1
        # 强制杀死（如果还在运行）
        if ps -p "$GRAPH_PID" > /dev/null 2>&1; then
            kill -9 "$GRAPH_PID" 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Graph 服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  Graph 服务进程不存在${NC}"
    fi
    rm -f "$PID_DIR/graph_service.pid"
else
    # 尝试通过端口查找并停止
    GRAPH_PID=$(lsof -ti:8101 2>/dev/null || true)
    if [ -n "$GRAPH_PID" ]; then
        echo "通过端口停止 Graph 服务 (PID: $GRAPH_PID)..."
        kill "$GRAPH_PID" 2>/dev/null || true
        sleep 1
        if ps -p "$GRAPH_PID" > /dev/null 2>&1; then
            kill -9 "$GRAPH_PID" 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Graph 服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  Graph 服务未运行${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo ""

