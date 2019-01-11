# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import tushare as ts
import pandas as pd
import datetime
from datetime import timedelta
from progressbar import ProgressBar,SimpleProgress,Bar,ETA,ReverseBar
import settings
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL


# connect to the database
conn = create_engine(URL(**settings.DATABASE))
df = pd.read_sql("SELECT * from \'002684\';",conn)
print((df))
