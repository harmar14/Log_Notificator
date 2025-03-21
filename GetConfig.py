from WriteError import WriteError
import os
import codecs
import json

CONFIG_PATH = "./config.json"

class GetConfig:
    
    def __init__(self):
        self.ok = True
        self.errMsg = ''
    
    def readConfig(self, config_path):
        
        # Проверяем, что файл конфигурации существует.
        if not (os.path.exists(config_path)):
            self.ok = False
            self.errMsg = f"Config file is not found with path {config_path}."
            # Пишем лог.
            WriteError().writeLog("ERROR", "GetConfig:readConfig", self.errMsg)
            return
        
        # Считываем файл конфигурации и конвертируем в словарь.
        try:
            with codecs.open(config_path, mode='r', encoding="utf-8") as config:
                self.config = json.load(config)
        except Exception as e:
            self.ok = False
            self.errMsg = e
            # Пишем лог.
            WriteError().writeLog("ERROR", "GetConfig:readConfig", self.errMsg)
            return
        
        return
    
    def execute(self):
        
        self.readConfig(CONFIG_PATH)
        
        if not (self.ok):             
            return
        
        return self.config