from plotly.offline import init_notebook_mode,iplot
import plotly.graph_objs as go
import plotly.io as pio

import os
import numpy as np
import pandas as pd
import sqlite3

init_notebook_mode(connected=True)

#########
conn = sqlite3.connect('cn_stocks.db')

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

labels = [str(s)+'%' for s in range(-10,11)]
tickvals = [s for s in range(-10,11)]
layout_one = dict(title = u'市场表现',
            xaxis=go.layout.XAxis(title=u'幅度',ticktext=labels,tickvals=tickvals),
            yaxis = dict(title = '数量',tick0=0, dtick=100)
            )

fig = go.Figure(data=graph_one, layout=layout_one)
iplot(fig)
pio.write_image(fig, '/Users/roy/Desktop/fig1.png', width=600, height=350, scale=2)

########
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
textposition = 'auto',
textfont=dict(
family='Arial',
size=3,
color='#000000',
),
marker=dict(
color='#d10031',
),
opacity=0.5
)
)

graph_two.append(
go.Bar(
x=data.index,
y=data['less_5%'],
name=u'下跌超5%',
text=data['less_5%'],
textposition = 'auto',
textfont=dict(
family='Arial',
size=3,
color='#000000',
),
marker=dict(
color='#02c927',
),
opacity=0.5
)
)

labels = [d[:-9] for d in data.index]
tickvals = data.index

layout_two = dict(title = u'市场表现二',
        xaxis=go.layout.XAxis(ticktext=labels,tickvals=tickvals,tickangle=-90),
        yaxis = dict(title = '数量',tick0=0, dtick=100),
        )
fig = go.Figure(data=graph_two, layout=layout_two)
iplot(fig)
pio.write_image(fig, '/Users/roy/Desktop/fig2.png', width=600, height=350, scale=3)
########
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
        yaxis = dict(title = '数量',tick0=0, dtick=100),
        )
fig = go.Figure(data=graph_three, layout=layout_three)
iplot(fig)
pio.write_image(fig, '/Users/roy/Desktop/fig3.png', width=600, height=350, scale=3)
########