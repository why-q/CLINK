# pip install arxiv
# pip install pymupdf

import re
import base64
import logging
import aiohttp
from langchain.document_loaders import SeleniumURLLoader, ArxivLoader
from urllib.parse import urljoin
from utils.utils import yaml_config


def get_special_type_of_url(url):
    logging.info(f"Getting special type of url: {url}...")
    if re.search(r"https://github\.com", url):
        logging.info("-> github")
        return "github"
    elif re.search(r"https://telegra\.ph", url):
        logging.info("-> telegraph")
        return "telegraph"
    elif re.search(r"https://mp\.weixin\.qq\.com", url):
        logging.info("-> wechat")
        return "wechat"
    elif re.search(r"https://arxiv\.org", url):
        logging.info("-> arxiv")
        return "arxiv"
    elif re.search(r"https://zhuanlan\.zhihu\.com", url):
        logging.info("-> zhihu")
        return "zhihu"
    elif re.search(r"https://sspai\.com", url):
        logging.info("-> sspai")
        return "sspai"
    else:
        logging.info("-> others")
        return "others"


async def get_titles_from_urls(urls: list) -> list[str]:
    logging.info("Getting titles from urls...")
    loader = SeleniumURLLoader(urls=urls)
    datas = loader.load()
    titles = []
    for url, data in zip(urls, datas):
        title = data.metadata["title"]
        type_of_url = get_special_type_of_url(url=url)
        if type_of_url == "wechat":
            idx = data.page_content.find("\n")
            if idx != -1:
                title = data.page_content[:idx].rstrip()
        if type_of_url == "telegraph":
            title = process_telegraph_title(title)
        if type_of_url == "sspai":
            title = process_sspai_title(title)
        titles.append(title)
    logging.info("Done.")
    return titles


async def get_titles_and_pcs_from_urls(urls: list) -> (list[str], list[str]):
    logging.info("Getting page contents from urls...")
    loader = SeleniumURLLoader(urls=urls)
    datas = loader.load()  # lists
    titles = []
    pcs = []
    for url, data in zip(urls, datas):
        # data: page_content (str), metadata (dict) -> document class
        title = data.metadata["title"]
        # logging.info(f"Title: {title}")
        type_of_url = get_special_type_of_url(url)
        if type_of_url == "wechat":
            idx = data.page_content.find("\n")
            if idx != -1:
                title = data.page_content[:idx].rstrip()
            pc = process_wechat_page_content(data.page_content)
        elif type_of_url == "github":
            pc = await get_page_content_from_github(url=url)
        elif type_of_url == "telegraph":
            title = process_telegraph_title(title)
            pc = clip_page_content(data.page_content)
        elif type_of_url == "sspai":
            title = process_sspai_title(title)
            pc = process_sspai_page_content(data.page_content)
        elif type_of_url == "arxiv":
            pc = clip_page_content(get_page_content_from_arxiv(url=url))
        else:
            # TODO
            # directly url2summary
            pc = None
        titles.append(title)
        pcs.append(pc)

    len_str = ""
    for pc in pcs:
        if pc is not None:
            len_str += f"{len(pc)} "
        else:
            len_str += "None "
    logging.info(f"Length of pcs: {len_str}")

    return titles, pcs


def get_user_and_repo_from_github_url(url) -> tuple:
    if not url.endswith("/"):
        url_ = url + "/"
    else:
        url_ = url
    return re.search(r"https://github\.com/(.*)/(.*)/", url_).groups()


def setup_github_api():
    GITHUB_API_TOKEN = yaml_config().get_github_api_token()
    HEADERS = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_API_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    API_BASE_URL = "https://api.github.com"
    return HEADERS, API_BASE_URL


def clip_page_content(page_content: str):
    logging.info("Clipping page content...")
    page_content_limit_num = yaml_config().get_page_content_limit_len()
    return (
        page_content
        if len(page_content) <= page_content_limit_num
        else page_content[:page_content_limit_num]
    )


def get_page_content_from_arxiv(url):
    logging.info("Getting page content from arxiv...")
    arxiv_id = re.search(r"https://arxiv\.org/abs/(.*)", url).group(1)
    logging.info(f"Arxiv id: {arxiv_id}")

    arxiv_loader = ArxivLoader(query=arxiv_id, load_max_doc=0)
    datas = arxiv_loader.load()
    summary = datas[0].metadata["Summary"]
    logging.info(f"Got summary: {summary}")
    return summary


async def get_page_content_from_github(url):
    HEADERS, API_BASE_URL = setup_github_api()
    user, repo = get_user_and_repo_from_github_url(url)

    url_ = urljoin(API_BASE_URL, f"/repos/{user}/{repo}/readme")
    async with aiohttp.ClientSession() as session:
        async with session.get(url_, headers=HEADERS) as response:
            readme = None
            if response.status == 200:
                response_json = await response.json()
                readme_b64 = response_json.get("content")
                readme = bytearray(base64.b64decode(readme_b64)).decode("utf-8")
                logging.info(f"Got readme file by {url}.")
            elif response.status == 404:
                logging.error(f"404: Failed to get readme file by {url}.")
            else:
                logging.error(f"Something wrong: Failed to get readme file by {url}.")

            if readme is not None:
                readme = clip_page_content(readme)
            return readme


def process_sspai_page_content(page_content: str) -> str:
    logging.info("Processing sspai page content...")
    idx = page_content.find("> 关注 少数派公众号，解锁全新阅读体验")
    if idx != -1:
        page_content = page_content[:idx]
    idx = page_content.rfind("关注健康生活")
    if idx != -1:
        page_content = page_content[idx + 7 :]

    logging.info(f"The len of processed sspai page content: {len(page_content)}")
    logging.info("Done.")
    return clip_page_content(page_content)


def process_wechat_page_content(page_content: str) -> str:
    logging.info("Processing wechat page content...")
    idx = page_content.find("发表于")
    if idx != -1:
        page_content_ = page_content[idx + 16 :]
    idx = page_content_.find("预览时标签不可点")
    if idx != -1:
        page_content_ = page_content_[:idx]

    logging.info("Done.")
    return clip_page_content(page_content_)


def process_telegraph_title(title: str) -> str:
    logging.info("Processing telegraph title...")
    if title.endswith(" – Telegraph"):
        title = title.replace(" – Telegraph", "")
    logging.info("Done.")
    return title


def process_sspai_title(title: str) -> str:
    logging.info("Processing sspai title...")
    if title.endswith(" - 少数派"):
        title = title.replace(" - 少数派", "")
    logging.info("Done.")
    return title
