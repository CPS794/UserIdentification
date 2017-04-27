import codecs
import pymongo
from pymongo import MongoClient

client = MongoClient()
db = client.uinfo
douban_ori = db.douban_original
weibo_ori = db.weibo_original

inList = open("2308.list", "r").readlines();
print(len(inList))

for user in inList:
	user = user[:len(user)-1]
	if (weibo_ori.count({"id":user})==1 and douban_ori.count({"id":user})==1):
		inuse = True
		
		winfo = weibo_ori.find_one({"id":user})
		if not "关注" in winfo or not "粉丝" in winfo or (winfo["关注"]<5 and winfo["粉丝"]<5):
			inuse = False
		dinfo = douban_ori.find_one({"id":user})
		if not "关注" in dinfo or not "粉丝" in dinfo or (dinfo["关注"]<5 and dinfo["粉丝"]<5):
			inuse = False

		if inuse == True:
			print(user)

