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
	stocks_60 	= {}
	stocks_125 	= {}

	## Check if today is trade day, if not, then return
	today = datetime.datetime.today()
	today_str = today.strftime("%Y-%m-%d")
	if not is_trade_date(today):
		return

	now =datetime.datetime.now()
	now_str = now.strftime("%Y-%m-%d %H:%M:%S")
	

	## Start do updating
	today_all  = ts.get_today_all()
	today_all['datetime'] = now_str
	today_all[today_all.changepercent>9.9].reset_index().to_sql('ceiling_tick',conn,if_exists='append',index=False)
	
def main():
    print('Updating data...\n')
    ceil()
    
if __name__ == '__main__':
    main()