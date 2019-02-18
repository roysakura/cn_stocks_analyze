# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import tushare as ts
import pandas as pd
import datetime
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import settings
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import sqlite3


# connect to the database
conn = sqlite3.connect('cn_stocks.db')
cur = conn.cursor()

all_stocks = ts.get_stock_basics()
all_stocks_list = all_stocks.index.tolist()

widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
pbar = ProgressBar(widgets=widgets,maxval=len(all_stocks_list)).start()
for i,code in enumerate(all_stocks_list):
		try:
			cur.execute('DELETE FROM \'{}\' WHERE date=\'20190218\''.format(code))
			conn.commit()
		except Exception as e:
			print(e)
			continue
		pbar.update(i + 1)

pbar.finish()
conn.close()



