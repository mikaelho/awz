# coding: utf-8
import ui
from proxy import ObjectWrapper
from markdown2 import markdown
from urllib import quote, unquote
import clipboard
import webbrowser
from string import Template

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
		self.alignment = None
		self.margins = (10, 10, 10, 10)
		
		self.loading_fragment = False
		
		self.link_prefix = 'pythonista-markdownview:relay?content='
		self.debug_prefix = 'pythonista-markdownview:debug?content='
		self.init_postfix = '#pythonista-markdownview-initialize'
		self.in_doc_prefix = None
		
		self.last_md = ''
		
		# Web fragment is used to find the right scroll position when moving from editing to viewing
		self.web_fragment = ui.WebView(flex = 'WH')
		self.web_fragment.hidden = True
		self.web_fragment.delegate = self
		self.add_subview(self.web_fragment)
		
		# Main display webview
		self.delegate = self
		
	def to_html(self, md, scroll_pos = -1, content_only = False):
		result = markdown(md, extras=self.extras)
		if not content_only:
			intro = Template(self.htmlIntro.safe_substitute(css = self.css))
			(font_name, font_size) = self.font
			result = intro.safe_substitute(
				background_color = self.to_css_rgba(self.background_color), 
				text_color = self.to_css_rgba(self.tint_color),
				font_family = font_name,
				text_align = self.to_css_alignment(),
				font_size = str(font_size)+'px',
				init_postfix = self.init_postfix,
				link_prefix = self.link_prefix,
				debug_prefix = self.debug_prefix,
				scroll_pos = scroll_pos
			) + result + self.htmlOutro
		return result
		
	def to_css_rgba(self, color):
		return 'rgba({:.0f},{:.0f},{:.0f},{})'.format(color[0]*255, color[1]*255, color[2]*255, color[3])

	alignment_mapping = { ui.ALIGN_LEFT: 'left', ui.ALIGN_CENTER: 'center', ui.ALIGN_RIGHT: 'right', ui.ALIGN_JUSTIFIED: 'justify', ui.ALIGN_NATURAL: 'start' }

	def to_css_alignment(self):
		alignment = self.alignment or ui.ALIGN_NATURAL
		return MarkdownWebView.alignment_mapping[alignment]
		
	def update_html(self, md, caret_position = 0):
		self.last_md = md
		if caret_position > 0:
			html = self.to_html(md[:caret_position])
			self.loading_fragment = True
			self.web_fragment.load_html(html)
		else:
			html = self.to_html(md, 0)
			self.load_html(html)
			
	def webview_did_finish_load(self, webview):
		if webview == self.web_fragment:
			if not self.loading_fragment: return
			self.loading_fragment = False
			
			scroll_pos = int(webview.eval_js('document.getElementById("content").clientHeight'))
			html = self.to_html(self.last_md, scroll_pos)
			self.scroll_pos = scroll_pos
			self.load_html(html)
			
	def webview_should_start_load(self, webview, url, nav_type):
		
		if webview == self.web_fragment:
			return True
			
		# HOUSEKEEPING
		
		# Loaded by the web view at start, allow
		if url == 'about:blank':
			return True
		
		# Debug message from web page, print to console
		if url.startswith(self.debug_prefix):
			debug_text = unquote(url.replace(self.debug_prefix, ''))
			logging.debug(debug_text)
			return False
		
		# Custom WebView initialization message
		# Used to check if in-doc links starting with '#'
		# have extra stuff in front
		if url.endswith(self.init_postfix):
			self.in_doc_prefix = url[:len(url)-len(self.init_postfix)]
			self.hidden = False
			return False
		
		# Clean the extra stuff from in-doc links
		if self.in_doc_prefix and url.startswith(self.in_doc_prefix):
			url = url[len(self.in_doc_prefix):]
		
		# START EDIT
		if url.startswith(self.link_prefix):
			left_side = unquote(url.replace(self.link_prefix, ''))
			words = left_side.split()
			caret_pos = 0
			for word in words:
				caret_pos = self.last_md.find(word, caret_pos) + len(word)
			self.click_func(caret_pos)
			return False
		
		# REGULAR LINKS
		
		# Click, should start edit in markdown
		
			
		# If link starts with the extra stuff detected
		# at initialization, remove the extra
		
		
		# Check for custom link handling
		if self.can_call('webview_should_start_load'):
			return self.proxy_delegate.webview_should_start_load(webview, url, nav_type)
		# Handle in-doc links within the page
		elif url.startswith('#'):
			if self.can_call('webview_should_load_internal_link'):
				return self.proxy_delegate.webview_should_load_internal_link(webview, url)
			return True
		# Open 'http(s)' links in Safari
		# 'file' in built-in browser
		# Others like 'twitter' as OS decides
		else:
			if self.can_call('webview_should_load_external_link'):
				return self.proxy_delegate.webview_should_load_external_link(webview, url)
			if url.startswith('http:') or url.startswith('https:'):
				url = 'safari-' + url
			webbrowser.open(url)
			return False
		
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
				var c = document.getElementById("content");
				var r = document.getElementById("relay");
				var range = new Range();
				range.selectNodeContents(c);
				var rangeEnd = document.caretRangeFromPoint(e.clientX, e.clientY);
				range.setEnd(rangeEnd.startContainer, rangeEnd.startOffset);
				r.href="$link_prefix"+encodeURIComponent(range.toString());
				r.click();
			}
			
			function closest(elem) {
				for ( ; elem && elem !== document; elem = elem.parentNode ) {
					if ( elem.classList.contains("awz-node-id") ) {
						return elem;
					}
				}
				return false;
			}
			
			function initialize() {
				var scrollPos = $scroll_pos;
				if (scrollPos > 0) {
					var totalHeight = document.getElementById("content").clientHeight;		
					var halfScreen = window.innerHeight/2;
					if ((totalHeight - scrollPos) > halfScreen) {
						scrollPos -= halfScreen;
					}
					window.scrollBy(0, scrollPos);
					activateLinks();
					var r = document.getElementById("relay");
					r.href = "$init_postfix"
					r.click()
				}
			}
		</script>
		</head>
		<body onload="initialize()">
			<a id="relay" style="display:none"></a>
			<a id="debug" style="display:none"></a>
			<div id="content" onclick="text_position()">
	''')
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
	'''
	
if __name__ == "__main__":
	v = MarkdownWebView(ui.WebView())
	
	import os
	readme_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.md')
	init_string = ''
	if os.path.exists(readme_filename):
		with open(readme_filename) as file_in:
			init_string = file_in.read()
			
	def click_func(caret_pos):
		print init_string[caret_pos-10:caret_pos+10]
		
	v.click_func = click_func
	print type(v)
	print v.__subject__
	
	v.update_html(init_string)
	v.present()