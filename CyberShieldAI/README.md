# CyberShield AI: Real-Time Instagram Cyberbullying Detection System

CyberShield AI is a local Flask project that detects cyberbullying in Instagram Reel comments using a Deep Learning Bidirectional LSTM model. It uses Selenium browser automation instead of paid APIs or the official Instagram API, keeps live evidence in memory while the app runs, and displays results in a responsive web dashboard.

## Features

- Accepts an Instagram Reel URL
- Opens the Reel with Selenium and ChromeDriver
- Supports manual Instagram login once, then stores cookies locally
- Extracts username, comment text, timestamp, and profile URL when available
- Classifies comments as `Bullying` or `Non-Bullying`
- Shows confidence score and explainable keyword reasons
- Avoids duplicate comments with an evidence hash cache
- Polls every 5 seconds for newly appearing comments
- Provides dashboard metrics, pie chart, bar chart, and trend graph
- Supports manual comment analysis
- Exports CSV and PDF evidence reports
- Runs locally with Flask, TensorFlow/Keras, NLTK, Selenium, and in-memory live storage

## Project Structure

```text
CyberShieldAI/
  app.py
  requirements.txt
  README.md
  dataset/
    download_kaggle_dataset.py
    cyberbullying_tweets.csv
  model/
    preprocess.py
    predictor.py
    train_model.py
    cyberbullying_model.h5
    tokenizer.pkl
  reports/
  scraper/
    instagram_scraper.py
  static/
    css/styles.css
    js/app.js
    images/
  templates/
    index.html
    dashboard.html
    scanner.html
    reports.html
```

## Installation

```bash
cd CyberShieldAI
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

TensorFlow wheels are Python-version specific. This project allows TensorFlow `2.20.x` to `2.21.x` because newer Python installs may not have older TensorFlow wheels available. If installation still fails, use Python 3.11 or 3.12 for the virtual environment.

If NLTK stopwords are missing, the project downloads them automatically the first time preprocessing runs.

## Train the Deep Learning Model

This project is configured for the large Kaggle dataset:

```text
andrewmvd/cyberbullying-classification
```

The downloaded Kaggle file `cyberbullying_tweets.csv` contains `tweet_text` and `cyberbullying_type`. The training script converts it into binary labels:

- `not_cyberbullying`: `0`
- all other cyberbullying categories: `1`

Train the model:

```bash
python -m model.train_model
```

If `dataset/cyberbullying_tweets.csv` is not present, the training command downloads it automatically from Kaggle using `kagglehub`. You can also download it manually:

```bash
python dataset/download_kaggle_dataset.py
```

This creates:

- `model/cyberbullying_model.h5`
- `model/tokenizer.pkl`
- `model/threshold.pkl`
- `model/evaluation_metrics.json`

The model architecture is:

```text
Input
Embedding(vocab_size=10000, embedding_dimension=128)
Bidirectional LSTM(units=64)
Dropout(0.5)
Dense(units=1, activation="sigmoid")
```

It is compiled with Adam, binary crossentropy, and accuracy, then trained for 10 epochs with batch size 32 and 20% validation split.

The training script reduces measurable class-imbalance bias by:

- fitting the tokenizer only on the training split, avoiding test-data leakage
- using stratified train/validation/test splits
- applying balanced class weights during training
- selecting the final prediction threshold using validation macro F1, so the minority `Non-Bullying` class is not ignored
- adding a small set of training-only hard examples for direct insults such as `you are dirty` and neutral uses such as `the room is dirty`

## Evaluate Precision, Recall, F1, and Confusion Matrix

Evaluate the saved model:

```bash
python -m model.evaluate_model
```

The command prints and saves:

- accuracy and balanced accuracy
- precision, recall, and F1 score
- macro precision, macro recall, macro F1, and weighted F1
- confusion matrix with TN, FP, FN, and TP counts
- per-class classification report for `Non-Bullying` and `Bullying`
- bias audit with recall gap, false-positive rate, and false-negative rate

Metrics are written to:

```text
model/evaluation_metrics.json
```

No model can be guaranteed completely unbiased from one dataset. This project now audits the measurable bias it can observe from the held-out test split and uses class balancing plus macro-F1 threshold selection to reduce majority-class bias.

## Run the App

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The app can start before training. In that case, it uses an explainable keyword fallback so the dashboard and APIs can be tested. After training, it automatically loads the saved Keras model and tokenizer.

## No Database Design

This version does not use SQLite or any other database. Analyzed comments are stored in a thread-safe Python list while Flask is running. Duplicate detection uses an in-memory evidence hash set. CSV and PDF exports are generated directly from the current live session results.

Important: when you stop or restart `python app.py`, the dashboard history is cleared. Export CSV/PDF before stopping the app if you want to keep evidence.

## API Endpoints

### POST `/predict`

Request:

```json
{
  "comment": "You are ugly"
}
```

Response:

```json
{
  "prediction": "Bullying",
  "confidence": 97.5,
  "reason": ["Detected appearance-based insult \"ugly\""]
}
```

### GET `/start_monitoring?reel_url=<url>`

Starts Selenium monitoring for the given Instagram Reel URL.

### GET `/stop_monitoring`

Stops the background monitoring loop.

### GET `/results`

Returns latest analyzed comments and dashboard summary.

### POST `/export_report`

Request:

```json
{
  "type": "csv"
}
```

Use `"pdf"` to export a PDF evidence report.

## Instagram Monitoring Notes

This project does not use paid APIs or Instagram official APIs. It uses Selenium and requires manual login in the Chrome window the first time monitoring starts. Cookies are saved to:

```text
scraper/instagram_cookies.pkl
```

Instagram changes its HTML often, so selectors may need small adjustments over time. This project is designed for ethical demonstrations and evidence assistance only. It does not automatically submit complaints, reports, messages, or any action on Instagram.


