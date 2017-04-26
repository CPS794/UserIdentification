# -*- coding: utf-8 -*-

import codecs
import pymongo
from pymongo import MongoClient
import jieba
import jieba.posseg as pseg

REMOVE_LIST=['x','u','p','c']
REMOVE_KEY_LIST=['.']
IGNORE_LIST=["_id","认证"]
RESERVED_LIST=["id", "昵称", "地区", "个性域名", "头像"]
WORD_COUNT_LIST=["简介", "个性签名"]
RESERVED_COUNT_LIST=["学习工作"]

def wordCount(info):
	for x in REMOVE_KEY_LIST:
		info = info.replace(x, " ")
	count = {}
	words = pseg.cut(info)
	for w in words:
		if not(w.flag[0] in REMOVE_LIST):
			if w.word in count:
				count[w.word] += 1
			else:
				count[w.word] = 1
	return count

def mergeInto(mapTo, mapFrom):
	for f in mapFrom:
		if f in mapTo:
			mapTo[f] += mapFrom[f]
		else:
			mapTo[f] = mapFrom[f]
	return mapTo
	
def count(info):
	if isinstance(info, int):
		return wordCount(str(info))
	elif isinstance(info, str):
		return wordCount(info)
	elif isinstance(info, list):
		result = {}
		for x in info:
			mergeInto(result, wordCount(x))
		return result
	else:
		result = {}
		for x in info:
			mergeInto(result, wordCount(info[x]))
		return result

def extract(userInfo):
	newInfo = {}
	detail = {}
	for info in userInfo:
		if not(info in IGNORE_LIST):
			if info in RESERVED_LIST:
				if info == "地区":
					newInfo[info] = userInfo[info].replace("海外","").replace("其他","")
				elif info == "个性域名":
					if not ("/" in userInfo[info]):
						newInfo[info] = userInfo[info]
				else:
					newInfo[info] = userInfo[info]
			elif info in WORD_COUNT_LIST:
				newInfo[info] = count(userInfo[info])
				detail = mergeInto(detail, newInfo[info])
			elif info in RESERVED_COUNT_LIST:
				newInfo[info] = userInfo[info]
				detail = mergeInto(detail, count(userInfo[info]))
			else:
				detail = mergeInto(detail, count(userInfo[info]))
	newInfo["详情"] = detail
	return newInfo

client = MongoClient()
db = client.uinfo
weibo_ori = db.weibo_original
weibo_new = db.weibo
douban_ori = db.douban_original
douban_new = db.douban

inList = open("2308.list", "r").readlines();
print(len(inList))

for inFileName in inList:
	# Deal with Weibo
	userInfo = extract(weibo_ori.find_one({"id":inFileName[:len(inFileName)-1]}))
	weibo_new.insert_one(userInfo)
	# print(userInfo)

	# Deal with Douban
	userInfo = extract(douban_ori.find_one({"id":inFileName[:len(inFileName)-1]}))
	douban_new.insert_one(userInfo)
	# print(userInfo)
	

				

