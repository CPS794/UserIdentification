# -*- coding: utf-8 -*-

import codecs
import json
import pymongo
from pymongo import MongoClient
from geopy.distance import vincenty
import Levenshtein
import numpy as np
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import GaussianNB
from sklearn.naive_bayes import MultinomialNB
from sklearn.naive_bayes import BernoulliNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import ExtraTreeClassifier

fname = "1301"
inFile = fname + ".list"
outFile = fname + ".out"

BASIC_LIST=["地区", "个性域名", "昵称"]
COUNT_LIST=["详情", "简介"]
WEIGHT={"昵称":1,"个性域名":1,"地区":1,"简介":1,"详情":1,"关注":0, "粉丝":0} # 

userList = []
userId = {}
winfo = []
dinfo = []
geoList = {}
simIntro = []
simDetail = []
maxFriendsWeibo = 0
maxFriendsDouban = 0
maxFansWeibo = 0
maxFansDouban = 0

# 数据读入及预处理
def init():
	global maxFriendsWeibo, maxFriendsDouban, maxFansWeibo, maxFansDouban
	# 连数据库 MongoDB
	client = MongoClient()
	db = client.uinfo
	weibo = db.weibo
	douban = db.douban
	geocode = db.geocode

	# 从文件中读入待比对的用户列表
	inList = open(inFile, "r").readlines()
	print(len(inList))

	for user in inList:
		userList.append(user[:len(user)-1])
		userId[user[:len(user)-1]] = len(userList)-1

	# 从数据库中读取用户信息
	for user in userList:
		winfo.append(weibo.find_one({"id":user}))
		dinfo.append(douban.find_one({"id":user}))

	# 初始化粉丝数和关注数的最大值
	for wid in range(len(userList)):
		info = winfo[wid]
		if ("关注" in info):
			maxFriendsWeibo = max(maxFriendsWeibo,info["关注"])
		else:
			winfo[wid]["关注"]=0
		if ("粉丝" in info):
			maxFansWeibo = max(maxFansWeibo,info["粉丝"])
		else:
			winfo[wid]["粉丝"]=0
	for did in range(len(userList)):
		info = dinfo[did]
		if ("关注" in info):
			maxFriendsDouban = max(maxFriendsDouban,info["关注"])
		else:
			dinfo[did]["关注"]=0
		if ("粉丝" in info):
			maxFansDouban = max(maxFansDouban,info["粉丝"])
		else:
			dinfo[did]["粉丝"]=0
	# print("Weibo Friends: %s" %(maxFriendsWeibo))
	# print("Weibo Fans: %s" %(maxFansWeibo))
	# print("Douban Friends: %s" %(maxFriendsDouban))
	# print("Douban Fans: %s" %(maxFansDouban))

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
			
			if ("关注" in weiboInfo and "关注" in doubanInfo):
				sw = weiboInfo["关注"]
				sd = doubanInfo["关注"]
				matrix[weiboId][doubanId]["关注"] = sw/maxFriendsWeibo - sd/maxFriendsDouban			
			
			if ("粉丝" in weiboInfo and "粉丝" in doubanInfo):
				sw = weiboInfo["粉丝"]
				sd = doubanInfo["粉丝"]
				matrix[weiboId][doubanId]["粉丝"] = sw/maxFansWeibo - sd/maxFansDouban

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
						# outList.write("%s\t%s\t%s\t%s\n" %(weiboInfo["id"],count,total,count/total))
			'''

			score = 0
			weight = 0
			for x in matrix[weiboId][doubanId]:
				if x!="id" and x in WEIGHT: #  and x!="个性域名"
					score += abs(matrix[weiboId][doubanId][x]) * WEIGHT[x]
					weight += WEIGHT[x]
			# tmpScore = score / weight
			# if not "个性域名" in matrix[weiboId][doubanId] or matrix[weiboId][doubanId]["个性域名"] < tmpScore:
			# 	matrix[weiboId][doubanId]["个性域名"] = tmpScore
			# score += matrix[weiboId][doubanId]["个性域名"] * WEIGHT["个性域名"]
			# weight += WEIGHT["个性域名"]
			score /= weight
			
			result[weiboId][doubanId]=score

def save(outFile,saveObject):
	out = codecs.open(outFile, "w", "utf-8")
	for x in saveObject:
		out.write(json.dumps(x))
		out.write("\n")

init()

# for wid in range(len(userList)):
# 	if "头像" in winfo[wid] and "头像" in dinfo[wid]:
# 		print("%s\t%s\t%s" %(userList[wid],winfo[wid]["头像"],dinfo[wid]["头像"]))
# 	else:
# 		print("%s\t头像缺失" %(userList[wid]))
# for wid in range(len(userList)):
# 	if ("关注" in winfo[wid] and "关注" in dinfo[wid]):
# 		print("%s\t%s\t%s\t%s\t%s" %(userList[wid],winfo[wid]["关注"]/maxFriendsWeibo,winfo[wid]["粉丝"]/maxFansWeibo,dinfo[wid]["关注"]/maxFriendsWeibo,dinfo[wid]["粉丝"]/maxFansWeibo))
print("maxFriendsWeibo: %s" %(maxFriendsWeibo))
print("maxFriendsDouban: %s" %(maxFriendsDouban))
print("maxFansWeibo: %s" %(maxFansWeibo))
print("maxFansDouban: %s" %(maxFansDouban))

sim()
# outF = codecs.open(outFile, "w", "utf-8")
# for wid in range(len(userList)):
# 	for weight in WEIGHT:
# 		if weight in matrix[userList[wid]][userList[wid]]:
# 			outF.write("%s\t" %(abs(matrix[userList[wid]][userList[wid]][weight])))
# 		else:
# 			outF.write("-1\t")
# 	outF.write("%s\t" %(result[userList[wid]][userList[wid]]))
# 	outF.write("%s\t%s\t%s\t%s\n" %(winfo[wid]["关注"],winfo[wid]["粉丝"],dinfo[wid]["关注"],dinfo[wid]["粉丝"]))
# 	# outF.write("\n")
save(outFile,[matrix,result])
exit()

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
				row.append(-1) # result[weiboId][doubanId]
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
# clf = svm.SVC(gamma=0.002, C=1000000.)
# clf = GaussianNB([(len(userList)-1)/len(userList),1/len(userList)])
clf = DecisionTreeClassifier()
# clf = ExtraTreeClassifier()
clf.fit(data[:n], target[:n]) 
ans = clf.predict(data[n:])
output = list(ans)
outList = codecs.open("72.out", "w", "utf-8")
m=len(userList)
i=0
j=0
cnt=0
cot=0
for x in output:
	if (x==1):
		# outList.write("%s %s %s" %(i,j,k))
		if (i==k+j):
			cnt+=1
			outList.write("%s " %(i))
		else:
			outList.write("%s " %(-1))
			cot+=1		
	i+=1
	# outList.write("%s " %(x))
	if (i==m):
		outList.write("\n")
		j+=1
		i=0
# outList.write("Count:%s\n" %(cnt))
# outList.write("Total:%s\n" %(j))
print("Count: %s" %(cnt))
print("Error: %s" %(cot))
print("Total: %s" %(j))
