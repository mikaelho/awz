# coding: utf-8
import ui
import console
import clipboard
import json
import copy
import re
import os
from markdown2 import markdown
from bs4 import BeautifulSoup

#from extend import extend

from SlidePanel import SlidePanel
from ReminderStore import ReminderStore
from EvenView import EvenView
from MarkdownWebView import MarkdownWebView
from MarkdownTextView import MarkdownTextView
from ItemDataSource import ItemDataSource
from BlurView import BlurView
from extend import Extender
import Server


class Model(ReminderStore):
	def __init__(self):
		ReminderStore.__init__(self, 'AWZ')
		
		self.link_regexp = re.compile(r'\[([^\]]*)\]\(awz-([^)]+)\)')
		
		if not 'state' in self:
			self['state'] = json.dumps({ 'history': [ [ 'start', 0 ] ], 'index': 0 })
		self.state = json.loads(self['state'])
		if not 'index' in self.state:
			self.state['index'] = len(self.state['history'] - 1)
		
		start_up = [ 'start', 'help' ]	
		for key in start_up:
			if not key in self:
				filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), key + '.md')
				if os.path.exists(filename):
					with open(filename) as file_in:
						init_string = file_in.read()
						self[key] = init_string
	
	def push(self, key, caret_pos = 0):
		#type = 'internal' if url else 'cross'
		# Only add a new item if different from previous current 
		if key <> self.state['history'][self.state['index']][0]:
			new_index = self.state['index'] + 1
			new_history = self.state['history'][:new_index]
			#new_history.append({ 'type': type, 'key': key, 'url': url, 'caret_pos': caret_pos })
			new_history.append([ key, caret_pos ])
			self.state['history'] = new_history
			self.state['index'] = new_index
		else:
			self.state['history'][self.state['index']] = [ key, caret_pos ]
		self.save_state()
		
	def update_current_scroll(self, scroll_pos):
		self.state['history'][self.state['index']][1] = scroll_pos
		self.save_state()
		
	def save_state(self):
		self['state'] = json.dumps(self.state)
		
	def can_move_back(self):
		return self.state['index'] > 0
		
	def back(self):
		if self.can_move_back():
			self.state['index'] = self.state['index'] - 1
			self.save_state()
			return self.state['history'][self.state['index']]
		return None
			
	def can_move_forward(self):
		return self.state['index'] < (len(self.state['history']) - 1)
		
	def forward(self):
		if self.can_move_forward():
			self.state['index'] = self.state['index'] + 1
			self.save_state()
			return self.state['history'][self.state['index']]
		return None
		
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
		
	def get_history_before_current(self):
		current_index = self.state['index'] + 1
		return copy.copy(self.state['history'][:current_index])
		'''
		keys = []
		for index, item in enumerate(self.state['history']):
			keys.append(item[0])
			if index == current_index: break
		return keys
		'''
		#return copy.copy(self.state['history'])
		
	'''
	def open(self, key, at_index = -1):
		history = self.state['history']
		seen = set()
		seen.add(key)
		self.pipe = [item_key for item_key in history[:at] if not item_key in seen]
		for item_key in self.pipe: seen.add(item_key)
		self.pipe.append(key)
		
		self.state['history'].append(key)
		self['state'] = json.dumps(self.state)
	'''
	
	def populate_pipe(self):
		history = self.get_history_before_current()
		focus_index = len(history) - 1
		open_item = history[focus_index]
		messy_history = [item[0] for item in history]
		messy_pipe = list(enumerate(messy_history + self.get_children(open_item[0])))
		
		# Remove duplicates within history, keeping the most recent, and always the focus item
		seen = set()
		seen_add = seen.add
		seen.add(open_item[0]) # Always keep the focus item
		pruned_pipe = [x for x in reversed(messy_pipe) if x[0] == focus_index or not (x[1] in seen or seen_add(x[1]))]
		pruned_pipe.reverse()
		
		# Only show max 5 items of history
		focus_pruned_index = 0
		for index, item in enumerate(pruned_pipe):
			if item[0] == focus_index:
				focus_pruned_index = index
				break
		pruned_pipe = pruned_pipe[max(0, focus_pruned_index - 5):]
		
		return (pruned_pipe, focus_index, open_item[1])
		
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
		self.edit.frame = self.bounds
		self.edit.hidden = True

		self.button_area = EvenView(margin = 20)
		self.button_area.flex = 'WT'
		self.button_area.frame = (0, self.height - self.button_area_height, self.width, self.button_area_height)
		self.web.background_color = self.edit.background_color = color1
		self.web.tint_color = self.edit.text_color =  color2
		self.button_area.background_color = color2
		self.web.font = self.edit.font = ('PingFang HK', 14)
		self.web.highlight_color = (1, 1, 1, 1)
		
		self.web.click_func = self.start_editing
		self.web.double_click_func = self.popup
		self.web.cross_link_func = self.cross_link
		self.edit.changed_func = self.save_current
		self.edit.end_edit_func = self.return_from_editing
		self.edit.new_item_func = self.model.set_new
		
		self.add_subview(self.web.__subject__)
		self.add_subview(self.edit)
		self.add_subview(self.button_area)
		self.margins_on_content = (5, 15, 5, 15)
		self.create_buttons(color1)
		
		self.navpanel = SlidePanel(active_edge_width = self.margins_on_content[1], from_left = False)
		self.add_subview(self.navpanel)
		
		self.list = ui.TableView()
		self.list.flex = 'WH'
		self.list.background_color = 'transparent' #color2
		self.list.tint_color = color1
		self.list.data_source = ItemDataSource(self.create_panel_items())
		self.list.data_source.action = self.tableview_did_select
		self.list.data_source.link_func = self.insert_link
		self.list.data_source.copy_func = self.insert_link_to_copy
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
		
		self.popup_view = ui.Button(flex = 'WH')
		self.popup_view.action = self.hide
		self.popup_view.frame = self.bounds
		self.popup_view.background_color = 'transparent'
		self.popup_view.hidden = True
		self.add_subview(self.popup_view)
		popup_button_blur = BlurView(style = 2, flex = 'LRTB')
		popup_button_blur.frame = (0,0,200,50)
		popup_button_blur.center = self.center
		self.popup_view.add_subview(popup_button_blur)
		popup_button_area = EvenView(margin = 20)
		popup_button_blur.add_subview(popup_button_area)
		popup_button_area.flex = 'WH'
		popup_button_area.frame = popup_button_blur.bounds
		popup_button_area.add_subview(ActionButton(ui.Button(), 'iob:link_32', self.copy_internal_link))
		popup_button_area.add_subview(ActionButton(ui.Button(), 'iob:ios7_world_outline_32', self.copy_external_link))
		popup_button_area.add_subview(ActionButton(ui.Button(), 'iob:arrow_shrink_32', self.change_focus))
		
		self.editing = False
		self.open_current()
		
	def new_item(self, value = None):
		value = value or '# '
		new_key = self.model.new_item()
		self.model[new_key] = value
		
	def save_current(self, md):
		self.model[self.pipe[self.editing_index][1]] = md
		
	def open_current(self):
		(self.pipe, focus_index, caret_pos) = self.model.populate_pipe()
		contents = [ (item[0], self.model[item[1]]) for item in self.pipe ]
		self.web.update_html(contents, focus_index, caret_pos)
		
	def cross_link(self, target_key, source_list_index = None, source_position = None):
		if source_list_index:
			source_key = self.pipe[source_list_index][1]
			self.model.push(source_key, source_position)
		self.model.push(target_key)
		self.open_current()
		'''
		(self.pipe, focus_index, caret_pos) = self.model.populate_pipe()
		(md, total_caret_pos) = self.total_md(focus_index)
		self.web.get_scroll_pos(md, total_caret_pos, result_callback = self.set_history_and_show)
		'''
	
	'''	
	def set_history_and_show_after_edit(self, md, scroll_pos):
		new_scroll_pos = max(0, scroll_pos - self.web.height/2)
		self.set_history_and_show(md, new_scroll_pos)
		
	def set_history_and_show(self, md, scroll_pos):
		# Set history
		self.model.update_current_scroll(scroll_pos)
		# Show
		self.web.update_html(md, scroll_pos)
		self.edit.hidden = True
	
	def total_md(self, focus_index = None, current_caret_pos = 0):
		total_caret_pos = current_caret_pos
		self.start_positions = []
		divider = '\n\n----------\n\n'
		md = divider
		for index, key in enumerate(self.pipe):
			self.start_positions.append(len(md))
			if index == focus_index:
				md += divider
				total_caret_pos += len(md)
			md += self.model[key]
			md += divider
			if index == focus_index:
				md += divider
		return (md, total_caret_pos)
	'''
		
	def popup(self, index):
		index = int(index)
		self.long_press_key = [item[1] for item in self.pipe if item[0] == index][0]
		
		self.popup_view.hidden = False
		
	def change_focus(self, sender):
		#(index, caret_pos) = self.caret_pos_to_index(caret_pos)
		self.popup_view.hidden = True
		self.cross_link(self.long_press_key)
		
	def copy_internal_link(self, sender):
		link_text = '[' + self.model.get_title(self.long_press_key) + '](awz-' + self.long_press_key + ')'
		self.set_clipboard(link_text)
		
	def copy_external_link(self, sender):
		link_text = self.model.get_title(self.long_press_key) + ' - http://joutsen.ddns.net/' + self.long_press_key
		self.set_clipboard(link_text)
		
	def set_clipboard(self, text):
		self.popup_view.hidden = True
		clipboard.set(text)
		console.hud_alert('Copied', duration=0.5)
		
	def start_editing(self, list_index, caret_pos):
		self.editing_index = list_index
		#(self.editing_index, caret_pos) = self.caret_pos_to_index(caret_pos)
		self.edit.text = self.model[self.pipe[self.editing_index][1]]
		self.edit.begin_editing()
		self.edit.set_selected_range(caret_pos, caret_pos)
		self.caret_pos = caret_pos
		self.edit.hidden = False
		self.editing = True
		
	def caret_pos_to_index(self, caret_pos):
		selected_index = 0
		rev = reversed(list(enumerate(self.start_positions)))
		for index, start_pos in rev:
			if caret_pos > start_pos:
				selected_index = index
				caret_pos -= start_pos
				break
		return (selected_index, caret_pos)
		
	def return_from_editing(self, caret_pos):
		self.editing = False
		self.model.push(self.pipe[self.editing_index][1], caret_pos)
		self.open_current()
		self.edit.hidden = True
		#self.web.get_scroll_pos(md, total_caret_pos, result_callback = self.set_history_and_show_after_edit)	
		
	def create_panel_items(self):
		items = []
		for key in self.model:
			if key == 'state': continue
			items.append({
					'title': self.model.get_title(key),
					'accessory_type': 'disclosure_indicator',
					'key': key
				}
			)
		return items
		
	def webview_should_load_external_link(self, webview, url):
		print 'external: ' + url
		return True
		
	def create_buttons(self, color):
		buttons = [
			#[ 'iob:ios7_world_outline_24', self.toggle_server ],
			[ 'iob:home_32', self.home ],
			[ 'iob:chevron_left_24', self.back ],
			[ 'iob:chevron_right_24', self.forward ],
			[ 'iob:navicon_32', self.show_list ]
			#[ 'iob:plus_round_24', self.add_new ]
		]
		# iob:ios7_compose_outline_32
		for spec in buttons:
			button = ui.Button(image = ui.Image.named(spec[0]))
			button.action = spec[1]
			button.tint_color = color
			self.button_area.add_subview(button)
		
	def show_list(self, sender):
		self.navpanel.reveal()
		
	def home(self, sender):
		self.cross_link('start')
	
	'''
	def add_new(self, sender):
		print self.main_scroll.height
		print self.main_scroll.content_size
	'''
	
	def toggle_server(self, sender):
		if Server.alive():
			Server.stop()
			sender.tint_color = color1
		else:
			Server.start(self.content_for_web)
			sender.tint_color = 'green'
		
	def back(self, sender):
		if self.model.back():
			self.open_current()
		
	def forward(self, sender):
		if self.model.forward():
			self.open_current()
		
	def update_list(self):
		pass
		
	def tableview_did_select(self, sender):
		self.navpanel.hide()
		
	def tableview_accessory_action(self, sender):
		data = sender.items[sender.selected_row - 1]
		key = data['key']
		title = data['title']
		result = 0
		if not self.editing:
			result = console.alert(title, '', 'Open')
		else:
			result = console.alert(title, '', 'Open', 'Link to copy', 'Insert link')
		if result == 3:
			(start, end) = self.edit.selected_range
			link = '[' + title + '](awz-' + key + ')'
			self.edit.replace_range((start, end), link)
			#self.edit.set_selected_range(start, start+len(link))
			
	def insert_link(self, key):
		if self.editing:
			self.navpanel.hide()
			title = self.model.get_title(key)
			(start, end) = self.edit.selected_range
			link = '[' + title + '](awz-' + key + ')'
			self.edit.replace_range((start, end), link)
			self.edit.set_selected_range(start, start+len(link))
		
	def insert_link_to_copy(self, key):
		if self.editing:
			new_key = self.model.new_item(self.model[key])
			self.insert_link(new_key)

	def content_for_web(self, key):
		# Strip 'awz-'
		key = key[4:]
		keys = [ key ] + self.model.get_children(key)
		contents = [(index, self.model[content_key]) for index, content_key in enumerate(keys)]
		return self.web.to_web_html(contents)

	def hide(self, sender):
		sender.hidden = True

class ActionButton(Extender):
	def __init__(self, image_name, handler_func):
		self.image = ui.Image.named(image_name)
		self.action = handler_func
		self.tint_color = color1
		self.background_color = 'transparent'
		self.size_to_fit()

vc = ViewController()
vc.background_color = '#91d4ff'
vc.present(title_bar_color = color1, title_color = color2)