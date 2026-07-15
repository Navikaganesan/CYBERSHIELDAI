# 🛡️ CyberShield AI – Real-Time Cyberbullying Detection System

**CyberShield AI** is a Deep Learning-powered web application that detects cyberbullying comments in real time from Instagram Reels using browser automation and Natural Language Processing (NLP). The system classifies comments as **Bullying** or **Non-Bullying**, provides a confidence score and explanation for each prediction, and generates evidence reports to assist users in identifying potentially harmful online interactions.

---

# 🚀 Features

* 💬 Real-time Instagram Reel comment monitoring
* 🧠 Deep Learning-based cyberbullying detection using a **Bidirectional LSTM (BiLSTM)** model
* 📊 Confidence score for every prediction
* 🔍 Explainable AI output with reasons behind each prediction
* 👤 Displays usernames along with detected comments
* 📄 Export evidence reports in CSV and PDF formats
* 🌙 Modern, responsive dashboard with Dark Mode support
* 📈 Live analytics and visualizations
* 🔄 Continuous monitoring for newly posted comments
* ⚡ Manual comment analysis for instant testing

---

# 🛠️ Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js

### Backend

* Python
* Flask

### Deep Learning

* TensorFlow
* Keras
* Bidirectional LSTM (BiLSTM)

### Natural Language Processing

* NLTK
* NumPy
* Pandas

### Browser Automation

* Selenium
* WebDriver Manager

### File Storage

* Trained Model (`.h5`)
* Tokenizer (`.pkl`)
* Generated CSV/PDF Reports

---

# 🧠 Model Architecture

```text
Input Layer
      │
Embedding Layer
      │
Bidirectional LSTM
      │
Dropout Layer
      │
Dense Layer
      │
Sigmoid Output Layer
```

The model classifies every Instagram comment into one of two categories:

* ✅ Non-Bullying
* 🚨 Bullying

---

# 📂 Project Structure

```text
CyberShieldAI/
│
├── app.py
├── requirements.txt
├── README.md
│
├── model/
│   ├── cyberbullying_model.h5
│   └── tokenizer.pkl
│
├── scraper/
│   └── instagram_scraper.py
│
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── scanner.html
│   └── reports.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── dataset/
│
└── reports/
```

---

# ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/CyberShieldAI.git
cd CyberShieldAI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

---

# 📋 How It Works

1. Enter an Instagram Reel URL.
2. Selenium opens Instagram and navigates to the specified Reel.
3. The scraper collects usernames and visible comments.
4. Every comment is preprocessed using NLP techniques.
5. The trained BiLSTM model predicts whether the comment is **Bullying** or **Non-Bullying**.
6. The dashboard displays:

   * Username
   * Comment
   * Prediction
   * Confidence Score
   * Explanation
7. Users can export the detected comments as an evidence report.

---

# 📊 Dashboard Features

* 📈 Total Comments Analyzed
* 🚨 Bullying Comments Detected
* ✅ Safe Comments
* 📉 Detection Statistics
* 🔴 Live Monitoring Status
* 📊 Interactive Charts
* ⚡ Real-Time Updates

---

# 📄 Evidence Report Generation

CyberShield AI generates downloadable reports containing:

* Username
* Comment
* Prediction
* Confidence Score
* Timestamp
* Instagram Reel URL

Supported formats:

* CSV
* PDF

---

# 🔍 Explainable AI

CyberShield AI provides an explanation for every prediction.

**Example:**

```text
Comment:
"You are worthless idiot"

Prediction:
Bullying

Confidence:
96.8%

Reason:
• Detected abusive keyword: "idiot"
• Detected insulting phrase: "worthless"
```

---

# 🔮 Future Enhancements

* 🌍 Multi-language cyberbullying detection
* 🖼️ OCR-based text extraction from images and memes
* 🎙️ Voice-based abuse detection
* 📱 Support for additional social media platforms
* 🧠 Advanced Explainable AI using SHAP/LIME
* ☁️ Cloud deployment
* 👥 User authentication
* 📊 Admin analytics dashboard

---

# 👩‍💻 Author

**Navika Ganesan**

**B.E. – Computer Science and Engineering (Artificial Intelligence & Machine Learning)**

Passionate about Artificial Intelligence, Deep Learning, Cybersecurity, Natural Language Processing, and Intelligent Automation.
