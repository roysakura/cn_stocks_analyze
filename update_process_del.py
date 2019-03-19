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
from stocks_update import update_data_base,is_trade_date,post_data_process,update_data_base_fast,update_concepts,clean_up_today,update_data_base_fast_simple
from export_graph import *
from send_email_intern import send_intern

ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')


def main():
	today = datetime.datetime.today().strftime("%Y-%m-%d")
	today = datetime.datetime.strptime(today,"%Y-%m-%d")
	conn = sqlite3.connect('cn_stocks.db')

	print('Updating today data...\n')
	update_data_base_fast_simple()
	conn.commit()

	print('Exporting Graph...\n')
	#top_break_graph(conn,today,True)
	#strong_industries(conn,today,True)
	#break_ma(conn,today,True)
	#strong_concepts(conn,today,True)
	strong_industries_concepts_combine_candidates(conn,today,True)

	conn.close()
		#continuous_limit_up_stocks()
	send_intern()

	clean_up_today()

if __name__ == '__main__':
	main()