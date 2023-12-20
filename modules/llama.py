import logging
from llamaapi import LlamaAPI
from utils.utils import yaml_config
from utils.llama_template import (
    get_llama_template_for_page_content,
    get_llama_template_for_url,
)
from modules.crawer import get_special_type_of_url


def setup_llama_api() -> LlamaAPI:
    logging.info("Setting up llama api...")
    LLAMA_API_TOKEN = yaml_config().get_llama_api_token()
    llama = LlamaAPI(LLAMA_API_TOKEN)
    logging.info("Done.")
    return llama


async def get_summaries_by_urls_or_pcs(urls: list, pcs: list) -> list[str]:
    logging.info("Getting summaries by pcs...")
    if len(pcs) == 0 or len(urls) == 0:
        logging.warning("Failed to get summaries by pcs. The list is empty.")
    summaries = []
    for url, pc in zip(urls, pcs):
        if pc is None:
            summary = await get_summary_by_url(url=url)
        elif get_special_type_of_url(url) == "arxiv":
            summary = pc
        else:
            summary = await get_summary_by_pc(pc=pc)
        summaries.append(summary)

    len_str = ""
    for summary in summaries:
        len_str += f"{len(summary)} "
    logging.info(f"Summary length: {len_str}")
    logging.info("Done.")

    return summaries


async def get_summary_by_url(url: str) -> str:
    logging.info(f"Getting summary by {url}...")
    ar = get_api_request_by_url(url=url)
    response = await run_request(ar)
    summary = get_summary_from_response(response)
    logging.info("Done.")
    return summary


async def get_summary_by_pc(pc: str) -> str:
    logging.info("Getting summary by pc...")
    ar = get_api_request_by_pc(pc=pc)
    response = await run_request(api_request=ar)
    summary = get_summary_from_response(response)
    logging.info("Done.")
    return summary


async def run_request(api_request: dict) -> dict:
    logging.info("Running request...")
    llama = setup_llama_api()
    logging.info("Done.")
    return await llama.run(api_request)


def get_api_request_by_url(url: str) -> dict:
    return get_llama_template_for_url(url=url)


def get_api_request_by_pc(pc: str) -> dict:
    return get_llama_template_for_page_content(pc=pc)


def get_summary_from_response(response: dict) -> str:
    return response["choices"][0]["message"]["content"]
