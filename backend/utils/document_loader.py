import os
import logging
from typing import List, Optional, Union, Tuple, Dict, Any
from .logger import logger_init

from langchain_community.document_loaders import WebBaseLoader,UnstructuredMarkdownLoader,TextLoader,PyPDFLoader,UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import bs4

logger = logger_init("document_loader")

def document_loader_markdown(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    加载并分割Markdown文档，按标题结构进行分割
    
    参数:
        file_path: Markdown文件路径
        chunk_size: 文本块大小，默认1000字符
        chunk_overlap: 块之间的重叠字符数，默认200
        
    返回:
        (texts, metadatas): 分割后的文本列表和对应的元数据列表
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Markdown文件不存在: {file_path}")

        # 加载Markdown文档
        loader = UnstructuredMarkdownLoader(file_path)
        data = loader.load()
        
        if len(data) == 0:
            logger.warning("Markdown文档为空")
            return []
        
        # 获取Markdown内容
        markdown_content = data[0].page_content
        
        # 定义要分割的标题层级
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6")
        ]
        
        # 使用MarkdownHeaderTextSplitter按标题分割
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(markdown_content)
        
        # 进一步使用RecursiveCharacterTextSplitter进行细粒度分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 分割文档并添加元数据(保留headers)
        final_splits = text_splitter.split_documents(md_header_splits)
        texts = []
        metadatas = []
        
        for doc in final_splits:
            headers = {k: v for k, v in doc.metadata.items() if k.startswith("Header")}
            metadata = {
                "source": file_path,
                "document_type": "markdown",
                "headers": " | ".join(headers.values()) if headers else "",  # 添加标题信息
                "chunk_index": len(texts),  # 添加块索引
                **headers  # 保留标题层级信息
            }
            texts.append(doc.page_content)
            metadatas.append(metadata)
        
        logger.info(f"Markdown文档已分割为 {len(texts)} 个文本块")
        return texts, metadatas
        
    except Exception as e:
        logger.error(f"处理Markdown文档时出错: {str(e)}")
        return [], []

def document_loader_txt(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200, 
                       encoding: str = "utf-8", autodetect_encoding: bool = False) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    加载并分割文本文件
    
    参数:
        file_path: 文本文件路径
        chunk_size: 文本块大小，默认1000字符
        chunk_overlap: 块之间的重叠字符数，默认200
        encoding: 文件编码，默认为'utf-8'
        autodetect_encoding: 是否自动检测编码，默认为False
        
    返回:
        (texts, metadatas): 分割后的文本列表和对应的元数据列表
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文本文件不存在: {file_path}")

        # 初始化TextLoader
        loader = TextLoader(
            file_path=file_path,
            encoding=encoding,
            autodetect_encoding=autodetect_encoding
        )
        
        # 加载文档
        data = loader.load()
        
        # 初始化文本分割器
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 分割文档
        splits = text_splitter.split_documents(data)
        
        # 提取文本内容和元数据
        texts = []
        metadatas = []
        
        for doc in splits:
            texts.append(doc.page_content)
            metadatas.append({
                "source": file_path,
                "document_type": "text",
                "chunk_index": len(texts) - 1,
                "line_numbers": doc.metadata.get("line_numbers", "")
            })
        
        logger.info(f"文本文件已分割为 {len(texts)} 个文本块")
        return texts, metadatas
        
    except FileNotFoundError:
        logger.error(f"文件未找到: {file_path}")
        return [], []
    except UnicodeDecodeError:
        logger.error(f"编码错误，请尝试使用 autodetect_encoding=True 或指定正确的编码格式")
        return [], []
    except Exception as e:
        logger.error(f"处理文本文件时出错: {str(e)}")
        return [], []

def document_loader_pdf(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200, password: Optional[str] = None, pages: Optional[List[int]] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    加载并分割PDF文档
    
    参数:
        file_path: PDF文件路径
        chunk_size: 文本块大小，默认1000字符
        chunk_overlap: 块之间的重叠字符数，默认200
        pages: 指定要加载的页面范围，默认None(加载所有页面)
        password: PDF密码，默认None
        
    返回:
        (texts, metadatas): 分割后的文本列表和对应的元数据列表
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")

        # 初始化PDF加载器
        if password:
            loader = PyPDFLoader(file_path, password=password)
        else:
            loader = PyPDFLoader(file_path)
        
        # 加载文档 
        docs = loader.load()
        
        logger.info(f"成功加载 {len(docs)} 页PDF文档")
        
        # 初始化文本分割器
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "？", "！", ".", "?", "!"]
        )
        
        # 分割文档
        splits = text_splitter.split_documents(docs)
        
        # 提取文本内容和元数据
        texts = []
        metadatas = []
        
        for doc in splits:
            texts.append(doc.page_content)
            metadatas.append({
                "source": file_path,
                "document_type": "pdf",
                "page": doc.metadata.get("page", 0),
                "chunk_index": len(texts) - 1
            })
        
        logger.info(f"PDF文档已分割为 {len(texts)} 个文本块")
        return texts, metadatas
        
    except FileNotFoundError:
        logger.error(f"文件未找到: {file_path}")
        return [], []
    except Exception as e:
        logger.error(f"处理PDF文档时出错: {str(e)}")
        return [], []

def document_loader_web(url: Union[str, List[str]], chunk_size: int = 1000, 
                        chunk_overlap: int = 200, verify_ssl: bool = True) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    从网页URL加载并分割内容
    
    参数:
        url: 网页URL地址或URL列表
        chunk_size: 文本块大小，默认1000字符
        chunk_overlap: 块之间的重叠字符数，默认200
        proxies: 代理设置，默认None
        verify_ssl: SSL验证，默认True
        
    返回:
        (texts, metadatas): 分割后的文本列表和对应的元数据列表
    """
    try:
        # 初始化WebBaseLoader
        loader = WebBaseLoader(
            web_paths=url if isinstance(url, list) else [url],
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header", "content", "article", "main")
                )
            ),
        )
        
        # 配置SSL验证
        if not verify_ssl:
            loader.requests_kwargs = {'verify': False}
        
        # 加载文档
        docs = loader.load()
        
        # 初始化文本分割器
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 分割文档
        splits = text_splitter.split_documents(docs)
        
        # 提取文本内容和元数据
        texts = []
        metadatas = []
        
        for doc in splits:
            texts.append(doc.page_content)
            source_url = url if isinstance(url, str) else doc.metadata.get("source", "unknown")
            metadatas.append({
                "source": source_url,
                "document_type": "web",
                "title": doc.metadata.get("title", ""),
                "chunk_index": len(texts) - 1
            })
        
        logger.info(f"网页内容已分割为 {len(texts)} 个文本块")
        return texts, metadatas
        
    except Exception as e:
        logger.error(f"加载网页内容时出错: {str(e)}")
        return [], []

def document_loader_html(html_file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200,
                         chunking_strategy: str = "by_title", max_characters: int = 1000) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    加载并分割本地HTML文件
    
    参数:
        html_file_path: HTML文件路径
        chunk_size: 文本块大小，默认1000字符
        chunk_overlap: 块之间的重叠字符数，默认200
        chunking_strategy: 分块策略，默认"by_title"
        max_characters: 最大分块字符数，默认1000
        
    返回:
        (texts, metadatas): 分割后的文本列表和对应的元数据列表
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(html_file_path):
            raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")

        # 初始化UnstructuredHTMLLoader
        loader = UnstructuredHTMLLoader(
            html_file_path,
            unstructured_kwargs={
                "chunking_strategy": chunking_strategy,
                "max_characters": max_characters
            }
        )
        
        # 加载文档
        data = loader.load()
        
        # 初始化文本分割器
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 分割文档
        splits = text_splitter.split_documents(data)
        
        # 提取文本内容和元数据
        texts = []
        metadatas = []
        
        for doc in splits:
            texts.append(doc.page_content)
            metadatas.append({
                "source": html_file_path,
                "document_type": "html",
                "title": doc.metadata.get("title", ""),
                "chunk_index": len(texts) - 1
            })
        
        logger.info(f"HTML文件已分割为 {len(texts)} 个文本块")
        return texts, metadatas
        
    except FileNotFoundError:
        logger.error(f"文件未找到: {html_file_path}")
        return [], []
    except Exception as e:
        logger.error(f"处理HTML文件时出错: {str(e)}")
        return [], []

def load_document(file_path: str, file_type: str = "auto", **kwargs) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    统一文档加载接口，根据文件类型自动选择加载器
    
    参数:
        file_path: 文件路径或URL
        file_type: 文件类型，可选值: "auto", "md", "txt", "pdf", "web", "html"
        **kwargs: 传递给具体加载器的参数
        
    返回:
        (texts, metadatas): 分割后的文本列表和对应的元数据列表
    """
    # 自动检测文件类型
    if file_type == "auto":
        if file_path.startswith(('http://', 'https://')) and file_path.endswith(('.html', '.htm')):
            file_type = "web"
        else:
            _, ext = os.path.splitext(file_path)
            if ext.lower() in ['.md', '.markdown']:
                file_type = "md"
            elif ext.lower() == '.txt':
                file_type = "txt"
            elif ext.lower() == '.pdf':
                file_type = "pdf"
            elif ext.lower() in ['.html', '.htm']:
                file_type = "html"
            else:
                raise ValueError(f"不支持的文件类型: {ext}")
    
    # 根据文件类型调用相应的加载器
    if file_type == "md":
        return document_loader_markdown(file_path, **kwargs)
    elif file_type == "txt":
        return document_loader_txt(file_path, **kwargs)
    elif file_type == "pdf":
        return document_loader_pdf(file_path, **kwargs)
    elif file_type == "web":
        return document_loader_web(file_path, **kwargs)
    elif file_type == "html":
        return document_loader_html(file_path, **kwargs)
    else:
        print(f"不支持的文件类型: {file_type}")
        return [], []

# 使用示例
if __name__ == "__main__":
    # 示例1: 加载Markdown文档
    md_texts, md_metadatas = document_loader_markdown("example.md", chunk_size=800)
    for i, (text, metadata) in enumerate(zip(md_texts, md_metadatas)):
        print(f"Markdown块 {i+1}: {text[:100]}...")
        print(f"元数据: {metadata}")
    
    # 示例2: 加载文本文件
    txt_texts, txt_metadatas = document_loader_txt("example.txt", chunk_size=1200, autodetect_encoding=True)
    for i, (text, metadata) in enumerate(zip(txt_texts, txt_metadatas)):
        print(f"文本块 {i+1}: {text[:100]}...")
        print(f"元数据: {metadata}")
    
    # 示例3: 加载PDF文档
    pdf_texts, pdf_metadatas = document_loader_pdf("example.pdf", pages=[0, 1, 2], chunk_size=1500)
    for i, (text, metadata) in enumerate(zip(pdf_texts, pdf_metadatas)):
        print(f"PDF块 {i+1}: {text[:100]}...")
        print(f"元数据: {metadata}")
    
    # 示例4: 加载网页内容
    web_texts, web_metadatas = document_loader_web("https://example.com/blog/post")
    for i, (text, metadata) in enumerate(zip(web_texts, web_metadatas)):
        print(f"网页块 {i+1}: {text[:100]}...")
        print(f"元数据: {metadata}")
    
    # 示例5: 加载HTML文件
    html_texts, html_metadatas = document_loader_html("local_page.html", chunk_size=1500)
    for i, (text, metadata) in enumerate(zip(html_texts, html_metadatas)):
        print(f"HTML块 {i+1}: {text[:100]}...")
        print(f"元数据: {metadata}")
    
    # 示例6: 使用统一接口
    texts, metadatas = load_document("example.md")
    for i, (text, metadata) in enumerate(zip(texts, metadatas)):
        print(f"文档块 {i+1}: {text[:100]}...")
        print(f"元数据: {metadata}")