# coding: utf-8
import ui
from Gestures import Gestures
from EvenView import EvenView

class ItemDataSource (object):
	def __init__(self, items=None):
		self.tableview = None
		self.reload_disabled = False
		self.delete_enabled = True
		self.move_enabled = False
		
		self.action = None
		self.edit_action = None
		self.accessory_action = None
		
		self.tapped_accessory_row = -1
		self.selected_row = -1
		
		if items is not None:
			self.items = items
		else:
			self.items = ui.ListDataSourceList([])
		self.background_color = None
		self.text_color = None
		self.highlight_color = None
		self.font = None
		self.number_of_lines = 1
	
	def reload(self):
		if self.tableview and not self.reload_disabled:
			self.tableview.reload()
	
	@property
	def items(self):
		return self._items
	
	@items.setter
	def items(self, value):
		self._items = ui.ListDataSourceList(value, self)
		self.reload()
	
	def tableview_number_of_sections(self, tv):
		self.tableview = tv
		return 1
	
	def tableview_number_of_rows(self, tv, section):
		return len(self.items)
	
	def tableview_can_delete(self, tv, section, row):
		return self.delete_enabled
	
	def tableview_can_move(self, tv, section, row):
		return self.move_enabled
	
	def tableview_accessory_button_tapped(self, tv, section, row):
		self.tapped_accessory_row = row
		if self.accessory_action:
			self.accessory_action(self)
	
	def tableview_did_select(self, tv, section, row):
		self.selected_row = row
		if self.action:
			self.action(self)
	
	def tableview_move_row(self, tv, from_section, from_row, to_section, to_row):
		if from_row == to_row:
			return
		moved_item = self.items[from_row]
		self.reload_disabled = True
		del self.items[from_row]
		self.items[to_row:to_row] = [moved_item]
		self.reload_disabled = False
		if self.edit_action:
			self.edit_action(self)
	
	def tableview_delete(self, tv, section, row):
		self.reload_disabled = True
		del self.items[row]
		self.reload_disabled = False
		tv.delete_rows([row])
		if self.edit_action:
			self.edit_action(self)
	
	def tableview_cell_for_row(self, tv, section, row):
		item = self.items[row]
		cell = ui.TableViewCell()
		cell.text_label.number_of_lines = self.number_of_lines
		if isinstance(item, dict):
			cell.text_label.text = item.get('title', '')
			img = item.get('image', None)
			if img:
				if isinstance(img, basestring):
					cell.image_view.image = Image.named(img)
				elif isinstance(img, Image):
					cell.image_view.image = img
			accessory = item.get('accessory_type', 'none')
			cell.accessory_type = accessory
			cell.key = item.get('key', None)
		else:
			cell.text_label.text = str(item)
		if self.text_color:
			cell.text_label.text_color = self.text_color
		if self.background_color:
			cell.background_color = self.background_color
		if self.highlight_color:
			bg_view = ui.View(background_color=self.highlight_color)
			cell.selected_background_view = bg_view
		if self.font:
			cell.text_label.font = self.font
		#cell.row = row
		#cell.button_view = EvenView(margin = 20)
		#cell.add_subview(cell.button_view)
		#cell.button_view.frame = cell.bounds
		#cell.button_view.background_color = 'black'
		#self.create_buttons(cell.button_view, 'white')
		#cell.button_view.hidden = True
		#Gestures().add_swipe(cell.button_view, self.swipe_left, direction = Gestures.LEFT)
		#Gestures().add_swipe(cell, self.swipe_right)
		return cell
		
	def swipe_right(self, view, location):
		view.button_view.hidden = False
		
	def swipe_left(self, view, location):
		view.hidden = True
		
	def copy(self, sender):
		pass
		
	def link(self, sender):
		pass
		
	def open(self, sender):
		pass
		
	def create_buttons(self, view, color):
		buttons = [
			[ 'iob:ios7_copy_outline_32', self.copy ],
			[ 'iob:link_32', self.link ],
			[ 'iob:chevron_right_32', self.open ]
		]
		# iob:ios7_compose_outline_32
		for spec in buttons:
			button = ui.Button(image = ui.Image.named(spec[0]))
			button.action = spec[1]
			button.tint_color = color
			view.add_subview(button)