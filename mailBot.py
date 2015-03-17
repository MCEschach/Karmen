#! /usr/local/bin/python3
#coding=utf-8

import sys
import imaplib
import getpass
import email
import datetime
#import git
import os
import re
import json
import time
import subprocess
import uuid
from twython import Twython
import fbconsole as F

LOCALDIR = os.path.dirname(os.path.realpath(__file__))

from configparser import SafeConfigParser
parser = SafeConfigParser()
parser.read(LOCALDIR+'/mailbot.config')

SERVER = parser.get('mail_credentials', 'SERVER')
sender = parser.get('mail_credentials', 'sender')
#Login credentials:
USERNAME = parser.get('mail_credentials', 'USERNAME')
PASSWORD = parser.get('mail_credentials', 'PASSWORD')

#Für Twitter:
TWITTER_APP_KEY = parser.get('mail_credentials', 'TWITTER_APP_KEY')
TWITTER_APP_SECRET = parser.get('mail_credentials', 'TWITTER_APP_SECRET')
TWITTER_ACCESS_TOKEN = parser.get('mail_credentials', 'TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = parser.get('mail_credentials', 'TWITTER_ACCESS_SECRET')

#Für Facebook:
FACEBOOK_APP_ID = parser.get('mail_credentials','FACEBOOK_APP_ID')
FACEBOOK_ACCESS_TOKEN = parser.get('mail_credentials','FACEBOOK_ACCESS_TOKEN')
FACEBOOK_GROUP_ID = parser.get('mail_credentials','FACEBOOK_GROUP_ID')

#Wichtig für Filter:
BOTADDRESS = USERNAME

#Ändern bei Änderungen am MemeGenerator:
MEMEGENPATH = LOCALDIR + "/out.jpg" #Alle Generatoren schreiben die gleiche Datei, da keine parallel Ausführung.

MAGGIGENERATORSCRIPT = LOCALDIR + "/maggiGenerator.sh"
JANGENERATORSCRIPT = LOCALDIR + "/janGenerator.sh"

#fbconsole konfigurieren:
F.APP_ID = FACEBOOK_APP_ID
F.ACCESS_TOKEN = FACEBOOK_ACCESS_TOKEN
F.AUTH_SCOPE = ['publish_actions']

def sendMail(to, subject, content, replyTo = "", attachImgPath = ""):
    destination = [to]

    # typical values for text_subtype are plain, html, xml
    text_subtype = 'plain'

    from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
    # from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)
    from email.mime.text import MIMEText
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

        conn = SMTP(SERVER)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, destination, msg.as_string())
        finally:
            conn.close()

    except Exception as exc:
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

        msg = email.message_from_bytes(data[0][1])
        msg_content = msg.get_payload()
        #print 'Message %s: %s' % (num, msg['Subject'])
        M.store(num, '+FLAGS', '\\Deleted') #Löschen
        newMails.append(msg) #... und an Rückgabe anfügen

    M.expunge() #Als gelöscht markierte Nachrichten entfernen
    return newMails #Erst wenn die abgerufenen Mails gelöscht wurden, die abgerufen mails zurückgeben

def getNewMails():
    mails = []
    try:
        M = imaplib.IMAP4_SSL(SERVER)
        try:
            M.login(USERNAME, PASSWORD)
        except imaplib.IMAP4.error:
            print ("LOGIN FAILED!")
            return mails

        #print "LOGIN SUCCEEDED!"

        rv, data = M.select("INBOX")
        if (rv == 'OK') & (int(data[0]) > 0):
            #print "Processing mailbox...\n"
            mails = process_mailbox(M) # where the magic happens
            M.close()
        #else:
            #print "INBOX not found or empty"
        #M.logout()
    except Exception as exc:
        print('Failure: ' ,exc)
        print ("Mail failure! Retry...")
    #finally:
    #    if M:
    #        M.logout()
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
    try:
        p = subprocess.Popen([ LOCALDIR+'/memeGenerator.sh', text])
        p.wait()
    except:
        return "" #Bei Fehler einfach kein Bild anhängen
    return MEMEGENPATH

def generate2LineMeme(text, generatorScript):
    text = text.strip(" \n\r") #Alle unnötigen Umbrüche entfernen
    #Im Anschluss den Text in 2 Teile teilen. Getrennt wird an der letzten leeren Zeile (\n\n)
    lines = text.split("\n")
    lines = lines[::-1] #Array umdrehen

    string1 = ""
    string2 = ""
    secondLine = True

    for string in lines:
        if secondLine:
            string2 = string+"\n"+string2
        else:
            string1 = string +"\n"+string1
        if len(string.strip(" \n\r\t"))<1: #Auch Zeilen mit Leerzeichen zählen als leere Zeile
            secondLine = False

    #leere Zeilen am Anfang und Ende der Strings entfernen.
    string1 = string1.strip(" \n\r")
    string2 = string2.strip(" \n\r")
    if len(string1) < 1:
        string1 = " "
    if len(string2) < 1:
        string2 = " "
    try:
        p = subprocess.Popen([ generatorScript, string1, string2])
        p.wait()#Das ist ein Problem und kann den Bot zum abstürzen bringen
    except:
        return "" #Bei Fehler einfach kein Bild anhängen
    return MEMEGENPATH

def sendPicReply(mail, content, pic):
    #Im Fehlerfall einfach Email ohne Bild senden: (Chat bots machen das so!)
    replyToMail(mail, content, pic)

def facebookFeet(text):
    text = text.strip(" \r\n")#Unnötige Leerzeichen entfernen
    #status = F.post('/'+FACEBOOK_GROUP_ID+'/feed', {'message':text})
    #print(status)
    try:
        status = F.post('/'+FACEBOOK_GROUP_ID+'/feed', {'message':text})
    except:
        return

def tweet(text):
    text = text.strip(" \r\n")#Unnötige Leerzeichen entfernen
    try:
        twitter = Twython(TWITTER_APP_KEY, TWITTER_APP_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        twitter.update_status(status=text)
    except:
        return

def processMail(mail):
    content = mail.get_payload()
    subject = mail['Subject']
    if not subject:
        subject = ""
    toAddress = mail['To']
    if not toAddress:
        toAddress = ""
    #Filter: (Es kann immer nur ein Filter zutreffen)
    if toAddress == BOTADDRESS:
        #Die Antworten auf direkte Anfragen zuerst:
        if u"#TobiHeult" in subject:
            tobiHeult = generateTobiMeme(content)
            sendPicReply(mail, "*heul*\n*flenn*\n#MCEschach", tobiHeult)
            return
        if u"#Schweinemann" in subject:
            jan = generate2LineMeme(content, JANGENERATORSCRIPT)
            sendPicReply(mail, "#Schweinemann trinkt was er kann!", jan)
            return
        if u"#MaggiNavigiert" in subject:
            maggi = generate2LineMeme(content, MAGGIGENERATORSCRIPT)
            sendPicReply(mail, "Maggi kennt den Weg!\n#MCEschachRegelt", maggi)
            return
        if u"#Twitter" in subject:
            tweet(content)
        if u"#Facebook" in subject:
            facebookFeet(content)
    if u"#KarmenSagDochWas" in content:
        replyToMail(mail, "Blah, Blah, Blah")
        return

print ("Mailbot start up...\nInfo: No Error Messages yet!")

while True: #Main loop
    time.sleep(3) #Immer kurz warten. System nicht überfordern
    mails = getNewMails()
    for mail in mails:
        processMail(mail)

