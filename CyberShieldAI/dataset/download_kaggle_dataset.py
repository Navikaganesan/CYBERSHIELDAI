import os
import shutil

import kagglehub


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
KAGGLE_DATASET = "andrewmvd/cyberbullying-classification"
SOURCE_FILENAME = "cyberbullying_tweets.csv"
TARGET_PATH = os.path.join(DATASET_DIR, SOURCE_FILENAME)


def main():
    os.makedirs(DATASET_DIR, exist_ok=True)
    download_path = kagglehub.dataset_download(KAGGLE_DATASET)
    source_path = os.path.join(download_path, SOURCE_FILENAME)

    if not os.path.exists(source_path):
        available = os.listdir(download_path)
        raise FileNotFoundError(
            f"Could not find {SOURCE_FILENAME} in Kaggle download. Available files: {available}"
        )

    shutil.copy2(source_path, TARGET_PATH)
    print(f"Downloaded {KAGGLE_DATASET}")
    print(f"Saved dataset to {TARGET_PATH}")


if __name__ == "__main__":
    main()
