from PyQt6.QtWidgets import(
	QApplication,
	QMainWindow,
	QStatusBar,
	QCheckBox,
	QTableWidget,
	QProgressBar,
	QMessageBox,
	QFileDialog,
	QInputDialog,
	QWidget,
	QLabel,
	QToolBar,
	QVBoxLayout,
	QLineEdit,
	QPlainTextEdit,
	QHeaderView,
)

from PyQt6.QtGui import(
	QAction,
	QDesktopServices,
)

from PyQt6.QtCore import(
	Qt,
	QSettings,
	QUrl
)

import openai
import sys
import datetime
from openpyxl import Workbook

class Main_window(QMainWindow):

	def __init__(self):
		super().__init__()
		self.chained_prompts = []

		self.toolbar = QToolBar(self)
		self.addToolBar(self.toolbar)

		self.progress_bar = QProgressBar(self)
		self.progress_bar.setTextVisible(True)
		self.progress_bar.setRange(0, 0)
		self.progress_bar.setValue(0)

		self.setStatusBar(QStatusBar(self))
		self.statusBar().addPermanentWidget(self.progress_bar, 1)

		self.central_widget = QWidget(self)
		self.setCentralWidget(self.central_widget)

		self.setup_toolbar()
		self.setup_central_widget()

		self.load_settings()
	
	def setup_central_widget(self):
		central_layout = QVBoxLayout(self.central_widget)

		self.input_line = QPlainTextEdit(self.central_widget)
		self.input_line.setPlaceholderText("Input Text")

		central_layout.addWidget(self.input_line)

		self.prompt_table = QTableWidget(self.central_widget)

		central_layout.addWidget(self.prompt_table)

		self.prompt_table.setColumnCount(3)
		self.prompt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
		self.prompt_table.setHorizontalHeaderLabels(['Enabled', 'Prompts', 'Chain Index'])

	def load_settings(self):
		settings = QSettings("chris", "tasks", self)
		settings.beginGroup("datum")

		self.api_key = settings.value("api_key")
		prompts = settings.value("prompts")

		input_line_text = settings.value("input_text")

		if input_line_text:
			self.input_line.insertPlainText(input_line_text)

		if not self.api_key:
			self.api_key = ""

		self.output_path = settings.value("output_path")

		if not self.output_path:
			self.output_path = "."

		if not prompts:
			prompts = []

		for prompt in prompts:
			self.add_prompt_to_layout(prompt)

		chained_nums = settings.value("chained_nums")

		if chained_nums and len(chained_nums) > 0:
			for num in chained_nums:
				check_box = self.prompt_table.cellWidget(int(num), 0)
				check_box.setCheckState(Qt.CheckState.Checked)

	def store_settings(self):
		settings = QSettings("chris", "tasks", self)
		settings.beginGroup("datum")
		settings.clear()

		prompts = []

		for i in range(0, self.prompt_table.rowCount()):
			prompts.append(self.prompt_table.cellWidget(i, 1).text())

		if len(prompts) > 0:
			settings.setValue("prompts", prompts)

		settings.setValue("api_key", self.api_key)

		if len(self.input_line.toPlainText()) != 0:
			settings.setValue("input_text", self.input_line.toPlainText())

		chained_nums = []

		for _, _, chain_num in self.chained_prompts:
			chained_nums.append(chain_num)

		if len(chained_nums) > 0:
			settings.setValue("chained_nums", chained_nums)

		settings.setValue("output_path", self.output_path)

	def setup_toolbar(self):
		self.run_action = QAction("Run", self.toolbar)
		self.add_prompt_action = QAction("Add New Prompt", self.toolbar)
		self.remove_prompt_action = QAction("Remove a Prompt", self.toolbar)
		self.set_api_key_action = QAction("Set API Key", self.toolbar)
		self.set_output_path_action = QAction("Set Output Path", self.toolbar)

		self.add_prompt_action.triggered.connect(self.on_add_prompt_clicked)
		self.remove_prompt_action.triggered.connect(self.on_remove_prompt_clicked)
		self.run_action.triggered.connect(self.on_run_clicked)
		self.set_api_key_action.triggered.connect(self.on_api_key_clicked)
		self.set_output_path_action.triggered.connect(self.on_set_output_path_clicked)

		self.toolbar.addActions([self.run_action, self.add_prompt_action, self.remove_prompt_action, self.set_api_key_action, self.set_output_path_action])

	def on_set_output_path_clicked(self):
		output_path = QFileDialog.getExistingDirectory()

		if len(output_path) == 0:
			return

		self.output_path = output_path

	def on_remove_prompt_clicked(self):

		if self.prompt_table.rowCount() == 0:
			return self.display_error_box("There isn't any prompt added to remove!")

		(prompt_num, prompt_num_ok) = QInputDialog().getInt(self, "Remove a Prompt", "Prompt number:")

		if not prompt_num_ok:
			return

		if prompt_num <= 0 or prompt_num > self.prompt_table.rowCount():
			return self.display_error_box(f"Invalid prompt number: {prompt_num}. Valid numbers: 1 -- {self.prompt_table.rowCount()}")

		check_box = self.prompt_table.cellWidget(prompt_num - 1, 0)

		if check_box.checkState() == Qt.CheckState.Checked:
			check_box.setCheckState(Qt.CheckState.Unchecked)

		self.prompt_table.removeRow(prompt_num - 1)

	def display_error_box(self, error_message):
		msg_box = QMessageBox(self)
		msg_box.setText(error_message)
		msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
		msg_box.setIcon(QMessageBox.Icon.Critical)
		return msg_box.exec()

	def on_run_clicked(self):

		if len(self.api_key) == 0:
			return self.display_error_box("API Key is not given. Please set it before running!")

		openai.api_key = self.api_key
		input_text = self.input_line.toPlainText()

		if len(input_text) == 0:
			return self.display_error_box("Input text cannot be empty!")

		if len(self.chained_prompts) == 0:
			return self.display_error_box("No prompts are added/selected. Atleast one prompt is required!")

		replies = []

		self.progress_bar.setRange(0, len(self.chained_prompts))
		self.progress_bar.setValue(0)

		for prompt_text_label, _, i in self.chained_prompts:
			message = prompt_text_label.text() + '\n\n' + (replies[-1][1] if len(replies) > 0 else input_text)

			try:
				reply = openai.ChatCompletion.create(
					model="gpt-3.5-turbo", 
					messages=[{"role": "user", "content": message}],
				)

				reply = reply["choices"][0]["message"]["content"]

				self.log_to_file(message, reply)
				replies.append((prompt_text_label.text(), reply))
				self.progress_bar.setValue(i + 1)
			except Exception as e:
				self.progress_bar.setValue(0)
				self.progress_bar.setRange(0, 0)
				return self.display_error_box(str(e))

		excel_filename = self.log_to_excel(replies)

		msg_box = QMessageBox(self)
		msg_box.setText(f"All prompts ran successfully. Output saved to: {self.output_path}\nWould you like to open the excel file containing final output?")
		msg_box.setIcon(QMessageBox.Icon.Information)

		msg_box.addButton(QMessageBox.StandardButton.Yes)
		msg_box.addButton(QMessageBox.StandardButton.No)
		msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

		if msg_box.exec() == QMessageBox.StandardButton.Yes:
			QDesktopServices.openUrl(QUrl.fromLocalFile(excel_filename))

		self.progress_bar.setValue(0)
		self.progress_bar.setRange(0, 0)

	def generate_output_path(self, extension):
		current_datetime = str(datetime.datetime.now().strftime("%Y-%m-%d.%H-%M-%S.%f"))
		filename = self.output_path + '/' + current_datetime + '.' + extension
		return filename

	def log_to_excel(self, messages):
		wb = Workbook()
		ws = wb.active

		for prompt, message in messages:
			ws.append([prompt, message])

		filename = self.generate_output_path('xlsx')
		wb.save(filename)
		return filename

	def log_to_file(self, message, reply):
		filename = self.generate_output_path('txt')

		with open(filename, 'w') as f:
			f.write(message + '\n\n' + reply)

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
				prompt_text_label = self.prompt_table.cellWidget(i, 1)

				if check:
					self.chained_prompts.append((prompt_text_label, prompt_rank_label, i))
				else:
					self.chained_prompts.remove((prompt_text_label, prompt_rank_label, i))
					prompt_rank_label.setText("")

				self.update_chained_prompts_ranking()
				break

	def update_chained_prompts_ranking(self):
		i = 1

		for _, prompt_rank_label, _ in self.chained_prompts:
			prompt_rank_label.setText(str(i))
			i = i + 1

	def on_add_prompt_clicked(self):
		(prompt, prompt_ok) = QInputDialog().getText(self, "Add New Prompt", "Prompt:")

		if not prompt_ok:
			return

		self.add_prompt_to_layout(prompt)

	def on_api_key_clicked(self):
		(api_key, api_key_ok) = QInputDialog().getText(self, "Set API Key", "API Key:", QLineEdit.EchoMode.Normal, self.api_key);

		if not api_key_ok:
			return

		self.api_key = api_key

def main():
	app = QApplication(sys.argv)

	with open("stylesheet.qss", 'r') as f:
		stylesheet = f.read()
		app.setStyleSheet(stylesheet)

	window = Main_window()
	window.show()
	app.exec()
	window.store_settings()

if __name__ == '__main__':
	main()
