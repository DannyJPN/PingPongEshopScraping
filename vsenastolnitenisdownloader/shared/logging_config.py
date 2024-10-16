import logging
import colorlog
import json
import os
import sys
def setup_logging(debug=False):
    # Load color configuration from the JSON file
    with open(os.path.join(os.path.dirname(sys.argv[0]),'shared/log_colors.json'), 'r') as f:
        color_config = json.load(f)

    # Set logging level based on the debug flag
    level = logging.DEBUG if debug else logging.INFO

    # Define a formatter using colorlog with a custom color scheme from the JSON
    log_format = '%(log_color)s%(levelname)s: %(message)s'
    formatter = colorlog.ColoredFormatter(
        log_format,
        log_colors={
            'DEBUG': color_config["DEBUG"],
            'INFO': color_config["INFO"],
            'WARNING': color_config["WARNING"],
            'ERROR': color_config["ERROR"],
            'CRITICAL': color_config["CRITICAL"],
        }
    )

    # Set up the console handler with the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Configure the root logger
    logging.basicConfig(level=level, handlers=[handler])
