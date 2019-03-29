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

def update_folder_industry():
	conn = sqlite3.connect('cn_stocks.db')
	industry_dict = {}
	for root, directories, filenames in os.walk('data/industry/'):
		for filename in filenames:
			c = pd.read_csv(u'data/industry/{}'.format(filename),sep='\t', encoding='gb2312')
			industry_dict[filename[:-12]]=','.join( [str(x) for x in c.iloc[:-1][u'代码'].values.tolist()])

	industry_df = pd.DataFrame.from_dict(industry_dict,orient='index')
	industry_df.columns = ['code']

	industry_dict = {}
	for n in industry_df.index:
		for code in industry_df.loc[n]['code'].split(','):
			industry_dict.setdefault(code,'')
			industry_dict[code] += n+','

	industry_df = pd.DataFrame.from_dict(industry_dict,orient='index')
	industry_df = industry_df.reset_index()
	industry_df.columns = ['code','industry']
	industry_df['industry'] = industry_df['industry'].map(lambda x:x[:-1])
	industry_df.sort_values('code',inplace=True)
	industry_df.to_sql('local_industry',conn,if_exists='replace',index=False)

def main():
    print('Updating industry...\n')
    update_folder_industry()
    
if __name__ == '__main__':
    main()