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

import openai

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
		central_layout = QVBoxLayout(self.central_widget)

		self.input_line = QLineEdit(self.central_widget)
		self.input_line.setPlaceholderText("Input Text")

		central_layout.addWidget(self.input_line)

		self.prompt_table = QTableWidget(self.central_widget)

		central_layout.addWidget(self.prompt_table)

		self.prompt_table.setColumnCount(3)
		self.prompt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
		self.prompt_table.setHorizontalHeaderLabels(['Enabled', 'Prompt', 'Chain Index'])
		self.prompt_table.verticalHeader().setVisible(False)

	def load_settings(self):
		settings = QSettings("chris", "tasks", self)
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
		settings = QSettings("chris", "tasks", self)
		settings.beginGroup("datum")
		settings.clear()

		settings.setValue("api_key", self.api_key)
		settings.setValue("prompts", self.prompts)

	def setup_toolbar(self):
		self.run_action = QAction("Run", self.toolbar)
		self.add_prompt_action = QAction("Add New Prompt", self.toolbar)
		self.set_api_key_action = QAction("Set API Key", self.toolbar)

		self.add_prompt_action.triggered.connect(self.on_add_prompt_clicked)
		self.run_action.triggered.connect(self.on_run_clicked)
		self.set_api_key_action.triggered.connect(self.on_api_key_clicked)

		self.toolbar.addActions([self.run_action, self.add_prompt_action, self.set_api_key_action])

	def display_error_box(self, error_message):
		msg_box = QMessageBox(self)
		msg_box.setText(error_message)
		msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
		msg_box.setIcon(QMessageBox.Icon.Critical)
		msg_box.exec()

	def on_run_clicked(self):

		if len(self.api_key) == 0:
			return self.display_error_box("API Key is not given. Please set it before running!")

		openai.api_key = self.api_key
		input_text = self.input_line.text()

		if len(input_text) == 0:
			return self.display_error_box("Input text cannot be empty!")

		try:
			completion = openai.ChatCompletion.create(
				model="gpt-3.5-turbo", 
				messages=[{"role": "user", "content": input_text}],
			)
		except Exception as e:
			return self.display_error_box("[ERROR FROM OPENAI] " + str(e))

		print(completion)

	def add_prompt_to_layout(self, prompt):
		self.prompt_table.setRowCount(self.prompt_table.rowCount() + 1)

		check_box = QCheckBox(self.prompt_table)
		check_box.stateChanged.connect(self.on_checkbox_clicked)

		row = self.prompt_table.rowCount() - 1
		assert row >= 0

		self.prompt_table.setCellWidget(row, 0, check_box)
		self.prompt_table.setCellWidget(row, 1, QLineEdit(prompt))
		self.prompt_table.setCellWidget(row, 2, QLabel(""))

	def on_checkbox_clicked(self, check):

		for i in range(0, self.prompt_table.rowCount()):
			check_box = self.prompt_table.cellWidget(i, 0)

			if check_box == self.sender():
				prompt_rank_label = self.prompt_table.cellWidget(i, 2)

				if check:
					self.chained_prompts.append(prompt_rank_label)
				else:
					self.chained_prompts.remove(prompt_rank_label)
					prompt_rank_label.setText("")

				self.update_chained_prompts_ranking()
				break

	def update_chained_prompts_ranking(self):
		i = 1

		for prompt_rank_label in self.chained_prompts:
			prompt_rank_label.setText(str(i))
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
