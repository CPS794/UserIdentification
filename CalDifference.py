# -*- coding: utf-8 -*-

import codecs
import pymongo
from pymongo import MongoClient
import Levenshtein

BASIC_LIST=["地区", "个性域名", "昵称"]
COUNT_LIST=["详情", "简介"]
WEIGHT={"昵称":10,"个性域名":7,"地区":3,"详情":1,"简介":1}

client = MongoClient()
db = client.uinfo
weibo = db.weibo
douban = db.douban
inList = open("243.list", "r").readlines();
print(len(inList))

matrix = {}
result = {}
match = {}

# outFile = codecs.open("72.out", "w", "utf-8")
for weiboUser in inList:
	weiboId=weiboUser[:len(weiboUser)-1]
	weiboInfo = weibo.find_one({"id":weiboId})
	matrix[weiboId]={"id":weiboId}
	result[weiboId]={}

	for doubanUser in inList:
		doubanId = doubanUser[:len(doubanUser)-1]
		doubanInfo = douban.find_one({"id":doubanId})
		matrix[weiboId][doubanId]={"id":doubanId}

		for attribute in BASIC_LIST:
			if (attribute in weiboInfo and attribute in doubanInfo):
				sw = weiboInfo[attribute].lower().replace(" ","")
				sd = doubanInfo[attribute].lower().replace(" ","")
				if attribute=="个性域名":
					if not(sw[0]=='u' or sd.isdigit()):
						matrix[weiboId][doubanId][attribute] = Levenshtein.jaro_winkler(sw,sd)
						# outFile.write("%s\t%s - %s:\t%s\t%s\t%s\t%s\n" %(weiboInfo["id"],sw,sd,Levenshtein.distance(sw,sd),Levenshtein.ratio(sw,sd),Levenshtein.jaro(sw,sd),Levenshtein.jaro_winkler(sw,sd)))
				else:
					matrix[weiboId][doubanId][attribute] = Levenshtein.jaro_winkler(sw,sd)
				
		for attribute in COUNT_LIST:
			if (attribute in weiboInfo and attribute in doubanInfo):
				sw = weiboInfo[attribute]
				sd = doubanInfo[attribute]
				if (len(sw)>0 and len(sd)>0):
					count = 0
					total = 0
					for x in sw:
						total += sw[x]
						if x in sd:
							count += min(sw[x], sd[x])
					for x in sd:
						total += sd[x]
					total -= count
					matrix[weiboId][doubanId][attribute] = count/total
					# outFile.write("%s\t%s\t%s\t%s\n" %(weiboInfo["id"],count,total,count/total))
		score = 0
		weight = 0
		for x in matrix[weiboId][doubanId]:
			if x!="id":
				score += matrix[weiboId][doubanId][x]
				weight += WEIGHT[x]
		score /= weight
		result[weiboId][doubanId]=score
					
for i in inList:
	score = 0.1
	for j in inList:
		weiboId=i[:len(i)-1]
		doubanId=j[:len(j)-1]
		if result[weiboId][doubanId] > score :
			score = result[weiboId][doubanId]
			match[weiboId] = doubanId
	# print(score)

# print(match)
for x in match:
	print("%s\t%s" %(x,match[x]))
