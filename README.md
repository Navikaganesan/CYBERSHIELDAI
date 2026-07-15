🛡️ CyberShield AI

Real-time cyberbullying detection on Instagram Reels using Deep Learning and NLP.

CyberShield AI monitors comments on a user-provided Instagram Reel in real time, classifies each comment as Bullying or Non-Bullying using a trained Bidirectional LSTM (BiLSTM) model, and explains why — highlighting the exact words or phrases that drove the prediction. Built to support informed manual moderation, not to auto-delete content blindly.


✨ Features


🔴 Live comment monitoring — pulls comments from a given Instagram Reel via browser automation (Selenium)
🧠 BiLSTM-based classification — deep learning model trained on labeled cyberbullying/toxic-comment data
📊 Confidence scores — every prediction comes with a probability, not just a label
🔍 Explainability — abusive words/phrases are highlighted so predictions can be manually verified
📈 Live analytics dashboard — bullying rate over time, flagged term frequency, comment volume
✍️ Manual comment analysis — test any comment outside of live monitoring
📄 Evidence reports — export analyzed comments as CSV or PDF for documentation/escalation



🧰 Tech Stack

LayerTechnologyLanguagePythonDeep LearningTensorFlow / KerasNLPNLTKModelBidirectional LSTM (BiLSTM) + GloVe embeddingsBrowser AutomationSeleniumBackendFlaskFrontendHTML, CSS, JavaScript (Flask templates)ReportsCSV export, PDF generation


🏗️ Architecture

Instagram Reel URL
        │
        ▼
Selenium Browser Automation ──► Live Comment Scraper
        │
        ▼
NLTK Preprocessing (clean, tokenize, remove stopwords)
        │
        ▼
BiLSTM Model (TensorFlow/Keras) ──► Prediction + Confidence Score
        │
        ▼
Explanation Module (abusive word highlighting)
        │
        ▼
Flask Backend ──► Live Dashboard ──► CSV / PDF Evidence Report

BiLSTM model:

Input (tokenized comment) → Embedding (GloVe) → Bidirectional LSTM (128 units)
→ Dropout (0.4) → Dense (64, ReLU) → Output (1, Sigmoid)


📁 Project Structure

cybershield-ai/
├── app.py                     # Flask application entry point
├── scraper/
│   └── selenium_scraper.py    # Live Instagram comment retrieval
├── model/
│   ├── train_bilstm.py        # Model training script
│   ├── preprocess.py          # NLTK preprocessing pipeline
│   └── bilstm_model.h5        # Trained model weights
├── explainability/
│   └── highlight.py           # Abusive word/phrase attribution
├── reports/
│   └── report_generator.py    # CSV / PDF export
├── templates/                 # Flask HTML templates
├── static/                    # CSS / JS assets
├── notebooks/
│   └── Evaluation.ipynb       # Model training & evaluation notebook
├── requirements.txt
├── PROPOSAL.md
├── LITERATURE_SURVEY.md
└── README.md


⚙️ Installation

bash# Clone the repository
git clone https://github.com/<your-username>/cybershield-ai.git
cd cybershield-ai

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required NLTK data
python -m nltk.downloader stopwords punkt wordnet

You'll also need Google Chrome and a matching ChromeDriver installed for Selenium to work.


▶️ Usage

bashpython app.py

Then open http://localhost:5000 in your browser:


Paste an Instagram Reel URL to start live comment monitoring.
Watch comments stream in with predictions, confidence scores, and highlighted explanations.
Use Manual Analysis to test any custom comment.
Export results as CSV or PDF from the dashboard at any time.



📊 Model Performance

Evaluated on a held-out test set:

MetricValueTest Accuracy87.4%Precision (Bullying class)85.1%Recall (Bullying class)83.6%F1-Score (Bullying class)84.3%


Full training details, dataset splits, and evaluation plots are in notebooks/Evaluation.ipynb.




🚀 Future Enhancements


Support for other platforms (YouTube, X/Twitter, TikTok)
Multilingual and code-mixed language detection
Multi-class severity levels (mild / moderate / severe)
Transformer-based classifier (fine-tuned BERT)
Automated alerts when bullying rate crosses a threshold
Browser extension for real-time in-page flagging
