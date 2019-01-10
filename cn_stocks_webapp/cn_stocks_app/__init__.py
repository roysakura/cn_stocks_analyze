from flask import Flask

app = Flask(__name__)

from cn_stocks_app import routes
