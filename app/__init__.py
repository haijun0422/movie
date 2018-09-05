# -*- coding: utf-8 -*-
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os

app = Flask(__name__)
"""SQLALCHEMY配置"""
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1:3306/movie'  # 连接数据库
app.config['SQLALCHEMY_TRACKK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
app.config['UP_DIR']=os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/upload/')  # 上传文件配置
app.config['SECRET_KEY'] = '763121a72e0745bc88ffc844a4d6808b'
app.debug = False
db = SQLAlchemy(app)


from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint,url_prefix='/admin')


@app.errorhandler(404)
def page_not_found(erro):
    return render_template('home/404.html'), 404
