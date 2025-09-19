import logging
import os
import sys

def logger_init(tag:str):
    # 配置日志
    logger = logging.getLogger(tag)
    logger.setLevel(logging.INFO)

    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 配置日志处理器
    os.makedirs("./logs", exist_ok=True)
    file_handler = logging.FileHandler("./logs/logger.log", encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
