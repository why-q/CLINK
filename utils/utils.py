import logging
from utils.config import YAMLConfig
from datetime import datetime


def write_list_to_file(my_list, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            for item in my_list:
                file.write(str(item))
        print(f"Write list to file: {file_path}")
    except Exception as e:
        print(f"Error when writing list to file: {str(e)}")


def write_text_to_file(text, path):
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        logging.info(f"Write text to file: {path}")
    except Exception as e:
        logging.error(f"Error when writing text to file: {e}")


def yaml_config() -> YAMLConfig:
    return YAMLConfig.get_instance()


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def wechat_page_content_process(page_content: str) -> str:
    idx = page_content.find("发表于")
    if idx != -1:
        page_content_ = page_content[idx + 16 :]
    idx = page_content_.find("预览时标签不可点")
    if idx != -1:
        page_content_ = page_content_[:idx]

    page_content_limit_num = yaml_config().get_page_content_limit_len()
    return (
        page_content_
        if len(page_content_) <= page_content_limit_num
        else page_content_[:page_content_limit_num]
    )


def article_page_content_process(page_content: str) -> str:
    page_content_limit_num = yaml_config().get_page_content_limit_len()
    return (
        page_content
        if len(page_content) <= page_content_limit_num
        else page_content[:page_content_limit_num]
    )


def bytes_to_strs(ll: list):
    return [item.decode("utf-8") if isinstance(item, bytes) else item for item in ll]


def merge_lists(*lists):
    return [list(item) for item in zip(*lists)]
