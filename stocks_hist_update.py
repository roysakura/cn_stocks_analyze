# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import tushare as ts
import pandas as pd
import datetime
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import sqlite3
import settings
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL


# connect to the database
conn = create_engine(URL(**settings.DATABASE))


#engine = create_engine('mysql+pymysql://stock:494904@120.79.35.86:3306/stocks?charset=utf8')

all_stocks = ts.get_stock_basics()
all_stocks_list = all_stocks.index.tolist()

connection = conn.raw_connection()
try:
	cursor = connection.cursor()
	cursor.execute("delete from all_stocks;")
	cursor.execute("alter table all_stocks convert to character set utf8;")
	cursor.close()
finally:
	connection.close()

all_stocks.reset_index().to_sql('all_stocks',conn,if_exists='append',index=False)
all_stocks_dict = {code:all_stocks.loc[code]['name'] for code in all_stocks.index.tolist()}
today = (datetime.datetime.today()-timedelta(days=2)).strftime("%Y-%m-%d")
ten_years_before = (datetime.datetime.today() - timedelta(days=3650)).strftime("%Y-%m-%d")

widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
pbar = ProgressBar(widgets=widgets,maxval=len(all_stocks_dict.keys())).start()
for i,code in enumerate(all_stocks_dict.keys()):
    stock = ts.get_hist_data(code,ten_years_before,today)
    pbar.update(i + 1)
    if stock is not None:
        stock = stock.reset_index().sort_values(by=['date'])
        stock.to_sql(code,conn,if_exists='replace',index=False)
    else:
        print(code)

pbar.finish()
log = pd.DataFrame({'date' : [today]})
log.to_sql('log',conn,if_exists='append')


#### update hist records ####
#today = (datetime.datetime.today()).strftime("%Y-%m-%d")
#
#all_stocks = ts.get_stock_basics()
#all_stocks_list = all_stocks.index.tolist()
#all_stocks_dict = {code:all_stocks.loc[code]['name'] for code in all_stocks.index.tolist()}
#
#for code in tqdm(all_stocks_dict.keys()):
#    stock = ts.get_hist_data(code,today,today)
#    if stock is not None and (os.path.exists('stocks_his/{}.csv'.format(code))):
#        stock_cur = pd.read_csv('stocks_his/{}.csv'.format(code),parse_dates=['date'],index_col=['date'])
#        stock.index = pd.to_datetime(stock.index)
#        stock_cur = pd.concat([stock,stock_cur])
#        stock_cur = stock_cur.groupby(stock_cur.index).first()
#        stock_cur.sort_index(ascending=False).to_csv('stocks_his/{}.csv'.format(code))
#    elif stock is not None:
#        stock_cur.sort_index(ascending=False).to_csv('stocks_his/{}.csv'.format(code))
#    else:
#        continue#