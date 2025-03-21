import os
import codecs
from datetime import datetime, date

LOG_PATH = ".\\logs"
LOG_NAME = f"{date.today()}.txt"

class WriteError:
    
    def __init__(self):
        self.ok = True
        self.errMsg = ''
    
    def writeLog(self, level, location, text):
        
        # Проверяем, что директория для логов существует.
        if not (os.path.isdir(LOG_PATH)):
            try:
                os.mkdir(self.path["merged_path"])
            except Exception as e:
                # Логирование - дополнительная функциональность. Не должна прерывать выполнение основного кода. Не будем делать ok=False.
                print(f"{LOG_PATH} does not exist. Attempt to create failed.")
                return
        
        try:
            # Пишем лог в файл.
            log_file = codecs.open(f"{LOG_PATH}\\{LOG_NAME}", mode='a', encoding="utf-8")
            log_file.write(f"{datetime.now()} {level} {location} {text}\n")
            log_file.close()
        except Exception as e:
            print(f"Error writing log: {e}")
            return