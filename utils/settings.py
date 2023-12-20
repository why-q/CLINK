class AppSettings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppSettings, cls).__new__(cls)
            cls._instance.search_keyword = None
            cls._instance.search_tag = None
        return cls._instance

    def update_search_keyword(self, new_keyword: str):
        self.search_keyword = new_keyword

    def update_search_tag(self, new_tag: str):
        self.search_tag = new_tag


app_settings = AppSettings()
