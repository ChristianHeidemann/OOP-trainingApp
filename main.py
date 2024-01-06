from PyQt5.QtWidgets import QApplication
from gui.form_layout import TrainingForm
from logic.language_detector import get_system_language

def main():
    """
    The main function to start the training plan application.

    This function initializes the application, sets up the main form with 
    the system's language, and starts the application's event loop.

    The system language is determined using the get_system_language() function 
    from the logic.language_detector module. A QApplication object is created, 
    and an instance of TrainingForm is initialized with the detected language.
    The form is then displayed, and the QApplication event loop is started.

    No arguments are required for this function.

    Returns:

    Example:

    Notes:
        This function is intended to be used as the entry point for running
        the TrainingPlan application. It should be called only if the 
        __name__ is "__main__" to ensure that the application starts 
        correctly when the script is executed directly.
    """
    print("Hello, welcome to the trainingplanApp!")
    language = get_system_language()
    app = QApplication([])
    ex = TrainingForm(language)
    ex.show()
    app.exec()

if __name__ == "__main__":
    main()
