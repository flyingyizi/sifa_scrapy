

## db配置

db涉及到的配置是`cust_cfg/custcfg.py`配置中的`'CONN_DB_INFO'`节点：

```python
#数据库
'CONN_DB_INFO' : {'DBTYPE':'mysql',
                  'CONN': {'host':'192.168.1.8', 'user':'wordpressuser',
                           'passwd':'xx', 'db':'wordpress', 'charset':'utf8'},},
```

对该节点有以下几点说明:

- `'DBTYPE'`key 对应value可以是：'mysql','redis'
- `'CONN'` key 对应子节点内keys与pymysql connect参数完全相同，对非mysql DB有选择使用其中部分子集，具体支持列表可查看各个db实现，例如redis 见`db.RedisClient.RedisClient.__init__`代码


