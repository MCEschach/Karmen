#! /usr/local/bin/python
#coding=utf-8

import sys
import imaplib
import getpass
import email
import datetime
import git
import os
import re
import json
import time
import subprocess
import uuid

LOCALDIR = os.path.dirname(os.path.realpath(__file__))

#Folgende Dinge sollten in eine Konfigurationsdatei ausgelagert werden:
SMTPserver = "ZENSORED"
sender =     "ZENSORED"
#Login credentials:
USERNAME = "ZENSORED"
PASSWORD = "ZENSORED"

#Wichtig für Filter:
BOTADDRESS = USERNAME

#Ändern bei Änderungen am MemeGenerator:
MEMEGENPATH = LOCALDIR + "/tobi.jpg"

def sendMail(to, subject, content, replyTo = "", attachImgPath = ""):
    destination = [to]

    # typical values for text_subtype are plain, html, xml
    text_subtype = 'plain'

    from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
    # from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)
    from email.MIMEText import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image     import MIMEImage

    try:
        msg = MIMEMultipart()
        msgText = MIMEText(content, text_subtype, "utf-8")
        msg.attach(msgText)
        msg['Subject']= subject
        msg['From']   = sender # some SMTP servers will do this automatically, not all
        msg['To'] = to
        if replyTo:
            msg['In-Reply-To'] = replyTo

        #Falls angegeben, Bild mit Anhängen:
        if attachImgPath:
            img = dict(title=attachImgPath, path=attachImgPath, cid=str(uuid.uuid4()))
            with open(img['path'], 'rb') as file:
                msg_image = MIMEImage(file.read(), name=os.path.basename(img['path']))
                msg.attach(msg_image)

        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.close()

    except Exception, exc:
        #sys.exit( "mail failed; %s" % str(exc) ) # give a error message
        #Keine Ausgabe in die Konsole... TODO: Logfile
        return #Einfach die Mail nicht absenden bei Fehler

def process_mailbox(M):
    newMails = []
    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        #print "No messages found!"
        return newMails

    for num in data[0].split(): #Alle Nachrichten durchlaufen
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            #print "ERROR getting message", num
            return [] #Keine Mails zurückgeben

        msg = email.message_from_string(data[0][1])
        msg_content = msg.get_payload()
        #print 'Message %s: %s' % (num, msg['Subject'])
        M.store(num, '+FLAGS', '\\Deleted') #Löschen
        newMails.append(msg) #... und an Rückgabe anfügen

    M.expunge() #Als gelöscht markierte Nachrichten entfernen
    return newMails #Erst wenn die abgerufenen Mails gelöscht wurden, die abgerufen mails zurückgeben

def getNewMails():
    mails = []
    try:
        M = imaplib.IMAP4_SSL(SMTPserver)
        try:
            M.login(USERNAME, PASSWORD)
        except imaplib.IMAP4.error:
            print "LOGIN FAILED!"
            return mails

        #print "LOGIN SUCCEEDED!"

        rv, data = M.select("INBOX")
        if (rv == 'OK') & (int(data[0]) > 0):
            print "Processing mailbox...\n"
            mails = process_mailbox(M) # where the magic happens
            M.close()
        else:
            print "INBOX not found or empty"
        #M.logout()
    except:
        print "Mail failure"
    finally:
        M.logout()
    return mails


def saveData(data):
    with open('mailbot.dat', 'w') as outfile:
        json.dump(data, outfile)

def loadData():
    json_data=open('json_data')
    data = json.load(json_data)
    json_data.close()
    return data

def replyToMail(mail, content, attachImgPath = ""):
    subject = mail['Subject']
    if not subject:
        subject = ""
    fromAddress = mail['From']
    if not fromAddress:
        return
    messageId = mail['Message-ID']
    if not messageId:
        messageId = ""
    sendMail(fromAddress, "Re: "+subject, content, messageId, attachImgPath)

def generateTobiMeme(text):
    #Bild generieren: Anmerkung text sollte vor der Übergabe an Bash überprüft werden
    p = subprocess.Popen([ LOCALDIR+'/memeGenerator.sh', text])
    p.wait()
    return MEMEGENPATH

def processMail(mail):
    content = mail.get_payload()
    subject = mail['Subject']
    if not subject:
        subject = ""
    toAddress = mail['To']
    if not toAddress:
        toAddress = ""
    #Filter:
    if toAddress == BOTADDRESS:
        #Die Antworten auf direkte Anfragen zuerst:
        if u"#TobiHeult" in subject:
            tobiHeult = generateTobiMeme(content)
            replyToMail(mail, "*heul*\n*flenn*\n#MCEschach", tobiHeult)
    if u"#KarmenSagDochWas" in content:
        replyToMail(mail, "Blah, Blah, Blah")

print "Mailbot start up...\nInfo: No Error Messages yet!"

while True: #Main loop
    time.sleep(3) #Immer kurz warten. System nicht überfordern
    mails = getNewMails()
    for mail in mails:
        processMail(mail)

