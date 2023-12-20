import chromadb
import logging
from modules.deepl import translate_texts_by_deepl


def get_chroma_collection(chroma_path, collection_name):
    client = chromadb.PersistentClient(chroma_path)
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def add_datas_to_chroma(
    chroma_path: str, collection_name: str, datas: list, ids: list, ctag="link"
) -> bool:
    if datas is None:
        logging.info("No any datas to add to chroma.")
        return False

    logging.info("Adding datas to chroma...")

    collection = get_chroma_collection(
        chroma_path=chroma_path, collection_name=collection_name
    )
    documents = []
    metadatas = []

    # data: url, title, summary, tag, time
    for data in datas:
        if ctag == "note":
            pass
        documents.append(data[2])
        metadatas.append(
            {"url": data[0], "title": data[1], "tag": data[3], "time": data[4]}
        )

    if ctag == "note":
        documents = translate_texts_by_deepl(documents)

    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logging.info("Done.")
        return True
    except ValueError as e:
        logging.error(f"Error occurred when adding datas to chromadb: {e}")
        return False


def search_by_query_from_chroma(
    chroma_path: str,
    collection_name: str,
    query_texts: list,
    n_results: int = 3,
    show_document=False,
) -> dict:
    logging.info("Searching by query from chroma...")
    collection = get_chroma_collection(
        chroma_path=chroma_path, collection_name=collection_name
    )
    results = collection.query(query_texts=query_texts, n_results=n_results)
    urls, titles = get_urls_and_titles_by_res(results)
    res_dict = {"urls": urls, "titles": titles}
    if show_document:
        res_dict["ids"] = get_ids_by_res(results)
    logging.info("Done.")
    return res_dict


def get_documents_by_res(res: dict) -> list[str]:
    logging.info("Getting documents by res...") 
    return res["documents"][0]


def get_ids_by_res(res: dict) -> list[str]:
    logging.info("Getting ifd by querying results...")
    return res["ids"][0]


# res -> dict: {"ids": list[0], "metadatas": list[0]: dict}
def get_urls_and_titles_by_res(res: dict) -> (list[str], list[str]):
    logging.info("Getting urls & titles by querying results...")
    urls = []
    titles = []
    metadatas = res["metadatas"][0]
    for metadata in metadatas:
        titles.append(metadata["title"])
        urls.append(metadata["url"])
    logging.info("Done.")
    return urls, titles


def get_metadatas_by_res(res: dict, *args: str) -> dict:
    logging.info("Getting metadatas by querying results...")
    if len(args) == 0:
        return None
    else:
        res = {}
        for arg in args:
            temp = []
            metadatas = res["metadatas"][0]
            for metadata in metadatas:
                temp.append(metadata[arg])
            res[arg] = temp
        return res


def get_ids_from_chroma(chroma_path: str, collection_name: str, ids: list):
    print("Getting ids from chroma...")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(collection_name)
    res = collection.get(ids=ids)
    return res


def delete_collection_from_chroma(chroma_path: str, collection_name: str):
    logging.info(f"Deleting collection `{collection_name}` from chroma...")
    client = chromadb.PersistentClient(path=chroma_path)
    try:
        client.delete_collection(name=collection_name)
        logging.info(f"Successfully deleted collection: {collection_name}.")
    except ValueError as e:
        logging.info(f"Error occured in deleting collection {collection_name}: {e}")


def list_collections_from_chroma(chroma_path: str):
    client = chromadb.PersistentClient(path=chroma_path)
    return client.list_collections()
