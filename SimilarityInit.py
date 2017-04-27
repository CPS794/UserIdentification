# -*- coding: utf-8 -*-

import codecs
import json
import SaveAndLoad
import Const
import pymongo
from pymongo import MongoClient
from geopy.distance import vincenty
import Levenshtein
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity


NUMBER_OF_TEST = 3
PATH = "./data/"
FILE_NAME = "72"

BASIC_LIST=["地区", "个性域名", "昵称"]
COUNT_LIST=["详情", "简介"]
WEIGHT={"昵称":1,"个性域名":1,"地区":1,"简介":1,"详情":1}

userList = []
userId = {}
userAmount = 0
winfo = []
dinfo = []
geoList = {}
simIntro = []
simDetail = []
matrix = {}

# 数据读入及预处理
def init(inFile):
	global userList, userId, userAmount, winfo, dinfo, simIntro, simDetail
	
	# 连数据库 MongoDB
	client = MongoClient()
	db = client.uinfo
	weibo = db.weibo
	douban = db.douban
	geocode = db.geocode

	# 从文件中读入待比对的用户列表
	[userList] = SaveAndLoad.load(inFile,1)
	userAmount = len(userList)
	print(userAmount)

	userId = {}
	for i in range(userAmount):
		userId[userList[i]] = i

	# 从数据库中读取用户信息
	winfo = []
	dinfo = []
	for user in userList:
		winfo.append(weibo.find_one({"id":user}))
		dinfo.append(douban.find_one({"id":user}))

	# 初始化地理位置信息
	for geo in geocode.find({},{"_id":0}):
		geoList[geo['name']]=geo['detail'][0]['geometry']['location']

	# 初始化语料库
	corpusIntro = []
	corpusDetail = []

	for wid in range(userAmount):
		info = winfo[wid]
		if ("简介" in info and len(info["简介"])>0):
			detail = info["简介"]
			doc = ""
			for x in detail:
				for y in range(detail[x]):
					doc += x + " "
			corpusIntro.append(doc)
		else:
			corpusIntro.append("")

	for did in range(userAmount):
		info = dinfo[did]
		if ("简介" in info and len(info["简介"])>0):
			detail = info["简介"]
			doc = ""
			for x in detail:
				for y in range(detail[x]):
					doc += x + " "
			corpusIntro.append(doc)
		else:
			corpusIntro.append("")

	for wid in range(userAmount):
		info = winfo[wid]
		if ("详情" in info and len(info["详情"])>0):
			detail = info["详情"]
			doc = ""
			for x in detail:
				for y in range(detail[x]):
					doc += x + " "
			corpusDetail.append(doc)
		else:
			corpusDetail.append("")

	for did in range(userAmount):
		info = dinfo[did]
		if ("详情" in info and len(info["详情"])>0):
			detail = info["详情"]
			doc = ""
			for x in detail:
				for y in range(detail[x]):
					doc += x + " "
			corpusDetail.append(doc)
		else:
			corpusDetail.append("")

	vec = CountVectorizer()
	countsIntro = vec.fit_transform(corpusIntro)
	countsDetail = vec.fit_transform(corpusDetail)
	tra = TfidfTransformer()
	tfidfIntro = tra.fit_transform(countsIntro)
	tfidfDetail = tra.fit_transform(countsDetail)

	cnt=0
	for row in tfidfIntro:
		simIntro.append(cosine_similarity(row, tfidfIntro).tolist()[0][userAmount:])
		cnt+=1;
		if (cnt>=userAmount):
			break

	cnt=0
	for row in tfidfDetail:
		simDetail.append(cosine_similarity(row, tfidfDetail).tolist()[0][userAmount:])
		cnt+=1;
		if (cnt>=userAmount):
			break

# 计算各项属性的相似度
def sim():
	global matrix
	matrix = {}

	N=(0,89.5)
	S=(0,-89.5)
	MAX_DISTANCE = vincenty(N, S).miles

	for wid in range(userAmount):
		weiboId = userList[wid]
		weiboInfo = winfo[wid]
		matrix[weiboId] = {"id":weiboId}

		for did in range(userAmount):
			doubanId = userList[did]
			doubanInfo = dinfo[did]
			matrix[weiboId][doubanId] = {"id":doubanId}

			if ("昵称" in weiboInfo and "昵称" in doubanInfo):
				sw = weiboInfo["昵称"].lower().replace(" ","")
				sd = doubanInfo["昵称"].lower().replace(" ","")
				matrix[weiboId][doubanId]["昵称"] = Levenshtein.jaro_winkler(sw,sd)
				if (matrix[weiboId][doubanId]["昵称"] == 0): 
					matrix[weiboId][doubanId]["昵称"] = min(Levenshtein.ratio(sw,sd),0.5)

			if ("个性域名" in weiboInfo and "个性域名" in doubanInfo):
				sw = weiboInfo["个性域名"].lower().replace(" ","")
				sd = doubanInfo["个性域名"].lower().replace(" ","")
				if not("/" in sw):
					default = True
					for x in sd:
						if not (x in "0123456789"):
							default = False
							break
					if not default:
						matrix[weiboId][doubanId]["个性域名"] = Levenshtein.jaro_winkler(sw,sd)

			if ("地区" in weiboInfo and "地区" in doubanInfo):
				sw = weiboInfo["地区"].lower().replace(" ","").replace("海外","").replace("其他","")
				sd = doubanInfo["地区"].lower().replace(" ","").replace("海外","").replace("其他","")
				if (len(sw)>0 and len(sd)>0):
					weiboLocation = (geoList[sw]['lat'], geoList[sw]['lng'])
					doubanLocation = (geoList[sd]['lat'], geoList[sd]['lng'])
					distance = vincenty(weiboLocation, doubanLocation).miles
					matrix[weiboId][doubanId]["地区"] = (1 - distance / MAX_DISTANCE) ** 100

			matrix[weiboId][doubanId]["简介"] = simIntro[wid][did]
			matrix[weiboId][doubanId]["详情"] = simDetail[wid][did]

if __name__ == "__main__":
	for x in range(Const.NUMBER_OF_TEST):
		fname = Const.PATH + Const.FILE_NAME + "/" + Const.FILE_NAME + "_" + str(x)

		init(fname + "_S"+".in")
		sim()
		SaveAndLoad.save(fname + "_S_matrix"+".out", [matrix])

		init(fname + "_T"+".in")
		sim()
		SaveAndLoad.save(fname + "_T_matrix"+".out", [matrix])


