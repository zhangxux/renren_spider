### Python 爬人人网学校数据
使用说明
0.    运行环境：python2.7
1.    `git clone`
2.    配置数据库`config/db.py`
3.    依赖 `pymysql`,`beautifulsoup4`
4.    创建数据库pythoncity
5.    执行sql文件pythoncity_structure.sql



项目主要爬取了全国所有的技校、高中、初中等信息，不包括香港和海外数据<br /> 
数据存储方式采用mysql，根据自己需要可更改<br /> 
数据库导出其他格式命令如下<br /> 
终端执行“mysql -h 127.0.0.1 -uroot -proot -P3306 -Ne 'use pythoncity;select p.name,c.name ,co.name ,j.name from provinces as p left join cities as c on p.id=c.province_id left join counties as co on c.id=co.city_id left join juniorschools as j on co.id=j.county_id;' > /home/python3/Desktop/text3.txt”保存初中信息<br /> 

 “mysql -h 127.0.0.1 -uroot -proot -P3306 -Ne 'use pythoncity;select p.name,c.name ,co.name ,h.name from provinces as p left join cities as c on p.id=c.province_id left join counties as co on c.id=co.city_id left join highschools as h on co.id=h.county_id ;' > /home/python3/Desktop/text2.txt”保存高中信息
 <br /> 
 N参数：表示去掉行头
 

