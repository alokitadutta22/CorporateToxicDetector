import joblib
from src.rag.llm_rag import llm_analyzer
from src.utils.pii_masker import pii_masker
from src.utils.audit_logger import log_inference
from src.utils.text_normalizer import text_normalizer

class ProductionPredictor:
    def __init__(self):
        """🎓 ML Fast + LLM Accurate = Corporate Hybrid"""
        self.ml_model = joblib.load('models/toxic_classifier.pkl')
        self.ml_vectorizer = joblib.load('models/tfidf_vectorizer.pkl')
        print("✅ HYBRID: ML(88%) + Toxic-BERT LLM(95%)")
        print("🔧 Anti-evasion normalizer active")
    
    def predict(self, comment: str):
        # Step 1: NORMALIZE to defeat adversarial obfuscation FIRST
        # (leet speak, misspellings, special chars, homoglyphs, transpositions)
        # This MUST run before PII masking, otherwise the PII masker
        # may misclassify obfuscated slurs (e.g. "fcuk" → PERSON)
        normalized_comment = text_normalizer.normalize(comment)

        # Step 2: MASK PII on the normalized text
        masked_comment = pii_masker.mask(normalized_comment)

        # Step 3: ML Score — uses NORMALIZED text
        vec = self.ml_vectorizer.transform([normalized_comment])
        ml_score = self.ml_model.predict_proba(vec)[0][1]
        
        # Step 4: LLM Analysis — uses NORMALIZED text
        llm_result = llm_analyzer.analyze(normalized_comment)
        
        # Step 5: HYBRID weighted score
        hybrid_score = (ml_score * 0.3) + (llm_result['confidence'] * 0.7)
        
        result = {
            'comment': comment,
            'masked_comment': masked_comment,
            'normalized_comment': normalized_comment,
            'ml_score': float(ml_score),
            'llm_label': llm_result['label'],
            'llm_confidence': float(llm_result['confidence']),
            'hybrid_score': float(hybrid_score),
            'is_toxic': hybrid_score > 0.5,
            'risk_level': 'HIGH' if hybrid_score > 0.7 else 'MEDIUM' if hybrid_score > 0.3 else 'LOW',
            'policy_violation': llm_result['policy'],
            'llm_explanation': llm_result['explanation']
        }
        
        # Write to enterprise audit log
        log_inference(masked_comment, result)
        
        return result

predictor = ProductionPredictor()