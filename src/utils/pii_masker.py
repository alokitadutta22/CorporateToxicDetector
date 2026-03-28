from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class PIIMasker:
    def __init__(self):
        print("🛡️ Initializing Enterprise PII Masker...")
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    def mask(self, text: str) -> str:
        """Detect and mask PII entities in the given text."""
        # Focus on High-Risk PII for demonstrations
        results = self.analyzer.analyze(
            text=text, 
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"], 
            language='en'
        )
        # Handle the anonymization
        anonymized_result = self.anonymizer.anonymize(
            text=text, 
            analyzer_results=results
        )
        return anonymized_result.text

# Singleton pattern for the masking service
pii_masker = PIIMasker()
