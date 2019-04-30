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
def combine_title(title_name,file):
	new_im = Image.open(file)
	title_tmp = Image.open('imgs/{}'.format(title_name))
	new_im.paste(title_tmp,(0,0),0)
	new_im.save(file)


def combine_subline(subline,file):
	ttfont = ImageFont.truetype("imgs/SIMHEI.TTF",36)
	im = Image.open(file)
	draw = ImageDraw.Draw(im)
	draw.text((75,65),subline,fill=(19,29,33),font=ttfont)
	im.save(file)

def frange(x, y, jump):
	l = []
	while x < y:
		l.append(x)
		x += jump
	return l

#Return numbers of trade day date list.
def get_dayrange(startfrom,num=5):
	pro = ts.pro_api()
	days_before = (startfrom-timedelta(days=120)).strftime("%Y%m%d")
	cal = pro.trade_cal(start_date=days_before, end_date=startfrom.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
	d_range = [datetime.datetime.strptime(d,'%Y%m%d') for d in cal[cal.is_open==1][:(num+1)].sort_values('cal_date',ascending=False)['cal_date']]

	return d_range

def draw_underline(file,xy,fill=(39,65,84),width=0):
	im = Image.open(file)
	draw = ImageDraw.Draw(im)
	draw.line(xy,fill=fill,width=width)
	im.save(file)


def performance(conn,date=datetime.datetime.today(),cloud_save=False):
	## First chart for over all performance
	title_desc = {u'扑街':frange(-11,-4,0.1),
				  u'很差':frange(-4,-2,0.1),
				  u'差':frange(-2,-0,0.1),
				  u'好':frange(0,2,0.1),
				  u'很好':frange(2,4,0.1),
				  u'劲抽':frange(4,11,0.1),}

	today_all_changepercent_over_0 =pd.read_sql('select p_change from stocks_60_days where volume>0 and p_change<11 and p_change>0 and date=\'{}\''.format(date),conn)
	hist_data_today_all_changepercent_over_0 = np.histogram(today_all_changepercent_over_0['p_change'],bins=10,range=(0,11))
	today_all_changepercent_less_0 =pd.read_sql('select p_change from stocks_60_days where volume>0 and p_change>-11 and p_change<0 and date=\'{}\''.format(date),conn)
	hist_data_today_all_changepercent_less_0 = np.histogram(today_all_changepercent_less_0['p_change'],bins=10,range=(-10.5,0))

	data_today = pd.read_sql('select p_change from stocks_60_days where volume>0 and date=\'{}\''.format(date),conn)
	hist_data_today = np.histogram(data_today['p_change'],bins=20,range=(-10.5,11))

	graph_one = []
	graph_one.append(
	go.Bar(
	x=(hist_data_today_all_changepercent_over_0[1]),
	y=hist_data_today_all_changepercent_over_0[0],
	name=u'{}只上涨'.format(sum(hist_data_today_all_changepercent_over_0[0])),
	text=hist_data_today_all_changepercent_over_0[0],
	textposition = 'outside',
	marker=dict(
	color='#E05744',
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
	color='#3CB19E',
	)
	)
	)

	labels = [str(s)+'%' for s in range(-10,11)]
	tickvals = [s for s in range(-10,11)]

	title=''
	for key,item in title_desc.items():
		if round(hist_data_today[1][np.argmax(hist_data_today[0])],1) in [round(x,1) for x in item]:
			title = u'市场表现{}'.format(key)

	layout_one = dict(font=dict(size=12),title = dict(text=title,x=0.06,y=0.93),
	        xaxis=go.layout.XAxis(title=u'幅度',ticktext=labels,tickvals=tickvals,tickangle=0,tickfont=dict(size=9)),
	        yaxis = dict(title = '数量',tick0=0, dtick=100))

	fig = go.Figure(data=graph_one, layout=layout_one)
	iplot(fig)

	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['PERFORMANCE_1']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig,file,scale=2)
	combine_title(str(settings.GRAPH['PERFORMANCE_1'])+'_title.png',file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['PERFORMANCE_1'])
		bucket.put_object_from_file(file_name,file)

def strong_week_graph(conn,date=datetime.datetime.today(),cloud_save=False):
	daterange = get_dayrange(startfrom=date,num=10)
	all_stocks =pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	stocks_60 =pd.read_sql('select * from stocks_60_days where date<=\'{} 00:00:00\' and date>=\'{} 00:00:00\''.format(daterange[0].strftime('%Y-%m-%d'),daterange[9].strftime('%Y-%m-%d')),conn)
	
	stats = {}
	for n,g in stocks_60.groupby('date'):
		stats.setdefault(n,{})
		stats[n].setdefault('over_5%',0)
		stats[n].setdefault('less_5%',0)
		stats[n]['over_5%'] = len(g[g.p_change>=5.0])
		stats[n]['less_5%'] = len(g[g.p_change<=-5.0])

	data = pd.DataFrame.from_dict(stats, orient='index')
	data.index.names = ['date']
	data = data.reset_index()

	data.sort_values('date',ascending = False,inplace=True)
	graph_two = []

	graph_two.append(
	go.Bar(
	y=data.index,
	x=data['less_5%'],
	name=u'下跌超5%',
	text=data['less_5%'],
	textposition = 'outside',
	marker=dict(
	color='#3CB19E',
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
	textposition = 'outside',
	marker=dict(
	color='#E05744',
	),
	opacity=0.8,
	orientation='h'
	)
	)

	

	labels = [d[:-9] for d in data['date']]
	tickvals = data.index
	title_sub1 = u'追涨' if (data.iloc[0]['over_5%'] > data.iloc[0]['less_5%']) else u'杀跌'
	title_sub2 = u'暴涨' if (np.sum(data['over_5%']) > np.sum(data['less_5%'])) else u'暴跌'
	title = u'今天{}的气氛更浓,纵观近期市场,{}个股总数更多.'.format(title_sub1,title_sub2)

	layout_two = dict(font=dict(size=12),title = dict(text=title,x=0.055,y=0.93),
	yaxis=go.layout.YAxis(ticktext=labels,tickvals=tickvals),
	xaxis = dict(title = '数量',tick0=0, dtick=100),
	)
	fig = go.Figure(data=graph_two, layout=layout_two)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['PERFORMANCE_2']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file, scale=2)
	combine_title(str(settings.GRAPH['PERFORMANCE_2'])+'_title.png',file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['PERFORMANCE_2'])
		bucket.put_object_from_file(file_name,file)


def hk_china_money_flow(conn,date=datetime.datetime.today(),cloud_save=False):
	daterange = get_dayrange(startfrom=date,num=10)
	mls =pd.read_sql('select trade_date,north_money,south_money from money_flow_hsgt where trade_date<=\'{}\' and trade_date>=\'{}\''.format(daterange[0].strftime('%Y%m%d'),daterange[-1].strftime('%Y%m%d')),conn)
	
	mls['trade_date'] = pd.to_datetime(mls['trade_date'])
	mls.sort_values('trade_date',ascending=True,inplace=True)
	mls = mls.reset_index()

	graph_two = []

	graph_two.append(
	go.Bar(
	y=mls.index,
	x=np.around(mls['south_money'],0),
	name=u'南下资金',
	text=np.around(mls['south_money'],0),
	textposition = 'outside',
	marker=dict(
	color='#3CB19E',
	),
	opacity=0.8,
	orientation='h'
	)
	)

	graph_two.append(
	go.Bar(
	y=mls.index,
	x=np.around(mls['north_money'],0),
	name=u'北上资金',
	text=np.around(mls['north_money'],0),
	textposition = 'outside',
	marker=dict(
	color='#E05744',
	),
	opacity=0.8,
	orientation='h'
	)
	)

	labels = [d for d in mls['trade_date']]
	tickvals = mls.index
	title_sub='没有强弱资金交换'

	if (mls.iloc[0]['north_money']>0)&((abs(mls.iloc[0]['north_money']) > abs(mls.iloc[0]['south_money']))):
		title_sub = u'北上买入资金较多' 
	elif (mls.iloc[0]['south_money']>0)&((abs(mls.iloc[0]['south_money']) > abs(mls.iloc[0]['north_money']))):
		title_sub = u'南下买入资金较多'
	elif (mls.iloc[0]['north_money']<0)&((abs(mls.iloc[0]['north_money']) > abs(mls.iloc[0]['south_money']))):
		title_sub = u'北上卖出资金较多'
	elif (mls.iloc[0]['south_money']<0)&((abs(mls.iloc[0]['south_money']) > abs(mls.iloc[0]['north_money']))):
		title_sub = u'南下卖出资金较多'

	title = u'今天{}'.format(title_sub)

	layout_two = dict(font=dict(size=12),title = dict(text=title,x=0.055,y=0.93),
	yaxis=go.layout.YAxis(ticktext=labels,tickvals=tickvals),
	xaxis = dict(title = u'资金'),
	)
	fig = go.Figure(data=graph_two, layout=layout_two)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['MONEY_FLOW']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file, scale=2)
	combine_title(str(settings.GRAPH['MONEY_FLOW'])+'_title.png',file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['MONEY_FLOW'])
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
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['PERFORMANCE_3']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['PERFORMANCE_3'])+'_title.png',file)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['PERFORMANCE_3'])
		bucket.put_object_from_file(file_name,file)

# check if it's ceiling at certain time
def ceil_first(conn,date=datetime.datetime.today(),cloud_save=False):
	daterange = get_dayrange(startfrom=date,num=2)
	all_stocks =pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	first_limit_up =pd.read_sql('select * from stocks_60_days where islimit=1 and date<=\'{} 00:00:00\' and date>=\'{} 00:00:00\''.format(daterange[0].strftime('%Y-%m-%d'),daterange[1].strftime('%Y-%m-%d')),conn).drop_duplicates(subset=['code'],keep=False)
	first_limit_up = first_limit_up[(first_limit_up.date==date.strftime('%Y-%m-%d 00:00:00')) & (first_limit_up.close!=first_limit_up.open)]
	today_ceil_first = pd.read_sql('select distinct code from ceiling_tick where date=\'{}\''.format(date.strftime('%Y-%m-%d')),conn)

	candidates = all_stocks[all_stocks.code.isin(list(set(first_limit_up['code'].tolist()).intersection(today_ceil_first['code'].tolist())))]

	#delete IPO
	ipo=[]
	for code in candidates.code.tolist():
		try:
			stock_record = pd.read_sql('select * from stocks_60_days where code=\'{}\';'.format(code),conn)
			if len(stock_record)<30:
				ipo.append(code)
		except:
			pass
	#delete t and flat
	candidates = candidates[~candidates.code.isin(ipo)]

	trace = go.Table(
	columnwidth=[20,30,30],
	header=dict(values=list([u'代码',u'名称',u'所属行业',]),
	fill = dict(color='#6C6F70'),
	font=dict(size=[30,30,30],color='#131D21'),height=45),
	cells=dict(values=[candidates.code, candidates.name,candidates.industry]
	,font=dict(size=[30,30,30],color='#131D21'),height=45,
	fill=dict(color='#FEDD66')))

	title = u"此表格个股数据来源市场,只为传达更多信息,非荐股,后果自负"

	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(candidates)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['LEAD_LIMIT']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['LEAD_LIMIT'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['LEAD_LIMIT'])
		bucket.put_object_from_file(file_name,file)


def continuous_limit_up_stocks(conn,date=datetime.datetime.today(),cloud_save=False):
	title_desc = {range(0,1):u'市场人气太差,游资不敢接力连板',
				  range(1,11):u'市场有点人气,游资少量接力连板',
				  range(11,31):u'市场人气强劲,游资积极接力连板',
				  range(31,61):u'无脑打连板的人太多,游资和机构接力连板',
				  range(61,1000):u'人气爆棚,全民接力连板,股市的盛宴'}

	all_stocks =pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left').set_index('code')
	today_limit_up_code =pd.read_sql('select code from stocks_60_days where islimit=1 and date=\'{}\''.format(date),conn)
	stock_limit_up_record = {}
	for stock_code in today_limit_up_code['code'].tolist():
		stock_record = pd.read_sql('select * from stocks_60_days where code=\'{}\' and date<=\'{}\';'.format(stock_code,date),conn)
		limit_str = ''.join([str(x) for x in stock_record.sort_values('date',ascending=False)['islimit'].values.tolist()])
		if len(limit_str)<30:
			continue
		current_limit = 0
		for limit in limit_str:
			if limit!='1':
				break
			else:
				current_limit+=1
		stock_limit_up_record[stock_code] = current_limit

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
	colors = ['#FFF4CC','#FCD770','#FDC600','#EC9833','#E87A49','#F57A3D','#E67969','#D86155','#E05744']
	limit_up_combined['color'] = limit_up_combined['freq'].map(lambda x: colors[x-2] if (x-2)<5 else colors[4])

	trace = go.Table(
	columnwidth = [12,20,12,20],
	header=dict(values=list([u'代码',u'名称',u'连板次数',u'所属行业',]),
	fill = dict(color='#6C6F70'),
	font = dict(size=[30,30,30,30],color='#131D21'),height=45),
	cells=dict(values=[limit_up_combined.code, limit_up_combined.name, limit_up_combined.freq, limit_up_combined.industry],
	fill = dict(color=[limit_up_combined.color]),
	font = dict(color='#131D21',size=[30,30,30,30]),
	height=45,))

	title = u"连板统计"

	for key,item in title_desc.items():
		if len(limit_up_combined) in key:
			title = u"{}".format(item)

	layout = dict(font=dict(size=14),margin=dict(l=20,r=20,b=30,t=100),height=len(limit_up_combined)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['CONTINUOUS_LIMIT']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['CONTINUOUS_LIMIT'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['CONTINUOUS_LIMIT'])
		bucket.put_object_from_file(file_name,file)

def strong_industries(conn,date=datetime.datetime.today(),cloud_save=False):
	days_range = 20
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	stocks_60 = stocks_60.merge(all_stocks,on='code',how='left')
	pro = ts.pro_api()
	d_range = get_dayrange(date,num=days_range)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	industry_top = {}
	for d in d_range:
	  industry_top.setdefault(d,{})
	  stocks_60_t = stocks_60[stocks_60.date.isin([d])][['code','name','islimit','industry']]
	  for n,g in stocks_60_t.groupby('industry'):
	      industry_top[d].setdefault(n,{})
	      industry_top[d][n]['number'] = len(g[g['islimit']==True])

	industry_top_df = pd.DataFrame.from_dict({(i,j): industry_top[i][j] 
	                         for i in industry_top.keys() 
	                         for j in industry_top[i].keys()},
	                     orient='index')

	industry_top_df_ = industry_top_df.reset_index()
	industry_top_df_.columns=['date','industry','number']
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
	colors = ['#FFF4CC','#FEDD66','#FDC600','#FFB776','#EA935F','#EC9A8F','#E67969','#E05744']
	top_rds['color'] = top_rds['color'].map(lambda x:colors[x])
	trace = go.Table(
	columnwidth=[12,20,8],
	header=dict(values=list([u'日期',u'所属行业',u'涨停个股',]),
	fill = dict(color='#6C6F70'),
	font=dict(size=[30,30,30],color='#131D21'),
	height=45),
	cells=dict(values=[top_rds.date, top_rds.industry, top_rds.number],
	fill = dict(color=[top_rds.color]),
	font = dict(color='#131D21',size=[30,30,30]),
	height=45))

	#Top 5 
	group_industry = {}
	for n,g in top_rds.groupby('industry'):
		group_industry[n]=len(g)

	industry_top = pd.DataFrame.from_dict(group_industry,orient='index')
	industry_top.columns = ['number']
	industry_top.sort_values('number',ascending=False,inplace=True)

	title = u'今天最强行业是{}，近一周的连续强势行业{}'.format(top_rds.iloc[0]['industry'],industry_top.index.tolist()[0] if industry_top.iloc[0]['number']>2 else u'还没出现,请耐心等待')

	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(top_rds)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_1']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['STRONG_INDUSTRIES_1'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_1'])
		bucket.put_object_from_file(file_name,file)


	graph = []
	graph.append(
	go.Pie(labels=industry_top.index.tolist(),values=industry_top.number,textfont=dict(size=20),pull=.1,hole=.1,
		text=industry_top.index.tolist(),textposition="inside",marker=dict(colors=['#E05744', '#E67969', '#EC9A8F', '#EA935F', '#FFB776', '#FDC600', '#fedd66', '#fff4cc', '#3cb29e', '#87d8ca', '#c3ebe4'])
		)
	)

	title = u'近期强势行业统计'
	layout = dict(font=dict(size=13),showlegend=False)

	fig = go.Figure(data=graph, layout=layout)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_2']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['STRONG_INDUSTRIES_2'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_2'])
		bucket.put_object_from_file(file_name,file)

def strong_concepts(conn,date=datetime.datetime.today(),cloud_save=False):
	days_range = 20
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	all_concepts = pd.read_sql('select code,c_name from all_concepts',conn)
	all_stocks = all_stocks.merge(all_concepts,on='code',how='left')
	stocks_60 = stocks_60.merge(all_stocks,on='code',how='left')
	pro = ts.pro_api()
	d_range = get_dayrange(date,num=days_range)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	industry_top = {}
	for d in d_range:
		l = []
		stocks_60_t = stocks_60[stocks_60.date.isin([d])][['code','name','islimit','c_name']]
		limit_stocks = stocks_60_t[stocks_60_t['islimit']==True]['c_name'].astype(str)
		for x in limit_stocks:
			l+=x.split(',')
		l = list(filter(('nan').__ne__, l))
		industry_top.setdefault(d,{})
		for k,v in dict(Counter(l)).items():
			industry_top[d].setdefault(k,{})
			industry_top[d][k]['number'] = v

		#industry_top[d] = sorted(industry_top[d].items(), key=lambda kv: kv[1],reverse=True)

	industry_top_df = pd.DataFrame.from_dict({(i,j): industry_top[i][j] 
	                         for i in industry_top.keys() 
	                         for j in industry_top[i].keys()},
	                     orient='index')

	industry_top_df_ = industry_top_df.reset_index()
	industry_top_df_.columns=['date','c_name','number']
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
	colors = ['#FFF4CC','#FEDD66','#FDC600','#FFB776','#EA935F','#EC9A8F','#E67969','#E05744']
	top_rds['color'] = top_rds['color'].map(lambda x:colors[x])
	trace = go.Table(
	columnwidth=[30,30,30],
	header=dict(values=list([u'日期',u'所属概念',u'涨停个股',]),
	fill = dict(color='#6C6F70'),
	font=dict(size=[30,30,30],color='#131D21'),
	height=45),
	cells=dict(values=[top_rds.date, top_rds.c_name, top_rds.number],
	fill = dict(color=[top_rds.color]),
	font = dict(color='#131D21',size=[30,30,30]),
	height=45))

	#Top 5 
	group_industry = {}
	for n,g in top_rds.groupby('c_name'):
		group_industry[n]=len(g)

	industry_top = pd.DataFrame.from_dict(group_industry,orient='index')
	industry_top.columns = ['number']
	industry_top.sort_values('number',ascending=False,inplace=True)

	title = u'今天最强概念是{}，近一周的连续强势概念{}'.format(top_rds.iloc[0]['c_name'],industry_top.index.tolist()[0] if industry_top.iloc[0]['number']>2 else u'还没出现,请耐心等待')

	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(top_rds)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_3']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['STRONG_INDUSTRIES_3'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_3'])
		bucket.put_object_from_file(file_name,file)


	graph = []
	graph.append(
	go.Pie(labels=industry_top.index.tolist(),values=industry_top.number,textfont=dict(size=20),pull=.1,hole=.1,
		text=industry_top.index.tolist(),textposition="inside",marker=dict(colors=['#E05744', '#E67969', '#EC9A8F', '#EA935F', '#FFB776', '#FDC600', '#fedd66', '#fff4cc', '#3cb29e', '#87d8ca', '#c3ebe4'])
		)
	)

	title = u'近期强势概念统计'
	layout = dict(font=dict(size=13),showlegend=False)

	fig = go.Figure(data=graph, layout=layout)
	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_4']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['STRONG_INDUSTRIES_4'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_INDUSTRIES_4'])
		bucket.put_object_from_file(file_name,file)

	#return top_rds.to_json(orient='index')

def strong_industries_concepts_combine(conn,date=datetime.datetime.today(),cloud_save=False):
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	all_concepts = pd.read_sql('select code,c_name from all_concepts',conn)
	all_stocks = all_stocks.merge(all_concepts,on='code',how='left')
	stocks_60 = stocks_60.merge(all_stocks,on='code',how='left')
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60 = stocks_60[stocks_60.date.isin([date]) & stocks_60.islimit==True]

	l = []
	for x in stocks_60['c_name'].astype(str):
		l+=x.split(',')
	l = list(filter(('nan').__ne__, l))
	concept_top = {}
	for k,v in dict(Counter(l)).items():
		concept_top[k] = v

	industry_top = {}
	for n,g in stocks_60.groupby('industry'):
		industry_top[n] = len(g)

	concept_top_5 = (list(sorted(concept_top.items(), key=lambda kv: kv[1],reverse=True))[:5])
	industry_top_5 = (list(sorted(industry_top.items(), key=lambda kv: kv[1],reverse=True))[:5])

	concept_top_5 = [x[0] for x in concept_top_5]
	industry_top_5 =[x[0] for x in industry_top_5]

	stocks_60['has_top_concepts'] = stocks_60['c_name'].map(lambda x: len(set(concept_top_5).intersection(set(x.split(',')))) > 0 if type(x)==str else False)
	stocks_60['intersect_concepts'] = stocks_60['c_name'].map(lambda x: list(set(concept_top_5).intersection(set(x.split(',')))) if type(x)==str else [])
	stocks_60['intersect_concepts_str'] = stocks_60['intersect_concepts'].map(lambda x: x[0] if len(x)>0 else '')
	strong_stocks = stocks_60[stocks_60.industry.isin(industry_top_5) & stocks_60.has_top_concepts==True]
	strong_stocks = strong_stocks[~(strong_stocks.high==strong_stocks.low)]

	trace = go.Table(
	columnwidth=[20,30,30],
	header=dict(values=list([u'代码',u'名称',u'所属行业',u'所属概念']),
	fill = dict(color='#6C6F70'),
	font=dict(size=[30,30,30,30],color='#131D21'),height=45),
	cells=dict(values=[strong_stocks.code, strong_stocks.name,strong_stocks.industry,strong_stocks.intersect_concepts_str]
	,font=dict(size=[30,30,30,30],color='#131D21'),height=45,
	fill=dict(color='#fedd66')))

	title = u"此表格个股数据来源市场,只为传达更多信息,非荐股,后果自负"
	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(strong_stocks)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_COMBINE']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['STRONG_COMBINE'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_COMBINE'])
		bucket.put_object_from_file(file_name,file)

def strong_industries_concepts_combine_candidates(conn,date=datetime.datetime.today(),cloud_save=False):
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	all_concepts = pd.read_sql('select code,c_name from all_concepts',conn)
	all_stocks = all_stocks.merge(all_concepts,on='code',how='left')
	stocks_60 = stocks_60.merge(all_stocks,on='code',how='left')
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60 = stocks_60[stocks_60.date.isin([date]) & stocks_60.islimit==True]
	stocks_candidate = stocks_60[stocks_60.date.isin([date])]

	l = []
	for x in stocks_60['c_name'].astype(str):
		l+=x.split(',')
	l = list(filter(('nan').__ne__, l))
	concept_top = {}
	for k,v in dict(Counter(l)).items():
		concept_top[k] = v

	industry_top = {}
	for n,g in stocks_60.groupby('industry'):
		industry_top[n] = len(g)

	concept_top_5 = (list(sorted(concept_top.items(), key=lambda kv: kv[1],reverse=True))[:5])
	industry_top_5 = (list(sorted(industry_top.items(), key=lambda kv: kv[1],reverse=True))[:5])

	concept_top_5 = [x[0] for x in concept_top_5]
	industry_top_5 =[x[0] for x in industry_top_5]

	stocks_candidate['has_top_concepts'] = stocks_candidate['c_name'].map(lambda x: len(set(concept_top_5).intersection(set(x.split(',')))) > 0 if type(x)==str else False)
	stocks_candidate['intersect_concepts'] = stocks_candidate['c_name'].map(lambda x: list(set(concept_top_5).intersection(set(x.split(',')))) if type(x)==str else [])
	
	strong_stocks = stocks_candidate[stocks_candidate.industry.isin(industry_top_5) | stocks_candidate.has_top_concepts==True]
	strong_stocks['p_change']  = strong_stocks['p_change'].map(lambda x: '{}%'.format(round(x,2)))
	trace = go.Table(
	columnwidth=[20,30,30],
	header=dict(values=list([u'代码',u'名称',u'所属行业',u'所属概念',u'涨幅']),
	fill = dict(color='#6C6F70'),
	font=dict(size=[30,30,30,30,30],color='#131D21'),height=45),
	cells=dict(values=[strong_stocks.code, strong_stocks.name,strong_stocks.industry,strong_stocks.intersect_concepts,strong_stocks.p_change]
	,font=dict(size=[20,20,20,18,20],color='#131D21'),height=45,
	fill=dict(color='#83C6C4')))

	title = u"强势行业{}<br>强势概念{}".format(','.join(industry_top_5),','.join(concept_top_5))
	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(strong_stocks)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_COMBINE_CANDIDATE']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['STRONG_COMBINE_CANDIDATE'])+'_title.png',file)
	combine_subline(title,file)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['STRONG_COMBINE_CANDIDATE'])
		bucket.put_object_from_file(file_name,file)


def break_ma(conn,date=datetime.datetime.today(),cloud_save=False):
	pro = ts.pro_api()
	stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
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

	if len(today_break_through)>0:
		bt_df = pd.DataFrame(today_break_through)
		bt_df.columns = ['code']
		bt_df = bt_df.merge(all_stocks,on='code',how='left')
		bt_df = bt_df.merge(stocks_60_2_days[stocks_60_2_days.date==two_days[1]],on=['code'],how='left').sort_values('p_change',ascending=False)
		bt_df['date'] = two_days[1]
		bt_df['p_change_str'] = bt_df['p_change'].map(lambda x: '{}%'.format(round(x,2)))

		trace = go.Table(
		columnwidth=[12,30,30,10],
		header=dict(values=list([u'代码',u'中文',u'所属行业',u'涨幅']),
		fill = dict(color='#6C6F70'),
		font=dict(size=[30,30,30,30],color='#131D21'),
		height=45),
		cells=dict(values=[bt_df.code, bt_df.name, bt_df.industry,bt_df.p_change_str],
		font=dict(size=[30,30,30,30],color='#131D21'),
		height=45)
		)

		title = u'突破图'
		layout = dict(font=dict(size=20),margin=dict(l=20,r=20,b=30,t=100),height=len(bt_df)*45+220)

		data = [trace]

		fig = go.Figure(data=data,layout=layout)

		iplot(fig)
		directory = os.path.join(home,"Documents","cnstocks")
		file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['BREAK_THROUGH']))
		if not os.path.exists(directory):
			os.makedirs(directory)
		pio.write_image(fig, file,scale=2)
		combine_title(str(settings.GRAPH['BREAK_THROUGH'])+'_title.png',file)
		combine_subline(title,file)
		if cloud_save:
			file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['BREAK_THROUGH'])
			bucket.put_object_from_file(file_name,file)
	else:
		return

def continuous_rise_stocks(conn,date=datetime.datetime.today(),cloud_save=False):
	continuous_rise = {}
	daterange = get_dayrange(startfrom=date,num=31)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	stocks_60 = pd.read_sql('select * from stocks_60_days where volume>0',conn)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60 = stocks_60[stocks_60.date.isin(daterange)]
	stocks_60 = stocks_60.sort_values('date',ascending=False)
	for n,g in stocks_60.groupby('code'):
		if len(g)<30:
			continue
		try:
			accumulate_change = (g.iloc[0]['close']-g.iloc[11]['close'])/g.iloc[11]['close']
		except:
			continue

		if (accumulate_change>=0.2) and (accumulate_change<=0.4) and (g.iloc[0:10]['p_change']>0).sum()>=8:
			continuous_rise[n] = round(accumulate_change*100,2) 


	continuous_rise_candidate_df = pd.DataFrame.from_dict(continuous_rise,orient='index')
	continuous_rise_candidate_df.columns = ['accumulate']
	continuous_rise_candidate_df = continuous_rise_candidate_df.sort_values('accumulate',ascending=False).reset_index()
	continuous_rise_candidate_df.columns = ['code','accumulate']
	continuous_rise_candidate_df = continuous_rise_candidate_df.merge(stocks_60[stocks_60.date==daterange[0]],on='code',how='left')
	continuous_rise_candidate_df['accumulate'] = continuous_rise_candidate_df['accumulate'].map(lambda x: '{}%'.format(x))
	continuous_rise_candidate_df['p_change_str'] = continuous_rise_candidate_df['p_change'].map(lambda x: '{}%'.format(round(x,2)))
	continuous_rise_candidate_df = continuous_rise_candidate_df.merge(all_stocks,on='code',how='left')
	continuous_rise_candidate_df = continuous_rise_candidate_df.head(10)
	#continuous_rise_candidate_df['color'] = continuous_rise_candidate_df['p_change'].map(lambda x: '#ff5a57' if x>0 else '#54ff68')

	trace = go.Table(
	columnwidth=[20,30,30,20],
	header=dict(values=list([u'代码',u'名称',u'所属行业',u'今日涨幅']),
	fill = dict(color='#6C6F70'),
	font=dict(size=(30,30,30,30),color='#131D21'),height=45),
	cells=dict(values=[continuous_rise_candidate_df.code, continuous_rise_candidate_df.name, continuous_rise_candidate_df.industry,continuous_rise_candidate_df.p_change_str],
	font=dict(size=[30,30,30,30],color='#131D21'),height=45,fill = dict(color='#FEDD66'),),
	)

	title = u"此表格个股数据来源市场,只为传达更多信息,非荐股,后果自负"
	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(continuous_rise_candidate_df)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['CONTINUOUSE_RISE']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig,file,scale=2)
	combine_title(str(settings.GRAPH['CONTINUOUSE_RISE'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['CONTINUOUSE_RISE'])
		bucket.put_object_from_file(file_name,file)

def top_rise_down(conn,date=datetime.datetime.today(),cloud_save=False):
	pro = ts.pro_api()
	stocks_60 = pd.read_sql('select * from stocks_60_days where volume>0',conn)
	all_stocks = pd.read_sql('select code,name from all_stocks',conn)
	local_industry = pd.read_sql('select code,industry from local_industry',conn)
	all_stocks = all_stocks.merge(local_industry,on='code',how='left')
	d_range = get_dayrange(startfrom=date,num=59)
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

	today_top_bottom['color'] = today_top_bottom['p_change'].map(lambda x: '#E67969' if x>0 else '#87D8CA')

	trace = go.Table(
	columnwidth=[20,30,30,20],
	header=dict(values=list([u'代码',u'名称',u'所属行业',u'幅度']),
	font=dict(size=[30,30,30,30],color='#131D21'),
	height=45,
	fill = dict(color='#6C6F70')
	),
	cells=dict(values=[today_top_bottom.code, today_top_bottom.name, today_top_bottom.industry,today_top_bottom.p_change_str],
	font = dict(size=[30,30,30,30],color='#131D21'),height=45,
	fill=dict(color=[today_top_bottom.color])
	)
	)
	title = u"此表格个股数据来源市场,只为传达更多信息,非荐股,后果自负"
	layout = dict(font=dict(size=13),margin=dict(l=20,r=20,b=30,t=100),height=len(today_top_bottom)*45+220)

	data = [trace]

	fig = go.Figure(data=data,layout=layout)

	iplot(fig)
	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['RANKING_1']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	pio.write_image(fig, file,scale=2)
	combine_title(str(settings.GRAPH['RANKING_1'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['RANKING_1'])
		bucket.put_object_from_file(file_name,file)

def signal_trend(conn,date=datetime.datetime.today(),cloud_save=False):
	title_desc = {0:[u'很弱',u'减至最低,只保留20%以下仓位'],
				  1:[u'弱',u'减少,保留40%以下仓位'],
				  2:[u'强',u'提高,保留60%左右仓位'],
				  3:[u'很强',u'大幅提高,加至80%左右仓位甚至满仓'],
				  4:[u'超级强',u'提高到满仓,轻仓是在犯罪']}

	daterange = get_dayrange(startfrom=date,num=1)
	stocks_60 = pd.read_sql('select * from stocks_60_days where volume>0',conn)
	stocks_60['date'] = pd.to_datetime(stocks_60['date'])
	stocks_60 = stocks_60[stocks_60.date.isin(daterange)]

	yesterday_top_break = stocks_60[(stocks_60.date == daterange[1]) & (stocks_60.islimit==1)].sort_values('code')
	today_good_pratice = stocks_60[(stocks_60.date == daterange[0]) & (stocks_60.code.isin(yesterday_top_break['code'].tolist()))].sort_values('code')
	yesterday_top_break = yesterday_top_break[['code','close']]
	today_good_pratice = today_good_pratice[['code','high']]
	combine_df = today_good_pratice.merge(yesterday_top_break,on='code',how='left')
	if len(yesterday_top_break)>0:
		signal = round(np.sum(np.where(((combine_df['high']-combine_df['close'])/combine_df['close'])>=0.08,1,0))/len(yesterday_top_break),2)
	else:
		signal = 0

	data_today = pd.read_sql('select p_change from stocks_60_days where volume>0 and date=\'{}\''.format(date),conn)
	hist_data_today = np.histogram(data_today['p_change'],bins=20,range=(-10.5,11))

	market_offset = 0
	if round(hist_data_today[1][np.argmax(hist_data_today[0])],1)<-4:
		market_offset = -2
	elif round(hist_data_today[1][np.argmax(hist_data_today[0])],1)<-2:
		market_offset = -1

	offset = (1 if len(yesterday_top_break)>=100 else (-1 if len(yesterday_top_break)<30 else 0))+market_offset
	score = (0+offset if signal<0.20 else (1+offset if signal>=0.2 and signal<0.4 else (2+offset if signal>=0.4 and signal<0.6 else (3+offset if signal>=0.6 and signal<0.8 else 4+offset))))
	score =  0 if score<0 else (4 if score>4 else score)
	ttfont = ImageFont.truetype("imgs/SIMHEI.TTF",36)
	im = Image.open('imgs/s-0{}.jpg'.format(score))
	draw = ImageDraw.Draw(im)
	title = u'今天赚钱效应{},仓位应{}'.format(title_desc[score][0],title_desc[score][1])

	directory = os.path.join(home,"Documents","cnstocks")
	file = os.path.join(home,"Documents","cnstocks","{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['GAUGE_1']))
	if not os.path.exists(directory):
		os.makedirs(directory)
	im.save(file)
	combine_title(str(settings.GRAPH['GAUGE_1'])+'_title.png',file)
	combine_subline(title,file)
	draw_underline(file,xy=[(0,110),(1400,110)],width=5)
	if cloud_save:
		file_name = "{}_{}.jpg".format(date.strftime('%Y%m%d'),settings.GRAPH['GAUGE_1'])
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
		strong_concepts(conn,date,True)
		strong_week_graph(conn,date,True)
		#break_ma(conn,date)
		continuous_rise_stocks(conn,date,True)
		top_rise_down(conn,date,True)
		ceil_first(conn,date,True)
		signal_trend(conn,date,True)
		strong_industries_concepts_combine(conn,date,True)
		strong_industries_concepts_combine_candidates(conn,date,True)
		hk_china_money_flow(conn,date,True)
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
