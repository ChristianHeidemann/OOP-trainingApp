import pytest
import os
print(os.getcwd())

from logic.business_logic import flatten_json, json_to_excel, remove_comment_and_validate_json, find_training_plan_in_text, call_openai_api, generate_training_plan
from logic.return_codes import ReturnCode
import logging
logging.basicConfig(level=logging.DEBUG,
                    filename='test_log.txt', 
                    filemode='a', 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockResponse:
    def __init__(self):
        self.choices = [type('choice', (), {'message': type('message', (), {'content': 'Mocked response'})})]

def test_flatten_json():
    input_json = {"a": {"b": {"c": "d"}}}

    expected_output = {"a_b_c": "d"}
    assert flatten_json(input_json) == expected_output

def test_json_to_excel():
    input_json = {"TrainingPlan": [{"week": 1, "day": "Monday"}]}
    expected_file = 'trainingsplan.xlsx'
    json_to_excel(input_json)
    assert os.path.isfile(expected_file)
    os.remove(expected_file)

def test_remove_comment_and_validate_json():
    input_json = '{"key": "value" // Kommentar }'
    expected_output = ({"key": "value"}, True)
    output = remove_comment_and_validate_json(input_json)
    assert remove_comment_and_validate_json(input_json) == expected_output

def test_find_training_plan_in_text():
    input_text = 'Some random text "TrainingPlan": [{"week": 1, "day": "Monday"}]} more text'
    expected_output = {"TrainingPlan": [{"week": 1, "day": "Monday"}]}
    assert find_training_plan_in_text(input_text) == expected_output

"""
def test_call_openai_api(mocker):
    mocker.patch('business_logic.client.chat.completions.create', return_value=MockResponse())
    assert call_openai_api("hello") is not None

def test_generate_training_plan(mocker):
    mocker.patch('business_logic.call_openai_api', return_value="Mocked response")
    mocker.patch('business_logic.translate_text', return_value="Translated text")
    assert generate_training_plan({"key": "value"})[0] == ReturnCode.SUCCESS
"""