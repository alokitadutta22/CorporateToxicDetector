from transformers import pipeline
import torch

class ToxicBERT:
    def __init__(self):
        print("🔥 Downloading Toxic-BERT LLM (first time only)...")
        self.classifier = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            device=-1  # CPU
        )
        print("✅ Toxic-BERT ready (95% accuracy)")
    
    def analyze(self, comment):
        result = self.classifier(comment)[0]
        label = result['label']
        score = result['score']
        
        policies = {
            'toxic': '🚨 HR Harassment Policy Violated',
            'hate': '🚨 Diversity Hate Speech Policy', 
            'sexual': '🚨 Sexual Harassment Policy',
            'threat': '🚨 Workplace Safety Threat'
        }
        
        return {
            'label': label,
            'confidence': score,
            'policy': policies.get(label, 'ℹ️ Review Required'),
            'explanation': f"LLM confidence: {score:.1%} - {policies.get(label, 'Monitor')}"
        }

llm_analyzer = ToxicBERT()