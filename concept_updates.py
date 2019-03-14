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


def update_folder_concepts():
	conn = sqlite3.connect('cn_stocks.db')
	concepts_dict = {}
	for root, directories, filenames in os.walk('data/concepts/'):
		for filename in filenames:
			c = pd.read_csv(u'data/concepts/{}'.format(filename),sep='\t', encoding='gb2312')
			concepts_dict[filename[:-12]]=','.join( [str(x) for x in c.iloc[:-1][u'代码'].values.tolist()])

	concepts_df = pd.DataFrame.from_dict(concepts_dict,orient='index')
	concepts_df.columns = ['code']

	concepts_dict = {}
	for n in concepts_df.index:
		for code in concepts_df.loc[n]['code'].split(','):
			concepts_dict.setdefault(code,'')
			concepts_dict[code] += n+','

	concepts_df = pd.DataFrame.from_dict(concepts_dict,orient='index')
	concepts_df = concepts_df.reset_index()
	concepts_df.columns = ['code','c_name']
	concepts_df['c_name'] = concepts_df['c_name'].map(lambda x:x[:-1])
	concepts_df.sort_values('code',inplace=True)
	concepts_df.to_sql('all_concepts',conn,if_exists='replace',index=False)

def main():
    print('Updating concepts...\n')
    update_folder_concepts()
    
if __name__ == '__main__':
    main()