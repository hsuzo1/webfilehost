# -*- coding: utf-8 -*-
from flask import Flask, render_template, url_for, request, redirect, send_from_directory, flash, jsonify
from sqlalchemy.orm import sessionmaker
from config import engine
from table import Flaskdemo, Qrymaininfo, Filetable
import os
from werkzeug.utils import secure_filename

"""
1.添加登录、注销功能
2.添加管理员面板：人员、部门、文档权限
3.添加管理员删除附件按钮
"""

app = Flask(__name__)
app.secret_key = "db112546-3fb3-43c3-b625-934603cd28a2"
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 最大20MB体积

path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')
DOWNLOAD_TEMPDIR = os.path.join(path, 'downloads')
# 建立文件上传下载文件夹
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
if not os.path.isdir(DOWNLOAD_TEMPDIR):
    os.mkdir(DOWNLOAD_TEMPDIR)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建表
# Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Flaskdemo(content=task_content)
        try:
            session.add(new_task)
            session.commit()
            return redirect('/posts')
        except:
            return 'There was an issue adding your task'
    else:
        tasks = session.query(Flaskdemo).all()
        return render_template('posts.html', tasks=tasks)


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = session.query(Flaskdemo).filter(Flaskdemo.id == id).one()
    try:
        session.delete(task_to_delete)
        session.commit()
        return redirect('/posts')
    except:
        return 'There was a problem deleting that task'


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = session.query(Flaskdemo).filter(Flaskdemo.id == id).one()
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            session.commit()
            return redirect('/posts')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('update.html', task=task)


@app.route('/qry', methods=['GET', 'POST'])
def qry():
    if request.method == 'POST':
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
        tasks = session.query(Qrymaininfo).order_by(Qrymaininfo.id).filter(
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
        return render_template('query.html', tasks=tasks)
    else:
        return render_template('query.html', )


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
    file = session.query(Filetable).filter(Filetable.id == '{}'.format(id)).first()
    if file.filename:
        filename = file.filename
        with open(os.path.join(DOWNLOAD_TEMPDIR, filename), 'wb') as f:
            f.write(file.fileblob)
        return send_from_directory(directory=DOWNLOAD_TEMPDIR, filename=filename, as_attachment=False,
                                   attachment_filename=filename)
    else:
        return error_msg


# 下载附件文档
@app.route('/mainfile1/<int:id>', methods=['GET', 'POST'])
def download_attachfile(id):
    file = session.query(Filetable).filter(Filetable.id == '{}'.format(id)).first()
    if file.filename1:
        filename = file.filename1
        with open(os.path.join(DOWNLOAD_TEMPDIR, filename), 'wb') as f:
            f.write(file.fileblob1)
        return send_from_directory(directory=DOWNLOAD_TEMPDIR, filename=filename, as_attachment=False,
                                   attachment_filename=filename)
    else:
        return error_msg


@app.route('/upload/<string:target>/<int:id>', methods=['POST'])
def upload_page(target, id):
    input_name = target + str(id)
    if request.method == 'POST':
        # check if the post request has the file part
        if input_name not in request.files:
            flash('没有发现上传的文件内容')
            return redirect(request.url)
    uploaded_file = request.files[input_name]
    filename = secure_filename(uploaded_file.filename)
    if filename == '':
        flash('No file selected for uploading')
        return redirect(request.url)
    if target == 'main':
        # file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # uploaded_file.save(file_path)
        try:
            new_tasks = Filetable(id=id, filename=filename, fileblob=uploaded_file.read())
            session.add(new_tasks)
            session.commit()
            update_Maininfo = session.query(Qrymaininfo).filter(Qrymaininfo.id == id).first()
            update_Maininfo.mainfile = "有正文"
            session.commit()
            flash('上传文件顺利完成！')
        except:
            session.rollback()
            flash('新增记录错误')
            return error_msg
    else:
        try:
            check_record = session.query(Filetable).filter(Filetable.id==id).first()
            if check_record:
                check_record.filename1 = filename
                check_record.fileblob1 = uploaded_file.read()
            else:
                new_tasks = Filetable(id=id, filename1=filename, fileblob1=uploaded_file.read())
                session.add(new_tasks)
            session.commit()
            update_maininfo = session.query(Qrymaininfo).filter(Qrymaininfo.id == id).first()
            update_maininfo.mainfile1 = "有附件"
            session.commit()
            flash('上传文件顺利完成！')
        except Exception as e:
            session.rollback()
            return error_msg
    return redirect(url_for('qry'))


# 测试ajax
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        filename = request.files['file'].filename
        msg = '成功'
        return jsonify({'filename' : filename, 'msg' : msg})
    return render_template('upload.html')


@app.before_request
def before_request_a():
    print('I am in before_request_a')


@app.before_request
def before_request_b():
    print('I am in before_request_b')


@app.after_request
def after_request_a(response):
    print('I am in after_request_a')

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
    # 关闭
    session.close()
