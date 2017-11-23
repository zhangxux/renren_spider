# -*- coding: utf-8 -*-

# “小蜘蛛”用于获取人人网地理位置以及学校相关数据
# 版本： v0.1
# 2015-11-30

# 依赖pymysql, beautifulsoup4

from config import db
from data import prvAndCity as prvcity
import pprint, pymysql, sys, time, threading, random,urllib2, re
from bs4 import BeautifulSoup as bsp


defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


class Spider(object):
    """用于获取人人网数据，并且自动填充到数据库"""
    version = '0.1'
    rrhighApi = 'http://support.renren.com/highschool/'
    rrjuniorApi = 'http://support.renren.com/juniorschool/'
    rrtechnicalApi = 'http://support.renren.com/collegeschool/'
    
    insertCountrySql = 'INSERT INTO `countries`(`name`, `created_at`, `updated_at`) VALUES (%s, now(), now())'
    countCountrySql = 'SELECT COUNT(`id`) AS `countnum` FROM `countries`'
    queryCountrySql = 'SELECT COUNT(`id`) AS `num` FROM `countries` WHERE `name` = %s'
    queryCountryIdSql = 'SELECT `id` FROM `countries` WHERE `name`=%s'

    insertProvinceSql = 'INSERT INTO `provinces` (`name`, `country_id`, `created_at`, `updated_at`) VALUES (%s, %s, now(), now())'
    countProvinceSql = 'SELECT COUNT(`id`) AS `countnum` FROM `provinces`'
    queryProvicneSql = 'SELECT COUNT(`id`) AS `num` FROM `provinces` WHERE `name` = %s'
    queryProvinceIdSql = 'SELECT `id` FROM `provinces` WHERE `name`=%s'

    insertCitySql = 'INSERT INTO `cities` (`name`, `province_id`, `created_at`, `updated_at`) VALUES (%s, %s, now(), now())'
    countCitySql = 'SELECT COUNT(`id`) AS `countnum` FROM `cities`'
    queryCitySql = 'SELECT COUNT(`id`) AS `num` FROM `cities` WHERE `name` = %s'
    queryCityIdSql = 'SELECT `id` FROM `cities` WHERE `name`=%s'

    insertCountySql = 'INSERT INTO `counties` (`name`, `city_id`, `created_at`, `updated_at`) VALUES (%s, %s, now(), now())'
    countCountySql = 'SELECT COUNT(`id`) AS `countnum` FROM `counties`'
    queryCountySql = 'SELECT COUNT(`id`) AS `num` FROM `counties` WHERE `name` = %s AND `city_id`=%s'
    queryCountyIdSql = 'SELECT `id` FROM `counties` WHERE `name`=%s AND `city_id` = %s'

    insertHighSql = 'INSERT INTO `highschools` (`name`, `county_id`, `created_at`, `updated_at`) VALUES (%s, %s, now(), now())'
    countHighSql = 'SELECT COUNT(`id`) AS `countnum` FROM `highschools`'
    queryHighSql = 'SELECT COUNT(`id`) AS `num` FROM `highschools` WHERE `name` = %s'

    insertJuniorSql = 'INSERT INTO `juniorschools` (`name`, `county_id`, `created_at`, `updated_at`) VALUES (%s, %s, now(), now())'
    countJuniorSql = 'SELECT COUNT(`id`) AS `countnum` FROM `juniorschools`'
    queryJuniorSql = 'SELECT COUNT(`id`) AS `num` FROM `juniorschools` WHERE `name` = %s'

    insertTechnicalSql = 'INSERT INTO `technicalschools` (`name`, `county_id`, `created_at`, `updated_at`) VALUES (%s, %s, now(), now())'
    countTechnicalSql = 'SELECT COUNT(`id`) AS `countnum` FROM `technicalschools`'
    queryTechnicalSql = 'SELECT COUNT(`id`) AS `num` FROM `technicalschools` WHERE `name` = %s'
    
    def __init__(self, dbconfig):
        '''self.__mydb  数据库连接句柄'''
        #初始化数据库连接句柄
        self.__mydb = pymysql.connect(host = dbconfig['host'],
            user = dbconfig['user'],
            password = dbconfig['pwd'],
            db  = dbconfig['database'],
            charset = dbconfig['charset'],
            cursorclass = pymysql.cursors.DictCursor)
        #打开日志文件
        self.log = open('exception.log', 'a')

    def addTechnicalSchools(self, cities):
        '插入技校数据'
        starttime = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        try:
            for city in cities:
                citynumber, cityname = tuple(city.split(':'))
                rqtApi = self.rrtechnicalApi + citynumber + '.html'
                print rqtApi

                try:
                    print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5555")
                    htmlhandle = urllib2.urlopen(rqtApi)

                    print htmlhandle
                except Exception as e:
                     self.log.write(time.asctime() + u'请求技校文档错误:' + str(e) + '\n')
                else:
                    print('---下载%s数据成功---' % (cityname))
                    htmldoc = htmlhandle.read().decode('utf-8')
                    print ("")
                    print htmldoc
                    htmlhandle.close()
                    btsp = bsp(htmldoc, 'html.parser')
                    countieshtml = btsp.find_all('a', href="#highschool_anchor")
                    counties = []
                    for countyhtml in countieshtml:
                         counties.append([countyhtml.string.strip(),  re.search(r'[0-9]{4,}', countyhtml['onclick']).group()])
                    mycursor.execute(self.queryCityIdSql, (cityname,))
                    cityid = mycursor.fetchone()['id']
                    for county in counties:
                        mycursor.execute(self.queryCountyIdSql, (county[0], cityid))
                        try:
                            countyid = mycursor.fetchone()['id']
                        except Exception as e:
                            self.log.write('没有找到%s-->%s的id\n' % (cityname, county[0]))
                        else:
                            techshtml = btsp.select('ul[id$=' + county[1] +']')
                            techshtml = techshtml[0].find_all('a') if isinstance(techshtml, list) and len(techshtml) else []
                            for tech in techshtml:
                                if isinstance(tech.string, str) and tech.string.strip():
                                    mycursor.execute(self.queryTechnicalSql, (tech.string.strip()))
                                    if mycursor.fetchone()['num'] == 0:
                                        insert += 1
                                        print('插入技校%s--%s--%s' % (cityname, county[0], tech.string))
                                        mycursor.execute(self.insertTechnicalSql, (tech.string.strip(), countyid))
                            self.__mydb.commit()
        except Exception  as e:
            self.log.write(time.asctime() + str(e) + '\n')
        mycursor.execute(self.countTechnicalSql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '技校')

    def addJuinorSchools(self, cities):
        '插入初中数据'
        starttime = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        try:
            for city in cities:
                citynumber, cityname = tuple(city.split(':'))
                rqtApi = self.rrjuniorApi + citynumber + '.html'
                try:
                    htmlhandle = urllib2.urlopen(rqtApi)
                except Exception as e:
                    self.log.write(time.asctime() + u'请求初中文档错误:' + str(e) + '\n')
                else:
                    print('---下载%s数据成功---' % (cityname))
                    htmldoc = htmlhandle.read().decode('utf-8')
                    htmlhandle.close()
                    btsp = bsp(htmldoc, 'html.parser')
                    countieshtml = btsp.find_all('a', href="#highschool_anchor")
                    counties = []
                    for countyhtml in countieshtml:
                         counties.append([countyhtml.string.strip(),  re.search(r'[0-9]{4,}', countyhtml['onclick']).group()])
                    mycursor.execute(self.queryCityIdSql, (cityname,))
                    cityid = mycursor.fetchone()['id']
                    for county in counties:
                        mycursor.execute(self.queryCountyIdSql, (county[0], cityid))
                        try:
                            countyid = mycursor.fetchone()['id']
                        except Exception as e:
                             self.log.write('没有找到%s-->%s的id\n' % (cityname, county[0]))
                        else:
                            juniorshtml = btsp.select('ul[id$=' + county[1] +']')
                            juniorshtml = juniorshtml[0].find_all('a') if len(juniorshtml) else []
                            for junior in juniorshtml:
                                if junior and  len(junior.string):
                                    mycursor.execute(self.queryJuniorSql, junior.string.strip())
                                    if mycursor.fetchone()['num'] == 0:
                                        insert += 1
                                        print('插入初中%s--%s--%s' % (cityname, county[0], junior.string))
                                        mycursor.execute(self.insertJuniorSql, (junior.string.strip(), countyid))
                            self.__mydb.commit()
        except Exception as e:
            self.log.write(time.asctime() + str(e) + '\n')
        mycursor.execute(self.countJuniorSql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '初中')

    def addHighSchools(self, cities):
        '添加高中数据'
        starttime = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        try:
            for city in cities:
                citynumber, cityname = tuple(city.split(':'))
                rqtApi = self.rrhighApi + citynumber + '.html'
                try:
                    htmlhandle = urllib2.urlopen(rqtApi)
                except Exception as e:
                    self.log.write(time.asctime() + u'请求高中文档错误:' + str(e) + '\n')
                else:
                    print('---下载%s数据成功---' % (cityname))
                    htmldoc = htmlhandle.read().decode('utf-8')
                    htmlhandle.close()
                    btsp = bsp(htmldoc, 'html.parser')

                    countieshtml = btsp.find_all('a', href="#highschool_anchor")
                    counties = []
                    for countyhtml in countieshtml:
                         counties.append([countyhtml.string.strip(),  re.search(r'[0-9]{4,}', countyhtml['onclick']).group()])
                    mycursor.execute(self.queryCityIdSql, (cityname,))
                    cityid = mycursor.fetchone()['id']
                    for county in counties:
                        mycursor.execute(self.queryCountyIdSql, (county[0], cityid))
                        try:
                            countyid = mycursor.fetchone()['id']
                        except Exception as e:
                            self.log.write('没有找到%s-->%s的id\n' % (cityname, county[0]))
                        else:
                            highshtml = btsp.select('ul[id$=' + county[1] +']')
                            highshtml = highshtml[0].find_all('a') if len(highshtml) else []
                            for high in highshtml:
                                mycursor.execute(self.queryHighSql, (high.string.strip(),))
                                if mycursor.fetchone()['num'] == 0:
                                    insert += 1 
                                    print('插入高中%s-->%s-->%s' % (cityname, county[0], high.string.strip()))
                                    mycursor.execute(self.insertHighSql, (high.string.strip(), countyid))
                            self.__mydb.commit()
        except Exception as e:
            self.log.write(time.asctime() + str(e) + '\n')
        mycursor.execute(self.countHighSql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '高中')

    def addCounties(self, cities):
        '添加县级城市'
        starttime  = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        try:
            for city in cities:
                citynumber, cityname = tuple(city.split(':'))
                rqtApi = self.rrhighApi + citynumber + '.html'
                try:
                    htmlhandle = urllib2.urlopen(rqtApi)
                except Exception as e:
                    self.log.write(time.asctime() + u'请求文档错误:' + str(e) + '\n')
                else:
                    print('---下载%s数据成功---' % (cityname))
                    htmldoc = htmlhandle.read().decode('utf-8')
                    htmlhandle.close()
                    btsp = bsp(htmldoc, 'html.parser')
                    
                    counties = btsp.find_all('a', href="#highschool_anchor")
                    mycursor.execute(self.queryCityIdSql, (cityname,))
                    cityid = mycursor.fetchone()['id']
                    for county in counties:
                        mycursor.execute(self.queryCountySql, (county.string, cityid))
                        if mycursor.fetchone()['num'] == 0:
                            insert += 1
                            print('插入%s-->%s' % (cityname, county.string))
                            mycursor.execute(self.insertCountySql, (county.string, cityid))
                    self.__mydb.commit()
        except Exception as e:
            self.log.write(time.asctime() + str(e) + '\n')
        mycursor.execute(self.countCountySql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '县区')
    
    def addCountries(self, countries):
        '添加国家'
        starttime = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        for country in countries:
            mycursor.execute(self.queryCountrySql, (country,))
            if mycursor.fetchone()['num'] == 0:
                insert += 1
                print(u'插入国家-->%s' % (country,))
                mycursor.execute(self.insertCountrySql, (country,))
        self.__mydb.commit()
        mycursor.execute(self.countCountrySql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '国家')

    def addProvinces(self, provinces):
        '添加省份'
        starttime = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        for country, sprovinces in provinces.items():
            mycursor.execute(self.queryCountryIdSql, (country,))
            try:
                cid = mycursor.fetchone()['id']
            except Exception as e:
                self.log.write((time.strftime('%Y-%m-%d %H:%M:%S') + u'没有查询到国家%s的id\n') % (country))
            else:
                for province in sprovinces:
                    mycursor.execute(self.queryProvicneSql, (province))
                    if mycursor.fetchone()['num'] == 0:
                        insert += 1
                        print(u'插入%s省份%s' % (country, province))
                        mycursor.execute(self.insertProvinceSql, (province, cid))
                self.__mydb.commit()
        mycursor.execute(self.countProvinceSql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '省份')

    def addCities(self, cities):
        '添加城市'
        starttime = time.time()
        insert = 0
        mycursor = self.__mydb.cursor()
        for province, scities in cities.items():
            mycursor.execute(self.queryProvinceIdSql, (province))
            try:
                pid = mycursor.fetchone()['id']
            except Exception as e:
                self.log.write((time.strftime('%Y-%m-%d %H:%M:%S') + u'没有查询到省份%s的id\n') % (province))
            else:
                for city in scities:
                    mycursor.execute(self.queryCitySql, (city,))
                    if mycursor.fetchone()['num'] == 0 :
                        insert += 1
                        print(u'插入%s市区%s' % (province, city))
                        mycursor.execute(self.insertCitySql, (city, pid))
                self.__mydb.commit()
        mycursor.execute(self.countCitySql)
        countnum = mycursor.fetchone()['countnum']
        endtime = time.time()
        self.printExeResult(insert, endtime - starttime, countnum, '地级市')

    def printExeResult(self, insert, time, count, etype):
        print('-' * 70)
        print(' ' * 10, "")
        print(u'新增%s:%d，%s总计:%d，耗时%.4fs' % (etype, insert, etype, count, time), '')
        print(' ' * 10)
        print('-' * 70)

    def __del__(self):
        self.log.close()
        self.__mydb.close()

if __name__ == '__main__':
    spider = Spider(db.config)
    spider.addCountries(prvcity.parseCountries(prvcity.countries))
    spider.addProvinces(prvcity.parseProvinces(prvcity.provinces))
    spider.addCities(prvcity.parseCities(prvcity.provinces))
    cities = prvcity.parseCityToNameAndNumber(prvcity.prvcities)
    spider.addCounties(cities)
    spider.addHighSchools(cities)
    spider.addJuinorSchools(cities)
    spider.addTechnicalSchools(cities)

