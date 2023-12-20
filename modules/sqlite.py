import sqlite3
import logging
from utils.utils import yaml_config


def create_table_if_not_existed(db_path: str, table_name: str, ct_command: str):
    logging.info(f"Creating table {table_name} of database in {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    )
    if cursor.fetchone() is None:
        cursor.execute(ct_command)
        conn.commit()
        logging.info(f"Table {table_name} created successfully.")
    else:
        logging.info(f"Table {table_name} already exists.")

    cursor.close()
    conn.close()


def delete_table_if_existed(db_path: str, table_name: str):
    logging.info(f"Deleting table {table_name} from database in {db_path}...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Table {table_name} deleted successfully.")
    except RuntimeError as e:
        logging.error(f"Error occured in deleting table {table_name}: {e}")


def insert_datas_to_sqlite(datas: list) -> False:
    db_path, table_name = setup_sqlite()
    if datas is None:
        logging.info("No any datas need to be inserted.")
        return False

    logging.info(f"Inserting datas into {db_path} of database in {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("BEGIN TRANSACTION;")
    try:
        cursor.executemany(
            f"INSERT INTO {table_name} (url, title, summary, tag, time) VALUES (?, ?, ?, ?, ?)",
            datas,
        )
        conn.commit()
        logging.info("Inserted successfully.")
        cursor.close()
        conn.close()
        return True
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred when insert: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def get_id_by_url_from_sqlite(db_path: str, table_name: str, url: str) -> int:
    logging.info(f"Getting id from sqlite by url: {url} ...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT id FROM {table_name} WHERE url = ?"

        cursor.execute(query, (url,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return str(result[0])
        else:
            logging.info(f"Cannot find id in sqlite by url: {url}")
            return None
    except sqlite3.Error as e:
        logging.error(
            f"Database error occured when querying id in sqlite by url: {url}. Details: {e}"
        )
        return None


def get_ids_by_urls_from_sqlite(db_path: str, table_name: str, urls: list) -> list:
    logging.info("Getting ids by urls from sqlite...")
    ids = []
    for url in urls:
        id = get_id_by_url_from_sqlite(db_path, table_name, url)
        if id is not None:
            ids.append(id)
    logging.info("Done.")
    return ids


def get_row_by_id(db_path: str, table_name: str, id: str) -> tuple:
    logging.info("Getting row by id...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name} WHERE id = ?"
        cursor.execute(query, (id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row
    except sqlite3.Error as e:
        logging.error(f"Database error occured when getting row by id: {e}")


def get_rows_by_ids(db_path: str, table_name: str, ids: list) -> list[tuple]:
    logging.info("Getting rows by ids...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name} WHERE id IN ({','.join(['?']*len(ids))})"
        cursor.execute(query, ids)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows
    except sqlite3.Error as e:
        logging.error(f"Database error occured when getting rows by ids: {e}")


def is_url_exists(db_path: str, table_name: str, url: str):
    logging.info(f"Checking if url {url} exists...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT COUNT(*) FROM {table_name} WHERE url = ?"
        cursor.execute(query, (url,))
        result = cursor.fetchone()
        if result[0] > 0:
            logging.info(f"Url {url} already exists.")
        cursor.close()
        conn.close()
        return result[0] > 0
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        cursor.close()
        conn.close()
        return False


def filter_existing_urls_in_sqlite(db_path, table_name, urls: list) -> list:
    logging.info("Filtering existing urls in sqlite...")
    existing_urls = []
    non_existing_urls = []
    for url in urls:
        if is_url_exists(db_path, table_name, url):
            existing_urls.append(url)
        else:
            non_existing_urls.append(url)
    logging.info("Done.")
    return existing_urls, non_existing_urls


def filter_noid_urls(db_path, table_name, urls: list) -> (list, list):
    logging.info("Filtering urls without id...")
    urls_ = []
    urls_noid = []
    for url in urls:
        if get_id_by_url_from_sqlite(db_path, table_name, url) is not None:
            urls_.append(url)
        else:
            urls_noid.append(url)
    logging.info("Done.")
    return urls_, urls_noid


def setup_sqlite():
    logging.info("Setting up sqlite...")
    DB_PATH = yaml_config().get_sqlite_path()
    TABLE_NAME = yaml_config().get_sqlite_table_name()
    # ct_command = yaml_config().get_sqlite_create_table_command()
    CT_COMMAND = f"CREATE TABLE {TABLE_NAME} (id INTEGER PRIMARY KEY AUTOINCREMENT, \
                                        url TEXT, \
                                        title TEXT, \
                                        summary TEXT, \
                                        tag TEXT, \
                                        time TIMESTAMP);"
    create_table_if_not_existed(
        db_path=DB_PATH, table_name=TABLE_NAME, ct_command=CT_COMMAND
    )
    return DB_PATH, TABLE_NAME
