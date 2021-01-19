# -*- coding: utf-8 -*-
from config import Base
from sqlalchemy import Column, Integer, String, engine, VARBINARY
from sqlalchemy.dialects.mssql import DATETIME, IMAGE
from sqlalchemy.dialects.mssql.base import MSExecutionContext
from datetime import datetime
from flask_login import UserMixin
"""
配置变动：
1.SQL数据库varchar字段全部更新为nvarchar
2.调整主记录的部门归属区分方式
"""


def pre_exec(self):
    if self.isinsert:
        tbl = self.compiled.statement.table
        seq_column = tbl._autoincrement_column
        insert_has_sequence = seq_column is not None

        self._select_lastrowid = (
            not self.compiled.inline
            and insert_has_sequence
            and not self.compiled.returning
            and not self._enable_identity_insert
            and not self.executemany
        )


def post_exec(self):
    conn = self.root_connection
    if self._select_lastrowid:
        if self.dialect.use_scope_identity:
            conn._cursor_execute(
                self.cursor,
                "SELECT scope_identity() AS lastrowid",
                (),
                self,
            )
        else:
            conn._cursor_execute(
                self.cursor, "SELECT @@identity AS lastrowid", (), self
            )
        # fetchall() ensures the cursor is consumed without closing it
        row = self.cursor.fetchall()[0]
        if row[0] is None:
            self._lastrowid = 99999999
        else:
            self._lastrowid = int(row[0])

    if (
        self.isinsert or self.isupdate or self.isdelete
    ) and self.compiled.returning:
        self._result_proxy = engine.FullyBufferedResultProxy(self)


MSExecutionContext.pre_exec = pre_exec
MSExecutionContext.post_exec = post_exec


class Flaskdemo(Base):
    __tablename__ = 'flaskdemo'
    # id 设置为主键
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    # 指定 name 映射到 name 字段
    content = Column('content', String(200))
    date_created = Column('date_created', DATETIME, default=datetime.today().strftime("%Y-%m-%d "))

    def __repr__(self):
        return '<Task %r>' % self.id


# 附件文档表
class Filetable(Base):
    __tablename__ = 'FileTable'
    id = Column('fieldid', Integer, primary_key=True, autoincrement=False)
    filename = Column('filename', String(100))
    filename1 = Column('filename1', String(100))
    filename2 = Column('filename2', String(100))
    fileblob = Column('fileblob', IMAGE)
    fileblob1 = Column('fileblob1', IMAGE)
    fileblob2 = Column('fileblob2', IMAGE)

    def __repr__(self):
        return '<Task %r>' % self.id


# 查询表
class Qrymaininfo(Base):
    # 指定映射表名
    __tablename__ = 'maininfo'
    # id 设置为主键
    id = Column('fileid', Integer, primary_key=True, autoincrement=True, nullable=False)
    filenumber = Column('filenumber', String(30), nullable=True)
    miji = Column('miji', String(4), nullable=True)
    title = Column('title', String(300), nullable=False)
    sendto = Column('sendto', String(300), nullable=True)
    ftype = Column('ftype', String(30), nullable=True)
    creater = Column('creater', String(30), nullable=True)
    crtime = Column('crtime', DATETIME, default=datetime.today().strftime("%Y-%m-%d "), nullable=True)
    xxgk = Column('xxgk', String(20), nullable=True)
    mainfile = Column('mainfile', String(20), nullable=True)
    mainfile1 = Column('mainfile1', String(20), nullable=True)
    memo1 = Column('memo1', String(500))
    operdept = Column('OperDept', String(50), nullable=True)
    operuser = Column('OperUser', String(30), nullable=True)

    def __repr__(self):
        return '<Task %r>' % self.id


# 用户表
class User(UserMixin, Base):
    __tablename__ = 'Login'
    id = Column('LoginNo', Integer, primary_key=True)
    username = Column('LoginName', String(30))
    password = Column('Password', VARBINARY(20))
    deptNo = Column('DeptNo', String(5))
    inUse = Column('InUse', String(5))
    # 标记为A的为管理员
    canUpdate = Column('IsValid', String(5))
    bmqx = Column('BMQX', String(500))


# 部门表
# 查询表
class Dept(Base):
    # 指定映射表名
    __tablename__ = 'Dept'
    id = Column('DeptNo', Integer, primary_key=True, autoincrement=True, nullable=False)
    deptName = Column('DeptName', String(50))
    deptLev = Column('DeptLev', String(10))
    password = Column('Password', String(20))
    shortName = Column('ShortName', String(20))
    fileHeader = Column('FileHeader', String(50))
