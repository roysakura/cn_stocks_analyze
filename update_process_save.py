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
from stocks_update import update_data_base,is_trade_date,post_data_process,update_data_base_fast,update_concepts
from export_graph import *
from send_email import send

ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')


def main():
	today = datetime.datetime.today().strftime("%Y-%m-%d")
	today = datetime.datetime.strptime(today,"%Y-%m-%d")
	conn = sqlite3.connect('cn_stocks.db')

	print('Updating today data...\n')
	update_data_base_fast()
	conn.commit()

	try:
		print('Exporting Graph...\n')
		performance(conn,today,True)
		continuous_limit_up_stocks(conn,today,True)
		ceil_first(conn,today,True)
		#top_break_graph(conn,today,True)
		strong_industries(conn,today,True)
		strong_week_graph(conn,today,True)
		#break_ma(conn,today,True)
		strong_concepts(conn,today,True)
		continuous_rise_stocks(conn,today,True)
		top_rise_down(conn,today,True)
		signal_trend(conn,today,True)
		strong_industries_concepts_combine(conn,today,True)
		hk_china_money_flow(conn,today,True)
		send()
	except Exception as e:
		print(e)

	conn.close()

	post_data_process()

if __name__ == '__main__':
	main()