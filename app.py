# -*- coding: utf-8 -*-
import os
from io import BytesIO
from flask import Flask, render_template, url_for, request, redirect, send_file, jsonify, \
    session, make_response, flash
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import pandas as pd
from pandas import ExcelWriter
from sqlalchemy import or_, cast, VARBINARY
from werkzeug.utils import secure_filename
from config import engine
from table import Flaskdemo, Qrymaininfo, Filetable, User, Dept
from datetime import timedelta

"""
1.添加登录、注销功能 
    2021.1.13完成
2.添加管理员面板：人员、部门、文档权限
3.添加管理员删除附件按钮
"""

app = Flask(__name__)
app.secret_key = "db112546-3fb3-43c3-b625-934603cd28a2"
app.config['SECRET_KEY'] = "db112546-3fb3-43c3-b625-934603cd28a2"
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024  # 限制上传的文件最大6MiB体积

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = u"请登录"
login_manager.init_app(app)

path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')
DOWNLOAD_TEMPDIR = os.path.join(path, 'downloads')
# 建立文件上传下载文件夹
# if not os.path.isdir(UPLOAD_FOLDER):
#     os.mkdir(UPLOAD_FOLDER)
# if not os.path.isdir(DOWNLOAD_TEMPDIR):
#     os.mkdir(DOWNLOAD_TEMPDIR)

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建表
# Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
dbsession = Session()


# 上传文件函数
def upload_file(id, filename, blob, flag):
    check_record = dbsession.query(Filetable).filter(Filetable.id == id).first()
    # True=正文 False=附件
    if flag:
        try:
            if check_record:
                check_record.filename = filename
                check_record.fileblob = blob.read()
            else:
                new_tasks = Filetable(id=id, filename=filename, fileblob=blob.read())
                dbsession.add(new_tasks)
            dbsession.commit()
        except:
            dbsession.rollback()
            return False
    else:
        try:
            if check_record:
                check_record.filename1 = filename
                check_record.fileblob1 = blob.read()
            else:
                new_tasks = Filetable(id=id, filename1=filename, fileblob1=blob.read())
                dbsession.add(new_tasks)
            dbsession.commit()
        except:
            dbsession.rollback()
            return False
    return True


@login_manager.user_loader
def load_user(user_id):
    return dbsession.query(User).get(int(user_id))


@app.route('/')
def index():
    if 'userName' in session:
        return render_template('index.html')
    else:
        return redirect('login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        deptNo = request.form.get('dept')
        dept = dbsession.query(Dept).filter(Dept.id == deptNo).first()
        # 返回的是用户登录时的LoginNo
        userId = request.form.get('usernames')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = dbsession.query(User).filter(User.id == userId).filter(
            or_(User.inUse == None, User.inUse != 'N')).first()
        if not user or not (user.password.decode() == password):
            flash('登录信息错误，请重试。')
            return redirect(url_for('login'))
        print(type(user.password))
        login_user(user, remember=remember)
        session['userName'] = user.username
        session['deptName'] = dept.deptName
        session['fileHeader'] = dept.fileHeader
        if user.canUpdate is not None:
            session['canUpdate'] = user.canUpdate
        else:
            session['canUpdate'] = 'N'
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)
        return redirect(url_for('index'))
    tasks = dbsession.query(Dept).all()
    # password = str.encode(encoding="gb2312") utf-8
    return render_template('login.html', tasks=tasks)


# 根据部门名称查找有效用户名
@app.route('/getuser/<int:dept>', methods=['POST'])
def getUser(dept):
    if request.method == 'POST':
        userNames = dbsession.query(User).order_by(User.id).filter(User.deptNo == dept).filter(
            or_(User.inUse == None, User.inUse != 'N')).all()
        userDict = {}
        for user in userNames:
            userDict[str(user.id)] = user.username
        return jsonify(userDict)


@app.route('/posts', methods=['GET', 'POST'])
@login_required
def posts():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Flaskdemo(content=task_content)
        try:
            dbsession.add(new_task)
            dbsession.commit()
            return redirect('/posts')
        except:
            return 'There was an issue adding your task'
    else:
        tasks = dbsession.query(Flaskdemo).all()
        return render_template('posts.html', tasks=tasks)


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task_to_delete = dbsession.query(Flaskdemo).filter(Flaskdemo.id == id).one()
    try:
        dbsession.delete(task_to_delete)
        dbsession.commit()
        return redirect('/posts')
    except:
        return 'There was a problem deleting that task'


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = dbsession.query(Flaskdemo).filter(Flaskdemo.id == id).one()
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            dbsession.commit()
            return redirect('/posts')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('update.html', task=task)


# 文档查询视图
@app.route('/qry', methods=['GET', 'POST'])
@login_required
def qry():
    if request.method == 'POST':
        # 获取部门名称，以限制上传权限
        deptName = session['deptName']
        canUpdate = session['canUpdate']
        userName = session['userName']
        title = request.form['inputTitle']
        header = request.form['inputHeader']
        syear = request.form['inputYear']
        f_year = Qrymaininfo.id.isnot(None)
        if syear:
            f_year = Qrymaininfo.filenumber.like("%[[]{}]%".format(syear))
        num = request.form['inputNum']
        sendto = request.form['inputSendto']
        bdate = request.form['inputBDate']
        edate = request.form['inputEDate']
        if bdate:
            bdate = Qrymaininfo.crtime >= bdate
        else:
            bdate = Qrymaininfo.id.isnot(None)
        if edate:
            edate = Qrymaininfo.crtime <= edate
        else:
            edate = Qrymaininfo.id.isnot(None)
        creater = request.form['inputCreater']
        ftype = request.form['inputType']
        attach = request.form['hasAttach']
        if attach == '全部':
            fltattach = Qrymaininfo.id.isnot(None)
        else:
            fltattach = Qrymaininfo.mainfile == attach
        memo = request.form['inputMemo']
        public = request.form['inputPublic']
        tasks = dbsession.query(Qrymaininfo).order_by(Qrymaininfo.id).filter(
            Qrymaininfo.title.like("%{}%".format(title)),
            Qrymaininfo.filenumber.like("%{}%".format(header)),
            f_year,
            Qrymaininfo.filenumber.like("%{}号".format(num)),
            Qrymaininfo.sendto.like("%{}%".format(sendto)),
            Qrymaininfo.creater.like("%{}%".format(creater)),
            Qrymaininfo.ftype.like("%{}%".format(ftype)),
            fltattach,
            bdate, edate,
            Qrymaininfo.memo1.like("%{}%".format(memo)),
            Qrymaininfo.xxgk.like("%{}%".format(public))
        )
        # 存储当前查询的SQL语句，用于数据导出
        session['sql'] = str(tasks.statement.compile(compile_kwargs={"literal_binds": True}))
        return render_template('query.html', tasks=tasks, dept=deptName, userName=userName, canUpdate=canUpdate)
    else:
        return render_template('query.html')


# 重置输入内容
@app.route('/clear', methods=['GET', 'POST'])
def clearinput():
    return redirect('/qry')


# 构造找不到文件时的页面提示信息，并用浏览器回退前一页面
hint = '&#128524;出了一点问题，请&nbsp;'
backscript = 'javascript:history.back()'
error_msg = "<h3 style='text-align:center;margin-top:100px'>{}<a href='{}'>返回</a></h3>".format(hint, backscript)


# 下载正文文档
@app.route('/mainfile/<int:id>', methods=['GET', 'POST'])
def download_mainfile(id):
    file = dbsession.query(Filetable).filter(Filetable.id == '{}'.format(id)).first()
    if file.filename:
        filename = file.filename
        return send_file(BytesIO(file.fileblob), attachment_filename=filename, as_attachment=True)
    else:
        return error_msg


# 下载附件文档
@app.route('/mainfile1/<int:id>', methods=['GET', 'POST'])
def download_attachfile(id):
    file = dbsession.query(Filetable).filter(Filetable.id == '{}'.format(id)).first()
    if file.filename1:
        filename = file.filename1
        if filename.find('.') < 0:
            filename = str(id) + '.' + filename
        return send_file(BytesIO(file.fileblob1), attachment_filename=filename, as_attachment=True)
    else:
        return error_msg


# 上传文件到数据库中
@app.route('/upload/<string:target>/<int:id>', methods=['POST'])
def upload_page(target, id):
    input_name = target + str(id)
    msg = ''
    if request.method == 'POST':
        # check if the post request has the file part
        if input_name not in request.files:
            msg = '没有发现上传的文件内容'
            return redirect(request.url)
    uploaded_file = request.files[input_name]
    filename = secure_filename(uploaded_file.filename)
    if filename == '':
        msg = 'No file selected for uploading'
        return redirect(request.url)

    if target == 'main':
        # file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # uploaded_file.save(file_path)
        if upload_file(id, filename, uploaded_file, True):
            try:
                update_Maininfo = dbsession.query(Qrymaininfo).filter(Qrymaininfo.id == id).first()
                update_Maininfo.mainfile = "有正文"
                dbsession.commit()
                msg = '上传文件顺利完成！'
            except:
                dbsession.rollback()
                msg = '新增记录错误'
        return jsonify({'msg': msg})
    else:
        if upload_file(id, filename, uploaded_file, False):
            try:
                update_maininfo = dbsession.query(Qrymaininfo).filter(Qrymaininfo.id == id).first()
                update_maininfo.mainfile1 = "有附件"
                dbsession.commit()
                msg = '上传文件顺利完成！'
            except:
                dbsession.rollback()
                msg = '新增记录错误'
        return jsonify({'msg': msg})


# 导出查询结果为xlsx文件
@app.route('/export', methods=['GET', 'POST'])
def export():
    """
        导出用户查询的数据表为可下载的excel文件
        Returns: xlsx文件
    """
    # 实例化字节类型IO对象,用来在内存中存储对象,不用在磁盘上生成临时文件了
    out: BytesIO = BytesIO()
    # 实例化输出xlsx的writer对象
    writer = ExcelWriter(out, engine='openpyxl')
    # 将SQLAlchemy模型的查询对象拆分SQL语句和连接属性传给pandas的read_sql方法
    df = pd.read_sql(session['sql'], engine)
    # 对df列名重命名
    df.rename(columns={
        'fileid': '识别号',
        'OperDept': '科室',
        'OperUser': '操作人员',
        'filenumber': '文号',
        'miji': '密级',
        'title': '文件标题',
        'sendto': '主送单位名称',
        'ftype': '公文种类',
        'creater': '拟稿人',
        'crtime': '印发日期',
        'xxgk': '信息公开选项',
        'mainfile': '有无正文',
        'mainfile1': '有无附件',
        'memo1': '备注'
    }, inplace=True)
    df.index.name = '序号'
    # 将df转excel保存在内存writer变量中,转换结果中不要包含index行号
    df.to_excel(writer, index=True)
    # 这一步不能漏了,不save的话浏览器下载的xls文件里面啥也没有
    writer.save()
    # 重置一下IO对象的指针到开头
    out.seek(0)
    # IO对象使用getvalue()可以返回二进制的原始数据,用来给要生成的response的data
    resp = make_response(out.getvalue())
    # 设置response的header,让浏览器解析为文件下载行为
    resp.headers['Content-Disposition'] = 'attachement; filename=QueryTable.xlsx'
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8'
    # resp.headers['Content-Length'] 获取文件大小（字节）
    return resp


# 新建发文登记
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    operName = session['userName']
    deptName = session['deptName']
    if request.method == 'POST':
        # 检索最大ID号
        maxID = dbsession.query(Qrymaininfo.id).order_by(Qrymaininfo.id.desc()).first().id + 1
        title = request.form['inputTitle']
        writer = request.form['inputCreater']
        fileNumber = request.form['inputHeader'] + '[' + request.form['inputYear'] + ']' + request.form[
            'inputNum'] + '号'
        createDate = request.form['inputBDate']
        sendTo = request.form['inputSendto']
        fileType = request.form['inputType']
        memo = request.form['inputMemo']
        public = request.form['inputPublic']
        miJi = request.form['miji']
        # 是否有上传正文文档或附件文档
        fileBlob = request.files['fileblob']
        fileBlob1 = request.files['fileblob1']
        has_mainFile = "无"
        if fileBlob.filename != '':
            has_mainFile = "有正文"
        has_mainFile1 = "无"
        if fileBlob1.filename != '':
            has_mainFile1 = "有正文"
        new_record = Qrymaininfo(id=maxID, filenumber=fileNumber, miji=miJi, title=title, sendto=sendTo,
                                 ftype=fileType, creater=writer, crtime=createDate, xxgk=public,
                                 mainfile=has_mainFile, mainfile1=has_mainFile1, memo1=memo, operdept=deptName,
                                 operuser=operName)
        try:
            dbsession.add(new_record)
            dbsession.commit()
        except:
            dbsession.rollback()

        # 连带上传电子文档
        if fileBlob.filename != '':
            upload_file(maxID, fileBlob.filename, fileBlob, True)
        if fileBlob1.filename != '':
            upload_file(maxID, fileBlob1.filename, fileBlob1, False)
        # return jsonify({'msg': fileNumber, 'id': maxID})

        tasks = dbsession.query(Qrymaininfo).order_by(Qrymaininfo.id.desc()).filter(
            Qrymaininfo.operdept.like("%{}%".format(deptName))).limit(10).all()
        return render_template('new.html', tasks=tasks, newNum=fileNumber, dept=deptName)
    # 此处增加科室权限检查
    tasks = dbsession.query(Qrymaininfo).order_by(Qrymaininfo.id.desc()).filter(
        Qrymaininfo.operdept.like("%{}%".format(deptName))).limit(10).all()
    # 此处不开放文件上传权限
    return render_template('new.html', tasks=tasks)


# 刷新最新文号
@app.route('/getMaxNum', methods=['POST'])
def getMaxNum():
    prefix = request.form["prefix"]
    num = request.form["num"]
    deptName = session['deptName']
    tasks = dbsession.query(Qrymaininfo).order_by(Qrymaininfo.id.desc()).filter(
        Qrymaininfo.filenumber.like("%{}[[]{}]%".format(prefix, num)), Qrymaininfo.operdept == deptName).first()
    if tasks:
        # 对文号按']'进行分割，获取具体号码，并加1返回
        newNum = int(tasks.filenumber.split(']')[1][:-1]) + 1
        return jsonify({'msg': prefix, 'num': str(newNum)})
    return jsonify({'msg': prefix, 'num': 1})


# 注销登录
@app.route('/logout')
@login_required
def logout():
    if 'userName' in session:
        session.pop('userName', None)
    if 'deptName' in session:
        session.pop('deptName', None)
    if 'fileHeader' in session:
        session.pop('fileHeader', None)
    if 'canUpdate' in session:
        session.pop('canUpdate', None)
    logout_user()
    return '<h1 style="text-align: center;margin-top: 10%;">You are now logged out!</h1>'


# 系统部门、人员等管理维护
@app.route('/setting', methods=['GET', 'POST'])
@login_required
def setting():
    # S系统级管理员  A科室文管员  N无权限  默认Null
    if (session['userName'] != '张旭州') and (session['canUpdate'] != 'S'):
        return redirect('/')
    return render_template('setting.html')


# 用户密码修改
@app.route('/updatePassword', methods=['GET', 'POST'])
@login_required
def updatePassword():
    if request.method == 'POST':
        newPwd = request.form['password']
        loginId = int(current_user.id)
        task = dbsession.query(User).filter(User.id == loginId).first()
        tmp = cast(newPwd.encode(), VARBINARY(10))
        task.password = tmp
        dbsession.commit()
        return jsonify({'msg': '修改成功'})
    return render_template('password.html')


# 部门科室信息设置
@app.route('/unit', methods=['GET', 'POST'])
@login_required
def setUnit():
    if request.method == 'POST':
        if request.form['deptNo'] != '' and request.form['deptName'] != '':
            id = request.form['deptNo']
            deptName = request.form['deptName']
            try:
                task = dbsession.query(Dept).filter(Dept.id == id).first()
                task.deptName = deptName
                task.fileHeader = request.form['fileHeader']
                dbsession.commit()
                flash('科室信息修改成功！')
            except:
                dbsession.rollback()
                flash('修改出现错误')
        else:
            flash('信息输入有误，请检查！')
        return redirect(url_for('setUnit'))
    tasks = dbsession.query(Dept).all()
    return render_template('unit.html', tasks=tasks)


# 新增加科室部门
@app.route('/addNewDept', methods=['POST'])
@login_required
def addNewDept():
    if request.method == 'POST':
        id = dbsession.query(Dept.id).order_by(Dept.id.desc()).first().id + 1
        newName = request.form['newDeptName']
        newFileHeader = request.form['newFileHeader']
        try:
            task = dbsession.query(Dept).first()
            task.id = id
            task.deptName = newName
            task.fileHeader = newFileHeader
            dbsession.commit()
            return jsonify({'msg': '新增成功！'})
        except:
            dbsession.rollback()
            return jsonify({'msg': '出现了一点问题！'})


@app.before_request
def before_request_a():
    print('I am in before_request_a')


@app.before_request
def before_request_b():
    print('I am in before_request_b')


@app.after_request
def after_request_a(response):
    print('request_a')
    return response


@app.after_request
def after_request_b(response):
    print('I am in after_request_b')
    return response


@app.teardown_request
def teardown_request_a(exc):
    print('I am in teardown_request_a')


@app.teardown_request
def teardown_request_b(exc):
    print('I am in teardown_request_b')


if __name__ == "__main__":
    app.run(port=3000, debug=True)  # host='0.0.0.0',
