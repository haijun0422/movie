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

# 定义装饰器，必须登录后才能访问后台管理页面
def admin_login_req(f):
    @wraps(f)
    def decotator_fun(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)

    return decotator_fun

# 权限控制装饰器
def admin_auth(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        admin = Admin.query.join(Role).filter(
            Role.id == Admin.role_id,
            Admin.id == session.get("admin_id")
        ).first()
        auths = admin.role.auths
        if auths:
            auths = list(map(lambda v: int(v), auths.split(",")))
            auth_list = Auth.query.all()
            urls = [v.url for v in auth_list for val in auths if val == v.id]
            rule = request.url_rule
            if str(rule) not in urls:
                abort(404)
            return func(*args, **kwargs)
        abort(404)
    return decorated_function

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


@admin.route('/preview/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        file_logo = secure_filename(form.logo.data.filename)

        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"])
        logo = change_filename(file_logo)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        preview = Preview(
            title=data.get("title"),
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash("添加预告成功!", "ok")
        return redirect(url_for("admin.preview_add"))
    return render_template("admin/preview_add.html", form=form)


@admin.route('/preview/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def preview_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(Preview.addtime.desc()).paginate(page=page, per_page=10)
    return render_template("admin/preview_list.html", page_data=page_data)


@admin.route("/preview/edit/<int:id>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(int(id))
    if request.method == "GET":
        form.title.data = preview.title
    if form.validate_on_submit():
        data = form.data
        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)
        preview.title = data.get("title")
        db.session.add(preview)
        db.session.commit()
        flash("修改预告成功！", "ok")
        return redirect(url_for("admin.preview_edit", id=id))
    return render_template("admin/preview_edit.html", form=form, preview=preview)

@admin.route("/preview/del/<int:id>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_del(id=None):
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()

    flash("删除预告成功！", "ok")
    return redirect(url_for("admin.preview_list", page=1))


@admin.route('/user/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def user_list(page=None):
    if page is None:
        page = 1
    page_data = User.query.order_by(User.addtime.asc()).paginate(page=page, per_page=3)
    return render_template("admin/user_list.html", page_data=page_data)


@admin.route('/user/view/<int:id>/', methods=['GET'])
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(int(id))
    return render_template("admin/user_view.html", user=user)


@admin.route("/user/del/<int:id>/", methods=['GET'])
@admin_login_req
@admin_auth
def user_del(id=None):
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash("删除会员成功", "ok")
    return redirect(url_for('admin.user_list', page=1))

@admin.route('/comment/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def comment_list(page=None):
    if page is None:
        page = 1
    page_data = Comment.query.join(Movie).join(User).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(Comment.addtime).paginate(page=page, per_page=10)

    return render_template("admin/comment_list.html", page_data=page_data)

@admin.route("/comment/del/<int:id>/", methods=['GET'])
@admin_login_req
@admin_auth
def comment_del(id=None):
    comment = Comment.query.get_or_404(int(id))
    db.session.delete(comment)
    db.session.commit()
    flash("删除评论成功", "ok")
    return redirect(url_for("admin.comment_list", page=1))

# 电影收藏列表
@admin.route('/moviecol/list/<int:page>/', methods=["GET"])
@admin_login_req
@admin_auth
def moviecol_list(page=None):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(Movie).join(User).filter(
        Movie.id == Moviecol.movie_id,
        User.id == Moviecol.user_id
    ).order_by(Moviecol.addtime).paginate(page=page, per_page=10)
    return render_template("admin/moviecol_list.html", page_data=page_data)

# 删除电影收藏
@admin.route("/moviecol/del/<int:id>/", methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_del(id=None):
    moviecol = Moviecol.query.get_or_404(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除收藏成功", "ok")
    return redirect(url_for("admin.moviecol_list", page=1))

# 用户操作日志
@admin.route('/oplog/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def oplog_list(page=None):
    if page is None:
        page = 1
    page_data = Oplog.query.join(Admin).filter(Admin.id == Oplog.admin_id).order_by(
        Oplog.addtime
    ).paginate(page=page, per_page=5)

    return render_template("admin/oplog_list.html", page_data=page_data)


@admin.route('/userloginlog/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def userloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.join(User).filter(User.id == Userlog.user_id).order_by(
        Userlog.id
    ).paginate(page=page, per_page=10)
    print(page_data)
    return render_template("admin/userloginlog_list.html", page_data=page_data)


@admin.route('/adminloginlog/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def adminloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Adminlog.query.join(Admin).filter(Admin.id == Adminlog.admin_id).order_by(
        Adminlog.addtime
    ).paginate(page=page, per_page=5)
    print(page_data.__dict__)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


@admin.route('/auth/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def auth_list(page=None):
    if page is None:
        page = 1
    page_data = Auth.query.order_by(Auth.id).paginate(page=page, per_page=10)
    return render_template("admin/auth_list.html", page_data=page_data)


@admin.route('/auth/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data.get('name'),
            url=data.get('url'),
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功！", "ok")
        return redirect(url_for("admin.auth_list", page=1))
    return render_template("admin/auth_add.html", form=form)


@admin.route("/auth/edit/<int:id>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        auth.name = data.get("name")
        auth.url = data.get('url')
        db.session.add(auth)
        db.session.commit()
        flash("修改权限成功！", "ok")
        return redirect(url_for("admin.auth_list", page=1))
    return render_template("admin/auth_edit.html", form=form, auth=auth)

@admin.route("/auth/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def auth_del(id=None):
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash("删除权限成功！", "ok")
    return redirect(url_for("admin.auth_list", page=1))

@admin.route('/role/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role = Role(
            name=data.get("name"),
            auths=",".join(map(lambda v: str(v), data.get("auths")))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功！", "ok")
        return redirect(url_for("admin.role_list", page=1))
    return render_template("admin/role_add.html", form=form)


@admin.route('/role/list/<int:page>/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_list(page=None):
    if page is None:
        page = 1
    page_data = Role.query.order_by(Role.id).paginate(page=page, per_page=10)
    return render_template("admin/role_list.html", page_data=page_data)

@admin.route("/role/edit/<int:id>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.get_or_404(id)
    if request.method == 'GET':
        auths = role.auths
        form.auths.data = list(map(lambda v: int(v), auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        role.name = data.get("name")
        role.auths = ",".join(map(lambda v: str(v), data.get('auths')))
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功！", "ok")
    return render_template("admin/role_edit.html", form=form, role=role)

@admin.route("/role/del/<int:id>/", methods=['GET'])
@admin_login_req
@admin_auth
def role_del(id=None):
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("角色删除成功！", "ok")
    return redirect(url_for("admin.role_list", page=1))

@admin.route('/admin/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def admin_list(page=None):
    if page is None:
        page = 1
    page_data = Admin.query.join(Role).filter(Role.id == Admin.role_id).order_by(
        Admin.id
    ).paginate(page=page, per_page=10)

    print("page_data:", page_data)
    return render_template("admin/admin_list.html", page_data=page_data)


@admin.route('/admin/add/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data.get("name"),
            pwd=generate_password_hash(data.get('pwd')),
            role_id=data.get("role_id"),
            is_super=1,
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加管理员成功！", "ok")
        return redirect(url_for('admin.admin_list', page=1))
    return render_template("admin/admin_add.html", form=form)