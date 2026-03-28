import pandas as pd
import numpy as np
import yaml
import os

def load_and_clean_data():
    """Corporate-grade data cleaning"""
    print("📊 Loading dataset...")
    df = pd.read_csv('data/train.csv')
    print(f"✅ Loaded {len(df)} rows")
    
    # Multi-label setup (add columns if missing)
    label_cols = ['toxic']
    if len(df.columns) > 2:
        label_cols += ['severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
    
    # Ensure all labels exist
    for col in label_cols[1:]:
        if col not in df.columns:
            df[col] = 0
    
    # Clean text
    df['comment_text'] = df['comment_text'].astype(str).str.lower().str.strip()
    
    # Sample for speed
    df_sample = df.sample(n=min(25000, len(df)), random_state=42).reset_index(drop=True)
    
    return df_sample

def save_config():
    config = {
        'data': {'train_split': 0.8, 'max_length': 512},
        'model': {
            'base_model': 'distilbert-base-uncased',
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
        },
        'training': {'epochs': 3, 'batch_size': 16}
    }
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    print("✅ config.yaml created")

if __name__ == "__main__":
    if not os.path.exists('data/train.csv'):
        print("❌ ERROR: data/train.csv missing!")
        print("Run: python download_dataset.py first")
    else:
        df = load_and_clean_data()
        df.to_csv('data/cleaned_train.csv', index=False)
        print(f"✅ Saved cleaned dataset: {len(df)} samples")
        save_config()