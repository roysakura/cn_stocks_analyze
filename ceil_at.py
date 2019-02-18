# -*- coding: utf-8 -*-
import tushare as ts
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import settings
import sqlite3

ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')

def get_dayrange(startfrom,num=5):
	pro = ts.pro_api()
	days_before = (startfrom-timedelta(days=120)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=days_before, end_date=startfrom.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	d_range = [datetime.datetime.strptime(d,'%Y%m%d') for d in cal[cal.is_open==1][:(num+1)].sort_values('cal_date',ascending=False)['cal_date']]

	return d_range

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

def ceil():
	## Initialize database and setup tushare interface
	conn = sqlite3.connect('cn_stocks.db')
	pro = ts.pro_api()

	## Check if today is trade day, if not, then return
	today = datetime.datetime.today()
	today_str = today.strftime("%Y-%m-%d")
	if not is_trade_date(today):
		return

	daterange = get_dayrange(startfrom=today,num=2)
	yesterday_all = pd.read_sql('select * from stocks_60_days where date=\'{} 00:00:00\''.format(daterange[1].strftime('%Y-%m-%d')),conn)
	yesterday_all = yesterday_all[['code','close']]
	

	## Start do updating
	today_all  = ts.get_today_all()
	today_all = today_all.merge(yesterday_all,on='code',how='left')
	today_all['date'] = today_str
	today_all['islimit'] = today_all['trade']>=np.round(today_all['close']*1.1,2)
	today_all = today_all[today_all.islimit==True]
	
	try:
		hist = pd.read_sql('select * from ceiling_tick where date=\'{}\''.format(today.strftime('%Y-%m-%d')),conn)
		conn.execute('delete from ceiling_tick where date=\'{}\''.format(today.strftime('%Y-%m-%d')),conn)
		conn.commit()
		candidates = list(set(today_all['code'].tolist()).intersection(hist['code'].tolist())) 
	except:
		candidates = today_all['code'].tolist()
	
	today_all = today_all[today_all.code.isin(candidates)]
	today_all.drop(['islimit','close'],axis=1,inplace=True)
	today_all.reset_index().to_sql('ceiling_tick',conn,if_exists='append',index=False)
	
def main():
    print('Updating data...\n')
    ceil()
    
if __name__ == '__main__':
    main()