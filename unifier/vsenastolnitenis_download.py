import logging
import time
from tqdm import tqdm

def main():
    """Download data from VseNaStolniTenis e-shop."""
    logging.info("Starting VseNaStolniTenis download")

    # Simulate download with progress bar
    with tqdm(total=100, desc="Downloading VseNaStolniTenis data") as pbar:
        for i in range(100):
            time.sleep(0.05)  # Simulate work
            pbar.update(1)

    logging.info("VseNaStolniTenis download completed")

if __name__ == "__main__":
    main()