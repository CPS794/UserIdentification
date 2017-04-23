# -*- coding: utf-8 -*-

import codecs
import json
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
from sklearn.neighbors.nearest_centroid import NearestCentroid

fname = "72"
inFile = fname + ".list"
outFile = fname + ".out"

BASIC_LIST=["地区", "个性域名", "昵称"]
COUNT_LIST=["详情", "简介"]
WEIGHT={"昵称":1,"个性域名":1,"地区":1,"简介":1,"详情":1} # ,"关注":1, "粉丝":1

userList = []
userId = {}
matrix = {}
result = {}

def load(inFile,saveObject):
	inList = open(inFile, "r").readlines()
	i = 0
	for x in saveObject:
		x = json.loads(inList[i])
		i += 1

# 从文件中读入待比对的用户列表
inList = open(inFile, "r").readlines()
print(len(inList))
for user in inList:
	userList.append(user[:len(user)-1])
	userId[user[:len(user)-1]] = len(userList)-1

inList = open(outFile, "r").readlines()
matrix = json.loads(inList[0])
result = json.loads(inList[1])
# exit()

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
# clf = DecisionTreeClassifier()
# clf = ExtraTreeClassifier()
clf = NearestCentroid()
clf.fit(data[:n], target[:n]) 
ans = clf.predict(data[n:])
output = list(ans)
outList = codecs.open("temp.out", "w", "utf-8")
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
