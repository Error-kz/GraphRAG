"""
Redis写入测试
简单测试Redis数据库的写入能力
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cache.redis_client import get_redis_client, cache_set


def test_redis_write():
    """测试Redis写入功能"""
    # 获取Redis客户端
    r = get_redis_client()
    
    # 写入测试数据
    cache_set(r, "测试问题1", "测试答案1")
    cache_set(r, "测试问题2", "测试答案2")
    cache_set(r, "什么是感冒？", "感冒是一种常见的呼吸道疾病")


if __name__ == "__main__":
    test_redis_write()
    print("Redis写入测试完成")

