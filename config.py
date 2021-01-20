# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import pymssql


# DBUser = 'flask'  # flask
# DBPassword = '123' #yufengcun123*
# DBHost = '192.168.100.5'  # 192.168.100.5

DBUser = 'SbP_yQ0vWKv'  # flask
DBPassword = 'l#Qk%k5MS8~H19o2e9!@PGuW' #yufengcun123*
DBHost = '106.52.154.209:58570'  # 192.168.100.5
DBName = 'filehost2017'

engine = create_engine(f'mssql+pymssql://{DBUser}:{DBPassword}@{DBHost}/{DBName}?charset=utf8')
# , echo=True

# 映射基类
Base = declarative_base()

# 关闭警告，否则会有警告提示
SQLALCHEMY_DATABASE_URI = False
SQLALCHEMY_TRACK_MODIFICATIONS = False