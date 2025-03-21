from WriteError import WriteError
import os
from datetime import datetime, date, time, timedelta

LOG_EXTENSIONS = [".xml", ".txt", ".csv"]

class FindFreshLogs:
    
    def __init__(self):
        self.ok = True
        self.errMsg = ''
    
    def getStartDate(self):
        
        # Получаем вчерашнюю дату, 18:00.
        yesterday = date.today() - timedelta(days=1)
        yesterday_date = date(yesterday.year, yesterday.month, yesterday.day)
        yesterday_time = time(18, 0, 0)
        yesterday = datetime.combine(yesterday_date, yesterday_time)
        
        return yesterday
    
    def scanDirectory(self, path, start_date, fresh_files=[]):
        
        # Обойдем структуру рекурсией, найдем в ней файлы.
        for obj in os.listdir(path):
            inner_path = os.path.join(path, obj)
            if (os.path.isdir(inner_path)):
                fresh_files = self.scanDirectory(inner_path, start_date, fresh_files)
            else:
                #Нашли файл. Проверяем его расширение и дату последнего изменения.
                name, ext = os.path.splitext(inner_path)
                if (ext.lower() in LOG_EXTENSIONS):
                    last_modified = datetime.fromtimestamp(os.path.getmtime(inner_path))
                    if (last_modified >= start_date):
                        # Добавляем путь к файлу в список, если это - свежий лог.
                        if (inner_path not in fresh_files):
                            fresh_files.append(inner_path)
        
        # Пишем информационный лог.
        WriteError().writeLog("INFO", "FindFreshLogs:scanDirectory", f"Logs found within directory {path}: {fresh_files}")
        
        return fresh_files
    
    def execute(self, root):
        
        # Свежие логи - созданные не ранее 18:00 вчерашнего дня.
        yesterday = self.getStartDate()
        
        # Искать свежие логи будем внутри директории root.
        if not (os.path.isdir(root)):
            self.ok = False
            self.errMsg = f"{root} is not a directory or does not exist."
            # Пишем лог.
            WriteError().writeLog("ERROR", "FindFreshLogs:execute", self.errMsg)            
            return
        
        return self.scanDirectory(root, yesterday, [])