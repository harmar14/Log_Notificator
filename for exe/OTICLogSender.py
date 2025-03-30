import os
import sys
import codecs
import json
import smtplib
import zipfile
from datetime import datetime, date, time, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

EXE_PATH = sys.executable
CONFIG_PATH = "\\".join(EXE_PATH.split('\\')[:-1]) + "\\config.json"
LOG_PATH = "\\".join(EXE_PATH.split('\\')[:-1]) + "\\logs"
LOG_NAME = f"{date.today()}.txt"
LOG_EXTENSIONS = [".xml", ".txt", ".csv"]
ZIP_NAME = "Logs.zip"

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

class SendEmail:
    
    def __init__(self):
        self.ok = True
        self.errMsg = ''
    
    def getConfig(self):
        
        # Считываем конфигурационный файл.
        config = GetConfig().execute()
        
        if (config is None):
            return
        
        # Верхнеуровнево разбиваем полученные данные.
        try:
            self.connection = config["connection"]
            self.sender = config["sender"]
            self.recievers = config["recievers"]
            self.message = config["message"]
            self.paths = config["paths"]
            self.admins = config["admins"]
        except Exception as e:
            self.ok = False
            self.errMsg = e
            # Пишем лог.
            WriteError().writeLog("ERROR", "SendMail:getConfig", self.errMsg)
            return
        return
    
    def getLogs(self):
        
        logs = []
        processed_paths = []
        
        try:
            for path in self.paths:
                # Во избежание запуска повторного поиска логов при наличии дублей путей делаем проверку.
                if not (path in processed_paths):
                    logs.append({"path":path["path"],"instrument":path["instrument"],"logs":FindFreshLogs().execute(path["path"])})
                    processed_paths.append(path)
            for path in self.admins["paths"]:
                if not (path in processed_paths):
                    logs.append({"path":path["path"],"instrument":path["instrument"],"logs":FindFreshLogs().execute(path["path"])})
                    processed_paths.append(path)
        except Exception as e:
            self.ok = False
            self.errMsg = e
            # Пишем лог.
            WriteError().writeLog("ERROR", "SendMail:getLogs", self.errMsg)
            return
        
        self.logs = logs
            
        return
    
    def makeMessageObject(self, reciever, log_path):
        
        # Создаем объект письма.
        msg = MIMEMultipart()
        msg["From"] = self.sender["email"]
        msg["To"] = reciever
        msg["Date"] = formatdate(localtime=True)
        
        # Указываем текст, который будет находиться в теле письма.
        message = "Это письмо сформировано автоматически. Пожалуйста, не отвечайте на него."
        msg.attach(MIMEText(message))
        
        # Ищем в self.logs логи по переданному пути path, также достаем название инструмента.
        logs_to_send = []
        instrument = ''
        for item in self.logs:
            if (item["path"] == log_path):
                logs_to_send = item["logs"]
                instrument = item["instrument"]
        
        # В тему письма пишем название инструмента.
        msg["Subject"] = f"{self.message['subject']}: {instrument}"
        
        # Прикрепляем во вложения к письму.
        for path in logs_to_send:
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename={}".format(Path(path).name))    
            msg.attach(part)
        
        # Если logs_to_send пуст, добавим метку об этом.
        is_empty = False
        if (logs_to_send == []):
            is_empty = True
        
        return {"message":msg, "is_empty":is_empty}
    
    def makeInfoMessageObject(self, reciever, log_path):
        
        # Создаем объект письма.
        msg = MIMEMultipart()
        msg["From"] = self.sender["email"]
        msg["To"] = reciever
        msg["Date"] = formatdate(localtime=True)
        
        # Ищем в self.logs название инструмента по переданному пути path.
        logs_to_send = []
        instrument = ''
        for item in self.logs:
            if (item["path"] == log_path):
                instrument = item["instrument"]
        
        # В тему письма пишем название инструмента.
        msg["Subject"] = f"{self.message['subject']}: {instrument}"
        
        # Указываем текст, который будет находиться в теле письма.
        message = f"Произошла ошибка отправки логов инструмента \"{instrument}\".\nПожалуйста, свяжитесь с администратором OTIC в корпоративном мессенджере.\n\nЭто письмо сформировано автоматически. Пожалуйста, не отвечайте на него."
        msg.attach(MIMEText(message))
        
        return msg
    
    def sendLogs(self):
        
        try:
            # Создаем объект подключения к почтовому серверу по SMTP.
            smtp_obj = smtplib.SMTP(self.connection["host"], self.connection["port"])
            
            # Указываем объекту на необходимость шифрования.
            smtp_obj.starttls()
            
            # Авторизуемся.
            smtp_obj.login(self.sender["email"], self.sender["password"])
        except Exception as e:
            self.ok = False
            self.errMsg = e
            # Пишем лог.
            WriteError().writeLog("ERROR", "SendMail:sendLogs", self.errMsg)
            return
        
        # Предварительно формируем список paths логов для обычных пользователей.
        log_paths = []
        for path in self.paths:
            log_paths.append(path["path"])
        
        # Проходим по обычным получателям и отправляем письма им.
        for reciever in self.recievers:
            # По каждому инструменту отправляется отдельное письмо, иначе выше вероятность упасть с ошибкой "слишком большой размер вложений для одного письма".
            for log_path in log_paths:
                try:
                    # Формируем письмо.
                    message = self.makeMessageObject(reciever["email"], log_path)
                    if not (message["is_empty"]):
                        # Отправляем письмо.
                        smtp_obj.send_message(message["message"], from_addr=self.sender["email"], to_addrs=reciever["email"], mail_options=(), rcpt_options=())
                        # Пишем информационный лог.
                        WriteError().writeLog("INFO", "SendMail:sendLogs", f"Logs from path {log_path} have been sent to {reciever['email']}")
                except Exception as e:
                    # Пишем лог.
                    WriteError().writeLog("ERROR", "SendEmail:sendLogs", f"reciever={reciever}, log_path={log_path}, error: {e}")
                    # Формируем письмо, информирующее об ошибке.
                    message = self.makeInfoMessageObject(reciever["email"], log_path)
                    smtp_obj.send_message(message, from_addr=self.sender["email"], to_addrs=reciever["email"], mail_options=(), rcpt_options=())
        
        # Формируем список paths логов для администраторов.
        log_paths = []
        for path in self.admins["paths"]:
            log_paths.append(path["path"])
        
        # Проходим по администраторам, формируем и отправляем письма им.
        for reciever in self.admins["recievers"]:
            for log_path in log_paths:
                try:
                    message = self.makeMessageObject(reciever["email"], log_path)
                    if not (message["is_empty"]):
                        smtp_obj.send_message(message["message"], from_addr=self.sender["email"], to_addrs=reciever["email"], mail_options=(), rcpt_options=())
                        # Пишем информационный лог.
                        WriteError().writeLog("INFO", "SendMail:sendLogs", f"Logs from path {log_path} have been sent to {reciever['email']}")                        
                except Exception as e:
                    # Пишем лог.
                    WriteError().writeLog("ERROR", "SendEmail:sendLogs", f"reciever={reciever}, log_path={log_path}, error: {e}")
                    # Формируем письмо, информирующее об ошибке.
                    message = self.makeInfoMessageObject(reciever["email"], log_path)
                    smtp_obj.send_message(message, from_addr=self.sender["email"], to_addrs=reciever["email"], mail_options=(), rcpt_options=())
        
        # Разрываем соединение.
        smtp_obj.quit()
        
    def execute(self):
        
        self.getConfig()
        
        if not (self.ok):
            return
        
        self.getLogs()
        
        if not (self.ok):
            return
        
        self.logs = ZipLogs().execute(self.logs)
        
        if (self.logs is None):
            return
        
        self.sendLogs()

SendEmail().execute()
