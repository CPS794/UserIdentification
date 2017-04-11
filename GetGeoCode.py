# -*- coding: utf-8 -*-

import codecs
import pymongo
from pymongo import MongoClient
import googlemaps
import time

gmaps = googlemaps.Client(key='API KEY HERE')
client = MongoClient()
db = client.uinfo
weibo = db.weibo
douban = db.douban
geocode = db.geocode
inList = open("243.list", "r").readlines()
print(len(inList))
userList = []
for user in inList:
	userList.append(user[:len(user)-1])

for user in userList:

	weiboInfo = weibo.find_one({"id":user})
	if not("地区" in weiboInfo) :
		continue
	location = weiboInfo["地区"].lower().replace(" ","").replace("海外","").replace("其他","")
	if len(location)>0:
		loca = geocode.find_one({"name":location})
		if loca==None:
			print(location)
			target = {"name":location}
			geocode_result = gmaps.geocode(location)
			target["detail"] = geocode_result
			geocode.insert_one(target)
			time.sleep(1)

	doubanInfo = douban.find_one({"id":user})
	if not("地区" in doubanInfo) :
		continue
	location = doubanInfo["地区"].lower().replace(" ","").replace("海外","").replace("其他","")
	if len(location)>0:
		loca = geocode.find_one({"name":location})
		if loca==None:
			print(location)
			target = {"name":location}
			geocode_result = gmaps.geocode(location)
			target["detail"] = geocode_result
			geocode.insert_one(target)
			time.sleep(1)

