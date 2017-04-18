# -*- coding: utf-8 -*-

import codecs
import pymongo
from pymongo import MongoClient

client = MongoClient()
db = client.uinfo
# collection = db.douban_original
# collection = db.weibo_original
# collection = db.douban
collection = db.weibo

inList = open("243-weibos.data", "r").readlines();
print(len(inList))

for user in inList:
	user=user.replace("\n","").split(" ")
	friends = int(user[1])
	fans = int(user[2])
	collection.update({"id":user[0]},{"$set":{"关注":friends,"粉丝":fans}})
	print(user)
