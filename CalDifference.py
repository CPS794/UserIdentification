# -*- coding: utf-8 -*-

import codecs
import pymongo
from pymongo import MongoClient
from geopy.distance import vincenty
import Levenshtein
import numpy as np
from sklearn import svm


BASIC_LIST=["地区", "个性域名", "昵称"]
COUNT_LIST=["详情", "简介"]
WEIGHT={"昵称":10,"个性域名":7,"地区":5,"详情":2,"简介":1}# 

client = MongoClient()
db = client.uinfo
weibo = db.weibo
douban = db.douban
geocode = db.geocode
inList = open("72.list", "r").readlines()
print(len(inList))
userList = []
userId = {}
winfo = []
dinfo = []
matrix = {}
result = {}
match = {}
geoList = {}

for user in inList:
	userList.append(user[:len(user)-1])
	userId[user[:len(user)-1]] = len(userList)-1

for user in userList:
	winfo.append(weibo.find_one({"id":user}))
	dinfo.append(douban.find_one({"id":user}))

for geo in geocode.find({},{"_id":0}):
	geoList[geo['name']]=geo['detail'][0]['geometry']['location']
# print(geoList)

N=(0,89.5)
S=(0,-89.5)
MAX_DISTANCE = vincenty(N, S).miles
# print(MAX_DISTANCE)

# outFile = codecs.open("72.out", "w", "utf-8")
for wid in range(len(userList)):
	weiboId=userList[wid]
	weiboInfo = winfo[wid]
	matrix[weiboId]={"id":weiboId}
	result[weiboId]={}

	for did in range(len(userList)):
		doubanId = userList[did]
		doubanInfo = dinfo[did]
		matrix[weiboId][doubanId]={"id":doubanId}

		for attribute in BASIC_LIST:
			if (attribute in weiboInfo and attribute in doubanInfo):
				sw = weiboInfo[attribute].lower().replace(" ","")
				sd = doubanInfo[attribute].lower().replace(" ","")
				if attribute=="个性域名":
					if not(sw[0]=='u' or sd.isdigit()):
						matrix[weiboId][doubanId][attribute] = Levenshtein.jaro_winkler(sw,sd)
						# outFile.write("%s\t%s - %s:\t%s\t%s\t%s\t%s\n" %(weiboInfo["id"],sw,sd,Levenshtein.distance(sw,sd),Levenshtein.ratio(sw,sd),Levenshtein.jaro(sw,sd),Levenshtein.jaro_winkler(sw,sd)))
				elif attribute=="地区":
					sw=sw.replace("海外","").replace("其他","")
					sd=sd.replace("海外","").replace("其他","")
					if (len(sw)>0 and len(sd)>0):
						weiboLocation = (geoList[sw]['lat'], geoList[sw]['lng'])
						doubanLocation = (geoList[sd]['lat'], geoList[sd]['lng'])
						distance = vincenty(weiboLocation, doubanLocation).miles
						matrix[weiboId][doubanId][attribute] = (1 - distance / MAX_DISTANCE) ** 500
						# if (wid==did):
						# 	print("%s\t%s - %s:\t%s\t%s" %(weiboInfo["id"],sw,sd,distance,matrix[weiboId][doubanId][attribute]))
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
			if x!="id" and x in WEIGHT:
				score += matrix[weiboId][doubanId][x]
				weight += WEIGHT[x]
		score /= weight
		result[weiboId][doubanId]=score
					
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
				row.append(-1.0)
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
clf = svm.SVC(gamma=0.001, C=1000000.)
clf.fit(data[:n], target[:n]) 
ans = clf.predict(data[n:])
output = list(ans)
outFile = codecs.open("72.out", "w", "utf-8")
m=len(userList)
i=0
j=0
cnt=0
for x in output:
	if (x==1):
		# outFile.write("%s %s %s" %(i,j,k))
		if (i==k+j):
			cnt+=1
			outFile.write("%s " %(i))
		else:
			outFile.write("%s " %(-1))			
	i+=1
	# outFile.write("%s " %(x))
	if (i==m):
		outFile.write("\n")
		j+=1
		i=0
# outFile.write("Count:%s\n" %(cnt))
# outFile.write("Total:%s\n" %(j))
print("Count: %s" %(cnt))
print("Total: %s" %(j))
