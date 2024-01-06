import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject 
from PyQt5.QtGui import QIcon
from qt_material import apply_stylesheet
from languages.translator import translate_text
from logic.business_logic import generate_training_plan, json_to_excel
from logic.return_codes import ReturnCode

def get_translation(key, language_code):
    """
    Retrieves the translated text for a given key and language code.

    Args:
        key (str): The key for the text to be translated.
        language_code (str): The language code to translate the text into.

    Returns:
        str: The translated text.
    """
    return translate_text(key, language_code)

class CodeExecutionThread(QThread):
    """
    Custom QThread for executing code asynchronously in a separate thread.
    
    Attributes:
        code_executed (pyqtSignal): Signal emitted after code execution with the result.
        user_input (dict): Input data for code execution.
        language (str): Language code for translation.

    Methods:
        run(): Executes the business logic and emits the result.
    """
    code_executed = pyqtSignal(int, dict) 

    def __init__(self, user_input, language):
        super().__init__()
        self.user_input = user_input
        self.language = language 

    def run(self):
        code, result = generate_training_plan(self.user_input, self.language)
        if result is None:
            result = {}        
        self.code_executed.emit(code, result)

class CodeExecutionHandler(QObject):
    """
    Handler class for executing code and emitting the result.

    Attributes:
        code_executed (pyqtSignal): Signal emitted after code execution with the result.
        user_input (dict): Input data for code execution.

    Methods:
        execute(): Executes the business logic and emits the result.
    """
    code_executed = pyqtSignal(int, dict) 

    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input

    def execute(self):
        code, result = generate_training_plan(self.user_input)
        self.code_executed.emit(code, result)

class TrainingForm(QWidget):
    """
    Main form for the Training Plan Generator application.

    This class creates a GUI for inputting user data, submitting the data to generate a training plan,
    and exporting the plan to an Excel file.

    Attributes:
        language (str): Language code for translation.

    Methods:
        initUI(): Initializes the UI components.
        export_to_excel(): Exports the generated training plan to an Excel file.
        on_submit(): Handles the submit button click event.
        on_code_executed(code, result): Handles the code execution completion event.
        closeEvent(event): Handles the event when the form is closed.
    """
    def __init__(self, language):
        super().__init__()
        self.language = language
        self.initUI()
        self.code_execution_thread = None
        
    def initUI(self):
        self.layout = QVBoxLayout()

        min_width = 300
        
        self.current_fitness_label = QLabel(get_translation('Current Fitness State', self.language))

        self.layout.addWidget(self.current_fitness_label)

        self.running_distance_input = QLineEdit()
        self.running_distance_input.setMinimumWidth(min_width)
        self.running_distance_input.setToolTip(get_translation('Example: Max 15 km without interruption', self.language))
        self.running_distance_input.setPlaceholderText(get_translation('How long are you able to jog continuously without taking a break?', self.language))
        self.layout.addWidget(self.running_distance_input)

        self.training_frequency_input = QLineEdit()
        self.training_frequency_input.setMinimumWidth(min_width)
        self.training_frequency_input.setToolTip(get_translation('Example: 3 times per week', self.language))
        self.training_frequency_input.setPlaceholderText(get_translation('How many training sessions would you like to carry out per week?', self.language))
        self.layout.addWidget(self.training_frequency_input)

        self.specific_goals_label = QLabel(get_translation('Specific Goals', self.language))
        self.layout.addWidget(self.specific_goals_label)

        self.goal_improve_5k_input = QLineEdit()
        self.goal_improve_5k_input.setMinimumWidth(min_width)
        self.goal_improve_5k_input.setToolTip(get_translation('Example: Improving 5km time', self.language))
        self.goal_improve_5k_input.setPlaceholderText(get_translation('What specific training goal are you pursuing?', self.language))
        self.layout.addWidget(self.goal_improve_5k_input)

        self.available_time_label = QLabel(get_translation('Available Time', self.language))
        self.layout.addWidget(self.available_time_label)

        self.weekly_training_hours_input = QLineEdit()
        self.weekly_training_hours_input.setMinimumWidth(min_width)
        self.weekly_training_hours_input.setToolTip(get_translation('Example: 3 hours per week', self.language))
        self.weekly_training_hours_input.setPlaceholderText(get_translation('How many hours per week can you realistically allocate for training?', self.language))
        self.layout.addWidget(self.weekly_training_hours_input)

        self.running_experience_label = QLabel(get_translation('Running Experience', self.language))
        self.layout.addWidget(self.running_experience_label)

        self.performance_measurement_input = QLineEdit()
        self.performance_measurement_input.setMinimumWidth(min_width)
        self.performance_measurement_input.setToolTip(get_translation('Example: 5km in 25 minutes', self.language))
        self.performance_measurement_input.setPlaceholderText(get_translation('Please provide a benchmark performance for a running distance of your choice as a starting point.', self.language))
        self.layout.addWidget(self.performance_measurement_input)
        
        
        self.submit_button = QPushButton(get_translation('Submit', self.language), self)
        self.submit_button.clicked.connect(self.on_submit)
        self.layout.addWidget(self.submit_button)        
        
        self.export_excel_button = QPushButton(get_translation('Save as Excel', self.language), self)
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setEnabled(False)
        self.layout.addWidget(self.export_excel_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        self.result_label = QLabel('')
        self.layout.addWidget(self.result_label)

        self.setLayout(self.layout)
        self.setWindowTitle('Training Plan Generator')
        
        current_directory = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_directory, 'running_man_13424.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(700, 300)

    def export_to_excel(self):
        try:
            if hasattr(self, 'json_data'):
                excel_path = json_to_excel(self.json_data)
                success_message = get_translation('Excel file created: {}', self.language).format(excel_path)
                self.result_label.setText(success_message)
            else:
                no_data_message = get_translation('No data to export.', self.language)
                self.result_label.setText(no_data_message)
        except PermissionError as e:
            error_message = get_translation('Error: Permission denied.', self.language)
            self.result_label.setText(error_message + f"\n{str(e)}")

        except Exception as e:
            general_error_message = get_translation('An error occurred:', self.language)
            self.result_label.setText(general_error_message + f"\n{str(e)}")

    def on_submit(self):
        user_input = {
            get_translation('How long are you able to jog continuously without taking a break?', self.language): self.running_distance_input.text(),
            get_translation('How many training sessions would you like to carry out per week?', self.language): self.training_frequency_input.text(),
            get_translation('What specific training goal are you pursuing?', self.language): self.goal_improve_5k_input.text(),
            get_translation('How many hours per week can you realistically allocate for training?', self.language): self.weekly_training_hours_input.text(),
            get_translation('Please provide a benchmark performance for a running distance of your choice as a starting point.', self.language): self.performance_measurement_input.text(),
            'In which language should the answer be given?': self.language
        }
        
        # Disable user interaction and show the progress bar
        self.setEnabled(False)
        self.progress_bar.show()
        processing_message = get_translation('Processing may take a few minutes...', self.language)
        self.result_label.setText(processing_message)
        # Start code execution in a separate thread
        self.code_execution_thread = CodeExecutionThread(user_input,self.language)
        self.code_execution_thread.code_executed.connect(self.on_code_executed)
        self.code_execution_thread.start()
        code_execution_handler = CodeExecutionHandler(user_input)
        code_execution_handler.moveToThread(self.code_execution_thread)
        self.code_execution_thread.started.connect(code_execution_handler.execute)
        code_execution_handler.code_executed.connect(self.on_code_executed)
        self.code_execution_thread.start()

        
    def on_code_executed(self, code, result):
        self.setEnabled(True)
        self.progress_bar.hide()

        if code == ReturnCode.SUCCESS:
            try:
                self.json_data = result
                success_message = get_translation('Training plan successfully generated.', self.language)
                self.result_label.setText(success_message)
                self.export_excel_button.setEnabled(True)
            except json.JSONDecodeError:
                json_error_message = get_translation('Error parsing JSON data.', self.language)
                self.result_label.setText(json_error_message)
                self.export_excel_button.setEnabled(False)
        else:
            self.export_excel_button.setEnabled(False)
            error_message_key = {
                ReturnCode.INPUT_TOO_LONG: 'Input too long. Please limit to 250 words.',
                ReturnCode.API_ERROR: 'Error communicating with the API.',
                ReturnCode.JSON_ERROR: 'Trainingplan could not be generated'
            }.get(code, 'Error communicating with the API.')
            error_message = get_translation(error_message_key, self.language)

            if code == ReturnCode.JSON_ERROR:
                additional_message = get_translation('no_excel_export_available', self.language)
                error_message += "\n\n" + additional_message

            self.result_label.setText(error_message)


    def closeEvent(self, event):
        # Ensure the code execution thread is stopped before closing the application
        if self.code_execution_thread and self.code_execution_thread.isRunning():
            self.code_execution_thread.terminate()
            self.code_execution_thread.wait()
        event.accept()


if __name__ == '__main__':
    """
    Main entry point of the application. Initializes and starts the application.
    """
    language = get_system_language()
    app = QApplication([])
    apply_stylesheet(app, theme='light_blue.xml')
    ex = TrainingForm(language)
    ex.show()
    app.exec_()
