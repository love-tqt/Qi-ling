# 故宫博物院向量数据库构建（增强版）
import os
import json
import pandas as pd
import numpy as np
import faiss
import jieba
import requests
import base64
import time
import tempfile
from paddlenlp.embeddings import TokenEmbedding
from openai import OpenAI

print("库导入成功！")

# 数据路径配置
MUSEUM_DOCS_PATH = "./data/museum_docs"
VECTOR_DB_PATH = "./data/vector_db"
VECTOR_INDEX_FILE = os.path.join(VECTOR_DB_PATH, "faiss.index")
DOCS_INFO_FILE = os.path.join(VECTOR_DB_PATH, "documents.json")
EXCEL_FILE_PATH = "./故宫博物院数字文物库.xlsx"

# 创建必要的目录
for dir_path in [MUSEUM_DOCS_PATH, VECTOR_DB_PATH]:
    os.makedirs(dir_path, exist_ok=True)

print("路径配置完成！")
print(f"Excel文件路径: {EXCEL_FILE_PATH}")
print(f"向量索引文件: {VECTOR_INDEX_FILE}")
print(f"文档信息文件: {DOCS_INFO_FILE}")

# 检查并删除已存在的向量数据库
def delete_existing_vector_db():
    """删除已存在的向量数据库文件"""
    deleted_files = []
    if os.path.exists(VECTOR_INDEX_FILE):
        os.remove(VECTOR_INDEX_FILE)
        deleted_files.append(VECTOR_INDEX_FILE)
        print(f"✓ 已删除: {VECTOR_INDEX_FILE}")
    
    if os.path.exists(DOCS_INFO_FILE):
        os.remove(DOCS_INFO_FILE)
        deleted_files.append(DOCS_INFO_FILE)
        print(f"✓ 已删除: {DOCS_INFO_FILE}")
    
    if deleted_files:
        print(f"\n已删除 {len(deleted_files)} 个向量数据库文件，将重新构建")
    else:
        print("\n未发现已存在的向量数据库文件")
    
    return len(deleted_files) > 0

# 执行删除操作
delete_existing_vector_db()

# 初始化ERNIE客户端
def init_ernie_client(api_key=None):
    """初始化ERNIE模型API客户端"""
    if not api_key:
        api_key = os.environ.get("AI_STUDIO_API_KEY") or "105296eef2bfd49d7cfb00e7e1c82828283cb0fb"
    
    if not api_key:
        print("⚠️ 警告: 未设置API密钥，图片识别功能将不可用")
        return None
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://aistudio.baidu.com/llm/lmapi/v3",
        )
        print("✓ ERNIE客户端初始化成功")
        return client
    except Exception as e:
        print(f"❌ 初始化ERNIE客户端失败: {str(e)}")
        return None

# 初始化客户端
ernie_client = init_ernie_client()

# 图片识别函数
def classify_artifact_image(client, image_url, kg_data=None):
    """使用ERNIE模型识别图片中的文物
    
    Args:
        client: ERNIE客户端
        image_url: 图片URL地址
        kg_data: 知识图谱数据（可选）
    
    Returns:
        tuple: (artifact_type, artifact_name, confidence, description)
    """
    if client is None:
        return "未知文物", "未知", 0.0, "无法识别：客户端未初始化"
    
    if not image_url or not image_url.strip():
        return "未知文物", "未知", 0.0, "无法识别：图片地址为空"
    
    try:
        # 下载图片
        response = requests.get(image_url, timeout=10)
        if response.status_code != 200:
            return "未知文物", "未知", 0.0, f"无法识别：下载图片失败（状态码：{response.status_code}）"
        
        # 将图片保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(response.content)
            tmp_image_path = tmp_file.name
        
        try:
            # 读取图片并转换为base64
            with open(tmp_image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 构建提示词
            prompt = """你是一位专业的中国古代文物识别专家。请仔细分析这张图片中的文物，并提供以下信息：

1. 文物类型（如：青铜器、陶俑、壁画、瓷器、玉器等）
2. 具体文物名称（如：司母戊鼎、兵马俑、清明上河图等，如无法确定具体名称则说"该类文物"）
3. 识别置信度（0.0-1.0之间的数值）
4. 简要介绍（50-100字，包括历史背景、艺术特色或文化价值）

请按以下格式回答：
文物类型：青铜器
具体名称：司母戊鼎
置信度：0.95
介绍：这是商代晚期的青铜器，具有重要的历史价值..."""
            
            # 调用模型服务
            start_time = time.time()
            if client is not None:
                response = client.chat.completions.create(
                    model="ernie-4.5-vl-28b-a3b-thinking",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1
                )
                result_text = response.choices[0].message.content
            else:
                return "未知文物", "未知", 0.0, "无法识别：模型服务不可用"
            response_time = time.time() - start_time
            
            # 提取信息
            artifact_type = "未知文物"
            artifact_name = "未知"
            confidence = 0.0
            description = "无法解析识别结果"
            
            lines = result_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('文物类型：') or line.startswith('文物类型:'):
                    artifact_type = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                elif line.startswith('具体名称：') or line.startswith('具体名称:'):
                    artifact_name = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                elif line.startswith('置信度：') or line.startswith('置信度:'):
                    try:
                        conf_str = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                        confidence = float(conf_str)
                    except:
                        confidence = 0.0
                elif line.startswith('介绍：') or line.startswith('介绍:'):
                    description = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            
            # 如果没有找到介绍，使用整个响应作为描述
            if description == "无法解析识别结果" and result_text:
                description = result_text[:200]  # 限制长度
            
            return artifact_type, artifact_name, confidence, description
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_image_path):
                os.remove(tmp_image_path)
                
    except requests.exceptions.RequestException as e:
        return "未知文物", "未知", 0.0, f"无法识别：网络请求失败 - {str(e)}"
    except Exception as e:
        return "未知文物", "未知", 0.0, f"无法识别：识别过程出错 - {str(e)}"

print("图片识别功能已加载")

# 加载词嵌入模型
def load_embedding_model():
    """加载词嵌入模型"""
    try:
        model = TokenEmbedding("w2v.baidu_encyclopedia.target.word-word.dim300")
        print("✓ 词嵌入模型加载成功")
        return model
    except Exception as e:
        print(f"❌ 加载词嵌入模型失败: {str(e)}")
        return None

embedding_model = load_embedding_model()

# 文本向量化函数
def embed_text(text, embedding_model):
    """将文本转换为向量嵌入
    
    Args:
        text: 要向量化的文本
        embedding_model: 词嵌入模型
    
    Returns:
        numpy.ndarray: 文本的向量表示（300维）
    """
    if embedding_model is None:
        return np.zeros(300)
    
    try:
        words = list(jieba.cut(text))
        word_embeddings = embedding_model.search(words)
        
        if len(word_embeddings) > 0:
            return np.mean(word_embeddings, axis=0)
        else:
            return np.zeros(300)
    except Exception as e:
        print(f"文本嵌入过程出错: {str(e)}")
        return np.zeros(300)

# 读取Excel文件并显示基本信息
try:
    df = pd.read_excel(EXCEL_FILE_PATH)
    print(f"✓ Excel文件读取成功，共 {len(df)} 条数据")
    print(f"  列名: {', '.join(df.columns.tolist())}")
except FileNotFoundError:
    print(f"❌ 错误: 找不到文件 '{EXCEL_FILE_PATH}'")
except Exception as e:
    print(f"❌ 读取Excel文件时出错: {str(e)}")

# 构建向量数据库
def build_vector_database(embedding_model):
    """从Excel文件构建故宫博物院文物知识的向量数据库（增强版）
    
    Args:
        embedding_model: 词嵌入模型
    
    Returns:
        tuple: (index, documents) FAISS索引和文档列表
    """
    documents = []
    
    # 检查Excel文件是否存在
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"❌ 错误: 找不到Excel文件 '{EXCEL_FILE_PATH}'")
        return None, []
    
    try:
        # 读取Excel文件，使用converters确保完整读取图片地址
        print(f"正在读取Excel文件: {EXCEL_FILE_PATH}")
        converters = {'图片地址': str}  # 确保图片地址列作为字符串完整读取
        df = pd.read_excel(EXCEL_FILE_PATH, converters=converters)
        
        # 检查必需的列是否存在
        required_columns = ['文物名称', '图片地址', '编号-年代', '历史', '工艺']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ 错误: Excel文件缺少必需的列: {missing_columns}")
            return None, []
        
        print(f"✓ 成功读取 {len(df)} 条文物数据")
        
        # 初始化ERNIE客户端用于图片识别
        print("\n正在初始化ERNIE客户端...")
        ernie_client = init_ernie_client()
        if ernie_client:
            print("✓ ERNIE客户端初始化成功")
        else:
            print("⚠️ ERNIE客户端初始化失败，将跳过图片识别")
        
        # 处理每一行数据
        print("\n开始处理数据并识别图片...")
        for idx, row in df.iterrows():
            # 获取各个字段
            artifact_name = str(row['文物名称']) if pd.notna(row['文物名称']) else ""
            image_url = str(row['图片地址']) if pd.notna(row['图片地址']) else ""
            number_period = str(row['编号-年代']) if pd.notna(row['编号-年代']) else ""
            history = str(row['历史']) if pd.notna(row['历史']) else ""
            craft = str(row['工艺']) if pd.notna(row['工艺']) else ""
            
            # 调用图片识别模型
            recognition_result = None
            if ernie_client and image_url and image_url.strip():
                if (idx + 1) % 100 == 0:
                    print(f"  正在识别第 {idx + 1}/{len(df)} 条数据的图片...")
                
                try:
                    artifact_type, recognized_name, confidence, description = classify_artifact_image(
                        ernie_client, image_url
                    )
                    recognition_result = {
                        "artifact_type": artifact_type,
                        "recognized_name": recognized_name,
                        "confidence": float(confidence),
                        "description": description
                    }
                except Exception as e:
                    print(f"  ⚠️ 第 {idx + 1} 条数据图片识别失败: {str(e)}")
                    recognition_result = {
                        "artifact_type": "未知文物",
                        "recognized_name": "未知",
                        "confidence": 0.0,
                        "description": f"识别失败: {str(e)}"
                    }
            else:
                # 如果没有客户端或图片地址，设置默认值
                recognition_result = {
                    "artifact_type": "未知文物",
                    "recognized_name": "未知",
                    "confidence": 0.0,
                    "description": "未进行识别"
                }
            
            # 组合文本内容用于向量化（包含所有相关信息，包括识别结果）
            content_parts = []
            if artifact_name:
                content_parts.append(f"文物名称：{artifact_name}")
            if number_period:
                content_parts.append(f"编号年代：{number_period}")
            if history:
                content_parts.append(f"历史：{history}")
            if craft:
                content_parts.append(f"工艺：{craft}")
            
            # 添加识别结果到内容中（用于向量搜索）
            if recognition_result:
                if recognition_result["artifact_type"] and recognition_result["artifact_type"] != "未知文物":
                    content_parts.append(f"识别类型：{recognition_result['artifact_type']}")
                if recognition_result["recognized_name"] and recognition_result["recognized_name"] != "未知":
                    content_parts.append(f"识别名称：{recognition_result['recognized_name']}")
                if recognition_result["description"] and recognition_result["description"] != "未进行识别":
                    content_parts.append(f"识别描述：{recognition_result['description']}")
            
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
                    "index": int(idx),
                    "recognition_result": recognition_result  # 添加识别结果字段
                }
            }
            documents.append(doc)
        
        print(f"✓ 处理完成，共 {len(documents)} 条有效文物数据")
        
    except Exception as e:
        print(f"❌ 读取Excel文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, []
    
    if not documents:
        print("❌ 没有找到有效数据，无法构建向量数据库")
        return None, []
    
    # 生成向量嵌入
    print("\n正在生成向量嵌入...")
    embeddings = []
    valid_docs = []
    
    for i, doc in enumerate(documents):
        if (i + 1) % 1000 == 0:
            print(f"  已处理 {i + 1}/{len(documents)} 条数据...")
        
        vector = embed_text(doc["content"], embedding_model)
        if vector is not None and vector.size > 0:
            embeddings.append(vector)
            valid_docs.append(doc)
    
    documents = valid_docs  # 只保留成功生成向量的文档
    
    if not embeddings:
        print("❌ 无法生成文档嵌入，无法构建向量数据库")
        return None, documents
    
    # 构建FAISS索引
    print("\n正在构建FAISS索引...")
    embeddings_np = np.array(embeddings).astype('float32')
    
    if len(embeddings_np.shape) < 2:
        print(f"⚠️ 嵌入数组形状不正确: {embeddings_np.shape}")
        if embeddings_np.size > 0:
            embeddings_np = embeddings_np.reshape(1, -1)
            print(f"✓ 已重塑为: {embeddings_np.shape}")
        else:
            return None, documents
    
    dimension = embeddings_np.shape[1] 
    index = faiss.IndexFlatL2(dimension)  
    index.add(embeddings_np)
    
    # 保存索引和文档信息
    faiss.write_index(index, VECTOR_INDEX_FILE)
    with open(DOCS_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 向量数据库构建完成！")
    print(f"   - 包含 {len(documents)} 个文物文档")
    print(f"   - 向量维度: {dimension}")
    print(f"   - 索引文件: {VECTOR_INDEX_FILE}")
    print(f"   - 文档文件: {DOCS_INFO_FILE}")
    return index, documents

# 构建向量数据库
print("=" * 80)
print("开始构建向量数据库")
print("=" * 80)

if embedding_model is None:
    print("❌ 词嵌入模型未加载，无法构建向量数据库")
    index, documents = None, []
else:
    index, documents = build_vector_database(embedding_model)
    
    if index is not None and documents:
        print("\n" + "=" * 80)
        print("向量数据库构建成功！")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("向量数据库构建失败！")
        print("=" * 80)

# 加载向量数据库
def load_vector_db():
    """加载向量数据库
    
    Returns:
        tuple: (index, documents) FAISS索引和文档列表
    """
    if os.path.exists(VECTOR_INDEX_FILE) and os.path.exists(DOCS_INFO_FILE):
        try:
            index = faiss.read_index(VECTOR_INDEX_FILE)
            with open(DOCS_INFO_FILE, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            print(f"✓ 向量数据库加载成功，包含 {len(documents)} 个文档")
            return index, documents
        except Exception as e:
            print(f"❌ 加载向量数据库失败: {str(e)}")
            return None, None
    else:
        print("❌ 向量数据库文件不存在")
        return None, None

# 向量搜索功能
def search_normal(query_text, embedding_model, index, documents, top_k=5):
    """普通向量搜索（基于文本相似度）
    
    Args:
        query_text: 查询文本
        embedding_model: 词嵌入模型
        index: FAISS索引
        documents: 文档列表
        top_k: 返回最相似的文档数量
    
    Returns:
        list: 相似文档列表，每个元素包含content、metadata和score
    """
    if index is None or documents is None or embedding_model is None:
        return []
    
    try:
        # 将查询文本转换为向量
        query_embedding = embed_text(query_text, embedding_model)
        if query_embedding is None or query_embedding.size == 0:
            return []
        
        query_embedding = np.array([query_embedding]).astype('float32')
        
        # 执行向量搜索
        distances, indices = index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(documents):
                similarity = 1.0 / (1.0 + float(distances[0][i]))
                
                results.append({
                    "content": documents[idx]["content"],
                    "metadata": documents[idx]["metadata"],
                    "score": similarity
                })
        
        return results
    except Exception as e:
        print(f"❌ 普通向量搜索过程出错: {str(e)}")
        return []

def search_enhanced(query_text, embedding_model, index, documents, top_k=5, image_weight=0.8):
    """增强向量搜索（结合图片描述信息）
    
    增强搜索会考虑文档中的图片识别结果，对包含相关图片描述的文档给予更高的权重。
    
    Args:
        query_text: 查询文本
        embedding_model: 词嵌入模型
        index: FAISS索引
        documents: 文档列表
        top_k: 返回最相似的文档数量
        image_weight: 图片描述权重（0-1之间），默认0.3，表示图片描述占30%的权重
    
    Returns:
        list: 相似文档列表，每个元素包含content、metadata和score
    """
    if index is None or documents is None or embedding_model is None:
        return []
    
    try:
        # 先进行普通向量搜索，获取更多候选结果（扩大搜索范围）
        candidate_k = min(top_k * 3, len(documents))  # 获取更多候选结果用于重排序
        
        query_embedding = embed_text(query_text, embedding_model)
        if query_embedding is None or query_embedding.size == 0:
            return []
        
        query_embedding = np.array([query_embedding]).astype('float32')
        distances, indices = index.search(query_embedding, candidate_k)
        
        # 对查询文本进行分词，用于匹配图片描述
        query_words = set(jieba.cut(query_text.lower()))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(documents):
                # 基础相似度分数
                base_similarity = 1.0 / (1.0 + float(distances[0][i]))
                
                # 获取图片识别结果
                metadata = documents[idx].get("metadata", {})
                recognition_result = metadata.get("recognition_result", {})
                
                # 计算图片描述匹配分数
                image_score = 0.0
                if recognition_result:
                    # 提取图片描述中的关键词
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
                    image_score = image_score * (0.5 + confidence * 0.5)  # 置信度影响图片分数
                
                # 综合分数：基础相似度 + 图片描述增强
                # image_weight 控制图片描述的权重
                final_score = (1 - image_weight) * base_similarity + image_weight * image_score
                
                results.append({
                    "content": documents[idx]["content"],
                    "metadata": documents[idx]["metadata"],
                    "score": final_score,
                    "base_score": base_similarity,  # 保留基础分数用于对比
                    "image_score": image_score  # 保留图片分数用于调试
                })
        
        # 按最终分数重新排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回 top_k 个结果
        return results[:top_k]
        
    except Exception as e:
        print(f"❌ 增强向量搜索过程出错: {str(e)}")
        return []

# 测试向量搜索功能
def test_normal_search(index, documents, embedding_model, test_queries=None, top_k=5):
    """测试普通向量搜索功能
    
    Args:
        index: FAISS索引
        documents: 文档列表
        embedding_model: 词嵌入模型
        test_queries: 测试查询列表，如果为None则使用默认查询
        top_k: 返回最相似的文档数量
    """
    if index is None or documents is None or embedding_model is None:
        print("⚠️ 向量数据库未构建，无法进行测试")
        return
    
    if test_queries is None:
        test_queries = [
            "白玉",
            "乾隆",
            "青铜器",
            "玉器工艺",
            "珐琅"
        ]
    
    print("\n" + "=" * 80)
    print("测试普通向量搜索功能")
    print("=" * 80)
    print(f"测试查询数量: {len(test_queries)}")
    print(f"每个查询返回结果数: {top_k}")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n【测试 {i}/{len(test_queries)}】查询: '{query}'")
        print("-" * 80)
        
        results = search_normal(query, embedding_model, index, documents, top_k=top_k)
        
        if results:
            print(f"✓ 找到 {len(results)} 个相关文物:")
            for j, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                score = result.get("score", 0)
                artifact_name = metadata.get('artifact_name', 'N/A')
                number_period = metadata.get('number_period', 'N/A')
                print(f"  {j}. {artifact_name}")
                print(f"     编号年代: {number_period}")
                print(f"     相似度: {score:.4f}")
        else:
            print("✗ 未找到相关文物")
    
    print("\n" + "=" * 80)
    print("普通搜索测试完成！")
    print("=" * 80)

def test_enhanced_search(index, documents, embedding_model, test_queries=None, top_k=5, image_weight=0.3):
    """测试增强向量搜索功能（包含图片描述）
    
    Args:
        index: FAISS索引
        documents: 文档列表
        embedding_model: 词嵌入模型
        test_queries: 测试查询列表，如果为None则使用默认查询
        top_k: 返回最相似的文档数量
        image_weight: 图片描述权重（0-1之间）
    """
    if index is None or documents is None or embedding_model is None:
        print("⚠️ 向量数据库未构建，无法进行测试")
        return
    
    if test_queries is None:
        test_queries = [
            "白玉",
            "乾隆",
            "青铜器",
            "玉器工艺",
            "珐琅"
        ]
    
    print("\n" + "=" * 80)
    print("测试增强向量搜索功能（包含图片描述）")
    print("=" * 80)
    print(f"测试查询数量: {len(test_queries)}")
    print(f"每个查询返回结果数: {top_k}")
    print(f"图片描述权重: {image_weight}")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n【测试 {i}/{len(test_queries)}】查询: '{query}'")
        print("-" * 80)
        
        # 执行增强搜索
        enhanced_results = search_enhanced(query, embedding_model, index, documents, top_k=top_k, image_weight=image_weight)
        
        # 同时执行普通搜索用于对比
        normal_results = search_normal(query, embedding_model, index, documents, top_k=top_k)
        
        if enhanced_results:
            print(f"✓ 增强搜索找到 {len(enhanced_results)} 个相关文物:")
            for j, result in enumerate(enhanced_results, 1):
                metadata = result.get("metadata", {})
                score = result.get("score", 0)
                base_score = result.get("base_score", 0)
                image_score = result.get("image_score", 0)
                artifact_name = metadata.get('artifact_name', 'N/A')
                number_period = metadata.get('number_period', 'N/A')
                
                # 获取图片识别结果
                recognition_result = metadata.get("recognition_result", {})
                artifact_type = recognition_result.get("artifact_type", "未知")
                recognized_name = recognition_result.get("recognized_name", "未知")
                confidence = recognition_result.get("confidence", 0.0)
                
                print(f"  {j}. {artifact_name}")
                print(f"     编号年代: {number_period}")
                print(f"     综合相似度: {score:.4f} (基础: {base_score:.4f}, 图片: {image_score:.4f})")
                if recognition_result and artifact_type != "未知文物":
                    print(f"     图片识别: {artifact_type} - {recognized_name} (置信度: {confidence:.2f})")
            
            # 对比普通搜索和增强搜索的差异
            print(f"\n  对比分析:")
            print(f"    - 增强搜索与普通搜索结果顺序是否相同: ", end="")
            enhanced_names = [r.get("metadata", {}).get("artifact_name") for r in enhanced_results]
            normal_names = [r.get("metadata", {}).get("artifact_name") for r in normal_results]
            if enhanced_names == normal_names:
                print("相同")
            else:
                print("不同（增强搜索考虑了图片描述）")
                if enhanced_names[0] != normal_names[0]:
                    print(f"    - 增强搜索第一名: {enhanced_names[0]}")
                    print(f"    - 普通搜索第一名: {normal_names[0]}")
        else:
            print("✗ 未找到相关文物")
    
    print("\n" + "=" * 80)
    print("增强搜索测试完成！")
    print("=" * 80)

# 执行测试
if index is not None and documents and embedding_model is not None:
    # 测试普通搜索
    test_normal_search(index, documents, embedding_model, top_k=5)
    
    # 测试增强搜索
    test_enhanced_search(index, documents, embedding_model, top_k=5, image_weight=0.3)
else:
    print("⚠️ 向量数据库未构建，跳过测试")
    print("提示: 请先运行 build_vector_database() 函数构建向量数据库")

# 本地图片识别功能
def classify_artifact_image_from_file(client, image_path):
    """从本地文件识别图片中的文物
    
    Args:
        client: ERNIE客户端
        image_path: 本地图片文件路径
    
    Returns:
        tuple: (artifact_type, artifact_name, confidence, description)
    """
    if client is None:
        return "未知文物", "未知", 0.0, "无法识别：客户端未初始化"
    
    if not image_path or not os.path.exists(image_path):
        return "未知文物", "未知", 0.0, "无法识别：图片文件不存在"
    
    try:
        # 读取图片并转换为base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 构建提示词
        prompt = """你是一位专业的中国古代文物识别专家。请仔细分析这张图片中的文物，并提供以下信息：

1. 文物类型（如：青铜器、陶俑、壁画、瓷器、玉器等）
2. 具体文物名称（如：司母戊鼎、兵马俑、清明上河图等，如无法确定具体名称则说"该类文物"）
3. 识别置信度（0.0-1.0之间的数值）
4. 简要介绍（50-100字，包括历史背景、艺术特色或文化价值）

请按以下格式回答：
文物类型：青铜器
具体名称：司母戊鼎
置信度：0.95
介绍：这是商代晚期的青铜器，具有重要的历史价值..."""
        
        # 调用ERNIE模型
        start_time = time.time()
        response = client.chat.completions.create(
             model="ernie-4.5-vl-28b-a3b-thinking",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1
        )
        response_time = time.time() - start_time
        
        # 解析响应
        result_text = response.choices[0].message.content
        
        # 提取信息
        artifact_type = "未知文物"
        artifact_name = "未知"
        confidence = 0.0
        description = "无法解析识别结果"
        
        lines = result_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('文物类型：') or line.startswith('文物类型:'):
                artifact_type = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            elif line.startswith('具体名称：') or line.startswith('具体名称:'):
                artifact_name = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            elif line.startswith('置信度：') or line.startswith('置信度:'):
                try:
                    conf_str = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                    confidence = float(conf_str)
                except:
                    confidence = 0.0
            elif line.startswith('介绍：') or line.startswith('介绍:'):
                description = line.split('：', 1)[-1].split(':', 1)[-1].strip()
        
        # 如果没有找到介绍，使用整个响应作为描述
        if description == "无法解析识别结果" and result_text:
            description = result_text[:200]  # 限制长度
        
        return artifact_type, artifact_name, confidence, description
        
    except Exception as e:
        return "未知文物", "未知", 0.0, f"无法识别：识别过程出错 - {str(e)}"

print("本地图片识别功能已加载")

# 图片路径识别测试功能
def test_image_path_recognition(image_path, ernie_client=None):
    """测试图片路径识别功能
    
    Args:
        image_path: 本地图片文件路径
        ernie_client: ERNIE客户端，如果为None则使用全局的ernie_client
    """
    if ernie_client is None:
        ernie_client = globals().get('ernie_client')
    
    if ernie_client is None:
        print("⚠️ ERNIE客户端未初始化，无法进行图片识别")
        print("提示: 请先运行 init_ernie_client() 函数初始化客户端")
        return None
    
    if not image_path or not os.path.exists(image_path):
        print(f"⚠️ 图片文件不存在: {image_path}")
        print("提示: 请提供有效的图片文件路径")
        return None
    
    print("=" * 80)
    print("开始识别图片...")
    print("=" * 80)
    print(f"图片路径: {image_path}")
    print("-" * 80)
    
    try:
        
        # 执行识别
        print("\n【识别中...】")
        start_time = time.time()
        artifact_type, artifact_name, confidence, description = classify_artifact_image_from_file(
            ernie_client, image_path
        )
        elapsed_time = time.time() - start_time
        
        # 显示识别结果
        print("\n" + "=" * 80)
        print("识别结果")
        print("=" * 80)
        print(f"文物类型: {artifact_type}")
        print(f"具体名称: {artifact_name}")
        print(f"置信度: {confidence:.2f}")
        print(f"识别耗时: {elapsed_time:.2f} 秒")
        print(f"\n介绍:")
        print(f"{description}")
        print("=" * 80)
        
        # 如果向量数据库已构建，可以进行相似文物搜索
        index = globals().get('index')
        documents = globals().get('documents')
        embedding_model = globals().get('embedding_model')
        
        if index is not None and documents and embedding_model is not None:
            print("\n" + "=" * 80)
            print("基于识别结果搜索相似文物")
            print("=" * 80)
            
            # 构建搜索查询（使用识别结果）
            search_query = f"{artifact_type} {artifact_name}"
            print(f"搜索查询: '{search_query}'")
            print("-" * 80)
            
            # 执行增强搜索
            results = search_enhanced(
                search_query, 
                embedding_model, 
                index, 
                documents, 
                top_k=5, 
                image_weight=0.3
            )
            
            if results:
                print(f"\n✓ 找到 {len(results)} 个相似文物:")
                for j, result in enumerate(results, 1):
                    metadata = result.get("metadata", {})
                    score = result.get("score", 0)
                    result_name = metadata.get('artifact_name', 'N/A')
                    number_period = metadata.get('number_period', 'N/A')
                    print(f"\n  {j}. {result_name}")
                    print(f"     编号年代: {number_period}")
                    print(f"     相似度: {score:.4f}")
            else:
                print("\n✗ 未找到相似文物")
            
            print("=" * 80)
        
        return {
            "artifact_type": artifact_type,
            "artifact_name": artifact_name,
            "confidence": confidence,
            "description": description,
            "elapsed_time": elapsed_time
        }
        
    except Exception as e:
        print(f"\n❌ 识别失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

print("图片路径识别测试功能已加载")

# 运行图片上传识别测试
# 注意：需要先初始化ERNIE客户端（ernie_client）才能使用
# 示例：
test_image_path_recognition("/home/aistudio/3.png")

print("\n所有核心功能已整合完成！")
print("主要功能包括：")
print("1. 向量数据库构建")
print("2. 普通向量搜索")
print("3. 增强向量搜索（结合图片识别）")
print("4. 图片识别功能")
print("5. 本地图片识别测试")