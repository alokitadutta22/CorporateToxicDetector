import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import yaml
import os

print("🚀 CORPORATE TOXIC MODEL TRAINING")

# Load + CLEAN data
df = pd.read_csv('data/cleaned_train.csv')
print(f"📊 Raw data: {len(df)} samples")

# ✅ FIX: Remove NaN/empty comments
df = df.dropna(subset=['comment_text'])
df = df[df['comment_text'].str.strip() != '']
df['comment_text'] = df['comment_text'].astype(str).fillna('empty comment')
print(f"✅ Clean data: {len(df)} samples")

# Features + labels
X = df['comment_text']
y = df['toxic'].astype(int)

# Split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Corporate TF-IDF
vectorizer = TfidfVectorizer(
    max_features=5000,
    stop_words='english',
    ngram_range=(1, 2),
    min_df=3
)

print("🎯 Vectorizing...")
X_train_vec = vectorizer.fit_transform(X_train)
X_val_vec = vectorizer.transform(X_val)

# Train
model = LogisticRegression(
    class_weight='balanced',
    max_iter=2000,
    random_state=42
)

print("🤖 Training...")
model.fit(X_train_vec, y_train)

# Results
train_acc = accuracy_score(y_train, model.predict(X_train_vec))
val_acc = accuracy_score(y_val, model.predict(X_val_vec))
print(f"✅ Train Accuracy: {train_acc:.1%}")
print(f"✅ Val Accuracy: {val_acc:.1%}")

print("\n📈 Report:")
print(classification_report(y_val, model.predict(X_val_vec)))

# Save
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/toxic_classifier.pkl')
joblib.dump(vectorizer, 'models/tfidf_vectorizer.pkl')
print("💾 MODEL SAVED!")

print("✅ READY FOR PRODUCTION!")