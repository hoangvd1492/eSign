import os
import configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "conf.ini")

DEFAULT_CONFIG = {
    "tsa_url": "http://ca.gov.vn/tsa"
}


class AppConfig:
    def __init__(self, config_file: str = CONFIG_PATH):
        self.config_file = config_file
        self.parser = configparser.ConfigParser()
        self.load()

    def load(self):
        """Đọc file cấu hình. Nếu chưa có file hoặc bị xóa thì tạo lại file mới với conf mặc định"""
        if not os.path.exists(self.config_file):
            self.parser["DEFAULT"] = dict(DEFAULT_CONFIG)
            self.save()
            return

        self.parser.read(self.config_file, encoding="utf-8")

    def save(self):
        """Ghi lại cấu hình hiện tại vào file conf.ini"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.parser.write(f)

    @property
    def tsa_url(self) -> str:
        return self.parser["DEFAULT"].get("tsa_url", DEFAULT_CONFIG["tsa_url"])

    @tsa_url.setter
    def tsa_url(self, value: str):
        self.parser["DEFAULT"]["tsa_url"] = str(value).strip()


config = AppConfig()
