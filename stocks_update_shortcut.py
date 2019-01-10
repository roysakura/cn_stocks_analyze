# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import tushare as ts
import pandas as pd
import datetime
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import sqlite3


ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')
pro = ts.pro_api()
conn = sqlite3.connect('cn_stocks.db')
#engine = create_engine('mysql+pymysql://stock:494904@120.79.35.86:3306/stocks?charset=utf8')

today = (datetime.datetime.today()).strftime("%Y-%m-%d")
today_all_real  = ts.get_today_all()

try:
	today_all = pd.read_sql('SELECT * from today_all',conn).drop(['date'],axis=1)
except:
	today_all = ts.today_all_real
	#today_all.reset_index().to_sql('today_all',conn,if_exists='replace',index=False)

if not today_all_real.equals(today_all):
	print('NOT EQUALS')
	today_all = today_all_real
	today_all['date'] = today
	today_all.reset_index().to_sql('today_all',conn,if_exists='replace',index=False)

today_all = today_all.set_index('code')


all_stocks = ts.get_stock_basics()
all_stocks.reset_index().to_sql('all_stocks',conn,if_exists='replace',index=False)
all_stocks_list = all_stocks.index.tolist()
all_stocks_dict = {code:all_stocks.loc[code]['name'] for code in all_stocks.index.tolist()}

widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
pbar = ProgressBar(widgets=widgets,maxval=len(all_stocks_dict.keys())).start()

for i,code in enumerate(all_stocks_dict.keys()):
	try:
		current_stock = pd.read_sql('SELECT * from \'{}\''.format(code),conn)
		stock = today_all.loc[code][['open','high','trade','low','volume','changepercent']]

		df_stock = pd.DataFrame([stock])
		df_stock['date'] = today
		df_stock['volume'] = df_stock['volume']/100.0
		df_stock.columns = ['open','high','close','low','volume','p_change','date']

		df_combine = pd.concat([current_stock.sort_values('date'),df_stock],sort=True)
		df_combine['ma5'] = df_combine['ma5'].fillna(df_combine['close'].rolling(5).mean())
		df_combine['max5'] = df_combine['close'].rolling(5).max()
		df_combine['min5'] = df_combine['close'].rolling(5).min()
		df_combine['ma10'] = df_combine['ma10'].fillna(df_combine['close'].rolling(10).mean())
		df_combine['max10'] = df_combine['close'].rolling(10).max()
		df_combine['min10'] = df_combine['close'].rolling(10).min()
		df_combine['ma20'] = df_combine['ma20'].fillna(df_combine['close'].rolling(20).mean())
		df_combine['max20'] = df_combine['close'].rolling(20).max()
		df_combine['min20'] = df_combine['close'].rolling(20).min()
		df_combine['ma30'] = df_combine['close'].rolling(30).mean()
		df_combine['max30'] = df_combine['close'].rolling(30).max()
		df_combine['min30'] = df_combine['close'].rolling(30).min()
		df_combine['ma60'] = df_combine['close'].rolling(60).mean()
		df_combine['max60'] = df_combine['close'].rolling(60).max()
		df_combine['min60'] = df_combine['close'].rolling(60).min()
		df_combine['ma120'] = df_combine['close'].rolling(120).mean()
		df_combine['max120'] = df_combine['close'].rolling(120).max()
		df_combine['min120'] = df_combine['close'].rolling(120).min()

		df_combine['v_ma5'] = df_combine['v_ma5'].fillna(df_combine['volume'].rolling(5).mean())
		df_combine['v_ma10'] = df_combine['v_ma10'].fillna(df_combine['volume'].rolling(10).mean())
		df_combine['v_ma20'] = df_combine['v_ma20'].fillna(df_combine['volume'].rolling(20).mean())
		df_combine['v_ma30'] = df_combine['volume'].rolling(30).mean()
		df_combine['v_ma60'] = df_combine['volume'].rolling(60).mean()
		df_combine['v_ma120'] = df_combine['volume'].rolling(120).mean()

		df_combine.to_sql(code,conn,if_exists='replace',index=False)
	except:
		continue
	pbar.update(i + 1)

stocks_5  	= {}#pd.DataFrame()
stocks_10 	= {}#pd.DataFrame()
stocks_20 	= {}#pd.DataFrame()
stocks_30 	= {}#pd.DataFrame()
stocks_60 	= {}#pd.DataFrame()
stocks_90 	= {}#pd.DataFrame()
stocks_125 	= {}#pd.DataFrame()


one_year_before = (datetime.datetime.today()-timedelta(days=365)).strftime("%Y%m%d")
cal = pro.trade_cal(start_date=one_year_before, end_date=datetime.datetime.today().strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
cal['cal_date'] = pd.to_datetime(cal['cal_date'])
trade_date = cal[cal.is_open==1]['cal_date']

for i,code in enumerate(all_stocks_dict.keys()):
	try:
		current_stock = pd.read_sql('SELECT * from \'{}\''.format(code),conn)
		current_stock['date'] = pd.to_datetime(current_stock['date'])
	except:
		continue

	current_stock['code'] = code
	current_stock = current_stock.drop_duplicates()

	mask_60 = (current_stock['date']>trade_date.iloc[60]) & (current_stock['date']<=trade_date.iloc[0])
	#stocks_60 = pd.concat([stocks_60,current_stock.loc[mask_60]],sort=True)
	stocks_60[code]= current_stock.loc[mask_60]

	#mask_90 = (current_stock['date']>trade_date.iloc[90]) & (current_stock['date']<=trade_date.iloc[0])
	#stocks_90 = pd.concat([stocks_90,current_stock.loc[mask_90]],sort=True)

	mask_125 = (current_stock['date']>trade_date.iloc[125]) & (current_stock['date']<=trade_date.iloc[0])
	#stocks_120 = pd.concat([stocks_120,current_stock.loc[mask_120]],sort=True)
	stocks_125[code]= current_stock.loc[mask_125]

	pbar.update(i + 1)

st60_df = pd.concat(stocks_60,sort=True)
st60_df.to_sql('stocks_60_days',conn,if_exists='replace',index=False)

st125_df = pd.concat(stocks_125,sort=True)
st125_df.to_sql('stocks_125_days',conn,if_exists='replace',index=False)

pbar.finish()

