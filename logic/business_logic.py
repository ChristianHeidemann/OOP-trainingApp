from openai import OpenAI
import os
from logic.return_codes import ReturnCode
from languages.translator import translate_text
import json
import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)

format = '{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"TrainingPlan":{"type":"array","items":{"type":"object","properties":{"week":{"type":"integer"},"day":{"type":"string"},"Activity":{"type":"object","properties":{"Warmup":{"type":"object","properties":{"Duration":{"type":"string"},"Description":{"type":"string"}},"required":["Duration","Description"]},"MainSession":{"type":"object","properties":{"Duration":{"type":"string"},"Distance":{"type":"integer","minimum":0},"Speed":{"type":"string"},"Description":{"type":"string"},"Intervals":{"type":"array","items":{"type":"object","properties":{"Effort":{"type":"object","properties":{"Distance":{"type":"integer","minimum":0},"Speed":{"type":"string"}},"required":["Distance","Speed"]},"Rest":{"type":"object","properties":{"Duration":{"type":"string"},"Speed":{"type":"string"}},"required":["Duration","Speed"]}},"required":["Effort","Rest"]}}},"required":["Duration","Description"]},"Cooldown":{"type":"object","properties":{"Duration":{"type":"string"},"Description":{"type":"string"}},"required":["Duration","Description"]}},"required":["Warmup","MainSession","Cooldown"]},"Notes":{"type":"string"}},"required":["week","day","Activity","Notes"]}},"AdditionalNotes":{"type":"string"}},"required":["TrainingPlan","AdditionalNotes"]}'


# Initialize OpenAI client with the API key
client = OpenAI(api_key=os.environ.get("OPENAI_KEY_TRAININGPLAN"))

def flatten_json(y):
    """
    Flattens a nested JSON object.

    Args:
        y (dict or list): The JSON object to flatten.

    Returns:
        dict: A flattened version of the JSON object where each key is a path through the original object.
    """
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
													   
                flatten(x[a], f"{name}{a}_")
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, f"{name}{i}_")
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

def json_to_excel(json_data):
    """
    Converts JSON data to an Excel file.

    Args:
        json_data (dict): JSON data to be converted.

    Returns:
        str: The path to the created Excel file.
    """
    if 'TrainingPlan' in json_data:
        flat_data = [flatten_json(item) for item in json_data['TrainingPlan']]
        df = pd.DataFrame(flat_data)
    else:
        logger.debug("The TrainingPlan key is not present in the JSON data")
        flat_data = flatten_json(json_data)
        df = pd.DataFrame([flat_data]) 

    excel_path = 'trainingsplan.xlsx'
    df.to_excel(excel_path, index=False)
    return excel_path

def remove_comment_and_validate_json(json_string):
    """
    Removes comments from a JSON string and validates it.

    Args:
        json_string (str): The JSON string to validate.

    Returns:
        tuple: A tuple containing the parsed JSON and a boolean indicating validity.
    """
    lines = json_string.split("\n")
    cleaned_lines = []
    logger.debug("remove_comment_and_validate_json Original JSON string: %s", json_string)

    for line in lines:
        comment_start = line.find("//")
        if comment_start != -1:
            post_comment = line[comment_start+2:]
            line = line[:comment_start].rstrip(", \t ")
            structure_chars = []
            for char in reversed(post_comment):
                if char in ['}', ']', ')']:
                    structure_chars.append(char)
                else:
                    break
            line += ''.join(reversed(structure_chars))
        cleaned_lines.append(line)

    cleaned_json_string = "\n".join(cleaned_lines)
    logger.debug("remove_comment_and_validate_json cleaned JSON string: %s", cleaned_json_string)

    try:
        parsed_json = json.loads(cleaned_json_string)
        return parsed_json, True
    except json.JSONDecodeError as e:
        logger.error("Error while parsing JSON: %s", e)
        return None, False

def find_training_plan_in_text(text):
    """
    Searches for a training plan in the provided text.

    Args:
        text (str): The text to search within.

    Returns:
        dict or None: The parsed JSON training plan, or None if not found.
    """
    pattern = r'"TrainingPlan"\s*:\s*\[.*?\](,|})'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        json_fragment = match.group(0).rstrip(',')

        if json_fragment[-1] != '}':
            json_string = '{' + json_fragment + '}'
        else:
            json_string = '{' + json_fragment

        try:
            parsed_json = json.loads(json_string)
            return parsed_json
        except json.JSONDecodeError:
            return None
    else:
        return None

def call_openai_api(user_input, model="gpt-4-1106-preview", temperature=0.1):
    """
    Makes a request to the OpenAI API.

    Args:
        user_input (str): The input string for the API.
        model (str, optional): The model to use. Defaults to "gpt-4-1106-preview".
        temperature (float, optional): The temperature setting for the API. Defaults to 0.1.

    Returns:
        str or None: The content of the response, or None if an error occurs.
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": user_input}],
            model=model,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("OpenAI API request error: %s", e)
        return None

def generate_training_plan(user_input, language='en_US'):
    """
    Generates a training plan based on the user input and language.

    Args:
        user_input (dict): The input data for generating the training plan.
        language (str, optional): The language code. Defaults to 'en_US'.

    Returns:
        tuple: A tuple containing a return code and the training plan or None.
    """
    user_input_string = "; ".join(f"{key}: {value}" for key, value in user_input.items())
    # Ensuring input is within the expected token range
    if len(user_input_string) > 700:  # approximation
        return ReturnCode.INPUT_TOO_LONG, None
    try:
        training_plan_request = translate_text("Please generate a training plan for 4 weeks", language)
        translated_text = translate_text("Return in the following JSON schema (without returning the schema itself): ", language)
        return_json_schema = translated_text + format
        user_input_string += f";{return_json_schema};{training_plan_request}"
        assistant_reply = call_openai_api(user_input_string)
        logger.debug("conplete response: %s", assistant_reply)
        # extract json trainingsplan
        start_marker = "```json"
        end_marker = "```"
        start = assistant_reply.find(start_marker) + len(start_marker) + 1
        end = assistant_reply.find(end_marker, start)
        if start >= len(start_marker) + 1 and end != -1:
            json_string = assistant_reply[start:end].strip()
            parsed_json, is_valid = remove_comment_and_validate_json(json_string)
            return ReturnCode.SUCCESS, parsed_json
        else:
            json_string = find_training_plan_in_text(assistant_reply)
            if not isinstance(json_string, dict) and (json_string is None or json_string.strip() in ('{}', '')):
                question = "Please correct the following text into a valid syntactically correct JSON format (without comment lines). \n"
                user_input_string += f";{question};{assistant_reply}"
                assistant_reply = call_openai_api(user_input_string)
                start = assistant_reply.find(start_marker) + len(start_marker) + 1
                end = assistant_reply.find(end_marker, start)
                if start >= len(start_marker) + 1 and end != -1:
                    try:
                        json_string = json.loads(assistant_reply[start:end].strip())
                    except json.JSONDecodeError as e:
                        logger.error("Error while parsing JSON string: %s", e)
                        json_string = None  
            return ReturnCode.SUCCESS, json_string

    except Exception as e:
        logger.error("Error: %s", e)
        return ReturnCode.API_ERROR, None
