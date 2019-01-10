# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import tushare as ts
import pandas as pd
import datetime
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import sqlite3

conn = sqlite3.connect('cn_stocks.db')
#engine = create_engine('mysql+pymysql://stock:494904@120.79.35.86:3306/stocks?charset=utf8')

today = (datetime.datetime.today()).strftime("%Y-%m-%d")

try:
	today_all = pd.read_sql('SELECT * from today_all',conn)
except:
	today_all = ts.get_today_all()
	today_all['date'] = today
	today_all.reset_index().to_sql('today_all',conn,if_exists='replace',index=False)

if today_all.iloc[0]['date']!=today:
	today_all = ts.get_today_all()
	today_all['date'] = today
	today_all.reset_index().to_sql('today_all',conn,if_exists='replace',index=False)

all_stocks = ts.get_stock_basics()
all_stocks.reset_index().to_sql('all_stocks',conn,if_exists='replace',index=False)
all_stocks_list = all_stocks.index.tolist()
all_stocks_dict = {code:all_stocks.loc[code]['name'] for code in all_stocks.index.tolist()}

#ten_years_before = (datetime.datetime.today() - timedelta(days=3650)).strftime("%Y-%m-%d")

log = pd.read_sql('SELECT date from log',conn)
last_update = (log.iloc[-1]['date'])

print(last_update,today)

widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
pbar = ProgressBar(widgets=widgets,maxval=len(all_stocks_dict.keys())).start()
for i,code in enumerate(all_stocks_dict.keys()):
	stock = ts.get_hist_data(code,last_update,today)
	pbar.update(i + 1)
	if stock is not None:
		stock = stock.reset_index().sort_values(by=['date'])
		stock.to_sql(code,conn,if_exists='append',index=False)
	else:
		print(code,stock)

pbar.finish()

log = pd.DataFrame({'date' : [today]})
log.to_sql('log',conn,if_exists='append')