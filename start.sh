#!/bin/bash

# ============================================================================
# GraphRAG 完整启动脚本
# 从数据读取到服务启动的一键自动化流程
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Python 命令，优先用 python3.11，可按需要修改
PYTHON_CMD="${PYTHON_CMD:-python3.11}"

# 默认配置
DEFAULT_DATA_FILE="${DATA_FILE:-data/raw/demo.jsonl}"
DEFAULT_DOMAIN="${DOMAIN:-medical}"
DEFAULT_VERSION="${VERSION:-1.0}"
DEFAULT_BATCH_SIZE="${BATCH_SIZE:-100}"

# 日志目录
LOG_DIR="$PROJECT_ROOT/storage/logs"
mkdir -p "$LOG_DIR"

# ============================================================================
# 辅助函数
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[步骤 $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 未安装或不在 PATH 中"
        return 1
    fi
    return 0
}

check_file() {
    if [ ! -f "$1" ]; then
        print_error "文件不存在: $1"
        return 1
    fi
    return 0
}

wait_for_port() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    print_step "等待" "等待 $service_name 服务就绪（端口 $port）..."
    
    while [ $attempt -lt $max_attempts ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            print_success "$service_name 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    print_warning "$service_name 服务可能未正常启动，请检查日志"
    return 1
}

# ============================================================================
# 环境检查
# ============================================================================

print_header "GraphRAG 完整启动流程"

print_step "1" "环境检查"

# 检查 Python
if ! check_command "$PYTHON_CMD"; then
    exit 1
fi
print_success "Python: $PYTHON_CMD"

# 检查 .env 文件
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_warning ".env 文件不存在，将使用环境变量或默认值"
    print_warning "建议创建 .env 文件并配置必要的环境变量"
else
    print_success ".env 文件存在"
fi

# 检查必要的 Python 包
print_step "检查" "检查 Python 依赖..."
if ! $PYTHON_CMD -c "import fastapi, neo4j, openai" 2>/dev/null; then
    print_warning "部分 Python 依赖可能缺失，建议运行: pip install -r requirements.txt"
else
    print_success "Python 依赖检查通过"
fi

# ============================================================================
# 参数解析
# ============================================================================

# 解析命令行参数
SKIP_INFER=false
SKIP_BUILD=false
CLEAR_GRAPH=false
DATA_FILE=""
DOMAIN=""
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --data-file)
            DATA_FILE="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --skip-infer)
            SKIP_INFER=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --clear)
            CLEAR_GRAPH=true
            shift
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --data-file FILE     数据文件路径（默认: $DEFAULT_DATA_FILE）"
            echo "  --domain DOMAIN      领域名称（默认: $DEFAULT_DOMAIN）"
            echo "  --version VERSION    版本号（默认: $DEFAULT_VERSION）"
            echo "  --skip-infer         跳过模式推断步骤"
            echo "  --skip-build         跳过图谱构建步骤"
            echo "  --clear              清空现有图谱后重新构建"
            echo "  --batch-size SIZE    批量处理大小（默认: $DEFAULT_BATCH_SIZE）"
            echo "  --help               显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 --data-file data/raw/medical.jsonl --domain medical --version 1.0"
            echo "  $0 --skip-infer --skip-build  # 仅启动服务"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 使用默认值
DATA_FILE="${DATA_FILE:-$DEFAULT_DATA_FILE}"
DOMAIN="${DOMAIN:-$DEFAULT_DOMAIN}"
VERSION="${VERSION:-$DEFAULT_VERSION}"
BATCH_SIZE="${BATCH_SIZE:-$DEFAULT_BATCH_SIZE}"

# 生成模式文件路径
SCHEMA_FILE="config/schemas/${DOMAIN}_schema_v${VERSION}.json"

echo ""
echo "配置信息:"
echo "  数据文件: $DATA_FILE"
echo "  领域: $DOMAIN"
echo "  版本: $VERSION"
echo "  模式文件: $SCHEMA_FILE"
echo "  批量大小: $BATCH_SIZE"
echo "  清空图谱: $CLEAR_GRAPH"
echo ""

# ============================================================================
# 步骤1: 模式推断
# ============================================================================

if [ "$SKIP_INFER" = false ]; then
    print_header "步骤1: 模式推断"
    
    # 检查数据文件
    if ! check_file "$DATA_FILE"; then
        print_error "数据文件不存在，无法进行模式推断"
        print_warning "请使用 --skip-infer 跳过此步骤，或提供正确的数据文件路径"
        exit 1
    fi
    
    # 检查模式文件是否已存在
    if [ -f "$SCHEMA_FILE" ]; then
        print_warning "模式文件已存在: $SCHEMA_FILE"
        read -p "是否重新推断模式？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_success "使用现有模式文件"
            SKIP_INFER=true
        fi
    fi
    
    if [ "$SKIP_INFER" = false ]; then
        print_step "执行" "开始推断图模式..."
        
        if $PYTHON_CMD scripts/infer_schema.py "$DATA_FILE" \
            --domain "$DOMAIN" \
            --version "$VERSION"; then
            print_success "模式推断完成"
        else
            print_error "模式推断失败"
            exit 1
        fi
    fi
else
    print_header "步骤1: 模式推断（已跳过）"
    if [ ! -f "$SCHEMA_FILE" ]; then
        print_error "模式文件不存在: $SCHEMA_FILE"
        print_error "请先运行模式推断或移除 --skip-infer 选项"
        exit 1
    fi
    print_success "使用现有模式文件: $SCHEMA_FILE"
fi

# ============================================================================
# 步骤2: 图谱构建
# ============================================================================

if [ "$SKIP_BUILD" = false ]; then
    print_header "步骤2: 图谱构建"
    
    # 检查模式文件
    if ! check_file "$SCHEMA_FILE"; then
        print_error "模式文件不存在: $SCHEMA_FILE"
        exit 1
    fi
    
    # 检查数据文件
    if ! check_file "$DATA_FILE"; then
        print_error "数据文件不存在: $DATA_FILE"
        exit 1
    fi
    
    # 构建参数
    BUILD_ARGS=(
        "$SCHEMA_FILE"
        "$DATA_FILE"
        --batch-size "$BATCH_SIZE"
    )
    
    if [ "$CLEAR_GRAPH" = true ]; then
        BUILD_ARGS+=(--clear)
        print_warning "将清空现有图谱后重新构建"
    fi
    
    print_step "执行" "开始构建知识图谱..."
    
    if $PYTHON_CMD scripts/build_graph.py "${BUILD_ARGS[@]}"; then
        print_success "图谱构建完成"
    else
        print_error "图谱构建失败"
        exit 1
    fi
else
    print_header "步骤2: 图谱构建（已跳过）"
    print_success "跳过图谱构建步骤"
fi

# ============================================================================
# 步骤3: 启动服务
# ============================================================================

print_header "步骤3: 启动服务"

# 清理旧的 PID 文件
rm -f storage/pids/*.pid
mkdir -p storage/pids

# 启动 Agent 服务
print_step "启动" "启动 Agent 服务（端口 8103）..."
$PYTHON_CMD scripts/start_agent.py > "$LOG_DIR/agent_service_simple.log" 2>&1 &
AGENT_PID=$!
echo $AGENT_PID > storage/pids/agent_service.pid
print_success "Agent 服务已启动 (PID: $AGENT_PID)"

# 启动 Graph 服务
print_step "启动" "启动 Graph 服务（端口 8101）..."
$PYTHON_CMD scripts/start_graph_service.py > "$LOG_DIR/graph_service_simple.log" 2>&1 &
GRAPH_PID=$!
echo $GRAPH_PID > storage/pids/graph_service.pid
print_success "Graph 服务已启动 (PID: $GRAPH_PID)"

# 等待服务就绪
wait_for_port 8103 "Agent"
wait_for_port 8101 "Graph"

# ============================================================================
# 完成
# ============================================================================

print_header "启动完成"

echo -e "${GREEN}✅ 所有服务已成功启动！${NC}"
echo ""
echo "服务地址:"
echo "  🤖 Agent 服务:  http://localhost:8103/"
echo "  🗺️  Graph 服务: http://localhost:8101/"
echo ""
echo "日志文件:"
echo "  📝 Agent 服务:  $LOG_DIR/agent_service_simple.log"
echo "  📝 Graph 服务:  $LOG_DIR/graph_service_simple.log"
echo ""
echo "进程 ID:"
echo "  🤖 Agent 服务:  $AGENT_PID"
echo "  🗺️  Graph 服务: $GRAPH_PID"
echo ""

# 自动打开浏览器（macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_step "浏览器" "正在打开浏览器..."
    sleep 2
    open http://localhost:8103/
    print_success "浏览器已打开"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v xdg-open &> /dev/null; then
        print_step "浏览器" "正在打开浏览器..."
        sleep 2
        xdg-open http://localhost:8103/ 2>/dev/null || true
    fi
fi

echo ""
echo -e "${YELLOW}提示:${NC}"
echo "  - 使用 Ctrl+C 停止服务"
echo "  - 查看日志: tail -f $LOG_DIR/*.log"
echo "  - 停止服务: ./stop.sh (如果存在) 或 kill $AGENT_PID $GRAPH_PID"
echo ""

# 保持脚本运行（可选）
# 如果希望脚本在后台运行，可以注释掉下面的 wait
# wait

print_success "启动流程完成！"

