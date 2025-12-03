#!/usr/bin/env python
"""
启动知识图谱服务
知识图谱查询服务启动脚本
"""
import sys
import os
import socket
import subprocess
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from services.graph_service import app
from config.settings import settings


def check_port_available(port: int) -> bool:
    """
    检查端口是否可用
    
    Args:
        port: 端口号
        
    Returns:
        True if 端口可用, False if 被占用
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False


def find_port_process(port: int) -> list:
    """
    查找占用指定端口的进程
    
    Args:
        port: 端口号
        
    Returns:
        进程信息列表
    """
    try:
        # 使用 lsof 命令查找占用端口的进程（macOS/Linux）
        result = subprocess.run(
            ['lsof', '-i', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1:]  # 跳过标题行
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    return []


def get_local_ip_addresses() -> list:
    """
    获取本机的IP地址列表（包括局域网IP）
    
    Returns:
        IP地址列表
    """
    ip_addresses = []
    
    try:
        # 方法1: 通过连接外部地址获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 连接一个不存在的地址，不会实际发送数据
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            ip_addresses.append(ip)
        except Exception:
            pass
        finally:
            s.close()
    except Exception:
        pass
    
    try:
        # 方法2: 获取主机名对应的IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip not in ip_addresses and not local_ip.startswith('127.'):
            ip_addresses.append(local_ip)
    except Exception:
        pass
    
    # 如果没有获取到IP，返回localhost
    if not ip_addresses:
        ip_addresses.append('127.0.0.1')
    
    return ip_addresses


def print_network_info(port: int, service_name: str = "服务"):
    """
    打印网络访问信息
    
    Args:
        port: 端口号
        service_name: 服务名称
    """
    ip_addresses = get_local_ip_addresses()
    
    print("\n" + "=" * 70)
    print(f"✅ {service_name}启动成功！")
    print("=" * 70)
    print(f"\n📡 本机网络信息:")
    print(f"   端口: {port}")
    
    if len(ip_addresses) > 0:
        print(f"\n🌐 访问地址:")
        # 显示localhost
        print(f"   本机访问: http://127.0.0.1:{port}")
        print(f"   本机访问: http://localhost:{port}")
        
        # 显示局域网IP
        print(f"\n   局域网访问（同一网络下的其他设备）:")
        for ip in ip_addresses:
            if not ip.startswith('127.'):
                print(f"   http://{ip}:{port}")
    
    print("\n" + "=" * 70)
    print("💡 提示: 确保防火墙允许该端口的访问")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    port = settings.GRAPH_SERVICE_PORT
    
    # 检查端口是否被占用
    if not check_port_available(port):
        print("\n" + "=" * 60)
        print(f"❌ 错误：端口 {port} 已被占用")
        print("=" * 60)
        
        # 尝试查找占用端口的进程
        processes = find_port_process(port)
        if processes:
            print("\n占用端口的进程：")
            for proc in processes:
                print(f"  {proc}")
            print("\n解决方法：")
            print(f"  1. 停止占用端口的进程：")
            print(f"     kill <进程ID>")
            print(f"  2. 或使用其他端口（修改 config/settings.py 中的 GRAPH_SERVICE_PORT）")
        else:
            print("\n解决方法：")
            print(f"  1. 查找并停止占用端口 {port} 的进程：")
            print(f"     lsof -i :{port}")
            print(f"     kill <进程ID>")
            print(f"  2. 或使用其他端口（修改 config/settings.py 中的 GRAPH_SERVICE_PORT）")
        
        print("=" * 60)
        sys.exit(1)
    
    # 显示网络信息
    print_network_info(port, "Graph 服务")
    
    # 启动服务
    print(f"正在启动 Graph 服务，端口: {port}")
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            workers=1
        )
    except OSError as e:
        if "address already in use" in str(e) or e.errno == 48:
            print(f"\n❌ 端口 {port} 启动时被占用，请检查是否有其他服务正在运行")
            sys.exit(1)
        raise

