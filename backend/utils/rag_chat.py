from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_core.messages.base import BaseMessage

import asyncio
import json
import os
from typing import List, Generator, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from langchain_community.chat_models import ChatZhipuAI
from .database_chat import get_session_history, Message
from ._config import humanRole, aiRole
from .logger import logger_init
from .chroma_store import load_chroma_store_retriever

logger = logger_init("rag_chat")

# 从环境变量或配置文件中读取配置
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "glm-4")
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
STREAM_DELAY = float(os.getenv("STREAM_DELAY", "0.01"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

def get_chat() -> ChatZhipuAI:
    """
    初始化并返回ChatZhipuAI实例。
    
    Returns:
        ChatZhipuAI: 配置好的ChatZhipuAI实例
    """
    chat = ChatZhipuAI(
        model=MODEL_NAME,
        streaming=True,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )
    return chat

def convert_db_messages_to_langchain_messages(session_id:str) -> list[BaseMessage]:
    """
    将数据库消息对象转换为langchain消息对象。
    
    Args:
        session_id: 会话ID
        
    Returns:
        List[BaseMessage]: langchain消息对象列表
    """
    langchain_messages: list[BaseMessage] = []

    # 获取会话历史
    db_messages = get_session_history(session_id=session_id)

    logger.info(f"检索到{len(db_messages)}条历史消息。")

    for msg in db_messages:
        # 现在msg是字典而不是ORM对象，使用字典访问方式
        if str(msg['role']) == humanRole:
            langchain_messages.append(HumanMessage(content=str(msg['content'])))
        elif str(msg['role']) == aiRole:
            langchain_messages.append(AIMessage(content=str(msg['content'])))
        else:
            # 系统消息应该使用SystemMessage类型
            langchain_messages.append(SystemMessage(content=str(msg['content'])))
    return langchain_messages

async def generate_rag_response_stream_with_context(
    input_text: str, 
    session_id: str, 
    kb_id: str = "0"
) :
    """
    生成基于RAG的流式响应，包含上下文感知。
    
    Args:
        input_text: 用户输入文本
        session_id: 会话ID
        kb_id: 知识库集合id，默认为"0" 默认系统知识库
        
    Yields:
        str: 流式响应文本块
    """
    if not input_text or not session_id:
        logger.error("输入文本或会话ID为空")
        yield f"data: {json.dumps({'content': '[ERROR] 输入参数无效'})}\n\n"
        return
        
    try:
        chat = get_chat()
        logger.info(f"处理会话 {session_id} 的请求，知识库: {kb_id}")
            
        # 转换为langchain消息
        langchain_history: list[BaseMessage] = convert_db_messages_to_langchain_messages(session_id=session_id)
        logger.info(f"检索到{len(langchain_history)}条历史消息。")

        # 加载知识库检索器
        retriever: VectorStoreRetriever = load_chroma_store_retriever(kb_id)
        
        # 创建上下文感知的问题（中文版本）
        contextualize_q_system_prompt = """根据聊天历史和最新的用户问题，
        该问题可能引用了聊天历史中的上下文，请重新构建一个独立的问题，
        使其在没有聊天历史的情况下也能被理解。请不要回答问题，
        只需在必要时重新构建问题，否则原样返回原始问题。
        如果无法理解或重构问题，请直接返回原始问题。
        不要添加任何解释、评论或额外内容。"""
        
        # 使用上下文感知检索器
        standalone_question = await chat.ainvoke(
            [
                {"role": "system", "content": contextualize_q_system_prompt},
                *[{"role": humanRole if isinstance(msg, HumanMessage) else aiRole, "content": msg.content} for msg in langchain_history],
                {"role": humanRole, "content": input_text}
            ]
        )
        
        # 检查重构后的问题是否有效
        reconstructed_question = standalone_question.content.strip() if isinstance(standalone_question.content, str) else input_text
        if not reconstructed_question or reconstructed_question.lower() == "不知道":
            logger.warning(f"问题重构失败，使用原始问题: {input_text}")
            reconstructed_question = input_text
        
        logger.info(f"重构后的问题: {reconstructed_question}")
        
        # # 检索相关文档
        # docs = retriever.invoke(reconstructed_question)
        # 检索时会返回带 score 的文档
        docs = retriever.invoke(reconstructed_question)
        logger.info(f"检索到 {len(docs)} 个相关文档")

        for i, doc in enumerate(docs):
            score = doc.metadata.get("score")
            
            logger.info(f"文档 {i+1} 内容: {doc.page_content[:200]}...")  # 记录前200个字符
            logger.info(f"文档 {i+1} 元数据: {doc.metadata}")
            logger.info(f"文档 {i+1} 相似度分数: {score if score is not None else '未知'}")
        
        # 构建系统提示，包含检索到的上下文（添加相似度分数）
        context_text = "\n\n".join([
            f"文档 {i+1} (相似度: {doc.metadata.get('score')}):\n{doc.page_content}" 
            for i, doc in enumerate(docs)
        ])
        logger.info(f"合并后的上下文总长度: {len(context_text)}")
        
        # 检查是否有相关上下文
        if not context_text.strip():
            system_prompt = """你是一个乐于助人的AI助手小Q。

            ## 限制
            我翻阅了所有笔记但没找到相关资料。下面我将根据自己的知识回答，但不会编造信息。
            如果我不知道答案，我会坦诚告诉你。
            """
        else:
            system_prompt = f"""你是一个乐于助人的AI助手小Q。请使用以下检索到的上下文信息来回答问题。

            ## 限制
            请基于检索到的上下文和你自己的知识回答，但不要编造信息。
            如果检索到的上下文不足以回答问题，请明确告知用户，然后尝试用你自己的知识回答。
            
            检索到的上下文:
            {context_text}
            """
        
        # 构建完整的消息历史
        final_messages: list[BaseMessage] = []
        
        # 添加系统消息
        final_messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        final_messages.extend(langchain_history)
        
        # 添加当前用户消息
        final_messages.append(HumanMessage(content=input_text))
        
        # 流式生成响应
        logger.info("开始生成流式响应")
        full_response = ""
        async for chunk in chat.astream(final_messages):
            content = chunk.content
            if content:
                full_response += str(content)
                yield f"data: {json.dumps({'content': content})}\n\n"
                await asyncio.sleep(STREAM_DELAY)  # 使用可配置的延迟时间
        
        # 打印完整响应内容用于调试
        logger.info(f"完整响应内容:\n{full_response}")

    except Exception as e:
        logger.error(f"生成RAG响应时出错: {str(e)}", exc_info=True)
        error_message = f"处理您的请求时发生错误: {str(e)}"
        yield f"data: {json.dumps({'content': error_message})}\n\n"