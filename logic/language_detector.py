import locale

def get_system_language():
    # Obtaining the system language
    language, _ = locale.getdefaultlocale()
    return language


