# Log_Notificator

### Общее описание ###

На сервере в ETL реализованы процессы миграций и массовых операций. Эти процессы поддерживают логирование в предзаданные директории.

Для обхода необходимости (:D) забирать логи руками и передавать кому-то был написан этот инструмент.

Инструмент опирается на конфигурационный файл, который обязательно должен находиться рядом с исполняемым файлом.

Также он имеет свое собственное логирование. Папка для логов создастся рядом с исполняемым файлом, если ее нет, и в нее будут добавляться файлы с датой в имени. За каждую дату может быть создан один файл логов, и каждый запуск инструмента приведет к добавлению новых записей в конец этого файла.

### Строение решения ###

config - файл конфигурации. Должен иметь именно такую структуру, какая представлена в загруженном варианте.
SendLogs - основной py-файл для запуска. Содержит подключение класса SendMail и вызов основной функции.
  |-- SendEmail - класс с основной логикой решения. Подключает классы GetConfig, FindFreshLogs, WriteError.
        |-- GetConfig - класс, описывающий получение данных из конфигурационного файла. Подключает WriteError.
        |-- FindFreshLogs - класс, с помощью которого выполняется поиск логов ETL, время последнего изменения которых равна или больше 18:00 предыдущего дня. Подключает WriteError.
              |-- WriteError - класс для обеспечения логирования.
OTICLogSender - код для сборки exe-файла. Содержит все выше перечисленные классы и вызов основной функции.

### О конфигурационном файле ###

Config-файл внутри себя содержит json со следующими атрибутами:
* connection(host, port) - данные почтового сервера для подключения по SMTP.
* sender(email, password) - данные пользователя, под которым выполняется подключение к почтовому серверу и отправка писем.
* recievers[(email),...] - пользователи, которым нужно отправлять файлы логов, найденных в paths.
* message(subject) - тема письма, которая конкатенируется с названием обрабатываемого инструмента и подставляется в письмо.
* paths[(path, instrument),...] - пути к директориям, которые на любом уровне вложенности внутри себя могут содержать лог-файлы.
* admins(recievers[(email),...], paths[(path, instrument),...]) - отдельный набор получателей и источников лог-файлов, предназначено для отправки логов администраторам: им требуется другой набор, нежели обычным пользователям.
