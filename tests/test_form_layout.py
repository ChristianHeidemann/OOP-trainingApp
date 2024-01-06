import sys
from PyQt5.QtWidgets import QApplication
from gui.form_layout import TrainingForm
from langdetect import detect


def test_training_form_multilanguage():
    app = QApplication(sys.argv)

    form_de = TrainingForm('de_DE')
    assert form_de.current_fitness_label.text() != "Current Fitness State"
    assert form_de.running_distance_input.placeholderText() != "How long are you able to jog continuously without taking a break?"
    assert detect(form_de.current_fitness_label.text()) == 'de'
    
    form_en = TrainingForm('en_US')
    assert form_en.current_fitness_label.text() == "Current Fitness State"
    assert form_en.running_distance_input.placeholderText() == "How long are you able to jog continuously without taking a break?"
    assert detect(form_en.current_fitness_label.text()) == 'en'

    form_es = TrainingForm('es_ES')
    assert form_es.current_fitness_label.text() != "Current Fitness State"
    assert form_es.running_distance_input.placeholderText() != "How long are you able to jog continuously without taking a break?"
    assert detect(form_es.current_fitness_label.text()) == 'es'

    app.exit()
