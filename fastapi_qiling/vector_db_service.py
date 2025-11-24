# 故宫博物院向量数据库服务
import os
import json
import pandas as pd
import numpy as np
import faiss
import jieba
import logging
from paddlenlp.embeddings import TokenEmbedding
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class VectorDatabaseService:
    """向量数据库服务类"""
    
    def __init__(self, 
                 excel_file_path: str = "./故宫博物院数字文物库.xlsx",
                 vector_db_path: str = "./data/vector_db"):
        """
        初始化向量数据库服务
        
        Args:
            excel_file_path: Excel文件路径
            vector_db_path: 向量数据库存储路径
        """
        self.excel_file_path = excel_file_path
        self.vector_db_path = vector_db_path
        self.vector_index_file = os.path.join(vector_db_path, "faiss.index")
        self.docs_info_file = os.path.join(vector_db_path, "documents.json")
        
        # 创建必要的目录
        os.makedirs(vector_db_path, exist_ok=True)
        
        # 初始化模型和索引
        self.embedding_model = None
        self.index = None
        self.documents = []
        
        # 加载词嵌入模型
        self._load_embedding_model()
        
        # 尝试加载已存在的向量数据库
        self._load_vector_db()
    
    def _load_embedding_model(self):
        """加载词嵌入模型"""
        try:
            self.embedding_model = TokenEmbedding("w2v.baidu_encyclopedia.target.word-word.dim300")
            logger.info("✓ 词嵌入模型加载成功")
        except Exception as e:
            logger.error(f"❌ 加载词嵌入模型失败: {str(e)}")
            self.embedding_model = None
    
    def _embed_text(self, text: str) -> np.ndarray:
        """将文本转换为向量嵌入
        
        Args:
            text: 要向量化的文本
        
        Returns:
            numpy.ndarray: 文本的向量表示（300维）
        """
        if self.embedding_model is None:
            return np.zeros(300)
        
        try:
            words = list(jieba.cut(text))
            word_embeddings = self.embedding_model.search(words)
            
            if len(word_embeddings) > 0:
                return np.mean(word_embeddings, axis=0)
            else:
                return np.zeros(300)
        except Exception as e:
            logger.error(f"文本嵌入过程出错: {str(e)}")
            return np.zeros(300)
    
    def build_vector_database(self, ernie_client=None, force_rebuild=False):
        """从Excel文件构建故宫博物院文物知识的向量数据库
        
        Args:
            ernie_client: ERNIE客户端（用于图片识别，可选）
            force_rebuild: 是否强制重建（删除已存在的数据库）
        
        Returns:
            bool: 是否构建成功
        """
        # 如果需要强制重建，删除已存在的数据库
        if force_rebuild:
            self._delete_existing_vector_db()
        
        # 如果已存在数据库，直接加载
        if os.path.exists(self.vector_index_file) and os.path.exists(self.docs_info_file):
            logger.info("向量数据库已存在，直接加载")
            return self._load_vector_db()
        
        if self.embedding_model is None:
            logger.error("❌ 词嵌入模型未加载，无法构建向量数据库")
            return False
        
        # 检查Excel文件是否存在
        if not os.path.exists(self.excel_file_path):
            logger.error(f"❌ 错误: 找不到Excel文件 '{self.excel_file_path}'")
            return False
        
        try:
            # 读取Excel文件
            logger.info(f"正在读取Excel文件: {self.excel_file_path}")
            converters = {'图片地址': str}  # 确保图片地址列作为字符串完整读取
            df = pd.read_excel(self.excel_file_path, converters=converters)
            
            # 检查必需的列是否存在
            required_columns = ['文物名称', '图片地址', '编号-年代', '历史', '工艺']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"❌ 错误: Excel文件缺少必需的列: {missing_columns}")
                return False
            
            logger.info(f"✓ 成功读取 {len(df)} 条文物数据")
            
            # 处理每一行数据
            documents = []
            logger.info("开始处理数据...")
            
            for idx, row in df.iterrows():
                # 获取各个字段
                artifact_name = str(row['文物名称']) if pd.notna(row['文物名称']) else ""
                image_url = str(row['图片地址']) if pd.notna(row['图片地址']) else ""
                number_period = str(row['编号-年代']) if pd.notna(row['编号-年代']) else ""
                history = str(row['历史']) if pd.notna(row['历史']) else ""
                craft = str(row['工艺']) if pd.notna(row['工艺']) else ""
                
                # 组合文本内容用于向量化
                content_parts = []
                if artifact_name:
                    content_parts.append(f"文物名称：{artifact_name}")
                if number_period:
                    content_parts.append(f"编号年代：{number_period}")
                if history:
                    content_parts.append(f"历史：{history}")
                if craft:
                    content_parts.append(f"工艺：{craft}")
                
                content = "\n".join(content_parts)
                
                if not content.strip():
                    continue  # 跳过空内容
                
                # 构建文档对象
                doc = {
                    "content": content,
                    "metadata": {
                        "artifact_name": artifact_name,
                        "image_url": image_url,
                        "number_period": number_period,
                        "history": history,
                        "craft": craft,
                        "index": int(idx)
                    }
                }
                documents.append(doc)
            
            logger.info(f"✓ 处理完成，共 {len(documents)} 条有效文物数据")
            
            # 生成向量嵌入
            logger.info("正在生成向量嵌入...")
            embeddings = []
            valid_docs = []
            
            for i, doc in enumerate(documents):
                if (i + 1) % 1000 == 0:
                    logger.info(f"  已处理 {i + 1}/{len(documents)} 条数据...")
                
                vector = self._embed_text(doc["content"])
                if vector is not None and vector.size > 0:
                    embeddings.append(vector)
                    valid_docs.append(doc)
            
            documents = valid_docs
            
            if not embeddings:
                logger.error("❌ 无法生成文档嵌入，无法构建向量数据库")
                return False
            
            # 构建FAISS索引
            logger.info("正在构建FAISS索引...")
            embeddings_np = np.array(embeddings).astype('float32')
            
            if len(embeddings_np.shape) < 2:
                logger.warning(f"⚠️ 嵌入数组形状不正确: {embeddings_np.shape}")
                if embeddings_np.size > 0:
                    embeddings_np = embeddings_np.reshape(1, -1)
                else:
                    return False
            
            dimension = embeddings_np.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_np)
            
            # 保存索引和文档信息
            faiss.write_index(index, self.vector_index_file)
            with open(self.docs_info_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            
            self.index = index
            self.documents = documents
            
            logger.info(f"✅ 向量数据库构建完成！")
            logger.info(f"   - 包含 {len(documents)} 个文物文档")
            logger.info(f"   - 向量维度: {dimension}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 构建向量数据库时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _delete_existing_vector_db(self):
        """删除已存在的向量数据库文件"""
        deleted_files = []
        if os.path.exists(self.vector_index_file):
            os.remove(self.vector_index_file)
            deleted_files.append(self.vector_index_file)
            logger.info(f"✓ 已删除: {self.vector_index_file}")
        
        if os.path.exists(self.docs_info_file):
            os.remove(self.docs_info_file)
            deleted_files.append(self.docs_info_file)
            logger.info(f"✓ 已删除: {self.docs_info_file}")
        
        if deleted_files:
            logger.info(f"已删除 {len(deleted_files)} 个向量数据库文件，将重新构建")
    
    def _load_vector_db(self) -> bool:
        """加载向量数据库
        
        Returns:
            bool: 是否加载成功
        """
        if os.path.exists(self.vector_index_file) and os.path.exists(self.docs_info_file):
            try:
                self.index = faiss.read_index(self.vector_index_file)
                with open(self.docs_info_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                logger.info(f"✓ 向量数据库加载成功，包含 {len(self.documents)} 个文档")
                return True
            except Exception as e:
                logger.error(f"❌ 加载向量数据库失败: {str(e)}")
                return False
        else:
            logger.warning("❌ 向量数据库文件不存在")
            return False
    
    def search_normal(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """普通向量搜索（基于文本相似度）
        
        Args:
            query_text: 查询文本
            top_k: 返回最相似的文档数量
        
        Returns:
            list: 相似文档列表，每个元素包含content、metadata和score
        """
        if self.index is None or not self.documents or self.embedding_model is None:
            return []
        
        try:
            # 将查询文本转换为向量
            query_embedding = self._embed_text(query_text)
            if query_embedding is None or query_embedding.size == 0:
                return []
            
            query_embedding = np.array([query_embedding]).astype('float32')
            
            # 执行向量搜索
            distances, indices = self.index.search(query_embedding, top_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.documents):
                    similarity = 1.0 / (1.0 + float(distances[0][i]))
                    
                    results.append({
                        "content": self.documents[idx]["content"],
                        "metadata": self.documents[idx]["metadata"],
                        "score": similarity
                    })
            
            return results
        except Exception as e:
            logger.error(f"❌ 普通向量搜索过程出错: {str(e)}")
            return []
    
    def search_enhanced(self, query_text: str, top_k: int = 5, image_weight: float = 0.3) -> List[Dict]:
        """增强向量搜索（结合图片描述信息）
        
        Args:
            query_text: 查询文本
            top_k: 返回最相似的文档数量
            image_weight: 图片描述权重（0-1之间），默认0.3
        
        Returns:
            list: 相似文档列表，每个元素包含content、metadata和score
        """
        if self.index is None or not self.documents or self.embedding_model is None:
            return []
        
        try:
            # 先进行普通向量搜索，获取更多候选结果
            candidate_k = min(top_k * 3, len(self.documents))
            
            query_embedding = self._embed_text(query_text)
            if query_embedding is None or query_embedding.size == 0:
                return []
            
            query_embedding = np.array([query_embedding]).astype('float32')
            distances, indices = self.index.search(query_embedding, candidate_k)
            
            # 对查询文本进行分词，用于匹配图片描述
            query_words = set(jieba.cut(query_text.lower()))
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.documents):
                    # 基础相似度分数
                    base_similarity = 1.0 / (1.0 + float(distances[0][i]))
                    
                    # 获取图片识别结果
                    metadata = self.documents[idx].get("metadata", {})
                    recognition_result = metadata.get("recognition_result", {})
                    
                    # 计算图片描述匹配分数
                    image_score = 0.0
                    if recognition_result:
                        artifact_type = recognition_result.get("artifact_type", "")
                        recognized_name = recognition_result.get("recognized_name", "")
                        description = recognition_result.get("description", "")
                        
                        # 构建图片描述文本
                        image_text = f"{artifact_type} {recognized_name} {description}".lower()
                        image_words = set(jieba.cut(image_text))
                        
                        # 计算查询词与图片描述的重叠度
                        if len(query_words) > 0 and len(image_words) > 0:
                            overlap = len(query_words & image_words)
                            image_score = overlap / max(len(query_words), 1)
                        
                        # 考虑识别置信度
                        confidence = recognition_result.get("confidence", 0.0)
                        image_score = image_score * (0.5 + confidence * 0.5)
                    
                    # 综合分数
                    final_score = (1 - image_weight) * base_similarity + image_weight * image_score
                    
                    results.append({
                        "content": self.documents[idx]["content"],
                        "metadata": self.documents[idx]["metadata"],
                        "score": final_score,
                        "base_score": base_similarity,
                        "image_score": image_score
                    })
            
            # 按最终分数重新排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 返回 top_k 个结果
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ 增强向量搜索过程出错: {str(e)}")
            return []
    
    def is_ready(self) -> bool:
        """检查向量数据库是否已准备好"""
        return self.index is not None and len(self.documents) > 0

