import codecs
import pymongo
from pymongo import MongoClient

client = MongoClient()
db = client.uinfo
douban_ori = db.douban_original
weibo_ori = db.weibo_original
douban = db.douban
weibo = db.weibo
WEIGHT={"昵称":1,"个性域名":1,"地区":1,"简介":1,"详情":1} # ,"关注":1, "粉丝":1

inList = open("2308.list", "r").readlines();
print(len(inList))

for user in inList:
	user = user[:len(user)-1]
	if (weibo_ori.count({"id":user})==1 and douban_ori.count({"id":user})==1):
		inuse = True
		winfo = weibo.find_one({"id":user})
		if not "关注" in winfo or not "粉丝" in winfo or (winfo["关注"]<5 and winfo["粉丝"]<5):
			inuse = False
		dinfo = douban.find_one({"id":user})
		if not "关注" in dinfo or not "粉丝" in dinfo or (dinfo["关注"]<5 and dinfo["粉丝"]<5):
			inuse = False
		# winfo = weibo.find_one({"id":user})
		# for weight in WEIGHT:
		# 	if not (weight in winfo) or len(winfo[weight]) == 0:
		# 		inuse = False
		# 		break
		# 	if weight=="个性域名":
		# 		if "/" in winfo[weight]:
		# 			inuse = False
		# 			break
		# dinfo = douban.find_one({"id":user})
		# for weight in WEIGHT:
		# 	if not (weight in dinfo) or len(dinfo[weight]) == 0:
		# 		inuse = False
		# 		break
		# 	if weight=="个性域名":
		# 		default = True
		# 		for x in dinfo[weight]:
		# 			if not (x in "0123456789"):
		# 				default = False
		# 				break
		# 		if default==True:
		# 			inuse = False
		# 			break
		if inuse == True:
			print(user)

