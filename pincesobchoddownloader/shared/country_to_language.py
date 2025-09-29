import locale
import logging

def get_language_code(country_code):
    """
    Map the given country code to a language code using the locale module.
    """
    try:
        # Normalize the country code to uppercase
        country_code = country_code.upper()

        # Get the locale for the given country code
        locale_code = locale.normalize(f"{country_code}_{country_code}.UTF-8")

        # Extract the language code from the locale
        language_code = locale_code.split('_')[0]

        return language_code
    except Exception as e:
        logging.error(f"Error mapping country code to language code: {e}", exc_info=True)
        raise










