# -*- coding: utf-8 -*-
import os
import tushare as ts
import pandas as pd
import numpy as np
import datetime
import time
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

def update_data_base_fast():
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
	last_125 = pd.read_sql('select * from stocks_125_days;',conn) 
	stocks_125_fast = {}
	stocks_60_fast = {}
	i=0
	for code,g in last_125.groupby('code'):
		current_stock = g.drop_duplicates(subset=['date'])
		stock = today_all.loc[code][['open','high','trade','low','volume','changepercent']]
		current_stock['datetime'] = pd.to_datetime(current_stock['date'])
		current_stock = current_stock[current_stock['datetime'] < today]
		current_stock.drop(['datetime'],axis=1,inplace=True)
		df_stock = pd.DataFrame([stock])
		df_stock['date'] = today.strftime('%Y-%m-%d 00:00:00')
		df_stock['code'] = code
		df_stock.columns = ['open','high','close','low','volume','p_change','date','code']
		df_combine = pd.concat([current_stock.sort_values('date'),df_stock])
		df_combine.drop_duplicates(subset='date',inplace=True)
		df_combine['l_close'] = df_combine['close'].shift(1)
		df_combine['islimit'] = df_combine.apply(lambda x: 1 if (x['volume']>0 and x['l_close']>0 and x['close']>=np.around((x['l_close']*1.1),decimals=2)) else (-1 if (x['volume']>0 and x['l_close']>0 and x['close']<=np.around((x['l_close']*0.9),decimals=2)) else 0),axis=1)
		df_combine['date'] = pd.to_datetime(df_combine['date'])
		mask_60 = (df_combine['date']>trade_date.iloc[60]) & (df_combine['date']<=trade_date.iloc[0])
		stocks_60_fast[code]= df_combine.loc[mask_60]
		stocks_125_fast[code] = df_combine
		pbar.update(i + 1)
		i+=1

	st60_df_fast = pd.concat(stocks_60_fast)
	st60_df_fast.to_sql('stocks_60_days',conn,if_exists='replace',index=False)
	st125_df_fast = pd.concat(stocks_125_fast)
	st125_df_fast.to_sql('stocks_125_days',conn,if_exists='replace',index=False)
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

	## Start do updating
	today_all = pd.read_sql('SELECT * from today_all',conn)
	today_all = today_all.set_index('code')

	stocks_60 	= {}
	stocks_125 	= {}

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
			df_combine['l_open'] = df_combine['open'].shift(1)
			df_combine['l_high'] = df_combine['high'].shift(1)
			df_combine['l_low'] = df_combine['low'].shift(1)
			df_combine['price_change'] = np.around((df_combine['close'] - df_combine['l_close']),decimals=2)
			df_combine['islimit'] = df_combine.apply(lambda x: 1 if (x['volume']>0 and x['l_close']>0 and x['close']>=np.around((x['l_close']*1.1),decimals=2)) else (-1 if (x['volume']>0 and x['l_close']>0 and x['close']<=np.around((x['l_close']*0.9),decimals=2)) else 0),axis=1)
			df_combine['ma5'] = df_combine['ma5'].fillna(df_combine['close'].rolling(5).mean())
			df_combine['max5'] = df_combine['close'].rolling(5).max()
			df_combine['min5'] = df_combine['close'].rolling(5).min()
			df_combine['ma10'] = df_combine['ma10'].fillna(np.around(df_combine['close'].rolling(10).mean(),decimals=2))
			df_combine['max10'] = df_combine['close'].rolling(10).max()
			df_combine['min10'] = df_combine['close'].rolling(10).min()
			df_combine['ma20'] = df_combine['ma20'].fillna(np.around(df_combine['close'].rolling(20).mean(),decimals=2))
			df_combine['max20'] = df_combine['close'].rolling(20).max()
			df_combine['min20'] = df_combine['close'].rolling(20).min()
			df_combine['ma30'] = np.around(df_combine['close'].rolling(30).mean(),decimals=2)
			df_combine['max30'] = df_combine['close'].rolling(30).max()
			df_combine['min30'] = df_combine['close'].rolling(30).min()
			df_combine['ma60'] = np.around(df_combine['close'].rolling(60).mean(),decimals=2)
			df_combine['max60'] = df_combine['close'].rolling(60).max()
			df_combine['min60'] = df_combine['close'].rolling(60).min()
			df_combine['ma120'] = np.around(df_combine['close'].rolling(120).mean(),decimals=2)
			df_combine['max120'] = df_combine['close'].rolling(120).max()
			df_combine['min120'] = df_combine['close'].rolling(120).min()
			df_combine['v_ma5'] = df_combine['v_ma5'].fillna(np.around(df_combine['volume'].rolling(5).mean(),decimals=2))
			df_combine['v_ma10'] = df_combine['v_ma10'].fillna(np.around(df_combine['volume'].rolling(10).mean(),decimals=2))
			df_combine['v_ma20'] = df_combine['v_ma20'].fillna(np.around(df_combine['volume'].rolling(20).mean(),decimals=2))
			df_combine['v_ma30'] = np.around(df_combine['volume'].rolling(30).mean(),decimals=2)
			df_combine['v_ma60'] = np.around(df_combine['volume'].rolling(60).mean(),decimals=2)
			df_combine['v_ma120'] = np.around(df_combine['volume'].rolling(120).mean(),decimals=2)

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
			print(e)
			continue

		pbar.update(i + 1)

	st60_df = pd.concat(stocks_60)
	st60_df.to_sql('stocks_60_days',conn,if_exists='replace',index=False)
	st125_df = pd.concat(stocks_125)
	st125_df.to_sql('stocks_125_days',conn,if_exists='replace',index=False)

	pbar.finish()

def update_concepts():
	pro = ts.pro_api()
	conn = sqlite3.connect('cn_stocks.db')
	all_stocks = pd.read_sql('select * from all_stocks',conn)
	concepts = pro.concept(src='ts')

	widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
	pbar = ProgressBar(widgets=widgets,maxval=len(concepts['code'])+1).start()
	all_concepts = pd.DataFrame()
	for i,code in enumerate(concepts['code'],1):
		cl = pro.concept_detail(id='{}'.format(code), fields='ts_code,name')
		cl['concepts'] = code
		all_concepts = pd.concat([all_concepts,cl])
		if i%90==0:
			time.sleep(60)
		pbar.update(i+1)

	pbar.finish()

	concepts.columns = ['code','c_name','src']
	all_concepts.columns= ['ts_code','name','code']
	all_concepts_merge = all_concepts.merge(concepts,on='code',how='left')
	concept_df = pd.DataFrame()
	for code,g in all_concepts_merge.groupby('ts_code'):
		concept_df = pd.concat([concept_df,pd.DataFrame([[code[:-3],list(g['c_name'].unique())]])])  
	concept_df.columns=['code','c_name']
	concept_df['c_name'] = concept_df['c_name'].map(lambda x: ','.join(x))

	concept_df.to_sql('all_concepts',conn,if_exists='replace',index=False)

def update_folder_concepts():
	concepts_dict = {}
	for root, directories, filenames in os.walk('data/concepts/'):
		for filename in filenames:
			c = pd.read_csv(u'data/concepts/{}'.format(filename),sep='\t', encoding='gb2312')
			concepts_dict[filename[:-12]]=','.join( [str(x) for x in c.iloc[:-1][u'代码'].values.tolist()])

	concepts_df = pd.DataFrame.from_dict(concepts_dict,orient='index')
	concepts_df.columns = ['code']

	concepts_dict = {}
	for n in concepts_df.index:
		for code in concepts_df.loc[n]['code'].split(','):
			concepts_dict.setdefault(code,'')
			concepts_dict[code] += n+','

	concepts_df = pd.DataFrame.from_dict(concepts_dict,orient='index')
	concepts_df = concepts_df.reset_index()
	concepts_df.columns = ['code','c_name']
	concepts_df['c_name'] = concepts_df['c_name'].map(lambda x:x[:-1])
	concepts_df.sort_values('code',inplace=True)
	concepts_df.to_sql('all_concepts',conn,if_exists='replace',index=False)

def main():
    print('Updating today data...\n')
    update_data_base_fast()
    post_data_process()
    #update_concepts()
    
if __name__ == '__main__':
    main()