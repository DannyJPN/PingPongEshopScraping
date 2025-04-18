import logging

def generate_eshop_scripts(eshop_names):
    """Generate Python script names for each e-shop without creating files."""
    script_names = []
    for eshop_name in eshop_names:
        script_name = eshop_name.replace(" ", "_").lower() + "_download.py"
        script_names.append(script_name)
        logging.info(f"Generated script name: {script_name}")
    logging.debug(f"All generated script names: {script_names}")
    return script_names
