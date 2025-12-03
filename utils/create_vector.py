"""
创建Milvus向量数据库
将JSON文件数据导入到milvus_agent.db向量数据库中
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径，以便导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import time
from tqdm import tqdm
from langchain_core.documents import Document
from langchain_milvus import Milvus, BM25BuiltInFunction
from pathlib import Path

from config.settings import settings
from core.models.embeddings import ZhipuAIEmbeddings
from core.cache.redis_client import get_redis_client, cache_set, cache_get
from utils.document_loader import prepare_document
from zai import ZhipuAiClient


class MilvusVectorBuilder:
    """
    Milvus向量数据库构建器
    用于将文档数据导入到milvus_agent.db向量数据库
    """
    
    def __init__(self, embedding_model: ZhipuAIEmbeddings = None, uri: str = None):
        """
        初始化向量数据库构建器
        
        Args:
            embedding_model: Embedding模型实例，如果为None则自动创建
            uri: Milvus数据库URI，如果为None则使用配置中的默认值
        """
        if embedding_model is None:
            client = ZhipuAiClient(api_key=settings.ZHIPU_API_KEY)
            self.embeddings = ZhipuAIEmbeddings(client)
        else:
            self.embeddings = embedding_model
        
        self.URI = uri or settings.MILVUS_AGENT_DB
        
        # 定义索引类型
        self.dense_index = {
            'metric_type': 'IP',
            'index_type': 'IVF_FLAT',
        }
        self.sparse_index = {
            'metric_type': 'BM25',
            'index_type': 'SPARSE_INVERTED_INDEX'
        }
    
    def _check_database_exists(self) -> bool:
        """
        检查数据库是否已存在
        
        Returns:
            True 如果数据库文件存在，False 否则
        """
        db_path = Path(self.URI)
        # 检查数据库目录或文件是否存在
        return db_path.exists() and (db_path.is_dir() or db_path.is_file())
    
    def _connect_to_existing_store(self):
        """
        连接到已存在的向量存储
        
        Returns:
            Milvus向量存储实例，如果连接失败返回 None
        """
        try:
            vectorstore = Milvus(
                embedding_function=self.embeddings,
                builtin_function=BM25BuiltInFunction(),
                vector_field=['dense', 'sparse'],
                index_params=[self.dense_index, self.sparse_index],
                connection_args={'uri': self.URI},
                consistency_level='Bounded',
            )
            return vectorstore
        except Exception as e:
            # 如果连接失败，可能是集合不存在或配置不匹配
            return None
    
    def create_vector_store(self, docs: list, append_mode: bool = True):
        """
        创建向量存储并添加文档（支持追加模式）
        
        Args:
            docs: 文档列表（LangChain Document对象）
            append_mode: 如果为 True，当数据库已存在时追加文档；如果为 False，覆盖现有数据库
            
        Returns:
            Milvus向量存储实例
        """
        if not docs:
            raise ValueError("文档列表不能为空")
        
        db_exists = self._check_database_exists()
        
        # 追加模式：尝试连接到现有数据库
        if append_mode and db_exists:
            print(f"📂 检测到已存在的数据库: {self.URI}")
            print("🔄 尝试连接到现有向量存储...")
            
            existing_store = self._connect_to_existing_store()
            if existing_store is not None:
                print("✅ 成功连接到现有向量存储，将追加新文档")
                self.vectorstore = existing_store
                
                # 直接追加所有文档
                count = 0
                temp = []
                
                for doc in tqdm(docs, desc="追加文档到Milvus"):
                    temp.append(doc)
                    if len(temp) >= 5:
                        self.vectorstore.add_documents(temp)
                        count += len(temp)
                        temp = []
                        print(f'已追加 {count} 条数据...')
                        time.sleep(1)  # 避免请求过快
                
                # 添加剩余的文档
                if temp:
                    self.vectorstore.add_documents(temp)
                    count += len(temp)
                
                print(f'✅ 总共追加 {count} 条新数据到现有数据库')
                return self.vectorstore
            else:
                print("⚠️  无法连接到现有数据库，将创建新的向量存储")
        
        # 创建新数据库或覆盖模式
        if not append_mode and db_exists:
            print("⚠️  覆盖模式：将删除现有数据库并创建新的")
        else:
            print(f"📝 创建新的向量数据库，共 {len(docs)} 条文档...")
        
        # 初始化前10个文档创建向量存储
        init_docs = docs[:10] if len(docs) >= 10 else docs
        
        print("正在初始化向量存储...")
        try:
            self.vectorstore = Milvus.from_documents(
                documents=init_docs,
                embedding=self.embeddings,
                builtin_function=BM25BuiltInFunction(),
                index_params=[self.dense_index, self.sparse_index],
                vector_field=['dense', 'sparse'],
                connection_args={'uri': self.URI},
                consistency_level='Bounded',
                drop_old=not append_mode,  # 追加模式不删除旧数据
            )
            print('✅ 已初始化创建 Milvus 向量存储')
        except Exception as e:
            error_msg = str(e)
            if "has been opened by another program" in error_msg or "Open local milvus failed" in error_msg:
                print("\n" + "=" * 60)
                print("❌ 数据库连接失败：数据库文件正在被其他程序使用")
                print("=" * 60)
                print("\n可能的原因：")
                print("  1. agent_service.py 正在运行中")
                print("  2. 另一个脚本正在使用该数据库")
                print("  3. 之前的连接未正确关闭")
                print("\n解决方法：")
                print("  1. 停止正在运行的 agent_service.py 服务：")
                print("     ps aux | grep agent_service")
                print("     kill <进程ID>")
                print("  2. 等待几秒后重试")
                print("  3. 如果问题持续，可以重启终端或检查是否有僵尸进程")
                print(f"\n数据库路径: {self.URI}")
                print("=" * 60)
            raise
        
        # 批量添加剩余文档
        if len(docs) > 10:
            count = 10
            temp = []
            
            for doc in tqdm(docs[10:], desc="添加文档到Milvus"):
                temp.append(doc)
                if len(temp) >= 5:
                    self.vectorstore.add_documents(temp)
                    count += len(temp)
                    temp = []
                    print(f'已插入 {count} 条数据...')
                    time.sleep(1)  # 避免请求过快
            
            # 添加剩余的文档
            if temp:
                self.vectorstore.add_documents(temp)
                count += len(temp)
            
            print(f'✅ 总共插入 {count} 条数据')
        else:
            print(f'✅ 总共插入 {len(docs)} 条数据')
        
        print('✅ 已创建 Milvus 索引完成！')
        
        return self.vectorstore


def build_milvus_database(file_paths: list = None, uri: str = None, append_mode: bool = True):
    """
    构建Milvus向量数据库的便捷函数（支持追加模式）
    
    Args:
        file_paths: JSONL文件路径列表，默认使用配置中的数据路径
        uri: Milvus数据库URI，默认使用配置中的MILVUS_AGENT_DB
        append_mode: 如果为 True，当数据库已存在时追加文档；如果为 False，覆盖现有数据库
        
    Returns:
        Milvus向量存储实例
    """
    # 加载文档
    print("=" * 60)
    if append_mode:
        print("开始构建/追加 Milvus 向量数据库（追加模式）")
    else:
        print("开始构建 Milvus 向量数据库（覆盖模式）")
    print("=" * 60)
    
    print("\n[步骤1] 加载JSON文档...")
    docs = prepare_document(file_paths)
    
    if not docs:
        print("❌ 未加载到任何文档，请检查文件路径")
        return None
    
    print(f"✅ 成功加载 {len(docs)} 条文档")
    
    # 创建向量存储
    print("\n[步骤2] 创建/追加向量存储...")
    builder = MilvusVectorBuilder(uri=uri)
    vectorstore = builder.create_vector_store(docs, append_mode=append_mode)
    
    print("\n" + "=" * 60)
    if append_mode:
        print("✅ 向量数据库追加完成！")
    else:
        print("✅ 向量数据库构建完成！")
    print("=" * 60)
    print(f"\n数据库路径: {builder.URI}")
    print("可以开始使用向量检索功能了！")
    
    return vectorstore


def main():
    """
    主函数，用于命令行执行
    默认使用追加模式，如果数据库已存在则追加新文档
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='构建 Milvus 向量数据库')
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='覆盖模式：如果数据库已存在，删除旧数据并重新创建（默认：追加模式）'
    )
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='要导入的JSONL文件路径（默认：使用配置中的data.jsonl）'
    )
    
    args = parser.parse_args()
    
    # 确定文件路径
    file_paths = [args.file] if args.file else [f'{settings.DATA_RAW_PATH}/dev.jsonl']
    
    # 追加模式（默认）：append_mode=True
    # 覆盖模式：append_mode=False
    append_mode = not args.overwrite
    
    try:
        vectorstore = build_milvus_database(
            file_paths=file_paths,
            append_mode=append_mode
        )
        if vectorstore:
            print("\n✅ 全部初始化完成，可以开始问答了！")
    except Exception as e:
        error_msg = str(e)
        if "has been opened by another program" in error_msg or "Open local milvus failed" in error_msg:
            # 已经在 create_vector_store 中处理了，这里不需要重复打印
            pass
        else:
            print(f"\n❌ 构建失败: {error_msg}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
