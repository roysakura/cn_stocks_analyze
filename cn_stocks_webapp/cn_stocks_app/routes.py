from cn_stocks_app import app
import json, plotly
from flask import render_template
from wrangling_scripts.wrangle_data import continuous_limit_up_stocks,return_figures,strong_industries

@app.route('/')
@app.route('/index')
def index():

    #figures = return_figures()

    # plot ids for the html id tag
    #ids = ['figure-{}'.format(i) for i, _ in enumerate(figures)]

    # Convert the plotly figures to JSON for javascript in html template
    #figuresJSON = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    figures = return_figures()

    # plot ids for the html id tag
    ids = ['figure-{}'.format(i) for i, _ in enumerate(figures)]

    # Convert the plotly figures to JSON for javascript in html template
    figuresJSON = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html',ids=ids,figuresJSON=figuresJSON,top_limit_data=continuous_limit_up_stocks())

@app.route('/si')
def si_table():
    return render_template('si.html',rds = strong_industries())