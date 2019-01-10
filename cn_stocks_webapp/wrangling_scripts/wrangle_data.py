# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from cnstocks_classes.Stock import Stock
from customdecorator.timer import timer
import sqlite3
import tushare as ts
import datetime
from datetime import timedelta


@timer
def continuous_limit_up_stocks():

  conn = sqlite3.connect('../cn_stocks.db')
  all_stocks =pd.read_sql('select code,name,industry from all_stocks',conn).set_index('code')
  today_limit_up_code =pd.read_sql('select code from today_all where changepercent>9.9',conn)
  all_stocks_records = {}
  for stock_code in today_limit_up_code['code'].tolist():
    try:
      stock_record = pd.read_sql('select * from \'{}\';'.format(stock_code),conn)
      stock_record = stock_record.drop_duplicates()
      all_stocks_records[stock_code] = stock_record
    except:
      continue

  stock_limit_up_record = {}
  for stock_code,stock_record in all_stocks_records.items():
    stock_limit_up_record.setdefault(stock_code,1)
    stock_record = stock_record.sort_values(by='date',ascending=False)
    
    for idx in range(1,len(stock_record)):
      try:
        pchange = (stock_record.iloc[idx]['close']-stock_record.iloc[idx+1]['close'])/stock_record.iloc[idx+1]['close']
        if pchange>0.099:
          stock_limit_up_record[stock_code]+=1
        else:
          break
      except:
        break

  limit_up_stocks = pd.DataFrame.from_dict(stock_limit_up_record,orient='index')
  limit_up_stocks.columns = ['freq']
  limit_up_combined = limit_up_stocks.merge(all_stocks,left_index=True,right_index=True).sort_values(by='freq',ascending=False)

  return limit_up_combined[limit_up_combined.freq>1].reset_index().to_json(orient='index')

@timer
def return_figures():
    """Creates four plotly visualizations

    Args:
        None

    Returns:
        list (dict): list containing the four plotly visualizations

    """

  # Load Data

    conn = sqlite3.connect('../cn_stocks.db')

    today_all_changepercent_over_0 =pd.read_sql('select changepercent from today_all where volume>0 and changepercent<11 and changepercent>0',conn)

    hist_data_today_all_changepercent_over_0 = np.histogram(today_all_changepercent_over_0['changepercent'],bins=10,range=(0,11))

    today_all_changepercent_less_0 =pd.read_sql('select changepercent from today_all where volume>0 and changepercent>-11 and changepercent<0',conn)

    hist_data_today_all_changepercent_less_0 = np.histogram(today_all_changepercent_less_0['changepercent'],bins=10,range=(-10.5,0))

  # first chart plots arable land from 1990 to 2015 in top 10 economies 
  # as a line chart
    print(sum(hist_data_today_all_changepercent_over_0[0]))
    print(sum(hist_data_today_all_changepercent_less_0[0]))

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

    #labels = [str(s)+'%' for s in (np.floor(hist_data_today_all_changepercent_less_0[1])+np.ceil(hist_data_today_all_changepercent_over_0[1]))]
    #print(labels)
    #tickvals = [s for s in (np.floor(hist_data_today_all_changepercent_less_0[1])+np.ceil(hist_data_today_all_changepercent_over_0[1]))]
    #print(tickvals)
    labels = [str(s)+'%' for s in range(-10,11)]
    tickvals = [s for s in range(-10,11)]
    layout_one = dict(title = u'市场表现',
                xaxis=go.layout.XAxis(title=u'幅度',ticktext=labels,tickvals=tickvals),
                yaxis = dict(title = '数量',autotick=False,tick0=0, dtick=100),
                height='500'
                )


    #graph_two

    stocks_60 =pd.read_sql('select * from stocks_60_days',conn)

    stats = {}
    for n,g in stocks_60.groupby('date'):
      stats.setdefault(n,{})
      stats[n].setdefault('over_5%',0)
      stats[n].setdefault('less_5%',0)
      stats[n]['over_5%'] = len(g[g.p_change>=5.0])
      stats[n]['less_5%'] = len(g[g.p_change<=-5.0])

    data = pd.DataFrame.from_dict(stats, orient='index')

    data = data[-20:]
    graph_two = []
    graph_two.append(
    go.Bar(
    x=data.index,
    y=data['over_5%'],
    name=u'上升超5%',
    text=data['over_5%'],
    textposition = 'outside',
    marker=dict(
    color='#d10031',
    )
    )
    )

    graph_two.append(
    go.Bar(
    x=data.index,
    y=data['less_5%'],
    name=u'下跌超5%',
    text=data['less_5%'],
    textposition = 'outside',
    marker=dict(
    color='#02c927',
    )
    )
    )
    
    labels = [d[:-9] for d in data.index]
    tickvals = data.index

    layout_two = dict(title = u'市场表现二',
            xaxis=go.layout.XAxis(ticktext=labels,tickvals=tickvals,tickangle=-90),
            yaxis = dict(title = '数量',autotick=False,tick0=0, dtick=100),
            )
    
    #graph three
    stocks_60 = pd.read_sql('select * from stocks_60_days ORDER BY date',conn)
    top_break_through = {}
    down_break_through = {}
    code_list = stocks_60['code'].unique().tolist()
    for code in code_list:
      cur_stock = stocks_60[stocks_60.code==code].sort_values('date')
      top_break_dates = cur_stock[cur_stock.close>=cur_stock.max120]['date'].values.tolist()
      for date in top_break_dates:
        top_break_through.setdefault(date,[])
        top_break_through[date].append(code)

      down_break_dates = cur_stock[cur_stock.close<=cur_stock.min120]['date'].values.tolist()
      for date in down_break_dates:
        down_break_through.setdefault(date,[])
        down_break_through[date].append(code)

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

    data = data[-20:]
    graph_three = []
    graph_three.append(
    go.Bar(
    x=data.index,
    y=data['top_break'],
    name=u'创半年新高',
    text=data['top_break'],
    textposition = 'outside',
    marker=dict(
    color='#d10031',
    )
    )
    )

    graph_three.append(
    go.Bar(
    x=data.index,
    y=data['down_break'],
    name=u'创半年新低',
    text=data['down_break'],
    textposition = 'outside',
    marker=dict(
    color='#02c927',
    )
    )
    )

    labels = [d.strftime('%m/%d') for d in data.index]
    tickvals = data.index

    layout_three = dict(title = u'市场表现三',
            xaxis=go.layout.XAxis(ticktext=labels,tickvals=tickvals,tickangle=-90),
            yaxis = dict(title = '数量',autotick=False,tick0=0, dtick=100),
            )

    # append all charts to the figures list
    figures = []
    figures.append(dict(data=graph_one, layout=layout_one))
    figures.append(dict(data=graph_two, layout=layout_two))
    figures.append(dict(data=graph_three, layout=layout_three))

    return figures

@timer
def strong_industries():
  conn = sqlite3.connect('../cn_stocks.db')
  stocks_60 = pd.read_sql('select * from stocks_60_days',conn)
  all_stocks = pd.read_sql('select code,name,industry from all_stocks',conn)
  stocks_60 = stocks_60.merge(all_stocks,on='code',how='left')
  today = datetime.datetime.today()
  ts.set_token('3c9fcd3daa9244ca0c45a7e47d5ba14004c9aff7208506910b991f30')
  pro = ts.pro_api()
  one_year_before = (datetime.datetime.today()-timedelta(days=60)).strftime("%Y%m%d")
  cal = pro.trade_cal(start_date=one_year_before, end_date=today.strftime("%Y%m%d")).sort_values('cal_date',ascending=False)
  d_range = [datetime.datetime.strptime(d,'%Y%m%d') for d in cal[cal.is_open==1][:20].sort_values('cal_date')['cal_date']]
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
  return top_rds.to_json(orient='index')