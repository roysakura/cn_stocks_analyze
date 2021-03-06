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
import settings

import datetime
import oss2
from os.path import expanduser

import sys
from PIL import Image
from wm import watermark


endpoint = 'http://oss-cn-shenzhen.aliyuncs.com' # Suppose that your bucket is in the Hangzhou region.
image_domain ="http://news-material.oss-cn-shenzhen.aliyuncs.com/"
auth = oss2.Auth(settings.OSS2_USER, settings.OSS2_PASS)
bucket = oss2.Bucket(auth, endpoint, 'cnstock')
home = expanduser("~")
COMMASPACE = ', '

def send_intern(date=datetime.datetime.today()):
    today = date.strftime('%Y%m%d')
    sender = '110672023@qq.com'
    gmail_password = 'cflgbqogaggmbibb'
    recipients = ['110672023@qq.com']

    # Create the enclosing (outer) message
    outer = MIMEMultipart()
    outer['Subject'] = u'{}分析'.format(today)
    outer['To'] = COMMASPACE.join(recipients)
    outer['From'] = sender
    outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'

    # List of attachments
    attachments = [ settings.IMGTEMPLATE['BANNER_INDI'],
                    settings.GRAPH['STRONG_COMBINE'],
                    settings.GRAPH['STRONG_COMBINE_CANDIDATE'],
                    ]
    combine_files = []
    for i in attachments:
        if type(i)==int:
            file = os.path.join(home,"Documents","{}.jpg".format(i))
            result = bucket.get_object_to_file('{}_{}.jpg'.format(today,i), file)
            mark = Image.open('imgs/watermark.png', 'r')
            img = Image.open(file)
            img = watermark(img, mark, 'scale', 0.1)
            img.save(file, format='JPEG', quality=90)
            combine_files.append(file)
        else:
            combine_files.append(i)

    combine(date,combine_files)       
    final_file = os.path.join(home,"Documents","{}_combine.jpg".format(today))
    try:
        with open(final_file, 'rb') as fp:
            msg = MIMEBase('application', "octet-stream")
            msg.set_payload(fp.read())
            encoders.encode_base64(msg)
            msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(final_file))
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

def combine(date,images_list):
    today = date.strftime('%Y%m%d')

    images = map(Image.open, [x for x in images_list])
    widths, heights = zip(*(i.size for i in images))

    max_width = max(widths)
    sum_height = sum(heights)


    new_im = Image.new('RGB', (max_width, sum_height))

    y_offset = 0
    for image in images_list:
      im = Image.open(image)
      new_im.paste(im, (0,y_offset))
      y_offset += im.size[1]

    file = os.path.join(home,"Documents","{}_combine.jpg".format(today))
    new_im.save(file)

if __name__ == '__main__':
    date = sys.argv[1:]
    date = datetime.datetime.strptime(date[0], '%Y-%m-%d')
    send(date)