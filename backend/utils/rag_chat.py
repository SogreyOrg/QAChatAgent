
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain_community.chat_models import ChatZhipuAI
from .database import get_session_history, Message
from ._config import humanRole, aiRole
from .logger import logger_init
from .chroma_store import load_chroma_store_retriever

logger = logger_init("rag_chat")

def get_chat() -> ChatZhipuAI:

    # 初始化ChatZhipuAI
    chat = ChatZhipuAI(
        model="glm-4",
        streaming=True,
        temperature=0.7,
        max_tokens=2048
    )

    return chat

async def generate_rag_response_stream_with_context(input_text: str, session_id: str, collection_name: str = "default"):
    try:
        chat = get_chat()

        db_messages:list[Message] = get_session_history(session_id=session_id)
        # 创建一个会话历史记录

        # 构建消息历史用于上下文感知检索
        chat_history = []    

        for msg in db_messages:
            # logger.info(f"角色: {str(msg.role)} : 消息: {str(msg.content)}")
            if str(msg.role) == humanRole:
                chat_history.append(HumanMessage(content=str(msg.content)))
            elif str(msg.role) == aiRole:
                chat_history.append(AIMessage(content=str(msg.content)))
            else:
                # 系统消息或其他类型
                chat_history.append(AIMessage(content=str(msg.content)))

        # 加载知识库检索器
        retriever = load_chroma_store_retriever(collection_name)
        
        # 创建上下文感知的问题
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""
        
        # 使用上下文感知检索器
        standalone_question = await chat.ainvoke(
            [
                {"role": "system", "content": contextualize_q_system_prompt},
                *[{"role": humanRole if isinstance(msg, HumanMessage) else aiRole, "content": msg.content} for msg in chat_history],
                {"role": humanRole, "content": input_text}
            ]
        )
        
        # 检索相关文档
        docs = retriever.invoke(standalone_question.content)
        
        # 构建系统提示，包含检索到的上下文
        context_text = "\n\n".join([doc.page_content for doc in docs])
        system_prompt = f"""你是一个乐于助人的AI助手小Q。请使用以下检索到的上下文信息来回答问题。

        ## 限制
        并且请基于你自己的知识回答，但不要编造信息。
        
        检索到的上下文:
        {context_text}
        """        
        # 如果上下文中没有相关信息，必须向用户说明`我翻阅了所有笔记但没找到相关资料。下面我将根据自己的知识回答。`，
        
        # 构建完整的消息历史
        langchain_messages = []
        
        # 添加系统消息
        langchain_messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        for msg in db_messages:
            # logger.info(f"角色: {str(msg.role)} : 消息: {str(msg.content)}")
            if str(msg.role) == humanRole:
                langchain_messages.append(HumanMessage(content=str(msg.content)))
            elif str(msg.role) == aiRole:
                langchain_messages.append(AIMessage(content=str(msg.content)))
            else:
                # 系统消息或其他类型
                langchain_messages.append(AIMessage(content=str(msg.content)))
        
        # 添加当前用户消息
        langchain_messages.append(HumanMessage(content=input_text))
        
        # 流式生成响应
        async for chunk in chat.astream(langchain_messages):
            content = chunk.content
            if content:
                yield f"data: {content}\n\n"
                await asyncio.sleep(0.01)  # 控制流式速度

    except Exception as e:
        logger.error(f"生成RAG响应时出错: {str(e)}")
        yield f"data: [ERROR] {str(e)}\n\n"

