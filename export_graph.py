# -*- coding: utf-8 -*-
import sys
import tushare as ts
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import settings
import sqlite3
import colorlover as cl
from sklearn.preprocessing import LabelEncoder
from collections import Counter
from pathlib import Path
from os.path import expanduser
import os
import oss2

#Include Plotly library for drawing data graph
from plotly.offline import init_notebook_mode,iplot
import plotly.graph_objs as go
import plotly.io as pio

from PIL import Image,ImageDraw,ImageFont

ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')
endpoint = 'http://oss-cn-shenzhen.aliyuncs.com' # Suppose that your bucket is in the Hangzhou region.
image_domain ="http://news-material.oss-cn-shenzhen.aliyuncs.com/"
auth = oss2.Auth(settings.OSS2_USER, settings.OSS2_PASS)
bucket = oss2.Bucket(auth, endpoint, 'cnstock')

home = expanduser("~")
#home = str(Path.home())

#Return numbers of trade day date list.
def get_dayrange(startfrom,num=5):
	pro = ts.pro_api()
	days_before = (startfrom-timedelta(days=120)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=days_before, end_date=startfrom.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	d_range = [datetime.datetime.strptime(d,'%Y%m%d') for d in cal[cal.is_open==1][:(num+1)].sort_values('cal_date',ascending=False)['cal_date']]

	return d_range


def performance(conn,date=datetime.datetime.today(),cloud_save=False):
	## First chart for over all performance
	today_all_changepercent_over_0 =pd.read_sql('select p_change from stocks_125_days where volume>0 and p_change<11 and p_change>0 and date=\'{}\''.format(date),conn)
	hist_data_today_all_changepercent_over_0 = np.histogram(today_all_changepercent_over_0['p_change'],bins=10,range=(0,11))
	today_all_changepercent_less_0 =pd.read_sql('select p_change from stocks_125_days where volume>0 and p_change>-11 and p_change<0 and date=\'{}\''.format(date),conn)
	hist_data_today_all_changepercent_less_0 = np.histogram(today_all_changepercent_less_0['p_change'],bins=10,range=(-10.5,0))

	graph_one = []
	graph_one.append(
	go.Bar(
	x=(hist_data_today_all_changepercent_over_0[1]),
	y=hist_data_today_all_changepercent_over_0[0],
	name=u'{}只上涨'.format(sum(hist_data_today_all_changepercent_over_0[0])),
	text=hist_data_today_all_changepercent_over_0[0],
	textposition = 'outside',
	marker=dict(
	color='#d10031',
	)
	)
	)

	graph_one.append(
	go.Bar(
	x=(hist_data_today_all_changepercent_less_0[1]),
	y=hist_data_today_all_changepercent_less_0[0],
	name=u'{}只下跌'.format(sum(hist_data_today_all_changepercent_less_0[0])),
	text=hist_data_today_all_changepercent_less_0[0],
	textposition = 'outside',
	marker=dict(
	color='#02c927',
	)
	)
	)

	labels = [str(s)+'%' for s in range(-10,11)]
	tickvals = [s for s in range(-10,11)]
	layout_one = dict(title = u'{} 市场表现'.format(date.strftime('%Y/%m/%d')),
	        xaxis=go.layout.XAxis(title=u'幅度',ticktext=labels,tickvals=tickvals),
	        yaxis = dict(title = '数量',tick0=0, dtick=100))

	fig = go.Figure(data=graph_one, layout=layout_one)
	iplot(fig)

	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_0.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig,file,scale=2)
	if cloud_save:
		file_name = "{}_0.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

def strong_week_graph(conn,date=datetime.datetime.today(),cloud_save=False):
	stocks_60 =pd.read_sql('select * from stocks_60_days',conn)
	stats = {}
	for n,g in stocks_60.groupby('date'):
		stats.setdefault(n,{})
		stats[n].setdefault('over_5%',0)
		stats[n].setdefault('less_5%',0)
		stats[n]['over_5%'] = len(g[g.p_change>=5.0])
		stats[n]['less_5%'] = len(g[g.p_change<=-5.0])

	data = pd.DataFrame.from_dict(stats, orient='index')
	data = data.reset_index()

	data = data[-10:]
	graph_two = []

	graph_two.append(
	go.Bar(
	y=data.index,
	x=data['less_5%'],
	name=u'下跌超5%',
	text=data['less_5%'],
	textposition = 'auto',
	marker=dict(
	color='#02c927',
	),
	opacity=0.8,
	orientation='h'
	)
	)

	graph_two.append(
	go.Bar(
	y=data.index,
	x=data['over_5%'],
	name=u'上涨超5%',
	text=data['over_5%'],
	textposition = 'auto',
	marker=dict(
	color='#d10031',
	),
	opacity=0.8,
	orientation='h'
	)
	)

	

	labels = [d[:-9] for d in data['index']]
	tickvals = data.index

	layout_two = dict(title = u'市场表现二',
	yaxis=go.layout.YAxis(ticktext=labels,tickvals=tickvals),
	xaxis = dict(title = '数量',tick0=0, dtick=100),
	)
	fig = go.Figure(data=graph_two, layout=layout_two)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_1.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file, scale=2)
	if cloud_save:
		file_name = "{}_1.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

def top_break_graph(conn,date=datetime.datetime.today(),cloud_save=False):
	stocks_60 = pd.read_sql('select * from stocks_60_days ORDER BY date',conn)
	top_break_through = {}
	down_break_through = {}
	stocks_60 = stocks_60[stocks_60.date<=date.strftime('%Y-%m-%d')]
	code_list = stocks_60['code'].unique().tolist()
	for code in code_list:
		cur_stock = stocks_60[stocks_60.code==code].sort_values('date')
		top_break_dates = cur_stock[cur_stock.close>=cur_stock.max120]['date'].values.tolist()
		for tdate in top_break_dates:
			top_break_through.setdefault(tdate,[])
			top_break_through[tdate].append(code)

		down_break_dates = cur_stock[cur_stock.close<=cur_stock.min120]['date'].values.tolist()
		for ddate in down_break_dates:
			down_break_through.setdefault(ddate,[])
			down_break_through[ddate].append(code)

	top_break_records = pd.DataFrame.from_dict(top_break_through,orient='index')
	top_break_records.index = pd.to_datetime(top_break_records.index)
	top_break_records = ~top_break_records.isnull()
	top_break_records = top_break_records.sort_index().sum(axis=1)

	down_break_records = pd.DataFrame.from_dict(down_break_through,orient='index')
	down_break_records.index = pd.to_datetime(down_break_records.index)
	down_break_records = ~down_break_records.isnull()
	down_break_records = down_break_records.sort_index().sum(axis=1)

	data = pd.concat([top_break_records,down_break_records],axis=1)
	data.columns=['top_break','down_break']
	data = data.fillna(0)

	data = data.reset_index()
	data = data[-10:]
	graph_three = []

	graph_three.append(
	go.Bar(
	x=data['top_break'],
	y=data.index,
	name=u'创半年新高',
	text=data['top_break'],
	textposition = 'auto',
	marker=dict(
	color='#d10031',
	),
	orientation='h',
	opacity=0.8
	)
	)

	graph_three.append(
	go.Bar(
	x=data['down_break'],
	y=data.index,
	name=u'创半年新低',
	text=data['down_break'],
	textposition = 'auto',
	marker=dict(
	color='#02c927',
	),
	orientation='h',
	opacity=0.8
	)
	)

	labels = [d.strftime('%m/%d') for d in data['index']]
	tickvals = data.index

	layout_three = dict(title = u'市场表现三',
	yaxis=go.layout.YAxis(ticktext=labels,tickvals=tickvals),
	xaxis = dict(title = '数量',tick0=0, dtick=100),
	)
	fig = go.Figure(data=graph_three, layout=layout_three)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_9.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_9.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

# check if it's ceiling at certain time
def ceil_first(conn,date=datetime.datetime.today(),cloud_save=False):
	daterange = get_dayrange(startfrom=date,num=2)
	all_stocks =pd.read_sql('select code,name,industry from all_stocks',conn)
	first_limit_up =pd.read_sql('select * from stocks_60_days where islimit=1 and date<=\'{} 00:00:00\' and date>=\'{} 00:00:00\''.format(daterange[0].strftime('%Y-%m-%d'),daterange[1].strftime('%Y-%m-%d')),conn).drop_duplicates(subset=['code'],keep=False)
	first_limit_up = first_limit_up[(first_limit_up.date==date.strftime('%Y-%m-%d 00:00:00')) & (first_limit_up.close!=first_limit_up.open)]
	today_ceil_first = pd.read_sql('select distinct code from ceiling_tick where date=\'{}\''.format(date.strftime('%Y-%m-%d')),conn)

	candidates = all_stocks[all_stocks.code.isin(list(set(first_limit_up['code'].tolist()).intersection(today_ceil_first['code'].tolist())))]

	#delete IPO
	ipo=[]
	for code in candidates.code.tolist():
		try:
			stock_record = pd.read_sql('select * from \'{}\';'.format(code),conn)
			if len(stock_record)<30:
				ipo.append(code)
		except:
			pass
	#delete t and flat
	candidates = candidates[~candidates.code.isin(ipo)]

	trace = go.Table(
	header=dict(values=list([u'代码',u'名称',u'所属行业',]),
	fill = dict(color='#C2D4FF'),
	align = ['left'] * 5),
	cells=dict(values=[candidates.code, candidates.name,candidates.industry],
	align = ['left'] * 5))

	layout = dict(title=u"{} 涨停先锋".format(date.strftime("%Y/%m/%d")),margin=dict(l=0,r=0,b=0,t=30),height=max([300,len(candidates)*25]))

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_2.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_2.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)


def continuous_limit_up_stocks(conn,date=datetime.datetime.today(),cloud_save=False):
	all_stocks =pd.read_sql('select code,name,industry from all_stocks',conn).set_index('code')
	today_limit_up_code =pd.read_sql('select code from stocks_60_days where islimit=1 and date=\'{}\''.format(date),conn)
	stock_limit_up_record = {}
	for stock_code in today_limit_up_code['code'].tolist():
		stock_record = pd.read_sql('select * from \'{}\' where date<=\'{}\';'.format(stock_code,date),conn)
		limit_str = ''.join([str(x) for x in stock_record.sort_values('date',ascending=False)['islimit'].values.tolist()])
		if len(limit_str)<30:
			continue
		stock_limit_up_record[stock_code] = limit_str.find('0')

	limit_up_stocks = pd.DataFrame()
	if len(stock_limit_up_record)>0:
		limit_up_stocks = pd.DataFrame.from_dict(stock_limit_up_record,orient='index')
	else:
		return

	limit_up_stocks.columns = ['freq']
	limit_up_combined = limit_up_stocks[limit_up_stocks.freq>1].merge(all_stocks,left_index=True,right_index=True).sort_values(by='freq',ascending=False)

	limit_up_combined = limit_up_combined.reset_index()
	limit_up_combined.columns = ['code','freq','name','industry']

	colors = cl.scales['9']['seq']['YlOrRd']
	limit_up_combined['color'] = limit_up_combined['freq'].map(lambda x: colors[x] if x<=8 else colors[8])

	trace = go.Table(
	header=dict(values=list([u'代码',u'名称',u'连板次数',u'所属行业',]),
	fill = dict(color='#C2D4FF'),
	align = ['left'] * 5),
	cells=dict(values=[limit_up_combined.code, limit_up_combined.name, limit_up_combined.freq, limit_up_combined.industry],
	fill = dict(color=[limit_up_combined.color]),
	font = dict(color='black'),
	align = ['left'] * 5))

	layout = dict(title=u"{} 连板统计".format(date.strftime("%Y/%m/%d")),margin=dict(l=0,r=0,b=0,t=30),height=max([300,len(limit_up_combined)*25]))

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_3.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_3.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

def strong_industries(conn,date=datetime.datetime.today(),cloud_save=False):
	days_range = 20
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name,industry from all_stocks',conn)
	stocks_60 = stocks_60.merge(all_stocks,on='code',how='left')
	today = date
	pro = ts.pro_api()
	one_year_before = (today-timedelta(days=60)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=one_year_before, end_date=today.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	d_range = [datetime.datetime.strptime(d,'%Y%m%d') for d in cal[cal.is_open==1][:days_range].sort_values('cal_date')['cal_date']]
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	industry_top = {}
	for d in d_range:
	  industry_top.setdefault(d,{})
	  stocks_60_t = stocks_60[stocks_60.date==d][['code','name','p_change','industry']].sort_values('p_change',ascending=False)
	  for n,g in stocks_60_t.groupby('industry'):
	      industry_top[d].setdefault(n,{})
	      industry_top[d][n]['number'] = len(g[g['p_change']>=9.5])
	      industry_top[d][n]['member'] = ','.join(g[g['p_change']>=9.5].sort_values('p_change',ascending=False)['name'].values.tolist()[:3])

	industry_top_df = pd.DataFrame.from_dict({(i,j): industry_top[i][j] 
	                         for i in industry_top.keys() 
	                         for j in industry_top[i].keys()},
	                     orient='index')

	industry_top_df_ = industry_top_df.reset_index()
	industry_top_df_.columns=['date','industry','number','member']
	industry_top_df_ = industry_top_df_.sort_values(['date','number'], ascending=[False, False])
	top_3_list = {}
	top_3_df = []
	for d,g in industry_top_df_.groupby('date'):
	  top_3_list.setdefault(d,None)
	  top_3_list[d] = g.head(3)
	  top_3_df.append(top_3_list[d])

	top_rds = pd.concat(top_3_df)  
	top_rds = top_rds.sort_values(['date','number'],ascending=[False,False]).astype('str')
	top_rds = top_rds[:(5*3)] # Five days records
	colors = cl.scales['5']['seq']['YlOrRd']
	top_rds['color'] = LabelEncoder().fit_transform(top_rds['date'])
	top_rds['color'] = top_rds['color'].map(lambda x:colors[x])
	trace = go.Table(
	header=dict(values=list([u'日期',u'所属行业',u'涨停个股',]),
	fill = dict(color='#C2D4FF'),
	align = ['left'] * 5),
	cells=dict(values=[top_rds.date, top_rds.industry, top_rds.number],
	fill = dict(color=[top_rds.color]),
	font = dict(color='black'),
	align = ['left'] * 5))

	layout = dict(title=u"每日强势板块",margin=dict(l=0,r=0,b=0,t=30),height=max([300,len(top_rds)*25]))

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_4.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_4.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

	#Top 5 
	c = dict( Counter(top_rds[:6]['industry']))
	industry_top = pd.DataFrame.from_dict(c,orient='index')
	industry_top.columns = ['number']
	industry_top = industry_top.sort_values('number',ascending=False)

	graph = []
	graph.append(
	go.Pie(labels=industry_top.index.tolist(),values=industry_top.number,textfont=dict(size=8),pull=.1,hole=.1)
	)

	layout = dict(title = u'强势行业龙虎榜')

	fig = go.Figure(data=graph, layout=layout)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_5.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_5.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

	#return top_rds.to_json(orient='index')

def break_ma(conn,date=datetime.datetime.today(),cloud_save=False):
	pro = ts.pro_api()
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name,industry from all_stocks',conn)
	month_before = (date-timedelta(days=30)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=month_before, end_date=date.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	two_days = [datetime.datetime.strptime(x,"%Y%m%d") for x in cal[cal.is_open==1][:2].cal_date.values.tolist()]
	two_days.sort()
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60_2_days = stocks_60[stocks_60.date.isin(two_days) & (stocks_60.volume>0)].sort_values('date',ascending=False)
	today_break_through = []
	for n,g in stocks_60_2_days.groupby('code'):
		try:
			g = g.sort_values('date',ascending=False)
			if (g.iloc[0]['close'] > g.iloc[0]['ma5']) & (g.iloc[0]['close'] > g.iloc[0]['ma10']) & (g.iloc[0]['close'] > g.iloc[0]['ma20']) & (g.iloc[0]['close'] > g.iloc[0]['ma60']) & (g.iloc[1]['close'] < g.iloc[0]['ma5']) & (g.iloc[1]['close'] < g.iloc[0]['ma10']) & (g.iloc[1]['close'] < g.iloc[0]['ma20']) & (g.iloc[1]['close'] < g.iloc[0]['ma60']):
				today_break_through.append(n)
		except:
			continue

	bt_df = pd.DataFrame(today_break_through)
	bt_df.columns = ['code']
	bt_df = bt_df.merge(all_stocks,on='code',how='left')
	bt_df = bt_df.merge(stocks_60_2_days[stocks_60_2_days.date==two_days[1]],on=['code'],how='left').sort_values('p_change',ascending=False)
	bt_df['date'] = two_days[1]


	trace = go.Table(
	header=dict(values=list([u'号码',u'中文',u'所属行业',u'涨幅']),
	fill = dict(color='#C2D4FF'),
	align = ['left'] * 5),
	cells=dict(values=[bt_df.code, bt_df.name, bt_df.industry,bt_df.p_change],
	align = ['left'] * 5))

	layout = dict(title=u"{} 突破图".format(two_days[1].strftime("%Y/%m/%d")),margin=dict(l=0,r=0,b=0,t=30),height=max([300,len(bt_df)*25]))

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_6.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_6.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

def continuous_rise_stocks(conn,date=datetime.datetime.today(),cloud_save=False):
	continuous_rise = {}
	daterange = get_dayrange(startfrom=date,num=31)
	all_stocks = pd.read_sql('select code,name,industry from all_stocks',conn)
	stocks_60 = pd.read_sql('select * from stocks_60_days where volume>0',conn)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60 = stocks_60[stocks_60.date.isin(daterange)]
	stocks_60 = stocks_60.sort_values('date',ascending=False)
	for n,g in stocks_60.groupby('code'):
		if len(g)<30:
			continue
		continuous_rise.setdefault(n,0)
		try:
			accumulate_change = (g.iloc[0]['close']-g.iloc[10]['close'])/g.iloc[10]['close']
		except:
			continue

		if (accumulate_change>=0.2) and (accumulate_change<=0.4) and (g.iloc[0:11]['p_change']>0).sum()>=8:
			continuous_rise[n] = round(accumulate_change*100,2) 


	continuous_rise_candidate_df = pd.DataFrame.from_dict(continuous_rise,orient='index')
	continuous_rise_candidate_df.columns = ['accumulate']
	continuous_rise_candidate_df = continuous_rise_candidate_df.sort_values('accumulate',ascending=False).reset_index()
	continuous_rise_candidate_df.columns = ['code','accumulate']
	continuous_rise_candidate_df['accumulate'] = continuous_rise_candidate_df['accumulate'].map(lambda x: '{}%'.format(x))
	continuous_rise_candidate_df = continuous_rise_candidate_df.merge(all_stocks,on='code',how='left')
	continuous_rise_candidate_df = continuous_rise_candidate_df.head(10)

	trace = go.Table(
	header=dict(values=list([u'号码',u'名称',u'所属行业',u'累计涨幅']),
	fill = dict(color='#C2D4FF')),
	cells=dict(values=[continuous_rise_candidate_df.code, continuous_rise_candidate_df.name, continuous_rise_candidate_df.industry,continuous_rise_candidate_df.accumulate]),
	)

	layout = dict(title=u"{} 连涨股".format(date.strftime("%Y/%m/%d")),margin=dict(l=0,r=0,b=0,t=30),height=max([300,len(continuous_rise_candidate_df)*25]))

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_7.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig,file,scale=2)
	if cloud_save:
		file_name = "{}_7.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

def top_rise_down(conn,date=datetime.datetime.today(),cloud_save=False):
	pro = ts.pro_api()
	stocks_60 = pd.read_sql('select * from stocks_60_days where volume>0',conn)
	all_stocks = pd.read_sql('select code,name,industry from all_stocks',conn)
	d_range = get_dayrange(startfrom=date,num=31)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60_sub_5_days = stocks_60[stocks_60.date.isin(d_range)].sort_values('date',ascending=False)
	today_top_rise = {}
	for n,g in stocks_60_sub_5_days.groupby('code'):
		if len(g)<30:
			continue
		today_top_rise.setdefault(n,0)
		try:
			today_top_rise[n] = (g.iloc[0]['close']-g.iloc[5]['close'])/g.iloc[5]['close']
		except:
			continue

	today_top_rise_dt = pd.DataFrame.from_dict(today_top_rise,orient='index')
	today_top_rise_dt.columns = ['p_change']
	today_top_rise_dt = today_top_rise_dt.sort_values('p_change',ascending=False)
	today_top_rise_dt = today_top_rise_dt.reset_index()
	today_top_rise_dt.columns = ['code','p_change']
	today_top_bottom = pd.concat([today_top_rise_dt.head(5),today_top_rise_dt.tail(5)])
	today_top_bottom = today_top_bottom.merge(all_stocks,on='code',how='left')
	today_top_bottom['p_change_str'] = today_top_bottom['p_change'].map(lambda x: '{0:.0f}%'.format(x*100))

	today_top_bottom['color'] = today_top_bottom['p_change'].map(lambda x: '#ff5a57' if x>0 else '#54ff68')

	trace = go.Table(
	header=dict(values=list([u'号码',u'名称',u'所属行业',u'幅度']),
	),
	cells=dict(values=[today_top_bottom.code, today_top_bottom.name, today_top_bottom.industry,today_top_bottom.p_change_str],
	fill = dict(color=[today_top_bottom.color])
	)
	)

	layout = dict(title=u"{} 五天涨跌幅排行榜".format(date.strftime("%Y/%m/%d")),margin=dict(l=0,r=0,b=0,t=30),height=max([300,len(today_top_bottom)*25]))

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_8.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	if cloud_save:
		file_name = "{}_8.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)

def signal_trend(conn,date=datetime.datetime.today(),cloud_save=False):
	daterange = get_dayrange(startfrom=date,num=1)
	stocks_60 = pd.read_sql('select * from stocks_60_days where volume>0',conn)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60 = stocks_60[stocks_60.date.isin(daterange)]

	yesterday_top_break = stocks_60[(stocks_60.date == daterange[1]) & (stocks_60.islimit==1)].sort_values('code')
	today_good_pratice = stocks_60[(stocks_60.date == daterange[0]) & (stocks_60.code.isin(yesterday_top_break['code'].tolist()))].sort_values('code')
	signal = round(np.sum(np.where((today_good_pratice['high'].reset_index()['high']-yesterday_top_break['close'].reset_index()['close'])/yesterday_top_break['close'].reset_index()['close']>=0.08,1,0))/len(yesterday_top_break),2)

	ttfont = ImageFont.truetype("imgs/hwfs.ttf",120)
	im = Image.open('imgs/s-0{}.png'.format(0 if signal<0.20 else (1 if signal>=0.2 and signal<0.4 else (2 if signal>=0.4 and signal<0.6 else (3 if signal>=0.6 and signal<0.8 else 4)))))
	draw = ImageDraw.Draw(im)
	draw.text((1400,225),u'{} 赚钱效应'.format(date.strftime('%Y/%m/%d')),fill=(0,0,0),font=ttfont)

	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_10.png".format(date.strftime('%Y%m%d')))
	if not os.path.exists(directory):
		os.makedirs(directory)
	im.save(file)
	if cloud_save:
		file_name = "{}_10.png".format(date.strftime('%Y%m%d'))
		bucket.put_object_from_file(file_name,file)


def main():
	conn = sqlite3.connect('cn_stocks.db')
	if len(sys.argv) == 2:
		date = sys.argv[1:]
		date = datetime.datetime.strptime(date[0], '%Y-%m-%d')
		print('Exporting Graph For Date {}...\n'.format(date))
		performance(conn,date,True)
		continuous_limit_up_stocks(conn,date,True)
		strong_industries(conn,date,True)
		strong_week_graph(conn,date,True)
		break_ma(conn,date,True)
		continuous_rise_stocks(conn,date,True)
		top_rise_down(conn,date,True)
		ceil_first(conn,date,True)
		top_rise_down(conn,date,True)
		signal_trend(conn,date,True)
	else:
		#performance(conn)
		#continuous_limit_up_stocks(conn)
		#strong_industries(conn)
		#strong_week_graph(conn)
		#break_ma(conn)
		pass

	conn.close()
		#continuous_limit_up_stocks()
if __name__ == '__main__':
	main()
