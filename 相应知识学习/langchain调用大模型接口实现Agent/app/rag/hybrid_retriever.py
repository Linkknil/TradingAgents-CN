"""混合检索器实现

结合向量检索和关键词检索的优势，提供更准确的文档检索结果。
"""

from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
import numpy as np
from collections import Counter
import re


class HybridRetriever(BaseRetriever):
    """混合检索器：结合向量检索和BM25关键词检索"""
    
    def __init__(
        self,
        vectorstore: Chroma,
        bm25_retriever: BM25Retriever,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        k: int = 10
    ):
        """
        初始化混合检索器
        
        Args:
            vectorstore: 向量数据库实例
            bm25_retriever: BM25关键词检索器
            vector_weight: 向量检索权重 (0-1)
            bm25_weight: BM25检索权重 (0-1)
            k: 返回文档数量
        """
        super().__init__()
        self.vectorstore = vectorstore
        self.bm25_retriever = bm25_retriever
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.k = k
        
        # 确保权重和为1
        total_weight = vector_weight + bm25_weight
        if abs(total_weight - 1.0) > 1e-6:
            self.vector_weight = vector_weight / total_weight
            self.bm25_weight = bm25_weight / total_weight
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager=None
    ) -> List[Document]:
        """执行混合检索"""
        
        # 1. 向量检索
        vector_docs = self.vectorstore.similarity_search_with_score(
            query, k=self.k * 2  # 获取更多候选文档
        )
        
        # 2. BM25关键词检索
        bm25_docs = self.bm25_retriever.get_relevant_documents(query)
        
        # 3. 融合检索结果
        combined_docs = self._combine_results(
            vector_docs, bm25_docs, query
        )
        
        return combined_docs[:self.k]
    
    def _combine_results(
        self, 
        vector_docs: List[Tuple[Document, float]], 
        bm25_docs: List[Document],
        query: str
    ) -> List[Document]:
        """融合向量检索和BM25检索结果"""
        
        # 创建文档到分数的映射
        doc_scores = {}
        
        # 处理向量检索结果
        for doc, score in vector_docs:
            doc_id = self._get_doc_id(doc)
            # 将相似度分数转换为0-1范围（分数越小越相似）
            normalized_score = 1.0 / (1.0 + score)
            doc_scores[doc_id] = {
                'doc': doc,
                'vector_score': normalized_score,
                'bm25_score': 0.0
            }
        
        # 处理BM25检索结果
        for i, doc in enumerate(bm25_docs):
            doc_id = self._get_doc_id(doc)
            # BM25分数通常已经标准化，这里直接使用
            bm25_score = 1.0 / (i + 1)  # 简单的排名分数
            
            if doc_id in doc_scores:
                doc_scores[doc_id]['bm25_score'] = bm25_score
            else:
                doc_scores[doc_id] = {
                    'doc': doc,
                    'vector_score': 0.0,
                    'bm25_score': bm25_score
                }
        
        # 计算综合分数
        scored_docs = []
        for doc_id, scores in doc_scores.items():
            combined_score = (
                self.vector_weight * scores['vector_score'] + 
                self.bm25_weight * scores['bm25_score']
            )
            scored_docs.append((scores['doc'], combined_score))
        
        # 按综合分数排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]
    
    def _get_doc_id(self, doc: Document) -> str:
        """生成文档唯一标识符"""
        # 使用文档内容的前100个字符作为ID
        content_preview = doc.page_content[:100]
        return hash(content_preview)
    
    def add_documents(self, documents: List[Document]) -> None:
        """添加文档到检索器"""
        # 添加到向量数据库
        self.vectorstore.add_documents(documents)
        
        # 添加到BM25检索器
        self.bm25_retriever.add_documents(documents)


class AdvancedHybridRetriever(HybridRetriever):
    """高级混合检索器：支持查询重写和结果重排序"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_expansion = True
        self.rerank = True
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager=None
    ) -> List[Document]:
        """执行高级混合检索"""
        
        # 1. 查询扩展（可选）
        expanded_queries = self._expand_query(query) if self.query_expansion else [query]
        
        all_docs = []
        
        # 2. 对每个查询变体执行检索
        for q in expanded_queries:
            vector_docs = self.vectorstore.similarity_search_with_score(q, k=self.k)
            bm25_docs = self.bm25_retriever.get_relevant_documents(q)
            
            combined_docs = self._combine_results(vector_docs, bm25_docs, q)
            all_docs.extend(combined_docs)
        
        # 3. 去重和重排序
        unique_docs = self._deduplicate_docs(all_docs)
        
        if self.rerank:
            unique_docs = self._rerank_documents(unique_docs, query)
        
        return unique_docs[:self.k]
    
    def _expand_query(self, query: str) -> List[str]:
        """查询扩展：生成查询的同义词和变体"""
        # 简单的同义词扩展（实际应用中可以使用更复杂的NLP技术）
        expansions = [query]
        
        # 添加一些常见的同义词
        synonyms = {
            "股票": ["股价", "股份", "证券", "投资"],
            "公司": ["企业", "机构", "组织"],
            "表现": ["业绩", "成绩", "结果", "情况"]
        }
        
        for original, syns in synonyms.items():
            if original in query:
                for syn in syns:
                    expanded = query.replace(original, syn)
                    if expanded not in expansions:
                        expansions.append(expanded)
        
        return expansions
    
    def _deduplicate_docs(self, docs: List[Document]) -> List[Document]:
        """文档去重"""
        seen = set()
        unique_docs = []
        
        for doc in docs:
            doc_id = self._get_doc_id(doc)
            if doc_id not in seen:
                seen.add(doc_id)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _rerank_documents(self, docs: List[Document], query: str) -> List[Document]:
        """文档重排序：基于查询和文档的匹配度"""
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        def calculate_relevance_score(doc: Document) -> float:
            doc_terms = set(re.findall(r'\w+', doc.page_content.lower()))
            
            # 计算词汇重叠度
            overlap = len(query_terms & doc_terms)
            total_terms = len(query_terms | doc_terms)
            
            if total_terms == 0:
                return 0.0
            
            # Jaccard相似度
            jaccard_sim = overlap / total_terms
            
            # 计算关键词密度
            doc_text = doc.page_content.lower()
            term_density = sum(doc_text.count(term) for term in query_terms) / len(doc_text)
            
            # 综合分数
            return 0.7 * jaccard_sim + 0.3 * term_density
        
        # 按相关性分数排序
        scored_docs = [(doc, calculate_relevance_score(doc)) for doc in docs]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]


def create_hybrid_retriever(
    vectorstore: Chroma,
    documents: List[Document],
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    k: int = 10,
    advanced: bool = False
) -> BaseRetriever:
    """
    创建混合检索器的便捷函数
    
    Args:
        vectorstore: 向量数据库实例
        documents: 文档列表
        vector_weight: 向量检索权重
        bm25_weight: BM25检索权重
        k: 返回文档数量
        advanced: 是否使用高级混合检索器
    
    Returns:
        配置好的混合检索器实例
    """
    # 创建BM25检索器
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = k
    
    # 选择检索器类型
    if advanced:
        retriever = AdvancedHybridRetriever(
            vectorstore=vectorstore,
            bm25_retriever=bm25_retriever,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            k=k
        )
    else:
        retriever = HybridRetriever(
            vectorstore=vectorstore,
            bm25_retriever=bm25_retriever,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            k=k
        )
    
    return retriever

