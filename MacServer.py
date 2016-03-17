# coding: utf-8
import requests
import json
import os
import re
import pickle
from urllib import quote
from markdown2 import markdown
from string import Template

web_intro = '''
		<html>
		<head>
		<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
		<title>The System</title>
		<style>
		* {
			font-size: 14px;
			font-family: "PingFang HK", sans-serif;
			color: #6f4f2c;
			-webkit-text-size-adjust: none;
			-webkit-tap-highlight-color: transparent;
		}
		h1 {
			font-size: larger;
		}
		h3 {
			font-style: italic;
		}
		h4 {
			font-weight: normal;
			font-style: italic;
		}
		code {
			font-family: monospace;
		}
		li {
			margin: .4em 0;
		}
		body {
			#line-height: 1;
			background: #fff7ee;
		}
		div.item {
			box-shadow: 5px 5px 5px #6f4f2c;
			margin: 10px 0px;
			padding: 10px;
		}
		div.highlight {
			border: 1px solid #6f4f2c;
			background: white;
		}
		</style>
		</head>
		<body>
			<div id="content">
'''
	
htmlOutro = '''
			</div>
		</body>
		</html>
'''

def get_content(key):

	cookie_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reminder_cookies.pickle')
	
	def get_cookies_from_file():
		cookies = None
		if os.path.exists(cookie_filename):
			with open(cookie_filename) as file_in:
				cookies = pickle.load(file_in)
		return cookies
		
	def save_cookies_to_file(cookies):
		with open(cookie_filename, "w") as file_out:
			pickle.dump(cookies, file_out)
			
	cookies = get_cookies_from_file()
	
	ws_url = 'https://p23-remindersws.icloud.com:443'
	dsid = '402169561'
	
	headers = {
		'Origin': 'https://www.icloud.com'
	}
	body = {
		'apple_id': 'mikael.honkala@iki.fi',
		'password': 'Dr0sd0n?!'
	}
	
	def create_session():
		resp = requests.request('POST', 'https://setup.icloud.com/setup/ws/1/login', verify = True, headers = headers, data = json.dumps(body))
		cookies = resp.cookies
		save_cookies_to_file(cookies)
		content = resp.json()
		#print json.dumps(content, indent=2, sort_keys=True)
		ws_url = content['webservices']['reminders']['url']
		dsid = content['dsInfo']['dsid']
		return cookies
	
	if not cookies:
		cookies =vcreate_session()
	
	params = {
		'usertz': 'EET',
		'lang': 'FI',
		'dsid': dsid
	}
	
	'''
	body = {
		'guid': 'E394001B-8F24-4ABA-A3EC-7E8BE399716D',
		'pGuid': 'CD8E4BFB-723C-4EA1-B410-D1683351032C'
	}
	'''
	
	#resp = requests.request('GET', ws_url + '/rd/startup', params = params, verify = True, headers = headers, cookies = cookies)
	
	resp = requests.request('GET', ws_url + '/rd/reminders/CD8E4BFB-723C-4EA1-B410-D1683351032C', params = params, verify = True, headers = headers, cookies = cookies)
	
	content = resp.json()
	
	if 'status' in content and content['status'] == 421:
		cookies = create_session()
		
		resp = requests.request('GET', ws_url + '/rd/reminders/CD8E4BFB-723C-4EA1-B410-D1683351032C', params = params, verify = True, headers = headers, cookies = cookies)
	
		content = resp.json()
	
	#print json.dumps(content, indent=2, sort_keys=True)
	
	contents_by_key = {}
	contents = []
	
	for item in content['Reminders']:
		if item['title'] == key:
			contents.append(item['description'])
		contents_by_key[item['title']] = item['description']
		
	markd = contents_by_key[key]
	seen = {}
	children = []
	link_regexp = re.compile(r'\[([^\]]*)\]\(awz-([^)]+)\)')
	matches = link_regexp.findall(markd)
	for item in matches:
		key1 = item[1]
		if not key1 in seen:
			children.append(key1)
			seen[key1] = item[0]
	
	for child_key in children:
		contents.append(contents_by_key[child_key])
		
	result = ''
	
	for index, md in enumerate(contents):
		highlight_class = ''
		if index == 0:
			highlight_class = ' highlight'
		result += '<div class = "item' + highlight_class + '">\n'
		result += markdown(md)
		result += '\n</div>\n'
		
	result = web_intro + result + htmlOutro
	
	return result

print get_content('e0c4ff77')