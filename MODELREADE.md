# 故宫博物院文物知识向量数据库系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个基于向量数据库的故宫博物院文物知识检索系统，支持文本搜索和图片识别功能，结合ERNIE多模态模型实现智能文物识别与检索。

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [使用示例](#使用示例)
- [部署指南](#部署指南)
- [模型说明](#模型说明)
- [API文档](#api文档)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 项目简介

本项目是一个智能化的文物知识检索系统，旨在帮助用户快速检索和了解故宫博物院的文物信息。系统结合了：

- **向量数据库技术**：使用FAISS构建高效的相似度搜索索引
- **自然语言处理**：基于PaddleNLP的词嵌入模型进行文本向量化
- **多模态AI**：集成ERNIE视觉模型实现图片识别功能
- **增强搜索**：结合文本和图片信息提供更精准的检索结果

### 应用场景

- 🏛️ 博物馆数字化管理
- 📚 文物知识库构建
- 🔍 智能文物检索
- 🖼️ 文物图片识别与分类
- 📖 文物知识问答系统

## ✨ 核心功能

### 1. 向量数据库构建
- 从Excel文件自动读取文物数据
- 使用PaddleNLP词嵌入模型进行文本向量化
- 基于FAISS构建高效的向量索引
- 支持增量更新和重建

### 2. 文本搜索
- **普通搜索**：基于文本相似度的向量搜索
- **增强搜索**：结合图片识别结果的多模态搜索
- 支持自定义返回结果数量（top_k）
- 返回相似度分数和详细元数据

### 3. 图片识别
- 支持URL和本地文件两种图片输入方式
- 使用ERNIE-4.5-VL多模态模型进行识别
- 自动识别文物类型、名称、置信度和描述
- 识别结果自动关联到向量数据库

### 4. 数据管理
- 自动检测并重建已存在的向量数据库
- 支持Excel格式的数据导入
- 文档信息持久化存储（JSON格式）
- 向量索引持久化存储（FAISS格式）

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户接口层                            │
│  (Jupyter Notebook / Python API / Web Interface)        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    应用服务层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  文本搜索    │  │  图片识别    │  │  数据管理    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│   向量数据库层    │              │    AI模型层       │
│  ┌────────────┐  │              │  ┌────────────┐  │
│  │  FAISS     │  │              │  │  PaddleNLP │  │
│  │  索引      │  │              │  │  词嵌入    │  │
│  └────────────┘  │              │  └────────────┘  │
│  ┌────────────┐  │              │  ┌────────────┐  │
│  │  文档存储  │  │              │  │  ERNIE-VL  │  │
│  │  (JSON)    │  │              │  │  视觉模型  │  │
│  └────────────┘  │              │  └────────────┘  │
└──────────────────┘              └──────────────────┘
```

### 技术栈

- **向量数据库**: FAISS (Facebook AI Similarity Search)
- **NLP框架**: PaddleNLP
- **深度学习**: PaddlePaddle
- **文本处理**: Jieba中文分词
- **数据处理**: Pandas, NumPy
- **AI模型**: ERNIE-4.5-VL-28B-A3B-Thinking
- **API客户端**: OpenAI SDK (兼容ERNIE API)

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本（推荐 3.8-3.11）
- 操作系统：Windows / Linux / macOS
- 内存：建议 8GB 以上
- 存储：至少 2GB 可用空间（用于模型和向量数据库）

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd qiling_model
```

#### 2. 创建虚拟环境（推荐）

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**: 如果安装PaddlePaddle遇到问题，请参考[官方安装指南](https://www.paddlepaddle.org.cn/install/quick)

#### 4. 配置API密钥

设置ERNIE API密钥（用于图片识别功能）：

**方法1：使用配置文件（推荐）**

1. 复制示例配置文件：
```bash
cp config.example.json config.json
```

2. 编辑 `config.json`，填入你的API密钥：
```json
{
  "api_key": "your_api_key_here",
  "museum_docs_path": "./data/museum_docs",
  "vector_db_path": "./data/vector_db",
  "excel_file_path": "./故宫博物院数字文物库.xlsx"
}
```

**方法2：使用环境变量**

**Windows:**
```bash
set AI_STUDIO_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export AI_STUDIO_API_KEY=your_api_key_here
```

**优先级说明：**
- 如果代码中直接传入`api_key`参数，则优先使用
- 其次使用`config.json`中的`api_key`
- 最后使用环境变量`AI_STUDIO_API_KEY`

#### 5. 准备数据文件

将文物数据Excel文件放置在项目根目录，文件名为 `故宫博物院数字文物库.xlsx`。

Excel文件应包含以下列：
- `文物名称`: 文物的名称
- `图片地址`: 文物图片的URL或本地路径
- `编号-年代`: 文物的编号和年代信息
- `历史`: 文物的历史背景
- `工艺`: 文物的工艺特点

#### 6. 运行Jupyter Notebook

```bash
jupyter notebook qiling.ipynb
```

按照notebook中的步骤依次执行：
1. 导入库
2. 配置路径
3. 初始化ERNIE客户端
4. 加载词嵌入模型
5. 构建向量数据库
6. 执行搜索和识别

## 📖 使用示例

### 示例1: 基本文本搜索

```python
from qiling_model import VectorDBSearch

# 初始化搜索器
searcher = VectorDBSearch()

# 执行普通搜索
results = searcher.search_normal("青铜器", top_k=5)

# 打印结果
for i, result in enumerate(results, 1):
    print(f"\n结果 {i}:")
    print(f"  相似度: {result['score']:.4f}")
    print(f"  内容: {result['content'][:100]}...")
    print(f"  文物名称: {result['metadata'].get('artifact_name', 'N/A')}")
```

### 示例2: 增强搜索（结合图片信息）

```python
# 执行增强搜索
results = searcher.search_enhanced("商代青铜器", top_k=5, image_weight=0.8)

# 增强搜索会考虑图片识别结果，对包含相关图片描述的文档给予更高权重
for result in results:
    recognition = result['metadata'].get('recognition_result', {})
    if recognition:
        print(f"图片识别: {recognition.get('artifact_type')} - {recognition.get('recognized_name')}")
```

### 示例3: 图片识别

```python
from qiling_model import ArtifactImageClassifier

# 初始化分类器
classifier = ArtifactImageClassifier()

# 从URL识别图片
artifact_type, name, confidence, description = classifier.classify_from_url(
    "https://example.com/artifact.jpg"
)

print(f"文物类型: {artifact_type}")
print(f"文物名称: {name}")
print(f"置信度: {confidence:.2f}")
print(f"描述: {description}")

# 从本地文件识别
artifact_type, name, confidence, description = classifier.classify_from_file(
    "./uploaded_images/artifact.png"
)
```

### 示例4: 完整工作流

```python
# 1. 构建向量数据库
from qiling_model import VectorDBBuilder

builder = VectorDBBuilder()
index, documents = builder.build_from_excel("故宫博物院数字文物库.xlsx")

# 2. 执行搜索
searcher = VectorDBSearch(index, documents)
results = searcher.search_enhanced("古代青铜器", top_k=3)

# 3. 对搜索结果中的图片进行识别（如果尚未识别）
classifier = ArtifactImageClassifier()
for result in results:
    image_url = result['metadata'].get('image_url')
    if image_url:
        artifact_type, name, conf, desc = classifier.classify_from_url(image_url)
        print(f"识别结果: {name} ({artifact_type}) - 置信度: {conf:.2f}")
```

更多示例代码请参考 [examples/](examples/) 目录。

## 🚢 部署指南

详细的部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

### 快速部署

#### 本地部署

1. 按照[快速开始](#快速开始)完成环境配置
2. 运行notebook构建向量数据库
3. 使用提供的Python模块进行集成

#### Docker部署

```bash
# 构建镜像
docker build -t qiling-model:latest .

# 运行容器
docker run -p 8888:8888 -v $(pwd)/data:/app/data qiling-model:latest
```

#### 生产环境部署

1. 使用Gunicorn或uWSGI部署Web服务
2. 配置Nginx反向代理
3. 设置环境变量和API密钥
4. 配置日志和监控

## 🤖 模型说明

### 词嵌入模型

- **模型名称**: `w2v.baidu_encyclopedia.target.word-word.dim300`
- **来源**: PaddleNLP预训练模型
- **维度**: 300维
- **用途**: 将中文文本转换为向量表示

### 视觉识别模型

- **模型名称**: `ernie-4.5-vl-28b-a3b-thinking`
- **类型**: 多模态视觉语言模型
- **功能**: 文物图片识别、分类和描述生成
- **API**: 通过百度AI Studio API调用

### 模型服务接口

系统支持通过统一的模型服务接口调用，便于切换不同的模型实现：

```python
class ModelService:
    def call_vision_model(self, prompt, base64_image, temperature=0.1):
        """调用视觉模型"""
        pass
```

## 📚 API文档

### VectorDBSearch

向量数据库搜索类

#### 方法

- `search_normal(query_text, top_k=5)`: 普通文本搜索
- `search_enhanced(query_text, top_k=5, image_weight=0.8)`: 增强搜索

### ArtifactImageClassifier

文物图片分类器

#### 方法

- `classify_from_url(image_url)`: 从URL识别图片
- `classify_from_file(image_path)`: 从本地文件识别图片

### VectorDBBuilder

向量数据库构建器

#### 方法

- `build_from_excel(excel_path)`: 从Excel文件构建向量数据库
- `load_existing()`: 加载已存在的向量数据库

详细API文档请参考 [API.md](docs/API.md)

## ❓ 常见问题

### Q1: 如何获取ERNIE API密钥？

A: 访问[百度AI Studio](https://aistudio.baidu.com/)，注册账号后获取API密钥。

### Q2: 向量数据库构建失败怎么办？

A: 
1. 检查Excel文件路径是否正确
2. 确认Excel文件包含必需的列
3. 检查磁盘空间是否充足
4. 查看错误日志获取详细信息

### Q3: 图片识别功能不可用？

A:
1. 确认已设置API密钥
2. 检查网络连接
3. 验证图片URL是否可访问
4. 确认API配额是否充足

### Q4: 如何提高搜索准确性？

A:
1. 使用增强搜索模式（`search_enhanced`）
2. 调整`image_weight`参数
3. 确保图片识别结果准确
4. 优化查询文本的关键词

### Q5: 支持哪些图片格式？

A: 支持常见图片格式（PNG, JPG, JPEG等），系统会自动处理格式转换。

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。



**注意**: 如果您询问关于模型相关的问题或判断问题，我会回答：

1. **模型名称**: `ernie-4.5-vl-28b-a3b-thinking`

---

*最后更新: 2025年*

