# 📰 Fake News Detection System

An AI-powered web application that detects whether a news article is **Real or Fake** using Machine Learning and Natural Language Processing (NLP).

The system allows users to analyze news through text, website URLs, and uploaded images containing news text. It also provides user authentication and personalized detection history.

## 🚀 Project Overview

The Fake News Detection System aims to identify misleading or fabricated news using machine learning techniques.

Users can register, log in, submit news for verification, and view their previous detection results through a personalized dashboard.

The application combines Machine Learning, NLP, OCR, web scraping, and Flask to provide multiple ways of analyzing news content.

## ✨ Key Features

### 1. Multiple News Detection Methods
- **Text Detection:** Enter or paste news content for prediction.
- **URL Detection:** Submit a news article URL to extract and analyze its content.
- **Image Detection:** Upload an image or screenshot containing news text. OCR extracts the text for prediction.

### 2. User Authentication
- User registration with username, email, password, and mobile number.
- Login and logout functionality.
- Session-based authentication.
- Personalized dashboard with a welcome message.

### 3. Personalized News History
- Automatically stores detection results for logged-in users.
- Displays previously analyzed news.
- Allows users to delete individual history records.
- Keeps detection history associated with the respective user account.

### 4. Machine Learning-Based Prediction
- Text preprocessing using NLP techniques.
- TF-IDF feature extraction.
- Machine learning classification.
- Experimental exploration of deep learning models, including LSTM and BERT-based approaches.

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | HTML, CSS |
| Backend | Flask |
| Database | SQLite |
| Machine Learning | Scikit-learn |
| NLP | TF-IDF, Text Preprocessing |
| Deep Learning Experiments | LSTM, DistilBERT |
| Image Processing | Pillow (PIL) |
| OCR | Tesseract, Pytesseract |
| Web Scraping | Requests, BeautifulSoup |
| Development Environment | VS Code |

## 🧠 Machine Learning Approach

The primary detection pipeline consists of:

1. **Text Preprocessing:** Cleaning and preparing news content.
2. **Feature Extraction:** Converting textual data into numerical features using TF-IDF.
3. **Classification:** Applying a trained Logistic Regression model to classify news.
4. **Prediction:** Producing a Real or Fake classification.

Additional experiments include LSTM and DistilBERT models to explore deep learning-based text classification.

## 📂 Project Structure

```text
Fake-News-Detection-System/
│
├── src/
│   ├── merge_data.py
│
├── static/
│   └── fake_news.jpg
│
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── detect.html
│   ├── history.html
│   ├── login.html
│   ├── register.html
│   └── result.html
│
├── models/
│   ├── logistic_model.pkl
│   └── tfidf_vectorizer.pkl
│
├── api.py
├── data_preprocess.py
├── evaluate_model.py
├── model_train_glove_lstm.py
├── model_train_lstm.py
├── test_lstm_model.py
├── train_model.py
├── web_app.py
│
├── database.db
└── README.md
```

*Note: Update the structure if your actual folders or model filenames differ. Do not upload your virtual environment or large generated model files unnecessarily.*

## ⚙️ Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/isharathore78622-lgtm/Fake-News-Project.git
```

### Step 2: Navigate to the Project Directory

```bash
cd Fake-News-Detection-System
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install flask numpy pandas scikit-learn nltk requests beautifulsoup4 pillow pytesseract
```

### Step 5: Install Tesseract OCR

Install Tesseract OCR separately and configure its executable path in the Python application if it is not automatically detected.

### Step 6: Run the Application

```bash
python web_app.py
```

### Step 7: Open in Browser

```text
http://127.0.0.1:5000/
```

## 🔍 Application Workflow

1. User opens the application.
2. User registers or logs into their account.
3. User accesses the dashboard.
4. User chooses a news input method: text, URL, or image.
5. The application extracts and preprocesses the news content.
6. The trained ML model predicts whether the news is Real or Fake.
7. The prediction result is displayed.
8. The result is saved to the logged-in user's history.

## 🎯 Project Objectives

- Identify potentially misleading news content.
- Apply machine learning techniques to text classification.
- Support multiple input formats for news verification.
- Provide a simple and accessible user interface.
- Maintain personalized detection records.
- Explore the application of NLP and deep learning in misinformation detection.

## 🔮 Future Enhancements

- Improve classification accuracy using advanced transformer models.
- Integrate more reliable real-time news verification sources.
- Support additional languages.
- Improve image and screenshot text extraction.
- Add confidence scores to prediction results.
- Enhance the detection system against misleading and manipulated content.

## 👩‍💻 Project Information

**Project:** Fake News Detection System

**Domain:** Machine Learning and Natural Language Processing

**Application Type:** Web-Based Application

**Primary Role:** Full-Stack Development and Machine Learning Integration

---

⭐ If you find this project interesting, consider giving the repository a star!
