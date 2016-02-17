# coding: utf-8
import ui
import console
import json
import copy
import re
import os
from markdown2 import markdown
from bs4 import BeautifulSoup

from SlidePanel import SlidePanel
from ReminderStore import ReminderStore
from EvenView import EvenView
from MarkdownWebView import MarkdownWebView
from MarkdownTextView import MarkdownTextView
from ItemDataSource import ItemDataSource
from BlurView import BlurView


class Model(ReminderStore):
	def __init__(self):
		ReminderStore.__init__(self, 'AWZ')
		
		self.link_regexp = re.compile(r'\[([^\]]*)\]\(awz-([^)]+)\)')
		
		if not 'state' in self:
			self['state'] = json.dumps({ 'history': [ 'start' ]})
		self.state = json.loads(self['state'])
		
		start_up = [ 'start', 'help' ]	
		for key in start_up:
			if not key in self:
				filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), key + '.md')
				if os.path.exists(filename):
					with open(filename) as file_in:
						init_string = file_in.read()
						self[key] = init_string
		
	def list_titles(self):
		titles = []
		for key in self:
			if key == 'state': continue
			titles.append(self.get_title(key))
		return titles
		
	def get_title(self, key):
		title = self[key]
		if not title:
			title = '# Empty'
			self[key] = title
		line_end = title.find('\n')
		if line_end > -1:
			title = title[:line_end]
		return self._flatten(title)
	
	def set_new(self, value = ''):
		value = self._flatten(value)
		if value == '':
			value = 'New'
		key = self.new_item('# ' + value)
		return (key, value)
		
	def _flatten(self, text):
		html = markdown(text).strip()
		soup = BeautifulSoup(html)
		return soup.get_text()
		
	def history(self):
		return copy.copy(self.state['history'])
		
	def open(self, key, at_index = -1):
		history = self.state['history']
		seen = set()
		seen.add(key)
		self.pipe = [item_key for item_key in history[:at] if not item_key in seen]
		for item_key in self.pipe: seen.add(item_key)
		self.pipe.append(key)
		
		self.state['history'].append(key)
		self['state'] = json.dumps(self.state)
		
	def get_children(self, key):
		markd = self[key]
		seen = {}
		children = []
		matches = self.link_regexp.findall(markd)
		for item in matches:
			key1 = item[1]
			if not key1 in seen:
				children.append(key1)
				seen[key1] = item[0]
		changed = False
		for key2 in seen:
			title = self.get_title(key2)
			if title <> seen[key2]:
				changed = True
				replacer = re.compile(r'\[([^\]]*)\]\(awz-' + key2 + '\)')
				markd = replacer.sub('[' + title + '](awz-' + key2 + ')', markd)
		if changed:
			self[key] = markd
		return children
		
	def back(self):
		pass
		
	def forward(self):
		pass

color1 = '#fff7ee'
color2 = '#6f4f2c'

class ViewController(ui.View):
	def __init__(self):
		self.model = Model()
		
		self.background_color = color1
		self.tint_color = color2
		
		self.button_area_height = 40
		self.web = MarkdownWebView(ui.WebView(flex = 'WH'))
		self.edit = MarkdownTextView(ui.TextView(flex = 'WH'))
		self.web.frame = (0, 0, self.width, self.height - self.button_area_height)
		self.edit.frame = (0, 0, self.width, self.height)
		self.edit.hidden = True

		self.button_area = EvenView(margin = 20)
		self.button_area.flex = 'WT'
		self.button_area.frame = (0, self.height - self.button_area_height, self.width, self.button_area_height)
		self.web.background_color = self.edit.background_color = color1
		self.web.tint_color = self.edit.text_color =  color2
		self.button_area.background_color = color2
		self.web.font = self.edit.font = ('PingFang HK', 14)
		
		self.web.click_func = self.start_editing
		self.edit.changed_func = self.save_current
		self.edit.end_edit_func = self.return_from_editing
		self.edit.new_item_func = self.model.set_new
		
		self.add_subview(self.web.__subject__)
		self.add_subview(self.edit.__subject__)
		self.add_subview(self.button_area)
		self.margins_on_content = (5, 15, 5, 15)
		self.create_buttons(color1)
		
		self.navpanel = SlidePanel(active_edge_width = self.margins_on_content[1])
		self.add_subview(self.navpanel)
		
		self.list = ui.TableView()
		self.list.flex = 'WH'
		self.list.background_color = 'transparent' #color2
		self.list.tint_color = color1
		self.list.data_source = ItemDataSource(self.create_panel_items())
		self.list.data_source.action = self.tableview_did_select
		self.list.data_source.accessory_action = self.tableview_accessory_action
		self.list.data_source.background_color = 'transparent'
		self.list.data_source.text_color = color1
		self.list.data_source.highlight_color = color2
		self.list.delegate = self.list.data_source
		
		panel_content = ui.View()
		blur = BlurView(style = 2, flex = 'WH')
		panel_content.add_subview(blur)
		panel_content.add_subview(self.list)
		blur.frame = self.list.frame = (0, 0, panel_content.width, panel_content.height)
		
		self.navpanel.add_subview(panel_content)
		# BlurView(style = 2)
		
		self.open_current()
		
	def new_item(self, value = ''):
		
		new_key = self.model.new_item()
		self.model[new_key] = '# '
		
	def save_current(self, md):
		self.model[self.editing_key] = md
		
	def open_current(self, pos = 0):
		history = self.model.history()
		open_key = history[-1]
		#mv = self.set_up_markdownview(open_key)
		self.pipe = history + self.model.get_children(open_key)
		self.active = open_key
		self.show_html()
		
	def show_html(self, current_key = None, caret_pos = 0):
		self.start_positions = []
		divider = '\n\n------------------------\n\n'
		md = divider
		for key in self.pipe:
			self.start_positions.append(len(md))
			if key == current_key:
				caret_pos += len(md)
			md += self.model[key]
			md += divider
		self.web.update_html(md, caret_pos)
		self.edit.hidden = True
		
	def start_editing(self, caret_pos):
		selected_index = 0
		for index, start_pos in reversed(list(enumerate(self.start_positions))):
			if caret_pos > start_pos:
				selected_index = index
				caret_pos -= start_pos
				break
		self.editing_key = self.pipe[selected_index]
		self.edit.text = self.model[self.editing_key]
		self.edit.begin_editing()
		self.edit.set_selected_range(caret_pos, caret_pos)
		self.caret_pos = caret_pos
		self.edit.hidden = False
		
	def return_from_editing(self, caret_pos):
		self.show_html(self.editing_key, caret_pos)
		
	def create_panel_items(self):
		items = []
		for key in self.model:
			if key == 'state': continue
			items.append({
					'title': self.model.get_title(key),
					'accessory_type': 'detail_disclosure_button',
					'key': key
				}
			)
		return items
		
	def webview_should_load_external_link(self, webview, url):
		print 'external: ' + url
		return True
		
	def create_buttons(self, color):
		buttons = [
			[ 'iob:navicon_32', self.show_list ],
			[ 'iob:chevron_left_24', self.back ],
			[ 'iob:chevron_right_24', self.forward ],
			[ 'iob:plus_round_24', self.add_new ]
		]
		# iob:ios7_compose_outline_32
		for spec in buttons:
			button = ui.Button(image = ui.Image.named(spec[0]))
			button.action = spec[1]
			button.tint_color = color
			self.button_area.add_subview(button)
			
	def show_list(self, sender):
		self.navpanel.reveal()
			
	def add_new(self, sender):
		print self.main_scroll.height
		print self.main_scroll.content_size
		
	def back(self, sender):
		print 'back'
		
	def forward(self, sender):
		print 'fwd'
		
	def update_list(self):
		pass
		
	def tableview_did_select(self, sender):
		self.navpanel.hide()
		
	def tableview_accessory_action(self, sender):
		data = sender.items[sender.selected_row - 1]
		key = data['key']
		title = data['title']
		result = 0
		if self.edit.hidden:
			result = console.alert(title, '', 'Open')
		else:
			result = console.alert(title, '', 'Open', 'Link to copy', 'Insert link')
		if result == 3:
			(start, end) = self.edit.selected_range
			link = '[' + title + '](awz-' + key + ')'
			self.edit.replace_range((start, end), link)
			#self.edit.set_selected_range(start, start+len(link))
		

vc = ViewController()
vc.background_color = '#91d4ff'
vc.present(title_bar_color = color1, title_color = color2)