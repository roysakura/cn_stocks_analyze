# -*- coding: utf-8 -*-
import tushare as ts
import pandas as pd
import numpy as np
import datetime
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
			current_stock = pd.read_sql('SELECT * from \'{}\''.format(code),conn)
			stock = today_all.loc[code][['open','high','trade','low','volume','changepercent']]

			df_stock = pd.DataFrame([stock])
			df_stock['date'] = today.strftime("%Y-%m-%d")
			df_stock['volume'] = df_stock['volume']/100.0
			df_stock.columns = ['open','high','close','low','volume','p_change','date']

			current_stock = current_stock[current_stock['date']< today.strftime("%Y-%m-%d")]
			df_combine = pd.concat([current_stock.sort_values('date'),df_stock])
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
			if stock:
				stock.to_sql(code,conn,if_exists='replace',index=False)
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
    
if __name__ == '__main__':
    main()