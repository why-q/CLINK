import yaml


class YAMLConfig:
    _instance = None

    @staticmethod
    def get_instance(file_path="./config.yaml"):
        if YAMLConfig._instance is None:
            YAMLConfig(file_path)
        return YAMLConfig._instance

    def __init__(self, file_path):
        if YAMLConfig._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            YAMLConfig._instance = self
            self.file_path = file_path
            self.data = None
            self._load()

    def _load(self):
        try:
            with open(self.file_path, "r") as yaml_file:
                self.data = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"YAML file not found at {self.file_path}")

    def _get(self, *keys):
        res = self.data
        for key in keys:
            try:
                res = res[key]
            except KeyError:
                print(f"Key Error: '{key}' not found in config file.")
                return None
        return res

    def get_llama_api_token(self) -> str:
        return self._get("llama", "api_token")

    def get_github_api_token(self) -> str:
        return self._get("github", "api_token")

    def get_tb_token(self) -> str:
        return self._get("telegram", "bot_token")

    def get_tb_start_text(self) -> str:
        return self._get("telegram", "start_text")

    def get_tb_processing_urls_text(self) -> str:
        return self._get("telegram", "processing_urls_text")

    def get_tb_processing_note_text(self) -> str:
        return self._get("telegram", "processing_note_text")

    def get_tb_searching_text(self) -> str:
        return self._get("telegram", "searching_text")

    def get_tb_help_text(self) -> str:
        return self._get("telegram", "help_text")

    def get_tb_no_any_accessiable_urls_text(self) -> str:
        return self._get("telegram", "no_any_accessible_urls")

    def get_tb_no_any_valid_urls_text(self) -> str:
        return self._get("telegram", "no_any_valid_urls_text")

    def get_tb_no_any_new_urls_text(self) -> str:
        return self._get("telegram", "no_any_new_urls_text")

    def get_tb_failed_to_search_text(self) -> str:
        return self._get("telegram", "failed_to_search_text")

    def get_tb_searching_note_text(self) -> str:
        return self._get("telegram", "searching_note_text")

    def get_tb_summarizing_text(self) -> str:
        return self._get("telegram", "summarizing_text")

    def get_no_searching_keyword_text(self) -> str:
        return self._get("telegram", "no_searching_keyword_text")

    def get_use_search_before_more_text(self) -> str:
        return self._get("telegram", "use_search_before_more_text")

    def get_wrong_input_format_text(self) -> str:
        return self._get("telegram", "wrong_input_format_text")

    def get_search_n_results(self) -> int:
        return int(self._get("telegram", "search_n_results"))

    def get_more_n_results(self) -> str:
        return int(self._get("telegram", "more_n_results"))

    def get_tb_non_command_text(self) -> str:
        return self._get("telegram", "non_command_text")

    def get_sqlite_path(self) -> str:
        return self._get("sqlite", "path")

    def get_sqlite_table_name(self) -> str:
        return self._get("sqlite", "table_name")

    def get_sqlite_create_table_command(self) -> str:
        return self._get("sqlite", "create_table_command")

    def get_chroma_path(self) -> str:
        return self._get("chroma", "path")

    def get_chroma_collection_name(self) -> str:
        return self._get("chroma", "collection_name")

    def get_chroma_note_collection_name(self) -> str:
        return self._get("chroma", "note_collection_name")

    def get_deepl_api_token(self) -> str:
        return self._get("deepl", "api_token")

    def get_page_content_limit_len(self) -> int:
        return self._get("others", "page_content_limit_len")
