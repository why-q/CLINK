import unittest
from modules.telegram_bot import setup_telegram_bot_service
from modules.sqlite import delete_table_if_existed
from modules.chroma import delete_collection_from_chroma
from utils.utils import yaml_config
from utils.logging import setup_logging


def reset():
    # delete sqlite table
    delete_table_if_existed(
        yaml_config().get_sqlite_path(), yaml_config().get_sqlite_table_name()
    )

    # delete chroma collection
    delete_collection_from_chroma(
        yaml_config().get_chroma_path(), yaml_config().get_chroma_collection_name()
    )

    # delete chroma note collection
    delete_collection_from_chroma(
        yaml_config().get_chroma_path(), yaml_config().get_chroma_note_collection_name()
    )


def main():
    setup_logging()
    # reset()
    setup_telegram_bot_service()


def test():
    setup_logging("test")
    test_loader = unittest.TestLoader()
    suite = test_loader.discover("./tests")
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == "__main__":
    # test()
    main()
