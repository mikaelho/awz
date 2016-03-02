# coding: utf-8
import ui
import json
from time import sleep
from proxy import ObjectWrapper
from objc_util import *
from markdown2 import markdown
from urllib import quote, unquote
import clipboard
import webbrowser
from string import Template
import logging

from Gestures import Gestures

# scrollViewDidEndDecelerating

class MarkdownWebView(ObjectWrapper):
	
	def __init__(self, obj):
		ObjectWrapper.__init__(self, obj)
		
		self.css = self.default_css
		self.extras = []
		self.click_func = None
		
		self.proxy_delegate = None
		
		self.scroll_pos = None
		self.font = ('Helvetica', 12)
		self.text_color = (.02, .19, .52, 1)
		self.highlight_color = (1, 1, 1, 1)
		self.alignment = None
		self.margins = (10, 10, 10, 10)
		
		self.loading_fragment = False
		
		self.link_prefix = 'pythonista-markdownview:relay?content='
		self.debug_prefix = 'pythonista-markdownview:debug?content='
		self.init_postfix = '#pythonista-markdownview-initialize'
		self.scroll_prefix = 'pythonista-markdownview:scroll?content='
		self.in_doc_prefix = None
		
		self.last_md = ''
		
		# Web fragment is used to find the right scroll position when moving from editing to viewing
		self.web_fragment = ui.WebView(flex = 'WH')
		self.web_fragment.hidden = True
		self.web_fragment.delegate = self
		self.add_subview(self.web_fragment)
		
		# Main display webview
		self.delegate = self
		
		Gestures().add_tap(self.__subject__, self.double_tap, number_of_touches_required = 2)
		
	def to_html(self, contents, highlight_index = None, caret_pos = 0, content_only = False):
		result = ''
		fragment = ''
		scroll_pos = 0
		for (index, md) in contents:
			highlight_class = ''
			if index == highlight_index:
				highlight_class = ' highlight'
				if caret_pos > 0:
					fragment = md[:caret_pos]
					#scroll_pos = self.get_scroll_pos(md, caret_pos)
			result += '<div class = "item' + highlight_class + '" id="item-' + str(index) + '">\n'
			result += markdown(md, extras=self.extras)
			result += '\n</div>\n'
		intro_template = self.htmlIntro if not content_only else self.fragmentIntro
		intro = Template(intro_template.safe_substitute(css = self.css))
		(font_name, font_size) = self.font
		result = intro.safe_substitute(
			background_color = self.to_css_rgba(self.background_color), 
			text_color = self.to_css_rgba(self.tint_color),
			highlight_color = self.to_css_rgba(self.highlight_color),
			font_family = font_name,
			text_align = self.to_css_alignment(),
			font_size = str(font_size)+'px',
			init_postfix = self.init_postfix,
			link_prefix = self.link_prefix,
			debug_prefix = self.debug_prefix,
			scroll_prefix = self.scroll_prefix,
			fragment = fragment
			#scroll_pos = scroll_pos
		) + result + self.htmlOutro
		return result
		
	def to_css_rgba(self, color):
		return 'rgba({:.0f},{:.0f},{:.0f},{})'.format(color[0]*255, color[1]*255, color[2]*255, color[3])

	alignment_mapping = { ui.ALIGN_LEFT: 'left', ui.ALIGN_CENTER: 'center', ui.ALIGN_RIGHT: 'right', ui.ALIGN_JUSTIFIED: 'justify', ui.ALIGN_NATURAL: 'start' }

	def to_css_alignment(self):
		alignment = self.alignment or ui.ALIGN_NATURAL
		return MarkdownWebView.alignment_mapping[alignment]

	'''
	def get_scroll_pos(self, md, caret_pos):
		#self.last_md = md
		#self.scroll_callback = result_callback
		
		html = self.to_html([ (0, md[:caret_pos]) ], content_only = True)
		self.synchronous_load(html)
		scroll_pos = int(self.web_fragment.eval_js('document.getElementById("content").clientHeight'))
		return scroll_pos
		'''
		#self.loading_fragment = True
		#self.web_fragment.load_html(html)
		
	def update_html(self, contents, highlight_index = None, caret_pos = 0):
		self.last_contents = contents
		html = self.to_html(contents, highlight_index, caret_pos)
		self.caret_pos = caret_pos
		self.load_html(html)
		
	'''
	def synchronous_load(self, html):
		self.loading_fragment = True
		self.web_fragment.load_html(html)
		while self.loading_fragment:
			sleep(0.05)
			'''
	'''
	def webview_did_finish_load(self, webview):
		if webview == self.web_fragment:
			self.loading_fragment = False
			#Synchronous.callback()
			'''
			
			#scroll_pos = int(webview.eval_js('document.getElementById("content").clientHeight'))
			#self.scroll_callback(self.last_contents, scroll_pos)
			
	def webview_should_start_load(self, webview, url, nav_type):
		
		#print  url
		
		if webview == self.web_fragment:
			return True
			
		# HOUSEKEEPING
		
		# Loaded by the web view at start, allow
		if url == 'about:blank':
			return True
		
		# Debug message from web page, print to console
		if url.startswith(self.debug_prefix):
			debug_text = unquote(url.replace(self.debug_prefix, ''))
			print debug_text
			return False
			
		# Scroll position update
		if url.startswith(self.scroll_prefix):
			scroll_pos = int(url.replace(self.scroll_prefix, ''))
			print scroll_pos
			return False
		
		# Custom WebView initialization message
		# Used to capture the generated page address
		if url.endswith(self.init_postfix):
			self.in_doc_prefix = url[:len(url)-len(self.init_postfix)]
			self.hidden = False
			return False
		
		# Clean the extra stuff from in-doc links
		if self.in_doc_prefix and url.startswith(self.in_doc_prefix):
			url = url[len(self.in_doc_prefix):]
		
		# START EDIT
		if url.startswith(self.link_prefix):
			(index, words) = json.loads(unquote(url.replace(self.link_prefix, '')))
			(list_index, caret_pos) = self.caret_pos_from_words(index, words)
			self.click_func(list_index, caret_pos)
			return False
		
		# REGULAR LINKS
		
		# Check for custom link handling
		if url.startswith('/awz-'):
			self.cross_link_func(url[5:])
			return False
		# Open 'http(s)' links in Safari
		# 'file' in built-in browser
		# Others like 'twitter' as OS decides
		else:
			'''
			if self.can_call('webview_should_load_external_link'):
				return self.proxy_delegate.webview_should_load_external_link(webview, url)
			'''
			if url.startswith('http:') or url.startswith('https:'):
				url = 'safari-' + url
			webbrowser.open(url)
			return False
		'''
		# Handle in-doc links within the page
		elif url.startswith('#'):
			if self.can_call('webview_should_load_internal_link'):
				return self.proxy_delegate.webview_should_load_internal_link(webview, url)
			return True
		'''
			
	def double_tap(self, data):
		call_str = 'focus_index(' + str(data.location.x) + ', ' + str(data.location.y) + ')'
		index = self.eval_js(call_str)
		if index > -1:
			self.double_click_func(index)
			
	def caret_pos_from_coords(self, coords):
		words = self.eval_js('text_up_to_point(' + str(coords.x) + ', ' + str(coords.y) + ')')
		return self.caret_pos_from_words(words)
			
	def caret_pos_from_words(self, index, words):
		word_list = words.split()
		caret_pos = 0
		md = ''
		list_index = -1
		for enum_index, item in enumerate(self.last_contents):
			if item[0] == index:
				md = item[1]
				list_index = enum_index
				break
		for word in word_list:
			caret_pos = md.find(word, caret_pos) + len(word)
		return (list_index, caret_pos)
		
	htmlIntro = Template('''
		<html>
		<head>
		<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
		<title>Markdown</title>
		<style>
			$css
		</style>
		<script type="text/javascript">
			function debug(msg) {
				var d = document.getElementById("debug");
				d.href="$debug_prefix" + msg;
				d.click();
			}
		
			function activateLinks() {
				content = document.getElementById("content");
				
				items = document.getElementsByClassName("item");
				for(var j = 0; j < items.length; j++) {
					items[j].addEventListener('click', text_position);
				}
				
				links = content.getElementsByTagName("a");
				for(var i = 0; i < links.length; i++) {
					links[i].addEventListener('click', anchor_click);
				}
			}
			
			function anchor_click() {
				var e = window.event;
				e.stopPropagation();
				return false;
			}
			
			function text_position() {
				var e = window.event;
				var t = text_up_to_point(e.currentTarget, e.clientX, e.clientY);
				var r = document.getElementById("relay");
				var data = JSON.stringify([ parseInt(e.currentTarget.id.substring(5)), t ]);
					
				r.href="$link_prefix"+encodeURIComponent(data);
				r.click();
			}
			
			function text_up_to_point(elem, x, y) {
				//var c = document.getElementById("content");
				var c = elem;
				var range = new Range();
				range.selectNodeContents(c);
				var rangeEnd = document.caretRangeFromPoint(x, y);
				range.setEnd(rangeEnd.startContainer, rangeEnd.startOffset);
				return range.toString();
			}
			
			function focus_index(x, y) {
				var elem = document.elementFromPoint(x, y);
				for ( ; elem && elem !== document; elem = elem.parentNode ) {
					if (elem.classList.contains("item")) {
						return parseInt(elem.id.substring(5));
					}
				}
				return -1;
			}
			
			function initialize() {
				var scrollPos = document.getElementById("fragment").clientHeight;
				var focusElem = document.getElementsByClassName("highlight")[0];
				var scrollTop = focusElem.offsetTop + scrollPos;
				if (scrollPos > 0) {
					var totalHeight = document.getElementById("content").clientHeight;
					var halfScreen = window.innerHeight/2;
					if ((totalHeight - scrollTop) > halfScreen) {
						scrollTop -= halfScreen;
					}
				}
				window.scrollBy(0, scrollTop);
				
				activateLinks();
				
				var r = document.getElementById("relay");
				r.href = "$init_postfix";
				r.click();
			}
			
			/**
			window.addEventListener('scroll', function(e) {
				var r = document.getElementById("relay");
				r.href = "$scroll_prefix"+window.scrollY;
				//r.href = "$scroll_prefix"+"0"
				r.click()
			});
			**/
			
		</script>
		</head>
		<body onload="initialize()">
			<a id="relay" style="display:none"></a>
			<a id="debug" style="display:none"></a>
			<div id="content">
				<div id="fragment" style="visibility:hidden;position:absolute;">$fragment</div>
	''')
	
	fragmentIntro = Template('''
		<html>
		<head>
		<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
		<style>
			$css
		</style>
		</head>
		<body>
			<div id="content">
	'''
	)
	htmlOutro = '''
			</div>
		</body>
		</html>
	'''
	default_css = '''
		* {
			font-size: $font_size;
			font-family: $font_family;
			color: $text_color;
			text-align: $text_align;
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
			background: $background_color;
		}
		div.item {
			box-shadow: 5px 5px 5px $text_color;
			margin: 10px 0px;
			padding: 10px;
		}
		div.highlight {
			border: 1px solid $text_color;
			background: $highlight_color;
		}
	'''
	
if __name__ == "__main__":
	v = MarkdownWebView(ui.WebView())
	
	import os
	readme_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.md')
	init_string = ''
	if os.path.exists(readme_filename):
		with open(readme_filename) as file_in:
			init_string = file_in.read()
			
	def click_func(index, caret_pos):
		print 'Item ' + str(index) + ' - caret: ' + str(caret_pos) + ': ' + init_string[caret_pos-10:caret_pos+10]
		
	v.click_func = click_func
	
	v.highlight_color = (0, 1, 0, 1)
	v.update_html([init_string[:1000], init_string[1000:]], highlight_index = 1)
	v.present()