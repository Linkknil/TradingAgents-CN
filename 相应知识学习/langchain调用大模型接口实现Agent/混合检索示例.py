#!/usr/bin/env python3
"""
混合检索示例演示

展示向量检索、关键词检索和混合检索的区别和效果。
"""

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
import numpy as np
from typing import List, Tuple


def create_sample_documents() -> List[Document]:
    """创建示例文档用于演示"""
    documents = [
        Document(
            page_content="苹果公司(AAPL)的股价在2024年第一季度上涨了15%，主要得益于iPhone销量增长和AI芯片业务的突破。公司CEO蒂姆·库克表示对未来发展充满信心。",
            metadata={"source": "财经新闻", "date": "2024-03-15"}
        ),
        Document(
            page_content="人工智能技术在金融领域的应用越来越广泛，包括量化交易、风险评估、智能投顾和算法交易等。这些技术正在改变传统的投资方式。",
            metadata={"source": "技术报告", "date": "2024-02-20"}
        ),
        Document(
            page_content="AAPL股票代码对应的公司是苹果公司，其市值超过3万亿美元，是全球市值最高的公司之一。苹果公司总部位于美国加利福尼亚州库比蒂诺。",
            metadata={"source": "公司简介", "date": "2024-01-10"}
        ),
        Document(
            page_content="股票投资需要关注公司的基本面分析，包括财务指标、行业地位、管理团队和未来发展前景。技术分析也是重要的投资工具。",
            metadata={"source": "投资指南", "date": "2024-02-05"}
        ),
        Document(
            page_content="苹果公司最新发布的iPhone 15系列手机在市场上表现优异，销量超出预期。同时，公司在AI和机器学习领域投入巨大，开发了A17 Pro芯片。",
            metadata={"source": "产品新闻", "date": "2024-03-20"}
        ),
        Document(
            page_content="量化交易使用数学模型和算法来分析市场数据，寻找投资机会。这种方法在股票、期货和外汇市场都有广泛应用。",
            metadata={"source": "交易策略", "date": "2024-01-25"}
        )
    ]
    return documents


def simple_vector_search(query: str, documents: List[Document]) -> List[Tuple[Document, float]]:
    """简单的向量搜索模拟（实际项目中会使用真实的embedding模型）"""
    # 这里使用简单的关键词匹配来模拟向量搜索
    query_words = set(query.lower().split())
    
    results = []
    for doc in documents:
        doc_words = set(doc.page_content.lower().split())
        # 计算词汇重叠度作为相似度分数
        overlap = len(query_words & doc_words)
        similarity = overlap / len(query_words) if query_words else 0
        results.append((doc, similarity))
    
    # 按相似度排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def keyword_search(query: str, documents: List[Document]) -> List[Document]:
    """关键词搜索"""
    query_words = set(query.lower().split())
    
    results = []
    for doc in documents:
        doc_text = doc.page_content.lower()
        # 计算关键词匹配数量
        matches = sum(1 for word in query_words if word in doc_text)
        if matches > 0:
            results.append((doc, matches))
    
    # 按匹配数量排序
    results.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in results]


def hybrid_search(
    query: str, 
    documents: List[Document], 
    vector_weight: float = 0.7, 
    keyword_weight: float = 0.3
) -> List[Document]:
    """混合搜索"""
    # 获取向量搜索结果
    vector_results = simple_vector_search(query, documents)
    
    # 获取关键词搜索结果
    keyword_results = keyword_search(query, documents)
    
    # 创建文档到分数的映射
    doc_scores = {}
    
    # 处理向量搜索结果
    for doc, score in vector_results:
        doc_id = id(doc)
        doc_scores[doc_id] = {
            'doc': doc,
            'vector_score': score,
            'keyword_score': 0.0
        }
    
    # 处理关键词搜索结果
    for i, doc in enumerate(keyword_results):
        doc_id = id(doc)
        keyword_score = 1.0 / (i + 1)  # 排名分数
        
        if doc_id in doc_scores:
            doc_scores[doc_id]['keyword_score'] = keyword_score
        else:
            doc_scores[doc_id] = {
                'doc': doc,
                'vector_score': 0.0,
                'keyword_score': keyword_score
            }
    
    # 计算综合分数
    scored_docs = []
    for doc_id, scores in doc_scores.items():
        combined_score = (
            vector_weight * scores['vector_score'] + 
            keyword_weight * scores['keyword_score']
        )
        scored_docs.append((scores['doc'], combined_score))
    
    # 按综合分数排序
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return [doc for doc, score in scored_docs]


def demonstrate_retrieval_methods():
    """演示不同检索方法的效果"""
    print("=" * 80)
    print("混合检索演示")
    print("=" * 80)
    
    # 创建示例文档
    documents = create_sample_documents()
    
    # 测试查询
    queries = [
        "苹果公司股票表现如何？",
        "人工智能在金融领域的应用",
        "AAPL公司的市值和总部位置",
        "量化交易和算法交易的区别"
    ]
    
    for query in queries:
        print(f"\n🔍 查询: {query}")
        print("-" * 60)
        
        # 1. 向量搜索
        print("\n📊 向量搜索结果:")
        vector_results = simple_vector_search(query, documents)
        for i, (doc, score) in enumerate(vector_results[:3], 1):
            print(f"  {i}. [相似度: {score:.3f}] {doc.page_content[:100]}...")
        
        # 2. 关键词搜索
        print("\n🔤 关键词搜索结果:")
        keyword_results = keyword_search(query, documents)
        for i, doc in enumerate(keyword_results[:3], 1):
            print(f"  {i}. {doc.page_content[:100]}...")
        
        # 3. 混合搜索（平衡权重）
        print("\n⚖️ 混合搜索结果 (平衡权重 0.5:0.5):")
        hybrid_results = hybrid_search(query, documents, 0.5, 0.5)
        for i, doc in enumerate(hybrid_results[:3], 1):
            print(f"  {i}. {doc.page_content[:100]}...")
        
        # 4. 混合搜索（向量权重高）
        print("\n🎯 混合搜索结果 (向量权重高 0.8:0.2):")
        vector_heavy_results = hybrid_search(query, documents, 0.8, 0.2)
        for i, doc in enumerate(vector_heavy_results[:3], 1):
            print(f"  {i}. {doc.page_content[:100]}...")
        
        # 5. 混合搜索（关键词权重高）
        print("\n🔍 混合搜索结果 (关键词权重高 0.2:0.8):")
        keyword_heavy_results = hybrid_search(query, documents, 0.2, 0.8)
        for i, doc in enumerate(keyword_heavy_results[:3], 1):
            print(f"  {i}. {doc.page_content[:100]}...")


def analyze_retrieval_characteristics():
    """分析不同检索方法的特点"""
    print("\n" + "=" * 80)
    print("检索方法特点分析")
    print("=" * 80)
    
    characteristics = {
        "向量检索": {
            "优势": [
                "理解语义相似性",
                "能匹配同义词和近义词",
                "适合概念性搜索",
                "对查询表达方式不敏感"
            ],
            "劣势": [
                "可能错过精确的关键词匹配",
                "对专业术语和数字不够敏感",
                "计算成本较高"
            ],
            "适用场景": [
                "概念性查询",
                "同义词丰富的领域",
                "需要语义理解的场景"
            ]
        },
        "关键词检索": {
            "优势": [
                "精确匹配特定术语",
                "检索速度快",
                "对数字、代码、专业术语敏感",
                "计算成本低"
            ],
            "劣势": [
                "无法理解语义关系",
                "对查询表达方式敏感",
                "可能错过相关但用词不同的内容"
            ],
            "适用场景": [
                "精确术语查询",
                "专业领域搜索",
                "需要快速响应的场景"
            ]
        },
        "混合检索": {
            "优势": [
                "结合两种方法的优势",
                "提高检索准确性和召回率",
                "适应不同类型的查询",
                "可调节权重平衡"
            ],
            "劣势": [
                "计算成本较高",
                "需要调优权重参数",
                "实现复杂度较高"
            ],
            "适用场景": [
                "综合知识库搜索",
                "需要高准确率的场景",
                "查询类型多样化的应用"
            ]
        }
    }
    
    for method, info in characteristics.items():
        print(f"\n📋 {method}:")
        print(f"  优势: {', '.join(info['优势'])}")
        print(f"  劣势: {', '.join(info['劣势'])}")
        print(f"  适用场景: {', '.join(info['适用场景'])}")


def show_implementation_tips():
    """展示实现建议"""
    print("\n" + "=" * 80)
    print("混合检索实现建议")
    print("=" * 80)
    
    tips = [
        "1. 权重调优: 根据具体应用场景调整向量检索和关键词检索的权重比例",
        "2. 查询预处理: 对用户查询进行清洗、扩展和标准化",
        "3. 结果去重: 避免返回重复的文档片段",
        "4. 性能优化: 使用缓存和异步处理提高响应速度",
        "5. 评估指标: 使用MRR、NDCG等指标评估检索效果",
        "6. 动态权重: 根据查询类型动态调整权重比例",
        "7. 查询扩展: 使用同义词、相关词扩展查询",
        "8. 结果重排序: 基于额外信号对结果进行重新排序"
    ]
    
    for tip in tips:
        print(f"  {tip}")


if __name__ == "__main__":
    # 运行演示
    demonstrate_retrieval_methods()
    analyze_retrieval_characteristics()
    show_implementation_tips()
    
    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)

