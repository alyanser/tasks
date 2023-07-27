from PyQt6.QtWidgets import(
	QApplication,
	QMainWindow,
	QTableWidget,
	QTableWidgetItem,
	QMessageBox,
	QInputDialog,
	QToolBar,
	QLineEdit,
	QHeaderView
)

from PyQt6.QtGui import(
	QAction
)

from PyQt6.QtCore import(
	Qt,
	QSettings,
)

class Main_window(QMainWindow):

	def __init__(self):
		super().__init__()

		self.toolbar = QToolBar(self)
		self.addToolBar(self.toolbar)

		self.setup_toolbar()
		self.load_settings()

	def load_settings(self):
		settings = QSettings("chris", "tasks")
		settings.beginGroup("datum")

		self.api_key = settings.value("api_key")
		self.prompts = settings.value("prompts")

		if not self.api_key:
			self.api_key = ""

		if not self.prompts:
			self.prompts = []

		print(self.prompts)
		print(self.api_key)

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
	

	def on_add_prompt_clicked(self):
		(prompt, prompt_ok) = QInputDialog().getText(self, "Add New Prompt", "Prompt:")

		if not prompt_ok:
			return

		self.prompts.append(prompt)

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
