# -*- coding: utf-8 -*-
import os
from io import BytesIO
from flask import Flask, render_template, url_for, request, redirect, send_file, jsonify, session, make_response
from sqlalchemy.orm import sessionmaker
import pandas as pd
from pandas import ExcelWriter
from werkzeug.utils import secure_filename
from config import engine
from table import Flaskdemo, Qrymaininfo, Filetable


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
dbsession = Session()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/posts', methods=['GET', 'POST'])
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
        try:
            # 检查是否已经有ID记录，有则更新，无则新增
            check_record = dbsession.query(Filetable).filter(Filetable.id == id).first()
            if check_record:
                check_record.filename = filename
                check_record.fileblob = uploaded_file.read()
            else:
                new_tasks = Filetable(id=id, filename=filename, fileblob=uploaded_file.read())
                dbsession.add(new_tasks)
            dbsession.commit()
            update_Maininfo = dbsession.query(Qrymaininfo).filter(Qrymaininfo.id == id).first()
            update_Maininfo.mainfile = "有正文"
            dbsession.commit()
            msg = '上传文件顺利完成！'
        except:
            dbsession.rollback()
            msg = '新增记录错误'
            return jsonify({'msg' : msg})
    else:
        try:
            check_record = dbsession.query(Filetable).filter(Filetable.id==id).first()
            if check_record:
                check_record.filename1 = filename
                check_record.fileblob1 = uploaded_file.read()
            else:
                new_tasks = Filetable(id=id, filename1=filename, fileblob1=uploaded_file.read())
                dbsession.add(new_tasks)
            dbsession.commit()
            update_maininfo = dbsession.query(Qrymaininfo).filter(Qrymaininfo.id == id).first()
            update_maininfo.mainfile1 = "有附件"
            dbsession.commit()
            msg = '上传文件顺利完成！'
        except Exception as e:
            dbsession.rollback()
            jsonify({'msg' : msg})
    return jsonify({'msg' : msg})


# 导出查询结果为xlsx文件
@app.route('/export', methods=['GET', 'POST'])
def export():
    """
        导出用户查询的数据表为可下载的excel文件
        Returns: xlsx文件
    """
    # 实例化字节类型IO对象,用来在内存中存储对象,不用在磁盘上生成临时文件了
    out = BytesIO()
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
    resp.headers['Content-Disposition'] = 'attachement; filename=querytable.xlsx'
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8'

    return resp


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


