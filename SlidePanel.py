# coding: utf-8
import ui

class SlidePanel(ui.View):
	
	def __init__(self, active_edge_width = 20, panel_width = 300, from_left = True):
		self.panel_width = panel_width
		self.total_width = panel_width + active_edge_width
		self.width = self.total_width
		self.edge = active_edge_width
		self.left = from_left
		
		self.hiding = True
		self.kb_y = 0
		self.speed = 0.15
		self.background_color = 'transparent'
		self.first = True
		
	def hidden_x(self):
		return 0 - self.width + self.edge if self.left else self.superview.width - self.edge
		
	def visible_x(self):
		return 0 # if self.left else self.superview.width - self.panel_width
		
	def layout(self):
		if self.first:
			self.x = self.hidden_x()
			self.first = False
		if self.kb_y == 0:
			self.height = self.superview.height
		else:
			self.height = self.kb_y - self.hierarchy_y()
		for view in self.subviews:
			if self.left:
				view.frame = (0, 0, self.panel_width - self.edge, self.height)
			else:
				view.frame = (self.superview.width - self.panel_width, 0, self.panel_width, self.height)
			break
			
	def hierarchy_y(self):
		dy = 0
		view = self
		while view:
			dy += view.y
			view = view.superview
		return dy
			
	def touch_began(self, touch):
		self.touch_start_time = touch.timestamp
		if not self.left:
			self.width = self.superview.width
			if self.hiding:
				self.x = self.panel_width
		
	def touch_moved(self, touch):
		new_x = self.x + touch.location[0] - touch.prev_location[0]
		if self.left:
			new_x = min(0, new_x)
			new_x = max(self.hidden_x(), new_x)
		else:
			new_x = min(self.superview.width - self.edge, new_x)
			new_x = max(0, new_x)
		self.x = new_x
		
	def touch_ended(self, touch):
		touch_duration = (touch.timestamp - self.touch_start_time) * 1000
		if touch_duration < 300:
			if self.hiding:
				self.reveal()
			else:
				self.hide()
		else:
			xd = touch.location[0] - touch.prev_location[0]
			if not self.left: xd = 0 - xd
			if xd < 0:
				self.hide()
			else:
				self.reveal()
		
	def hide(self):
		self.hiding = True
		if self.left: self.width = self.total_width
		def animation(): self.x = self.hidden_x()
		ui.animate(animation, self.speed)
		
	def reveal(self):
		self.hiding = False
		if self.left:
			self.width = self.superview.width
		def animation():
			self.x = self.visible_x()
		ui.animate(animation, self.speed)
		
	def keyboard_frame_did_change(self, frame):
		self.kb_y = frame[1]
		self.layout()

if __name__ == "__main__":
	base = ui.Label()
	base.text = "Main screen - swipe from the sides"
	base.alignment = ui.ALIGN_CENTER
	base.background_color ='#c4d8ff'	
	
	panel = SlidePanel()
	panel_content = ui.TextView()
	panel_content.text = "This is the sidebar content. Swipe from the right or click anywhere to the right of the sidebar to hide it."
	panel.add_subview(panel_content)
	
	panel2 = SlidePanel(from_left=False)
	panel2_content = ui.TextView()
	panel2_content.text = "This is the other sidebar content. Swipe from the left or click anywhere to the left of the sidebar to hide it."
	panel2.add_subview(panel2_content)
	
	base.add_subview(panel)
	base.add_subview(panel2)
	base.present()