from WriteError import WriteError
import os
import zipfile

ZIP_NAME = "Logs.zip"

class ZipLogs:
    
    def __init__(self):
        self.ok = True
        self.errMsg = ''
    
    def ZipFiles(self, paths):
        
        for path in paths:
            # Запускаем преобразование только тогда, когда есть, что преобразовывать.
            if (len(path["logs"]) > 0):
                
                # Проверяем существование целевой директории.
                if not (os.path.isdir(path["path"])):
                    self.ok = False
                    self.errMsg = f"{path['path']} does not exist."
                    return
                
                # Формируем полный путь к архиву.
                destination = f"{path['path']}\\{ZIP_NAME}"
                
                # Если такой архив уже существует, сначала удаляем существующий.
                if (os.path.exists(destination)):
                    try:
                        os.remove(destination)
                    except Exception as e:
                        self.ok = False
                        self.errMsg = e
                        return
                
                # Открываем zip-файл.
                with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Проходим по всем найденным лог-файлам.
                    for log_path in path["logs"]:
                        # Добавляем логи в архив, предварительно проверив, что это файлы.
                        if (os.path.isfile(log_path)):
                            zip_file.write(log_path)
                
                # Перезаписываем path["logs"] на полученный архив.
                path["logs"] = [destination]
        
        return paths
    
    def execute(self, paths):
        
        paths = self.ZipFiles(paths)
        
        if not (self.ok):
            # Пишем лог.
            WriteError().writeLog("ERROR", "ZipLogs:execute", self.errMsg)
            return
        
        return paths