import logging
import time
from tqdm import tqdm

def main():
    """Download data from Gewo e-shop."""
    logging.info("Starting Gewo download")

    # Simulate download with progress bar
    with tqdm(total=100, desc="Downloading Gewo data") as pbar:
        for i in range(100):
            time.sleep(0.05)  # Simulate work
            pbar.update(1)

    logging.info("Gewo download completed")

if __name__ == "__main__":
    main()