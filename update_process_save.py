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
from stocks_update import update_data_base,is_trade_date
from export_graphs import *

ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')


def main():
	today = datetime.datetime.today().strftime('%Y-%m-%d')
	conn = sqlite3.connect('cn_stocks.db')

	print('Updating today data...\n')
	update_data_base()

	print('Exporting Graph...\n')
	export_graphs(conn,date,True)
	continuous_limit_up_stocks(conn,date,True)
	strong_industries(conn,date,True)
	strong_week_graph(conn,date,True)
	break_ma(conn,date,True)
	continuous_rise_stocks(conn,date,True)
	top_rise_down(conn,date,True)

	conn.close()
		#continuous_limit_up_stocks()
if __name__ == '__main__':
	main()