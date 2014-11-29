#!/usr/bin/python
# -*- coding: utf8 -*-
"""
This utility allows you to publish your pelican articles to Diaspora*.
For now, it's only bare, rough and WIP project. This is a first shot
before writting a real Pelican plugin in order to publish directly
from pelican to diaspora*.
This tiny piece of software is a PoC more than a real tool.

License : GPLv3 <URL:http://www.gnu.org/licenses/quick-guide-gplv3.html>
"""
from diaspy import *
import argparse
import os, os.path
import sys,string
SITE_URL="https://home.tuxfarm.org/blog/"
PUBLISHEDFILENAME = "published.txt";

parser = argparse.ArgumentParser(description="Processes Pelican Markdown article to publish them to Diaspora*")
parser.add_argument('-v',nargs='?',help='Verbose output')
parser.add_argument('-d',required=True,dest="pod",help="Diaspora* pod")
parser.add_argument('-u',required=True,dest="user",help="Diaspora* username")
parser.add_argument('-p',required=True,dest="pwd",help="Diaspora* password")
parser.add_argument('-c',nargs='*',dest="categories",help="Categories filter")
parser.add_argument('directory', nargs="?", help="Pelican \"root\" directory", default='../blog/')
args = parser.parse_args()

#Diaspora connection
c = connection.Connection(pod      = args.pod,
						  username = args.user,
						  password = args.pwd)
token = c.login()
flux = streams.Stream(c)

# Already published articles
published = []

# This is a bookmark file to keep record of what we already published
try:
	with open(PUBLISHEDFILENAME) as alreadypub :
		for fn in alreadypub:
			published.append(fn[:-1])
		alreadypub.close()
except:
	pass

#TODO: Use the scan directory to directly autoconfigure url with SITE_URL from pelican conf
configfile = os.path.join(args.directory,"pelicanconf.py")
sys.path.append(args.directory)
#pconf = __import__(os.path.basename(args.directory))
#print pelicanconf.SITE_URL

# Actually published this round
inpub = []
# Scan articles in content directory
for root,dirs, files in os.walk(os.path.join(args.directory,"content")):
	for f in files:
		#ensure this is markdown extension
		if f[-3:]==".md":
			#ensure it is not previously published
			if not f in published:
				mdfilename = os.path.join(root,f)
				with open(mdfilename,"r") as fmd:
					starttext = False
					text = ""
					tags=[]
					webpage = ""
					cat = ""
					# Start a kind of header mapping
					# Use Category as filter if defined in command line
					# Rebuild Web URL
					# Get Tags
					# Get Text
					for l in fmd:					
						if not starttext :
							if l.startswith('Category:'):
								cat = l[len('Category:'):].strip()
							if l.startswith('Tags:'):
								tags = map(lambda a: "#%s"%a.strip(), l[len('Tags:'):].strip().split(","))
							if l.startswith('Slug:'):
								webpage = "%s%s.html"%(SITE_URL,l[len('Slug:'):].strip())
							if l.startswith('Summary:'):
								starttext = True
								text = l[len('Summary:'):].strip()
						else:
							text = text + l
					# publish if no category was given in command line or
					# an article matching selected categories
					if not(args.categories) or (cat in args.categories):
						# Add only if published
						inpub.append(f)
						print "Post article ",f,"\n\tTags : ",string.join(tags,", "),"\n\tCategory :",cat,"\n\tweb :",webpage
						text = text + "\n\nTags : "+string.join(tags,", ")+"\n\nURL : "+webpage
						#print text
						flux.post(text=text)
			else:
				print "Already published ",f
# Regenerate record of what we published
with open(PUBLISHEDFILENAME,"w") as pubfiles :	
	for fn in published+inpub:
		pubfiles.write("%s\n"%fn)
	pubfiles.close()
