# -*- coding: utf-8 -*-

import codecs
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient

client = MongoClient()
db = client.uinfo
collection = db.douban_original

inList = open("72.list", "r").readlines();
print(len(inList))

for inFileName in inList:
	inFile = codecs.open(inFileName[:len(inFileName)-1]+".html", "r", "utf-8")
	content = inFile.read()
	inFile.close()
	soup = BeautifulSoup(content, "html5lib")
	failed = soup.find_all("div", "mn")
	if len(failed) > 0:
		print("该用户已经主动注销帐号: "+inFileName[:len(inFileName)-1])
	else:
		collectedInfo = {"id":inFileName[:len(inFileName)-1]}
		collectedInfo["昵称"] = soup.title.string.replace("\n","")
		usefulInfo = soup.find_all("div", "pic")
		collectedInfo["头像"] = usefulInfo[0].img.attrs['src']
		usefulInfo = soup.find_all(id="display")
		if len(usefulInfo) > 0:
			collectedInfo["个性签名"] = usefulInfo[0].string
		usefulInfo = soup.find_all("div", "user-info")
		detailedInfo = list(usefulInfo[0].stripped_strings)
		if detailedInfo[0].find("常居") == -1:
			collectedInfo["个性域名"] = detailedInfo[0]
		else:
			collectedInfo["地区"] = detailedInfo[1]
			collectedInfo["个性域名"] = detailedInfo[2]
		usefulInfo = soup.find_all(id="intro_display")
		if len(usefulInfo) > 0:
			collectedInfo["简介"] = list(usefulInfo[0].stripped_strings)
		# print(collectedInfo)
		collection.insert_one(collectedInfo)
