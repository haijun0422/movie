# -*- coding: utf-8 -*-
from . import admin
from app.admin.forms import LoginForm, TagForm, MovieForm
from flask import render_template, redirect, url_for, flash, session, request
from functools import wraps
from app.models import Admin, Tag, Movie
from app import db,app
from werkzeug.utils import secure_filename # 把文件问转化成安全的文件名
import os
import uuid
from datetime import datetime

def admin_login_req(f):
    @wraps(f)
    def decotator_fun(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)

    return decotator_fun


# 修改上传文件名称
def change_filename(filename):
    fileinfo=os.path.splitext(filename)
    filename=datetime.now().strftime('%Y%m%d%H%M%S')+str(uuid.uuid4().hex)+fileinfo[-1]
    return filename


@admin.route('/')
@admin_login_req
def index():
    return render_template('admin/index.html')


@admin.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin.check_pwd(data['pwd']):
            flash(u'密码错误')
            return redirect(url_for('admin.login'))
        session['admin'] = data['account']
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html', form=form)


@admin.route('/logout/')
@admin_login_req
def logout():
    session.pop('account', None)
    return redirect(url_for('admin.login'))


@admin.route('/pwd/')
@admin_login_req
def pwd():
    return render_template('admin/pwd.html')


@admin.route('/tag/add/', methods=['GET', 'POST'])
@admin_login_req
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag_add = Tag.query.filter_by(name=data['name']).count()
        if tag_add == 1:
            flash('标签名已存在', 'err')
            return redirect(url_for('admin.tag_add'))
        tag=Tag(
            name=data['name']
        )
        db.session.add(tag)
        db.session.commit()
        flash('操作成功','ok')
        return redirect(url_for('admin.tag_add'))
    return render_template('admin/tag_add.html', form=form)


@admin.route('/tag/list/<int:page>/',methods=['GET'])
@admin_login_req
def tag_list(page=None):
    if page is None:
        page=1
    page_data=Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page,per_page=2)
    return render_template('admin/tag_list.html',page_data=page_data)


@admin.route('/tag/del/<int:id>/',methods=['GET'])
@admin_login_req
def tag_del(id=None):
    tag=Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash('删除成功','ok')
    return redirect(url_for('admin.tag_list',page=1))

@admin.route('/tag/edit/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
def tag_edit(id):
    tag=Tag.query.get_or_404(id)
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data['name']).count()
        if tag.name!=data['name'] and tag_count==1:
            flash('标签名已存在', 'err')
            return redirect(url_for('admin.tag_edit',id=id))
        tag.name=data['name']
        db.session.add(tag)
        db.session.commit()
        flash('修改成功','ok')
        return redirect(url_for('admin.tag_edit',id=id))
    return render_template('admin/tag_edit.html', form=form,tag=tag)

@admin.route('/movie/add/',methods=['GET','POST'])
@admin_login_req
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data=form.data
        file_url=secure_filename(form.url.data.filename)
        file_logo=secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'],'rw')
        url=change_filename(file_url)
        logo=change_filename(file_logo)
        form.url.data.save(app.config['UP_DIR']+url)
        form.logo.data.save(app.config['UP_DIR']+logo)
        movie=Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data['length']

        )
        db.session.add(movie)
        db.session.commit()
        flash('添加电影成功','ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


@admin.route('/movie/list/<int:page>',methods=['GET'])
@admin_login_req
def movie_list(page=None):
    if page is None:
        page=1
    # 关联Tag查询,filter_by是单表查询，filter是多表关联查询
    page_data=Movie.query.join(Tag).filter( 
         Tag.id==Movie.tag_id
    ).order_by( 
        Movie.addtime.desc()
    ).paginate(page=page,per_page=2)
    return render_template('admin/movie_list.html',page_data=page_data)

@admin.route('/movie/del/<int:id>/',methods=['GET'])
@admin_login_req
def movie_del(id=None):
    movie=Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash('删除电影成功','ok')
    return redirect(url_for('admin.movie_list',page=1))


@admin.route('/movie/edit/<int:id>',methods=['GET','POST'])
@admin_login_req
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators=[]
    form.logo.validators=[]
    movie = Movie.query.get_or_404(int(id))
    if request.method=='GET':
        form.info.data=movie.info
        form.tag_id.data=movie.tag_id
        form.star.data=movie.star
    if form.validate_on_submit():
        data=form.data
        movie_count=Movie.query.filter_by(title=data['title']).count()
        if movie_count ==1 and movie.title!=data['title']:
            flash('片名已存在!','err')
            return redirect(url_for('admin.movie_edit',id=id))
        '''上传操作'''    
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'],'rw')
        if form.url.data.filename !='':
            file_url=secure_filename(form.url.data.filename)
            movie.url=change_filename(file_url)
            form.url.data.save(app.config['UP_DIR']+movie.url)
        if form.logo.data.filename !='':
            file_logo=secure_filename(form.logo.data.filename)
            movie.logo=change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR']+movie.logo)
        movie.star=data['star']
        movie.tag_idr=data['tag_id']
        movie.info=data['info']
        movie.title=data['title']
        movie.area=data['area']
        movie.length=data['length']
        movie.release_time=data['release_time']

        db.session.add(movie)
        db.session.commit()
        flash('修改电影成功','ok')
        return redirect(url_for('admin.movie_edit',id=id))
    return render_template('admin/movie_edit.html', form=form, movie=movie)


@admin.route('/preview/add/')
@admin_login_req
def preview_add():
    return render_template('admin/preview_add.html')


@admin.route('/preview/list/')
@admin_login_req
def preview_list():
    return render_template('admin/preview_list.html')


@admin.route('/user/list/')
@admin_login_req
def user_list():
    return render_template('admin/user_list.html')


@admin.route('/user/view/')
@admin_login_req
def user_view():
    return render_template('admin/user_view.html')


@admin.route('/comment/list/')
@admin_login_req
def comment_list():
    return render_template('admin/comment_list.html')


@admin.route('/moviecol/list/')
@admin_login_req
def moviecol_list():
    return render_template('admin/moviecol_list.html')


@admin.route('/oplog/list/')
@admin_login_req
def oplog_list():
    return render_template('admin/oplog_list.html')


@admin.route('/userloginlog/list/')
@admin_login_req
def userloginlog_list():
    return render_template('admin/userloginlog_list.html')


@admin.route('/adminloginlog/list/')
@admin_login_req
def adminloginlog_list():
    return render_template('admin/adminloginlog_list.html')


@admin.route('/auth/list/')
@admin_login_req
def auth_list():
    return render_template('admin/auth_list.html')


@admin.route('/auth/add/')
@admin_login_req
def auth_add():
    return render_template('admin/auth_add.html')


@admin.route('/role/add/')
@admin_login_req
def role_add():
    return render_template('admin/role_add.html')


@admin.route('/role/list/')
@admin_login_req
def role_list():
    return render_template('admin/role_list.html')


@admin.route('/admin/list/')
@admin_login_req
def admin_list():
    return render_template('admin/admin_list.html')


@admin.route('/admin/add/')
@admin_login_req
def admin_add():
    return render_template('admin/admin_add.html')
