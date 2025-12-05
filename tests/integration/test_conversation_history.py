"""
对话历史存储测试
简单测试Redis存储对话历史的功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cache.redis_client import get_redis_client, save_conversation_history
import json


def test_save_conversation_history():
    """测试保存对话历史"""
    # 获取Redis客户端
    r = get_redis_client()
    
    # 测试数据
    session_id = "test-session-001"
    question = "感冒了有什么症状？"
    answer = "感冒的常见症状包括流鼻涕、打喷嚏、咳嗽、头痛等。"
    
    # 保存对话历史
    save_conversation_history(r, session_id, question, answer)
    print(f"✅ 已保存对话历史")
    print(f"   Session ID: {session_id}")
    print(f"   问题: {question}")
    print(f"   答案: {answer[:50]}...")
    
    # 验证是否保存成功
    key = f'chat:history:{session_id}'
    history_length = r.llen(key)
    print(f"✅ 对话历史列表长度: {history_length}")
    
    # 读取最新的一条记录
    if history_length > 0:
        latest_record = r.lindex(key, -1)
        if latest_record:
            record = json.loads(latest_record)
            print(f"✅ 最新记录:")
            print(f"   问题: {record['question']}")
            print(f"   答案: {record['answer'][:50]}...")
            print(f"   时间: {record['timestamp']}")
    
    # 测试保存多条记录
    print("\n测试保存多条记录...")
    for i in range(3):
        save_conversation_history(r, session_id, f"问题{i+1}", f"答案{i+1}")
    
    history_length = r.llen(key)
    print(f"✅ 保存3条记录后，列表长度: {history_length}")
    
    # 验证最多保留20条
    print("\n测试限制最多20条记录...")
    for i in range(25):
        save_conversation_history(r, session_id, f"问题{i+3}", f"答案{i+3}")
    
    history_length = r.llen(key)
    print(f"✅ 保存25条后，列表长度: {history_length} (应该最多20条)")
    
    print("\n" + "=" * 50)
    print("对话历史存储测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    test_save_conversation_history()

