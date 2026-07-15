# Dataset

This folder is configured for Kaggle's large Cyberbullying Classification dataset:

```text
andrewmvd/cyberbullying-classification
```

The Kaggle file is expected to be:

```text
cyberbullying_tweets.csv
```

The training script converts it to binary labels:

- `not_cyberbullying` -> `0`
- every other cyberbullying category -> `1`

Run:

```powershell
python dataset/download_kaggle_dataset.py
python -m model.train_model
```
