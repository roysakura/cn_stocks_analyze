#!/usr/bin/env python
# encoding: utf-8
"""
python_3_email_with_attachment.py
Created by Robert Dempsey on 12/6/14.
Copyright (c) 2014 Robert Dempsey. Use at your own peril.

This script works with Python 3.x

NOTE: replace values in ALL CAPS with your own values
"""

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

import datetime
import oss2
from os.path import expanduser


endpoint = 'http://oss-cn-shenzhen.aliyuncs.com' # Suppose that your bucket is in the Hangzhou region.
image_domain ="http://news-material.oss-cn-shenzhen.aliyuncs.com/"
auth = oss2.Auth('LTAI3SvDl7ftuirM', 'iXKSQMMJCOJIzVenlMXgoXtv539zfE')
bucket = oss2.Bucket(auth, endpoint, 'cnstock')
home = expanduser("~")
COMMASPACE = ', '

def send():
    today = (datetime.datetime.today()).strftime('%Y%m%d')
    sender = '110672023@qq.com'
    gmail_password = 'cflgbqogaggmbibb'
    recipients = ['110672023@qq.com','150096055@qq.com']
    
    # Create the enclosing (outer) message
    outer = MIMEMultipart()
    outer['Subject'] = u'{}分析'.format(today)
    outer['To'] = COMMASPACE.join(recipients)
    outer['From'] = sender
    outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'

    # List of attachments
    attachments = range(0,9)
    for i in attachments:
        file = os.path.join(home,"Documents","{}.png".format(i))
        result = bucket.get_object_to_file('{}_{}.png'.format(today,i), file)

        try:
            with open(file, 'rb') as fp:
                msg = MIMEBase('application', "octet-stream")
                msg.set_payload(fp.read())
            encoders.encode_base64(msg)
            msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
            outer.attach(msg)
        except:
            print("Unable to open one of the attachments. Error: ", sys.exc_info()[0])
            raise

    composed = outer.as_string()

    # Send the email
    try:
        with smtplib.SMTP('smtp.qq.com', 587) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(sender, gmail_password)
            s.sendmail(sender, recipients, composed)
            s.close()
        print("Email sent!")
    except:
        print("Unable to send the email. Error: ", sys.exc_info()[0])
        raise

if __name__ == '__main__':
    send()