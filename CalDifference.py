# -*- coding: utf-8 -*-

import codecs
import pymongo
from pymongo import MongoClient
from geopy.distance import vincenty
import Levenshtein
import numpy as np
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity

BASIC_LIST=["地区", "个性域名", "昵称"]
COUNT_LIST=["详情", "简介"]
WEIGHT={"昵称":7,"个性域名":5,"地区":4,"简介":3,"详情":2} # 

userList = []
userId = {}
winfo = []
dinfo = []
geoList = {}
simIntro = []
simDetail = []

# 数据读入及预处理
def init():
	# 连数据库 MongoDB
	client = MongoClient()
	db = client.uinfo
	weibo = db.weibo
	douban = db.douban
	geocode = db.geocode

	# 从文件中读入待比对的用户列表
	inList = open("72.list", "r").readlines()
	print(len(inList))

	for user in inList:
		userList.append(user[:len(user)-1])
		userId[user[:len(user)-1]] = len(userList)-1

	# 从数据库中读取用户信息
	for user in userList:
		winfo.append(weibo.find_one({"id":user}))
		dinfo.append(douban.find_one({"id":user}))

	# 初始化地理位置信息
	for geo in geocode.find({},{"_id":0}):
		geoList[geo['name']]=geo['detail'][0]['geometry']['location']

	# 初始化语料库
	corpusIntro = []
	corpusDetail = []

	for wid in range(len(userList)):
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

	for did in range(len(userList)):
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

	for wid in range(len(userList)):
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

	for did in range(len(userList)):
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
		simIntro.append(cosine_similarity(row, tfidfIntro).tolist()[0][len(inList):])
		cnt+=1;
		if (cnt>=len(inList)):
			break

	cnt=0
	for row in tfidfDetail:
		simDetail.append(cosine_similarity(row, tfidfDetail).tolist()[0][len(inList):])
		cnt+=1;
		if (cnt>=len(inList)):
			break

matrix = {}
result = {}

# 计算各项属性的相似度
def sim():

	N=(0,89.5)
	S=(0,-89.5)
	MAX_DISTANCE = vincenty(N, S).miles

	for wid in range(len(userList)):
		weiboId=userList[wid]
		weiboInfo = winfo[wid]
		matrix[weiboId]={"id":weiboId}
		result[weiboId]={}

		for did in range(len(userList)):
			doubanId = userList[did]
			doubanInfo = dinfo[did]
			matrix[weiboId][doubanId]={"id":doubanId}

			if ("昵称" in weiboInfo and "昵称" in doubanInfo):
				sw = weiboInfo["昵称"].lower().replace(" ","")
				sd = doubanInfo["昵称"].lower().replace(" ","")
				matrix[weiboId][doubanId]["昵称"] = Levenshtein.jaro_winkler(sw,sd)
				if (matrix[weiboId][doubanId]["昵称"] == 0): 
					matrix[weiboId][doubanId]["昵称"] = min(Levenshtein.ratio(sw,sd),0.5)

			if ("个性域名" in weiboInfo and "个性域名" in doubanInfo):
				sw = weiboInfo["个性域名"].lower().replace(" ","")
				sd = doubanInfo["个性域名"].lower().replace(" ","")
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
			
			'''	
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
			'''

			score = 0
			weight = 0
			for x in matrix[weiboId][doubanId]:
				if x!="id" and x!="个性域名" and x in WEIGHT: # 
					score += matrix[weiboId][doubanId][x] * WEIGHT[x]
					weight += WEIGHT[x]
			tmpScore = score / weight
			if not "个性域名" in matrix[weiboId][doubanId] or matrix[weiboId][doubanId]["个性域名"] < tmpScore:
				matrix[weiboId][doubanId]["个性域名"] = tmpScore
			score += matrix[weiboId][doubanId]["个性域名"] * WEIGHT["个性域名"]
			weight += WEIGHT["个性域名"]
			score /= weight
			
			result[weiboId][doubanId]=score
	
init()

# for wid in range(len(userList)):
# 	if "头像" in winfo[wid] and "头像" in dinfo[wid]:
# 		print("%s\t%s\t%s" %(userList[wid],winfo[wid]["头像"],dinfo[wid]["头像"]))
# 	else:
# 		print("%s\t头像缺失" %(userList[wid]))
# exit()

sim()

match = {}
					
for weiboId in userList:
	score = 0
	for doubanId in userList:
		if result[weiboId][doubanId] > score :
			score = result[weiboId][doubanId]
			match[weiboId] = doubanId
	# print(score)

# print(match)
count = 0
for x in match:
	# print("%s\t%s" %(x,match[x]))
	if x==match[x]:
		count += 1
	# else:
	# 	print("%s\t%s\t%s\t%s\t%s\t%s\t" %(x,match[x],result[x][x],result[x][match[x]],matrix[x][x]["昵称"],matrix[x][match[x]]["昵称"]))
		# print(matrix[x][x],matrix[x][match[x]])
	
print(count)

tempMatrix = []
tagMatrix = []
for wid in range(len(userList)):
	weiboId=userList[wid]
	for did in range(len(userList)):
		doubanId=userList[did]
		row = [] 
		for weight in WEIGHT:
			if (weight in matrix[weiboId][doubanId]):
				row.append(matrix[weiboId][doubanId][weight])
			else:
				row.append(result[weiboId][doubanId])
		tempMatrix.append(row)
		if (did==wid): 
			tagMatrix.append(1)
		else:
			tagMatrix.append(0)
# print(tempMatrix)			
data = np.array(tempMatrix)
target = np.array(tagMatrix)
# print(data)
# print(target)

k=int(len(userList)/2)
n=k*len(userList)
clf = svm.SVC(gamma=0.01, C=1000000.)
clf.fit(data[:n], target[:n]) 
ans = clf.predict(data[n:])
output = list(ans)
outFile = codecs.open("72.out", "w", "utf-8")
m=len(userList)
i=0
j=0
cnt=0
cot=0
for x in output:
	if (x==1):
		# outFile.write("%s %s %s" %(i,j,k))
		if (i==k+j):
			cnt+=1
			outFile.write("%s " %(i))
		else:
			outFile.write("%s " %(-1))
			cot+=1		
	i+=1
	# outFile.write("%s " %(x))
	if (i==m):
		outFile.write("\n")
		j+=1
		i=0
# outFile.write("Count:%s\n" %(cnt))
# outFile.write("Total:%s\n" %(j))
print("Count: %s" %(cnt))
print("Error: %s" %(cot))
print("Total: %s" %(j))
