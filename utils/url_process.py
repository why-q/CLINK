# pip install selenium
# pip install unstructured
import aiohttp
import logging
from urllib.parse import urlparse
from langchain.document_loaders import SeleniumURLLoader


def reg_url(url: str) -> str:
    if url.endswith("/"):
        url = url[:-1]
    return url


def reg_urls(urls: list) -> list:
    return [reg_url(url) for url in urls]


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def filter_valid_urls(urls: list) -> (list[str], list[str]):
    valid_urls = []
    invalid_urls = []
    for url in urls:
        if is_valid_url(url):
            valid_urls.append(url)
        else:
            invalid_urls.append(url)
    return valid_urls, invalid_urls


async def is_accessible_url(url: str) -> bool:
    logging.debug(f"Check the accessibility of url: {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(url, timeout=10) as response:
                return response.status == 200
        except aiohttp.ClientError as e:
            logging.error(f"Error occured in checking accessibility of {url}: {e}")
            return False
        except Exception as e:
            logging.error(f"Error occured in checking accessibility of {url}: {e}")
            return False


async def filter_accessible_urls(urls: list) -> (list[str], list[str]):
    logging.info("Filtering accessible urls...")
    accessible_urls = []
    inaccessible_urls = []
    for url in urls:
        if await is_accessible_url(url):
            accessible_urls.append(url)
        else:
            inaccessible_urls.append(url)
    logging.info("Done.")
    return accessible_urls, inaccessible_urls


# def get_readme_from_github_url(url) -> str:
#     GITHUB_API_TOKEN = yaml_config().get_github_api_token()

#     # TODO
#     HEADERS = {
#         "Accept": "application/vnd.github+json",
#         "Authorization": f"Bearer {GITHUB_API_TOKEN}",
#         "X-GitHub-Api-Version": "2022-11-28",
#     }
#     API_BASE_URL = "https://api.github.com"

#     user, repo = get_user_and_repo_from_github_url(url)
#     print(f"user: {user}, repo: {repo}")
#     url_ = urljoin(API_BASE_URL, f"/repos/{user}/{repo}/readme")
#     response = requests.get(url_, headers=HEADERS)

#     readme = None
#     if response.status_code == 200:
#         readme_b64 = response.json().get("content")
#         readme = bytearray(base64.b64decode(readme_b64)).decode("utf-8")
#     elif response.status_code == 404:
#         print("Resource not found.")
#     else:
#         print("Validation failed, or the endpoint has been spammed.")

#     return readme


def get_title_from_url(url: str) -> str:
    loader = SeleniumURLLoader(urls=[url])
    data = loader.load()
    return data[0].metadata["title"]


# def get_titles_from_urls(urls: list) -> list:
#     print("Getting titles from urls...")
#     loader = SeleniumURLLoader(urls=urls)
#     datas = loader.load()
#     titles = []
#     for data in datas:
#         title = data.metadata["title"].rstrip()
#         # TODO deal telegraph
#         if title.endswith(" – Telegraph"):
#             title = title.replace(" – Telegraph", "")
#         titles.append(title)
#     return titles


def get_page_content_from_url(url: str) -> str:
    print(f"Getting page content from url {url}...")
    loader = SeleniumURLLoader(urls=[url])
    data = loader.load()
    return data[0].page_content


# def get_page_contents_from_urls(urls: list) -> list:
#     contents = []
#     loader = SeleniumURLLoader(urls=urls)
#     datas = loader.load()
#     for data in datas:
#         contents.append(data.page_content)


# def get_titles_and_page_contents_from_urls(urls: list) -> (list, list):
#     titles = []
#     contents = []
#     loader = SeleniumURLLoader(urls=urls)
#     datas = loader.load()
#     for data in datas:
#         titles.append(data.metadata["title"])
#         contents.append(data.page_content)
#     return titles, contents


# async def urls_process(urls: list) -> list:
#     if len(urls) == 0:
#         print("No any urls to process.")
#         return None

#     logging.info("Processing urls...")
#     summaries = await get_summaries_from_urls(urls)
#     titles = get_titles_from_urls(urls)

#     # DEEPL_API_TOKEN = yaml_config().get_deepl_api_token()
#     # summaries_ = translate_texts_by_deepl(DEEPL_API_TOKEN, bytes_to_strs(summaries))
#     summaries_ = bytes_to_strs(summaries)
#     titles_ = bytes_to_strs(titles)

#     datas = [
#         [url, title, summary] for url, title, summary in zip(urls, titles_, summaries_)
#     ]
#     return datas


def urls_text_2_list(urls: str) -> list:
    return urls.split("\n")
