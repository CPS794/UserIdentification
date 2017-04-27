# -*- coding: utf-8 -*-

import codecs
import json
import SaveAndLoad
import Const

# WEIGHT={"昵称":7,"个性域名":5,"地区":3,"简介":2,"详情":1}
# WEIGHT={"昵称":1,"个性域名":1,"地区":1,"简介":1,"详情":1}
# WEIGHT={'昵称': 15.501474532434486, '个性域名': 1.848183474922682, '地区': 6.566005489302448, '简介': 38.0179142042232, '详情': 22.61778696771042}
# WEIGHT={'昵称': 8.998136053471097, '个性域名': 1.3271057530957364, '地区': 5.0409826052652305, '简介': 4.999145713899801, '详情': 2.4508710588251486}

def precalWeight():
	global weight
	global aveSelf
	global aveOthers
	weight = {"昵称":1,"个性域名":1,"地区":1,"简介":1,"详情":1}
	aveSelf = {"昵称":{"total":0.0,"count":0}, "个性域名":{"total":0.0,"count":0}, "地区":{"total":0.0,"count":0}, "简介":{"total":0.0,"count":0}, "详情":{"total":0.0,"count":0}} 
	aveOthers = {"昵称":{"total":0.0,"count":0}, "个性域名":{"total":0.0,"count":0}, "地区":{"total":0.0,"count":0}, "简介":{"total":0.0,"count":0}, "详情":{"total":0.0,"count":0}} 
	for user in matrix:
		difference = matrix[user]
		for target in difference:
			if target != "id":
				for attribute in weight:
					if target == user and attribute in difference[target]:
						aveSelf[attribute]["total"] += difference[target][attribute]
						aveSelf[attribute]["count"] += 1
					elif attribute in difference[target]:
						aveOthers[attribute]["total"] += difference[target][attribute]
						aveOthers[attribute]["count"] += 1

def calWeight(exponent):
	global weight
	global WEIGHT
	# print(aveSelf)
	# print(aveOthers)
	for attribute in weight:
		if aveSelf[attribute]["count"] == 0:
			weight[attribute] = 0
		elif aveOthers[attribute]["count"] == 0 or aveOthers[attribute]["total"] == 0:
			weight[attribute] = 100 ** exponent
		else:
			weight[attribute] = (aveSelf[attribute]["total"] / aveSelf[attribute]["count"]) ** exponent / (aveOthers[attribute]["total"] / aveOthers[attribute]["count"])
	WEIGHT = weight
	# print("exponent: %.3f" %(exponent))
	# print(weight)

def calScore():
	global result
	for wid in range(len(userList)):
		weiboId=userList[wid]
		result[weiboId]={}
		for did in range(len(userList)):
			doubanId = userList[did]
			score = 0
			weight = 0
			for x in matrix[weiboId][doubanId]:
				if x!="id" and x in WEIGHT:
					score += abs(matrix[weiboId][doubanId][x]) * WEIGHT[x]
					weight += WEIGHT[x]
			result[weiboId][doubanId] = score / weight

def matchUser(threshold):
	global match
	for weiboId in userList:
		score = threshold
		for doubanId in userList:
			if result[weiboId][doubanId] > score :
				score = result[weiboId][doubanId]
				match[weiboId] = doubanId

def calMatch(threshold):
	global result,match
	if threshold == 0:
		result = {}
		calScore()
	# else:
	# 	print("Threshold: %.3f" %(threshold))
	# print(result)

	match = {}
	matchUser(threshold)
	# print(match)

	count = 0
	error = 0
	for x in match:
		if x==match[x]:
			count += 1
		else:
			error += 1
						
	# print("accuracy: %s / %s = %.3f" %(count,len(userList),count/len(userList)))
	# f1-score = 2 * precision * recall / (precision + recall)
	if count + error == 0 :
		# print("Match Failed！")
		return 0
	else:
		precision = count / (count + error)
		recall = count / len(userList)
		f1_score = 2 * precision * recall / (precision + recall)
		# print("Precision: %s / %s = %.3f" %(count, count + error, precision))
		# print("Recall: %s / %s = %.3f" %(count, len(userList), recall))
		# print("F1-score: %.3f" %(f1_score))
		# print()
		return f1_score

def trisectionWeight(l,r):
	precalWeight()
	if r-l < 0.001 :
		return (l+r)/2
	calWeight(l)
	scoreL = calMatch(0)
	calWeight(r)
	scoreR = calMatch(0)
	for x in range(30):
		ml = l + (r - l) * 1 / 3
		mr = l + (r - l) * 2 / 3
		calWeight(ml)
		scoreML = calMatch(0)
		calWeight(mr)
		scoreMR = calMatch(0)
		if scoreML<scoreMR:
			l = ml
			scoreL = scoreML
		elif scoreML==scoreMR:
			if scoreL < scoreR:
				l = ml
				scoreL = scoreML
			else:
				r = mr
				scoreR = scoreMR
		else:
			r = mr
			scoreR = scoreMR
	return (ml+mr)/2

def trisectionThreshold(l,r):
	if r-l < 0.001 :
		return (l+r)/2
	scoreL = calMatch(l)
	scoreR = calMatch(r)
	for x in range(30):
		ml = l + (r - l) * 1 / 3
		mr = l + (r - l) * 2 / 3
		scoreML = calMatch(ml)
		scoreMR = calMatch(mr)
		if scoreML<scoreMR:
			l = ml
			scoreL = scoreML
		elif scoreML==scoreMR:
			if scoreL < scoreR:
				l = ml
				scoreL = scoreML
			else:
				r = mr
				scoreR = scoreMR
		else:
			r = mr
			scoreR = scoreMR
	return (ml+mr)/2

def calculateThreshold():
	global userList, userId, result, match, parameter
	userList = []
	userId = {}
	for user in matrix:
		userId[user]=len(userList)
		userList.append(user)
	result ={}
	match ={}
	parameter["exponent"] = trisectionWeight(0,5)
	parameter["threshold"] = trisectionThreshold(0,1)
	print(parameter)

matrix = {}
userList = []
userId = {}
result ={}
match ={}
aveSelf ={}
aveOthers ={}
parameter = {}

if __name__ == "__main__":
	for x in range(Const.NUMBER_OF_TEST):
		fname = Const.PATH + Const.FILE_NAME + "/" + Const.FILE_NAME + "_" + str(x)

		[matrix] = SaveAndLoad.load(fname + "_S_matrix"+".out", 1)
		calculateThreshold()
		SaveAndLoad.save(fname + "_S_score"+".mul-out", [result, parameter, weight])

		[matrix] = SaveAndLoad.load(fname + "_T_matrix"+".out", 1)
		calculateThreshold()
		SaveAndLoad.save(fname + "_T_score"+".mul-out", [result, parameter, weight])
