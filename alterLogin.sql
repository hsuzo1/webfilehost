select * into #login from login

--删除数据表
drop table login

--创建数据表（并设置标识列）
create table login([LoginNo] int  identity(1,1),
  [LoginName] nvarchar(50) COLLATE Chinese_PRC_CI_AS  NOT NULL,
  [Password] varbinary(50)  NULL,
  [DeptNo] int  NOT NULL,
  [InUse] char(1) COLLATE Chinese_PRC_CI_AS  NULL,
  [IsValid] char(1) COLLATE Chinese_PRC_CI_AS  NULL,
  [BMQX] nvarchar(200) COLLATE Chinese_PRC_CI_AS  NULL)

--设置标识列允许插入
set identity_insert login on

--将数据从临时表转移过来
insert into login(LoginNo,LoginName,Password,DeptNo,InUse,IsValid,BMQX)
select LoginNo,LoginName,Password,DeptNo,InUse,IsValid,BMQX from #login

--关闭标识列插入
set identity_insert login off

--强制设置标识列的起始值:
DBCC CHECKIDENT (login, RESEED, 1) --强制使标识值从1开始.

--SELECT COLUMNPROPERTY( OBJECT_ID('Login'),'LoginNo','IsIdentity')
--设置主键 id name