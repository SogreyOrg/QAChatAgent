from typing import List
from zhipuai import ZhipuAI
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings

# 加载环境变量
load_dotenv()

class EmbeddingGenerator(Embeddings):
    def __init__(self, model_name):
        self.model_name = model_name
        self.client = ZhipuAI()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            response = self.client.embeddings.create(model=self.model_name, input=text)
            if hasattr(response, 'data') and response.data:
                embeddings.append([float(x) for x in response.data[0].embedding])
            else:
                # 如果获取嵌入失败，返回一个零向量
                embeddings.append([0.0] * 1024)  # 假设嵌入向量维度为 1024
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询文本"""
        response = self.client.embeddings.create(model=self.model_name, input=text)
        if hasattr(response, 'data') and response.data:
            return [float(x) for x in response.data[0].embedding]
        return [0.0] * 1024  # 如果获取嵌入失败，返回零向量

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入文档"""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入查询"""
        return self.embed_query(text)


def get_embedding_generator(model_name: str) -> EmbeddingGenerator:
    return EmbeddingGenerator(model_name)


