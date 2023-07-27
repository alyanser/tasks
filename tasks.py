from PyQt6.QtWidgets import(
	QApplication,
	QPushButton,
	QMainWindow,
	QRadioButton,
	QCheckBox,
	QTableWidget,
	QTableWidgetItem,
	QMessageBox,
	QInputDialog,
	QScrollArea,
	QTreeWidgetItem,
	QTreeWidget,
	QWidget,
	QLabel,
	QToolBar,
	QHBoxLayout,
	QVBoxLayout,
	QLineEdit,
	QHeaderView
)

from PyQt6.QtGui import(
	QAction
)

from PyQt6.QtCore import(
	Qt,
	QSettings,
	QObject
)

class Main_window(QMainWindow):

	def __init__(self):
		super().__init__()
		self.chained_prompts = []

		self.toolbar = QToolBar(self)
		self.addToolBar(self.toolbar)

		self.central_widget = QWidget(self)
		self.setCentralWidget(self.central_widget)

		self.setup_toolbar()
		self.setup_central_widget()

		self.load_settings()
	
	def setup_central_widget(self):
		layout = QVBoxLayout(self.central_widget)

		input_line = QLineEdit(self)
		input_line.setPlaceholderText("Input Text")

		layout.addWidget(input_line)

		top_hlayout = QHBoxLayout()
		layout.addLayout(top_hlayout)

		bot_vlayout = QVBoxLayout()

		top_hlayout.addLayout(bot_vlayout)

		scroll_area = QScrollArea()
		bot_vlayout.addWidget(scroll_area)

		self.scroll_layout = QVBoxLayout()
		scroll_area.setLayout(self.scroll_layout)

	def load_settings(self):
		settings = QSettings("chris", "tasks")
		settings.beginGroup("datum")

		self.api_key = settings.value("api_key")
		self.prompts = settings.value("prompts")

		if not self.api_key:
			self.api_key = ""

		if not self.prompts:
			self.prompts = []

		for prompt in self.prompts:
			self.add_prompt_to_layout(prompt)

	def store_settings(self):
		settings = QSettings("chris", "tasks")
		settings.beginGroup("datum")
		settings.clear()

		settings.setValue("api_key", self.api_key)
		settings.setValue("prompts", self.prompts)

	def setup_toolbar(self):
		self.add_prompt_action = QAction("Add New Prompt")
		self.set_api_key_action = QAction("Set API Key")

		self.add_prompt_action.triggered.connect(self.on_add_prompt_clicked)
		self.set_api_key_action.triggered.connect(self.on_api_key_clicked)

		self.toolbar.addActions([self.add_prompt_action, self.set_api_key_action])

	def add_prompt_to_layout(self, prompt):
		layout = QHBoxLayout()
		self.scroll_layout.addLayout(layout)

		label = QLabel(prompt)
		check_box = QCheckBox()
		label.setBuddy(check_box)

		layout.addWidget(check_box)
		layout.addWidget(label)
		layout.addWidget(QLabel(""))

		check_box.clicked.connect(self.on_checkbox_clicked)

	def on_checkbox_clicked(self, check):
		layout = self.sender().parent().layout()

		for i in range(0, layout.count()):
			h_layout = layout.itemAt(i)

			if h_layout.itemAt(0).widget() == self.sender():
				if check:
					self.chained_prompts.append(h_layout)
				else:
					self.chained_prompts.remove(h_layout)
					h_layout.itemAt(2).widget().setText("")

				self.update_chained_prompts_ranking()
				break

	def update_chained_prompts_ranking(self):
		i = 1

		for layout in self.chained_prompts:
			counter_label = layout.itemAt(2).widget()
			counter_label.setText(str(i))
			i = i + 1

	def on_add_prompt_clicked(self):
		(prompt, prompt_ok) = QInputDialog().getText(self, "Add New Prompt", "Prompt:")

		if not prompt_ok:
			return

		self.prompts.append(prompt)
		self.add_prompt_to_layout(prompt)

	def on_api_key_clicked(self):
		(api_key, api_key_ok) = QInputDialog().getText(self, "Set API Key", "API Key:", QLineEdit.EchoMode.Normal, self.api_key);

		if not api_key_ok:
			return

		self.api_key = api_key

def main():
	app = QApplication([])
	window = Main_window()
	window.show()
	app.exec()
	window.store_settings()

if __name__ == '__main__':
	main()
