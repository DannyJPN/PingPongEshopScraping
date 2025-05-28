import logging
import time
from tqdm import tqdm

def main():
    """Download data from SportSpin e-shop."""
    logging.info("Starting SportSpin download")

    # Simulate download with progress bar
    with tqdm(total=100, desc="Downloading SportSpin data") as pbar:
        for i in range(100):
            time.sleep(0.05)  # Simulate work
            pbar.update(1)

    logging.info("SportSpin download completed")

if __name__ == "__main__":
    main()
