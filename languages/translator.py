from argostranslate import package, translate

installed_languages = translate.get_installed_languages()
from_lang = next((lang for lang in installed_languages if lang.code == 'en'), None)

def install_language_packages():
    """
    Installs language packages for translation.

    This function installs several language translation models. 
    It specifically installs English to German, English to Spanish,
    and English to French translation models.

    The models are expected to be located in the 'languages' directory with 
    their respective file names.

    No arguments are required and the function does not return any value.
    """
    package.install_from_path("languages/translate-en_de-1_0.argosmodel")
    package.install_from_path("languages/translate-en_es-1_0.argosmodel")
    package.install_from_path("languages/translate-en_fr-1_9.argosmodel")

def translate_text(text, target_lang_code):
    """
    Translates a given text to a specified target language.

    Args:
        text (str): The text to be translated.
        target_lang_code (str): The target language code (e.g., 'en', 'es'). 
                                Only the first two characters of the code are used.

    Returns:
        str: The translated text if the target language is supported, otherwise 
             returns a message indicating that the language is not supported.

    Note:
        This function requires the source language to be English ('en'). It uses
        the installed language packages for translation. If the specified target
        language is not installed, it returns an error message.
    """
    actual_lang_code = target_lang_code[:2]
    to_lang = next((lang for lang in installed_languages if lang.code == actual_lang_code), None)

    if from_lang and to_lang:
        translation = from_lang.get_translation(to_lang)
        return translation.translate(text)
    else:
        return 'This language is not supported'
