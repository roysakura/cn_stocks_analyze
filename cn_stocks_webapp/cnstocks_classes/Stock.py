'''
This Class is created for Stock. Data Attribute is accroding to Tushare open library

'''

class Stock():

	def __init__(self,code,name,industry,area,pe,outstranding,
				totals,totalAssets,fixedAssets,reserved,reservedPerShare,
				esp,bvps,pb,timeToMarket,undp,perundp,rev,profit,
				gpr,npr,holders,records=None):
		'''
		This is docstring

		'''
		self.code = code
		self.name = name
		self.indutry = industry
		self.area = area
		self.pe = pe
		self.outstranding = outstranding
		self.totals = totals
		self.totalAssets = totalAssets
		self.fixedAssets = fixedAssets
		self.reserved = reserved
		self.reservedPerShare = reservedPerShare
		self.esp = esp
		self.bvps = bvps
		self.pb	= pb
		self.timeToMarket = timeToMarket
		self.undp = undp
		self.perundp = perundp
		self.rev = rev
		self.profit = profit
		self.gpr = gpr	
		self.npr = npr
		self.holders = holders
		self.records = records

	def is_limit_up(self,date):
		if (self.records[date].close - self.records[date].open)/self.records[date].open > 0.099:
			return True
		else:
			return False


	def is_limit_down(self,date):
		if (self.records[date].open - self.records[date].close)/self.records[date].open > 0.099:
			return True
		else:
			return False	



