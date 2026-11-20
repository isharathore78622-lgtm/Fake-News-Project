import pandas as pd
import re
import pickle

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

# LOAD DATA
true_df = pd.read_csv("data/True.csv", engine="python")
fake_df = pd.read_csv("data/Fake.csv", engine="python")

# LABELS
true_df["label"] = 1
fake_df["label"] = 0

# COMBINE TEXT
true_df["content"] = true_df["title"] + " " + true_df["text"]
fake_df["content"] = fake_df["title"] + " " + fake_df["text"]

df = pd.concat([true_df, fake_df])
df = df[["content", "label"]]

df.dropna(inplace=True)
df = df.sample(frac=1, random_state=42)

# CLEAN
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

df["content"] = df["content"].apply(clean_text)

# SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    df["content"], df["label"], test_size=0.2, random_state=42
)

# TF-IDF
vectorizer = TfidfVectorizer(
    max_features=10000,
    stop_words="english",
    ngram_range=(1,2),
    min_df=2
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# MODEL (🔥 KEY CHANGE)
model = MultinomialNB()
model.fit(X_train_vec, y_train)

# EVALUATE
pred = model.predict(X_test_vec)
print("Accuracy:", accuracy_score(y_test, pred))

# SAVE
pickle.dump(model, open("models/svm_model.pkl", "wb"))
pickle.dump(vectorizer, open("models/vectorizer.pkl", "wb"))

print("Model trained successfully ✅")