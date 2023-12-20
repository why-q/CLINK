def get_llama_template_for_url(url: str) -> dict:
    return {
        "model": "llama-70b-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant to summarize the web content by following url.\
                            Attention: Please answer directly in English,\
                            without any non-English symbols and polite formula.\
                            The answer should be start with: 'It is",
            },
            {
                "role": "assistant",
                "content": f"{url}",
            },
        ],
        "stream": False,
    }


def get_llama_template_for_page_content(pc: str):
    return {
        "model": "llama-70b-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant to summarize the following content.\
                            Attention: Please answer directly in English,\
                            without any non-English symbols and polite formula.\
                            The answer should be start with: 'It is",
            },
            {
                "role": "assistant",
                "content": f"Summarize the following content: {pc}",
            },
        ],
        "stream": False,
    }


    # return {
    #     "messages": [
    #         {
    #             "role": "assistant",
    #             "content": f"Summarize the acticle base on the following content segment:\
    #                         [{page_content}]\
    #                         Attention: Please answer directly in English,\
    #                         without any non-English symbols and polite formula.\
    #                         The answer should be start with: 'This article'",
    #         },
    #     ],
    #     "stream": False,
    # }
