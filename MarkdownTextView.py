#coding: utf-8
import ui
from markdown2 import markdown
from urllib import quote, unquote
#from proxy import ObjectWrapper
from objc_util import *
from Gestures import Gestures
from extend import Extender

class MarkdownTextView(Extender):
#class MarkdownTextView(ObjectWrapper):
		
	def __init__(self):
		self.create_accessory_toolbar()
		self.delegate = self
		self.to_add_to_beginning = ('', -1)
		self.set_keyboard_dismiss_mode()
		
	# Temporary fix for a bug where setting selected_range throws a range error if placing caret at the end of the text
	@on_main_thread
	def set_selected_range(self, start, end):
		ObjCInstance(self).setSelectedRange_((start, (end-start)))
		
	@on_main_thread
	def set_keyboard_dismiss_mode(self):
		ObjCInstance(self).keyboardDismissMode = 2
		# 0 - normal
		# 1 - on scroll
		# 2 - on scroll interactive
		
	@on_main_thread
	def create_accessory_toolbar(self):
		
		def create_button(label, func):
			button_width = 25
			black = ObjCClass('UIColor').alloc().initWithWhite_alpha_(0.0, 1.0)
			action_button = ui.Button()
			action_button.action = func
			accessory_button = ObjCClass('UIBarButtonItem').alloc().initWithTitle_style_target_action_(label, 0, action_button, sel('invokeAction:'))
			accessory_button.width = button_width
			accessory_button.tintColor = black
			
			return (action_button, accessory_button)
		
		vobj = ObjCInstance(self)

		keyboardToolbar = ObjCClass('UIToolbar').alloc().init()
		
		keyboardToolbar.sizeToFit()
		
		Gestures().add_swipe(keyboardToolbar, self.hide_keyboard, Gestures.DOWN)
		
		Gestures().add_pan(keyboardToolbar, self.move_caret)
		
		button_width = 25
		black = ObjCClass('UIColor').alloc().initWithWhite_alpha_(0.0, 1.0)
		
		# Create the buttons
		# Need to retain references to the buttons used
		# to handle clicks
		(self.indentButton, indentBarButton) = create_button(u'\u21E5', self.indent)
		
		(self.outdentButton, outdentBarButton) = create_button(u'\u21E4', self.outdent)
		
		(self.quoteButton, quoteBarButton) = create_button('>', self.block_quote)
		
		(self.linkButton, linkBarButton) = create_button('[]', self.link)
		
		#(self.anchorButton, anchorBarButton) = create_button('<>', self.anchor)
		
		(self.hashButton, hashBarButton) = create_button('#', self.heading)
		
		(self.numberedButton, numberedBarButton) = create_button('1.', self.numbered_list)
		
		(self.listButton, listBarButton) = create_button('•', self.unordered_list)
		
		(self.underscoreButton, underscoreBarButton) = create_button('_', self.insert_underscore)
		
		(self.backtickButton, backtickBarButton) = create_button('`', self.insert_backtick)
		
		(self.newButton, newBarButton) = create_button('+', self.new_item)
		
		# Flex between buttons
		f = ObjCClass('UIBarButtonItem').alloc().initWithBarButtonSystemItem_target_action_(5, None, None)
		
		#doneBarButton = ObjCClass('UIBarButtonItem').alloc().initWithBarButtonSystemItem_target_action_(0, vobj, sel('endEditing:')) 
		
		keyboardToolbar.items = [indentBarButton, f, outdentBarButton, f, quoteBarButton, f, linkBarButton, f, hashBarButton, f, numberedBarButton, f, listBarButton, f, underscoreBarButton, f, backtickBarButton, f, newBarButton]
		vobj.inputAccessoryView = keyboardToolbar
	
	def indent(self, sender):
		def func(line):
			return '  ' + line
		self.transform_lines(func)
		
	def outdent(self, sender):
		def func(line):
			if str(line).startswith('  '):
				return line[2:]
		self.transform_lines(func, ignore_spaces = False)
	
	def insert_underscore(self, sender):
		self.insert_character('_', '___')
		
	def insert_backtick(self, sender):
		self.insert_character('`', '`')
		
	def insert_character(self, to_insert, to_remove):
		tv = self
		(start, end) = tv.selected_range
		(r_start, r_end) = (start, end)
		r_len = len(to_remove)
		if start <> end:
			if tv.text[start:end].startswith(to_remove):
				if end - start > 2*r_len + 1 and tv.text[start:end].endswith(to_remove):
					to_insert = tv.text[start+r_len:end-r_len]
					r_end = end-2*r_len
			elif start-r_len > 0 and tv.text[start-r_len:end].startswith(to_remove):
				if end+r_len <= len(tv.text) and tv.text[start:end+r_len].endswith(to_remove):
					to_insert = tv.text[start:end]
					start -= r_len
					end += r_len
					r_start = start
					r_end = end-2*r_len
			else:
				r_end = end + 2*len(to_insert)
				to_insert = to_insert + tv.text[start:end] + to_insert
		tv.replace_range((start, end), to_insert)
		if start <> end:
			tv.set_selected_range(r_start, r_end)
		
	def heading(self, sender):
		def func(line):
			return line[3:] if str(line).startswith('###') else '#' + line
		self.transform_lines(func, ignore_spaces = False)
		
	def numbered_list(self, data):
		def func(line):
			if line.startswith('1. '):
				return line[3:]
			else:
				return '1. ' + (line[2:] if line.startswith('* ') else line)
		self.transform_lines(func)
		
	def unordered_list(self, sender):
		def func(line):
			if str(line).startswith('* '):
				return line[2:]
			else:
				return '* ' + (line[3:] if line.startswith('1. ') else line)
		self.transform_lines(func)
		
	def block_quote(self, sender):
		def func(line):
			return '> ' + line
		self.transform_lines(func, ignore_spaces = False)
		
	def link(self, sender):
		templ = "[#]($)"
		(start, end) = self.selected_range
		templ = templ.replace('$', self.text[start:end])
		new_start = start + templ.find('#')
		new_end = new_start + (end - start)
		templ = templ.replace('#', self.text[start:end])
		self.replace_range((start, end), templ)
		self.set_selected_range(new_start, new_end)
		
	def new_item(self, sender):
		(start, end) = self.selected_range
		(new_key, value) = self.new_item_func(self.text[start:end])
		link = '[' + value + '](awz-' + new_key + ')'
		self.replace_range((start, end), link)
		
	def hide_keyboard(self, data):
		self.end_editing()
		
	def move_caret(self, data):
		if data.velocity[1] > 500 and data.translation > 50:
			self.end_editing()
			return 
		if data.state == Gestures.BEGAN:
			self.translation_baseline = 0
		dx = data.translation[0] - self.translation_baseline
		if abs(dx) > 15:
			self.translation_baseline = data.translation[0]
			change = 1 if dx > 0 else -1
			(start, end) = self.selected_range
			new_start = start + change
			(ns, ne) = (start, new_start) if dx > 0 else (new_start, start)
			if ns > -1:
				if not self.text[ns:ne] == '\n':
					self.set_selected_range(new_start, new_start)
		
	'''
	OBSOLETE: Use heading-ids or toc markdown extra instead
	
	* __<>__ - In-document links - Creates an anchor (`<a>` tag) after the selection, assumed to be some heading text. At the same time, places a link to the anchor on the clipboard, typically to be pasted in a table of contents.
	'''
	def anchor(self, sender):
		templ = " <a name='#'></a>"
		(start, end) = self.selected_range
		link_label = self.text[start:end]
		link_name = quote(self.text[start:end])
		templ = templ.replace('#', link_name)
		self.replace_range((end, end), templ)
		link = "[" + link_label + "](#" + link_name + ")"
		clipboard.set(link)
		
	def make_list(self, list_marker):
		self.get_lines()
		
	def transform_lines(self, func, ignore_spaces = True):
		(orig_start, orig_end) = self.selected_range
		(lines, start, end) = self.get_lines()
		replacement = []
		for line in lines:
			spaces = ''
			if ignore_spaces:
				space_count = len(line) - len(line.lstrip(' '))
				if space_count > 0:
					spaces = line[:space_count]
					line = line[space_count:]
			replacement.append(spaces + func(line))
		self.replace_range((start, end), '\n'.join(replacement))
		new_start = orig_start + len(replacement[0]) - len(lines[0])
		if new_start < start:
			new_start = start
		end_displacement = 0
		for index, line in enumerate(lines):
			end_displacement += len(replacement[index]) - len(line)
		new_end = orig_end + end_displacement
		if new_end < new_start:
			new_end = new_start
		self.set_selected_range(new_start, new_end)
		
	def get_lines(self):
		(start, end) = self.selected_range
		text = self.text
		new_start = text.rfind('\n', 0, start)
		new_start = 0 if new_start == -1 else new_start + 1
		new_end = text.find('\n', end)
		if new_end == -1: new_end = len(text)
		#else: new_end -= 1
		if new_end < new_start: new_end = new_start
		return (text[new_start:new_end].split('\n'), new_start, new_end)
		
	def textview_did_end_editing(self, textview):
		(start, end) = self.selected_range
		self.changed_func(self.text)
		self.end_edit_func(start)
			
	def textview_should_change(self, textview, range, replacement):
		self.to_add_to_beginning = ('', -1)
		if replacement == '\n': #and range[0] == range[1] 
			pos = range[0]
			next_line_prefix = ''
			# Get to next line
			pos = self.text.rfind('\n', 0, pos)
			if not pos == -1:
				pos = pos + 1
				rest = self.text[pos:]
				# Copy leading spaces
				space_count = len(rest) - len(rest.lstrip(' '))
				if space_count > 0:
					next_line_prefix += rest[:space_count]
					rest = rest[space_count:]
				# Check for prefixes
				prefixes = [ '1. ', '+ ', '- ', '* ']
				for prefix in prefixes:
					if rest.startswith(prefix + '\n'):
						self.replace_range((pos + space_count, pos + space_count + len(prefix)), '')
						break
					elif rest.startswith(prefix):
						next_line_prefix += prefix
						break
				if len(next_line_prefix) > 0:
					diff = range[0] - pos
					if diff < len(next_line_prefix):
						next_line_prefix = next_line_prefix[:diff]
					self.to_add_to_beginning = (next_line_prefix, range[0]+1)		
		return True
			
	def textview_did_change(self, textview):
		add = self.to_add_to_beginning
		if add[1] > -1:
			self.to_add_to_beginning = ('', -1)
			self.replace_range((add[1], add[1]), add[0])
		self.changed_func(self.text)

if __name__ == "__main__":
	import os
	readme_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.md')
	
	markdown_edit = MarkdownTextView(ui.TextView())
	# Use this if you do not want accessory keys:
	#markdown_edit = MarkdownView(accessory_keys = False)
	markdown_edit.name = 'MarkdownView Documentation'
	
	init_string = ''
	if os.path.exists(readme_filename):
		with open(readme_filename) as file_in:
			init_string = file_in.read()
	markdown_edit.text = init_string
	
	markdown_edit.font = ('Apple SD Gothic Neo', 16)
	markdown_edit.background_color = '#f7f9ff'
	markdown_edit.text_color = '#030b60'
	
	markdown_edit.present() 
	
	leader = 'Share code Gestures for Pythonista'
	markdown_edit.place_caret_after(leader.split())