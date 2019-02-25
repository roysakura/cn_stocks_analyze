# -*- coding: utf-8 -*-
import tushare as ts
import pandas as pd
import numpy as np
import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import settings
import sqlite3

#Include Plotly library for drawing data graph
from plotly.offline import init_notebook_mode,iplot
import plotly.graph_objs as go
import plotly.io as pio

ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')

def is_trade_date(date):
	## Initialize tushare interface
	pro = ts.pro_api()

	one_month_ago = (date-timedelta(days=30))
	one_month_ago_str = one_month_ago.strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=one_month_ago_str, end_date=date.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	if cal.iloc[0]['is_open']==0:
		return False
	else:
		return True

def update_data_base():
	## Initialize database and setup tushare interface
	conn = sqlite3.connect('cn_stocks.db')
	pro = ts.pro_api()
	stocks_60 	= {}
	stocks_125 	= {}

	## Check if today is trade day, if not, then return
	today = datetime.datetime.today()
	today_str = today.strftime("%Y-%m-%d")
	if not is_trade_date(today):
		return

	one_year_before_str = (today-timedelta(days=365)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=one_year_before_str, end_date=today.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	cal['cal_date'] = pd.to_datetime(cal['cal_date'])
	trade_date = cal[cal.is_open==1]['cal_date']

	
	## Start do updating
	today_all  = ts.get_today_all()
	today_all['date'] = today_str
	today_all.reset_index().to_sql('today_all',conn,if_exists='replace',index=False)
	today_all = today_all.set_index('code')

	all_stocks = ts.get_stock_basics()
	all_stocks.reset_index().to_sql('all_stocks',conn,if_exists='replace',index=False)
	all_stocks_list = all_stocks.index.tolist()

	widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
	pbar = ProgressBar(widgets=widgets,maxval=len(all_stocks_list)).start()
	for i,code in enumerate(all_stocks_list):
		try:
			current_stock = pd.read_sql('SELECT * from \'{}\''.format(code),conn).drop_duplicates(subset=['date'])
			stock = today_all.loc[code][['open','high','trade','low','volume','changepercent']]

			current_stock['datetime'] = pd.to_datetime(current_stock['date'])
			current_stock = current_stock[current_stock['datetime'] < today]
			current_stock.drop(['datetime'],axis=1,inplace=True)
			df_stock = pd.DataFrame([stock])
			df_stock['date'] = today.strftime("%Y-%m-%d")
			df_stock['volume'] = df_stock['volume']/100.0
			df_stock.columns = ['open','high','close','low','volume','p_change','date']
			df_combine = pd.concat([current_stock.sort_values('date'),df_stock])
			df_combine['l_close'] = df_combine['close'].shift(1)
			df_combine['islimit'] = df_combine.apply(lambda x: 1 if (x['volume']>0 and x['l_close']>0 and x['close']>=np.around((x['l_close']*1.1),decimals=2)) else (-1 if (x['volume']>0 and x['l_close']>0 and x['close']<=np.around((x['l_close']*0.9),decimals=2)) else 0),axis=1)
			current_stock = df_combine.copy()
			current_stock['date'] = pd.to_datetime(current_stock['date'])
			current_stock['code'] = code
			current_stock = current_stock.drop_duplicates()
			mask_60 = (current_stock['date']>trade_date.iloc[60]) & (current_stock['date']<=trade_date.iloc[0])
			stocks_60[code]= current_stock.loc[mask_60]
			mask_125 = (current_stock['date']>trade_date.iloc[125]) & (current_stock['date']<=trade_date.iloc[0])
			stocks_125[code]= current_stock.loc[mask_125]

			df_combine.to_sql(code,conn,if_exists='replace',index=False)
		except Exception as e:
			ten_years_before = (today-timedelta(days=3650)).strftime("%Y%m%d")
			stock = ts.get_hist_data(code,ten_years_before,today_str)
			try:
				stock.to_sql(code,conn,if_exists='replace',index=False)
			except Exception as ee:
				print('ee->{}'.format(ee))
			print('e->{}'.format(e))
			continue

		pbar.update(i + 1)

	st60_df = pd.concat(stocks_60)
	st60_df.to_sql('stocks_60_days',conn,if_exists='replace',index=False)
	st125_df = pd.concat(stocks_125)
	st125_df.to_sql('stocks_125_days',conn,if_exists='replace',index=False)

	pbar.finish()

def post_data_process():
	pro = ts.pro_api()
	conn = sqlite3.connect('cn_stocks.db')
	all_stocks = pd.read_sql('SELECT * from all_stocks',conn)
	all_stocks_list = all_stocks['code'].values.tolist()

	## Check if today is trade day, if not, then return
	today = datetime.datetime.today()
	today_str = today.strftime("%Y-%m-%d")
	if not is_trade_date(today):
		return

	one_year_before_str = (today-timedelta(days=365)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=one_year_before_str, end_date=today.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	cal['cal_date'] = pd.to_datetime(cal['cal_date'])
	trade_date = cal[cal.is_open==1]['cal_date']

	stocks_60 	= {}
	stocks_125 	= {}

	widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
	pbar = ProgressBar(widgets=widgets,maxval=len(all_stocks_list)).start()
	for i,code in enumerate(all_stocks_list):
		try:
			current_stock = pd.read_sql('SELECT * from \'{}\''.format(code),conn).drop_duplicates(subset=['date'])
			current_stock['l_close'] = current_stock['close'].shift(1)
			current_stock['l_open'] = current_stock['open'].shift(1)
			current_stock['l_high'] = current_stock['high'].shift(1)
			current_stock['l_low'] = current_stock['low'].shift(1)
			current_stock['price_change'] = np.around((current_stock['close'] - current_stock['l_close']),decimals=2)
			current_stock['ma5'] = current_stock['ma5'].fillna(current_stock['close'].rolling(5).mean())
			current_stock['max5'] = current_stock['close'].rolling(5).max()
			current_stock['min5'] = current_stock['close'].rolling(5).min()
			current_stock['ma10'] = current_stock['ma10'].fillna(np.around(current_stock['close'].rolling(10).mean(),decimals=2))
			current_stock['max10'] = current_stock['close'].rolling(10).max()
			current_stock['min10'] = current_stock['close'].rolling(10).min()
			current_stock['ma20'] = current_stock['ma20'].fillna(np.around(current_stock['close'].rolling(20).mean(),decimals=2))
			current_stock['max20'] = current_stock['close'].rolling(20).max()
			current_stock['min20'] = current_stock['close'].rolling(20).min()
			current_stock['ma30'] = np.around(current_stock['close'].rolling(30).mean(),decimals=2)
			current_stock['max30'] = current_stock['close'].rolling(30).max()
			current_stock['min30'] = current_stock['close'].rolling(30).min()
			current_stock['ma60'] = np.around(current_stock['close'].rolling(60).mean(),decimals=2)
			current_stock['max60'] = current_stock['close'].rolling(60).max()
			current_stock['min60'] = current_stock['close'].rolling(60).min()
			current_stock['ma120'] = np.around(current_stock['close'].rolling(120).mean(),decimals=2)
			current_stock['max120'] = current_stock['close'].rolling(120).max()
			current_stock['min120'] = current_stock['close'].rolling(120).min()
			current_stock['v_ma5'] = current_stock['v_ma5'].fillna(np.around(current_stock['volume'].rolling(5).mean(),decimals=2))
			current_stock['v_ma10'] = current_stock['v_ma10'].fillna(np.around(current_stock['volume'].rolling(10).mean(),decimals=2))
			current_stock['v_ma20'] = current_stock['v_ma20'].fillna(np.around(current_stock['volume'].rolling(20).mean(),decimals=2))
			current_stock['v_ma30'] = np.around(current_stock['volume'].rolling(30).mean(),decimals=2)
			current_stock['v_ma60'] = np.around(current_stock['volume'].rolling(60).mean(),decimals=2)
			current_stock['v_ma120'] = np.around(current_stock['volume'].rolling(120).mean(),decimals=2)

			current_stock.to_sql(code,conn,if_exists='replace',index=False)

			current_stock['date'] = pd.to_datetime(current_stock['date'])
			current_stock['code'] = code
			current_stock = current_stock.drop_duplicates()
			mask_60 = (current_stock['date']>trade_date.iloc[60]) & (current_stock['date']<=trade_date.iloc[0])
			stocks_60[code]= current_stock.loc[mask_60]
			mask_125 = (current_stock['date']>trade_date.iloc[125]) & (current_stock['date']<=trade_date.iloc[0])
			stocks_125[code]= current_stock.loc[mask_125]

		except Exception as e:
			print(e)
			continue

		pbar.update(i + 1)

	st60_df = pd.concat(stocks_60)
	st60_df.to_sql('stocks_60_days',conn,if_exists='replace',index=False)
	st125_df = pd.concat(stocks_125)
	st125_df.to_sql('stocks_125_days',conn,if_exists='replace',index=False)

	pbar.finish()


def main():
    print('Updating today data...\n')
    update_data_base()
    post_data_process()
    
if __name__ == '__main__':
    main()