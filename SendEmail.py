from GetConfig import GetConfig
from FindFreshLogs import FindFreshLogs
from ZipLogs import ZipLogs
from WriteError import WriteError
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

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
