# -*- coding: utf-8 -*-

import codecs
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient

client = MongoClient()
db = client.uinfo
collection = db.weibo_original

inList = open("2358.list", "r").readlines();
print(len(inList))

for inFileName in inList:
	inFile = codecs.open("D:\\Projects\\SublimeText\\Jianshu\\2358\\W\\"+inFileName[:len(inFileName)-1]+".html", "r", "utf-8")
	content = inFile.read()
	inFile.close()
	soup = BeautifulSoup(content, "html5lib")
	usefulInfo = soup.find_all("div", "c")
	if len(usefulInfo) <= 2:
		print("该用户已经主动注销帐号: "+inFileName[:len(inFileName)-1])
	else:
		collectedInfo = {"id":inFileName[:len(inFileName)-1]}
		collectedInfo["头像"] = usefulInfo[0].img.attrs['src']
		tags = [];
		for s in usefulInfo[2].stripped_strings:
			s = s.replace("：",":")
			if (s.find(":") == -1 and s.find(">>") == -1):
				tags.append(s)
			elif (s.find("标签") == -1 and s.find(">>") == -1):
				collectedInfo[s[:s.find(":")]] = s[s.find(":")+1:]
		studyAndWork = []
		collectedInfo["标签"] = tags
		for i in range(3,len(usefulInfo)-3):
			for x in usefulInfo[i].stripped_strings:
				studyAndWork.append(x.replace("\xa0"," "))
		collectedInfo["学习工作"] = studyAndWork
		for x in usefulInfo[len(usefulInfo)-3].stripped_strings:
			if (x.find("互联网") != -1):
				collectedInfo["个性域名"] = x[len("互联网:http://weibo.com/"):]
		# print(collectedInfo)
		collection.insert_one(collectedInfo)
