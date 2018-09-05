# -*- coding: utf-8 -*-
# from flask import Flask, render_template
# from flask_sqlalchemy import SQLAlchemy
# import pymysql

# app = Flask(__name__)
# """SQLALCHEMY配置"""
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1:3306/movie'  # 连接数据库
# app.config['SQLALCHEMY_TRACKK_MODIFICATIONS'] = True
# app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
# app.config['SECRET_KEY'] = '763121a72e0745bc88ffc844a4d6808b'
# app.debug = False
# db = SQLAlchemy(app)



from datetime import datetime
from app import db


class User(db.Model):
    """会员"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(20), unique=True)  # 昵称
    pwd = db.Column(db.String(100))  # 密码
    email = db.Column(db.String(30), unique=True)  # 邮箱
    phone = db.Column(db.String(11), unique=True)  # 手机
    info = db.Column(db.String(100))  # 简介
    face = db.Column(db.String(100))  # 头像
    addTime = db.Column(db.DateTime, index=True, default=datetime.now)  # 日期
    uuid = db.Column(db.String(255), unique=True)  # 唯一标识符
    user_logs = db.relationship('UserLog', backref='user')  # 会员日志外键关系关联
    comment_user = db.relationship('Comment', backref='user')  # 评论外键关系关联
    col_user = db.relationship('MovieCol', backref='user')  # 收藏外键关系关联

    def __repr__(self):
        return '<User %r>' % self.name


class UserLog(db.Model):
    """会员日志"""
    __tablename__ = 'userlog'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip = db.Column(db.String(100))
    dataTime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<UserLog %r>' % self.id


class Tag(db.Model):
    """标签"""
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    movie_tag = db.relationship('Movie', backref='tag')  # 电影外键关系关联

    def __repr__(self):
        return '<tag %r>' % self.name


class Movie(db.Model):
    """电影"""
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    url = db.Column(db.String(255), unique=True)
    info = db.Column(db.Text)
    logo = db.Column(db.String(255), unique=True)
    star = db.Column(db.SmallInteger)
    playnum = db.Column(db.BigInteger)
    commentnum = db.Column(db.BigInteger)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))
    area = db.Column(db.String(100))
    release_time = db.Column(db.Date)  # 上映时间
    length = db.Column(db.String(100))  # 播放时间
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    comment_movie = db.relationship('Comment', backref='movie')  # 评论外键关系关联
    col_movie = db.relationship('MovieCol', backref='movie')  # 收藏外键关系关联

    def __repr__(self):
        return '<movie %r>' % self.title


class Preview(db.Model):
    """电影预告"""
    __tablename__ = 'preview'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    logo = db.Column(db.String(255), unique=True)
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<preview %r>' % self.title


class Comment(db.Model):
    """电影评论"""
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<comment %r>' % self.id


class MovieCol(db.Model):
    """电影收藏"""
    __tablename__ = 'moviecol'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<comment %r>' % self.id


class Auth(db.Model):
    """权限"""
    __tablename__ = 'auth'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(200), unique=True)  # 名称
    url = db.Column(db.String(255), unique=True)
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<auth %r>' % self.name


class Roles(db.Model):
    """角色"""
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(200), unique=True)
    auths = db.Column(db.String(600), unique=True)  # 权限列表
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    admin_role = db.relationship('Admin', backref='roles')  # 管理员外键关联

    def __repr__(self):
        return '<role %r>' % self.name


class Admin(db.Model):
    """管理员"""
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)
    pwd = db.Column(db.String(100))  # 密码
    is_super = db.Column(db.Integer)  # 是否为超级管理员，0为是超级管理员
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)
    admin_log = db.relationship('Adminlog', backref='admin')  # 管理员登录日志外键关系关联
    option_log = db.relationship('Oplog', backref='admin')  # 管理员操作日志外键关系关联

    def check_pwd(self, pwd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


class Adminlog(db.Model):
    """管理员登录日志"""
    __tablename__ = 'adminlog'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    ip = db.Column(db.String(255))
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<adminlog %r>' % self.id


class Oplog(db.Model):
    """管理员操作日志"""
    __tablename__ = 'oplog'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    ip = db.Column(db.String(255))
    reason = db.Column(db.String(255))  # 操作原因
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<oplog %r>' % self.id


# if __name__ == '__main__':
#     # db.create_all()
    
#     from werkzeug.security import generate_password_hash    
#     admin=Admin(
#         name='admin',
        
#         pwd=generate_password_hash('admin'),
#         is_super = 0,
#         role_id=1
#     )
#     db.session.add(admin)
#     db.session.commit()
