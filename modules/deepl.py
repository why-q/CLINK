import deepl
import logging
from utils.utils import yaml_config


def setup_deepl_api():
    DEEPL_API_TOKEN = yaml_config().get_deepl_api_token()
    translator = deepl.Translator(DEEPL_API_TOKEN)
    return translator


def translate_text_by_deepl(text: str, target_lang: str = "EN-US") -> str:
    logging.info("Translating text by deepl...")
    try:
        translator = setup_deepl_api()
        result = translator.translate_text(text, target_lang=target_lang)
        logging.info("Done.")
        return result.text
    except ValueError as e:
        logging.error(f"Error occured in translating text by deepl: {e}")
        return None


def translate_texts_by_deepl(
    texts: list[str], target_lang: str = "EN-US"
) -> list[str]:
    print("Translating texts...")
    try:
        translator = setup_deepl_api()
        results = translator.translate_text(texts, target_lang=target_lang)
        res = []
        for result in results:
            res.append(result.text)
        print("Done.")
        return res
    except ValueError as e:
        print(f"Error in translating texts: {e}")
        return None
