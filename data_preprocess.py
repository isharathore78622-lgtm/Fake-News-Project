import pandas as pd
import re
import spacy
from tqdm import tqdm
import os

# 🔥 Load spaCy model
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

# 🔥 CLEAN FUNCTION
def clean_text(text):

    text = str(text).lower()

    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text)

    # Remove numbers
    text = re.sub(r'\d+', '', text)

    # Keep only alphabets
    text = re.sub(r'[^a-z\s]', ' ', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # spaCy lemmatization
    doc = nlp(text)

    tokens = []
    for token in doc:
        if len(token) > 2:   # ❌ DO NOT remove stopwords
            tokens.append(token.lemma_)

    return " ".join(tokens)


if __name__ == "__main__":

    print("📥 Loading dataset...")
    df = pd.read_csv("data/fakenews_combined.csv")

    # 🔥 REMOVE NULL TEXT
    df = df.dropna(subset=['text'])

    # 🔥 FIX LABEL FORMAT
    df['label'] = df['label'].astype(str).str.upper()

    print("🧹 Cleaning text data...")
    tqdm.pandas()

    df['clean_text'] = df['text'].progress_apply(clean_text)

    # 🔥 REMOVE DATASET BIAS WORDS
    df['clean_text'] = df['clean_text'].str.replace(
        r'\b(reuters|said|says|report)\b',
        '',
        regex=True
    )

    # 🔥 REMOVE EMPTY TEXT
    df = df[df['clean_text'].str.strip() != ""]

    # 🔥 REMOVE VERY SHORT TEXT (IMPORTANT)
    df = df[df['clean_text'].str.split().str.len() > 5]

    # 🔥 REMOVE DUPLICATES
    df = df.drop_duplicates(subset=['clean_text'])

    # 🔥 CHECK LABEL DISTRIBUTION
    print("\nBefore balancing:")
    print(df['label'].value_counts())

    # 🔥 BALANCE DATASET
    real = df[df['label'] == 'REAL']
    fake = df[df['label'] == 'FAKE']

    min_len = min(len(real), len(fake))

    df = pd.concat([
        real.sample(min_len, random_state=42),
        fake.sample(min_len, random_state=42)
    ])

    # 🔥 SHUFFLE DATA
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    print("\nAfter balancing:")
    print(df['label'].value_counts())

    # 🔥 SAVE FILE
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(BASE_DIR, "..", "data", "processed")

    os.makedirs(processed_dir, exist_ok=True)

    output_path = os.path.join(processed_dir, "cleaned.csv")
    df.to_csv(output_path, index=False)

    print(f"\n✅ Cleaned data saved at: {output_path}")
