


DATABASE = {
    'drivername': 'mysql',
    'host': 'localhost',
    'port': '3306',
    'username': '',
    'password': '',
    'database': 'cnstock',
    'query': {'charset': 'utf8'},
}

OSS2_USER = ''
OSS2_PASS = ''


GRAPH = {
	'PERFORMANCE_1':0,
	'PERFORMANCE_2':1,
	'LEAD_LIMIT':2,
	'CONTINUOUS_LIMIT':3,
	'STRONG_INDUSTRIES_1':4,
	'STRONG_INDUSTRIES_2':5,
	'BREAK_THROUGH':6,
	'CONTINUOUSE_RISE':7,
	'RANKING_1':8,
	'PERFORMANCE_3':9,
	'GAUGE_1':10,
	'STRONG_INDUSTRIES_3':11,
	'STRONG_INDUSTRIES_4':12,
	'STRONG_COMBINE':13,
	'STRONG_COMBINE_CANDIDATE':14,
	'MONEY_FLOW':15,

}

IMGTEMPLATE = {
	'HEAD':'imgs/head.png',
	'BANNER_MARKET':'imgs/banner_market.png',
	'BANNER_INDUST':'imgs/banner_industry.png',
	'BANNER_INDI':'imgs/banner_individual.png',
	'FOOTER':'imgs/footer.png',
}

SEND_USERS = {
	'ROY':{'email':'110672023@qq.com',
			'qrcode':'imgs/qrcode/duoduo.png',
			'attachments' : [
                        	IMGTEMPLATE['BANNER_MARKET'],
                        	GRAPH['PERFORMANCE_1'],
                        	GRAPH['PERFORMANCE_2'],
                        	GRAPH['MONEY_FLOW'],
                        	IMGTEMPLATE['BANNER_INDUST'],
                        	GRAPH['STRONG_INDUSTRIES_1'],
                        	GRAPH['STRONG_INDUSTRIES_2'],
                        	GRAPH['STRONG_INDUSTRIES_3'],
                        	GRAPH['STRONG_INDUSTRIES_4'],
                        	IMGTEMPLATE['BANNER_INDI'],
                        	GRAPH['LEAD_LIMIT'],
                        	GRAPH['RANKING_1'],
                        	GRAPH['CONTINUOUSE_RISE'],
                        	GRAPH['CONTINUOUS_LIMIT'],
                        	GRAPH['GAUGE_1']
                        	]
             },

	'LIMINGCONG':{'email':'150096055@qq.com',
					'qrcode':'imgs/qrcode/limingcong.png',
					'attachments' : [
                        	IMGTEMPLATE['BANNER_MARKET'],
                        	GRAPH['PERFORMANCE_1'],
                        	GRAPH['PERFORMANCE_2'],
                        	IMGTEMPLATE['BANNER_INDUST'],
                        	GRAPH['STRONG_INDUSTRIES_1'],
                        	GRAPH['STRONG_INDUSTRIES_2'],
                        	GRAPH['STRONG_INDUSTRIES_3'],
                        	GRAPH['STRONG_INDUSTRIES_4'],
                        	IMGTEMPLATE['BANNER_INDI'],
                        	GRAPH['LEAD_LIMIT'],
                        	GRAPH['RANKING_1'],
                        	GRAPH['CONTINUOUSE_RISE'],
                        	GRAPH['CONTINUOUS_LIMIT'],
                        	GRAPH['GAUGE_1']
                        	]
                    }
}