#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import smtplib
import time
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pretty_errors
import tqdm
from icecream import ic

import config

pretty_errors.activate()


def loadSentFiles():
    if os.path.exists('sentFiles.txt'):
        return open('sentFiles.txt').read().splitlines()
    return []


def getMailMessage(fileName):
    # 创建一个带附件的实例
    message = MIMEMultipart()
    message['From'] = Header(config.sender, 'utf-8')
    message['To'] = Header(config.receiver, 'utf-8')
    subject = '「资源备份」' + fileName
    message['Subject'] = Header(subject, 'utf-8')
    # 邮件正文内容
    message.attach(MIMEText('', 'plain', 'utf-8'))
    return message


def notBackupFiles(sentFiles):
    exclude_prefixes = ('__', '.')
    for root, dirs, files in os.walk(config.backupDir):
        dirs[:] = [dirname
                   for dirname in dirs
                   if not dirname.startswith(exclude_prefixes)]
        for file in files:
            if file.startswith('.'):
                continue
            filePath = os.path.join(root, file)
            lastModTime = os.path.getmtime(filePath)
            ic(file, lastModTime)
            fileAndLastModTime = str((file, lastModTime))
            if fileAndLastModTime not in sentFiles:
                print(fileAndLastModTime, sentFiles)
                yield fileAndLastModTime, filePath, file


def getAttach(filePath, fileName):
    part = MIMEApplication(open(filePath, 'rb').read())
    part.add_header('Content-Disposition', 'attachment', filename=fileName)
    return part


def log(fileAndLastModTime):
    with open('sentFiles.txt', 'a') as f:
        f.write(fileAndLastModTime + '\n')


def sleep(n):
    print('sleep {} seconds...'.format(n))
    for _ in tqdm.trange(n):
        time.sleep(1)


def main():
    os.chdir(config.curDir)
    sentFiles = loadSentFiles()
    server = smtplib.SMTP_SSL("smtp.qq.com", 465)
    server.login(config.sender, config.passwd)

    for fileAndLastModTime, filePath, fileName in notBackupFiles(sentFiles):
        ic(fileAndLastModTime, filePath, fileName)
        message = getMailMessage(fileName)
        attach = getAttach(filePath, fileName)
        message.attach(attach)
        server.sendmail(config.sender, [config.receiver, ], message.as_string())
        log(fileAndLastModTime)
        sleep(10)

    server.quit()


if __name__ == '__main__':
    main()
