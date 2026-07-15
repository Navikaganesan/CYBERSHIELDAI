import os
from .preprocess import clean_text
from detoxify import Detoxify

class CyberbullyingPredictor:
    def __init__(self):
        self.model = None
        self.threshold = 0.5
        self.model_status = "Loading"
        self._load_model()

    def _load_model(self):
        try:
            # Load the original detoxify model which predicts: 
            # toxicity, severe_toxicity, obscene, threat, insult, identity_attack
            self.model = Detoxify('original')
            self.model_status = "Detoxify (Pretrained)"
        except Exception as exc:
            self.model_status = f"fallback: {exc}"
            self.model = None

    def predict(self, comment):
        cleaned = clean_text(comment)
        
        if self.model is None:
            return {
                "prediction": "Non-Bullying",
                "confidence": 0.0,
                "reason": ["Model failed to load"],
                "cleaned_text": cleaned,
                "model_status": self.model_status,
            }

        try:
            # Get predictions (Detoxify returns a dictionary of probabilities)
            results = self.model.predict(comment)
        except Exception as e:
            return {
                "prediction": "Non-Bullying",
                "confidence": 0.0,
                "reason": [f"Prediction error: {e}"],
                "cleaned_text": cleaned,
                "model_status": self.model_status,
            }

        reasons = []
        max_score = 0.0
        
        # Determine the maximum score and build reasoning strings
        for category, score in results.items():
            score_val = float(score)
            if score_val > max_score:
                max_score = score_val
                
            if score_val >= self.threshold:
                display_cat = category.replace('_', ' ').title()
                reasons.append(f"Detected {display_cat} ({score_val*100:.1f}%)")

        if max_score >= self.threshold:
            prediction = "Bullying"
            confidence = max_score * 100
        else:
            prediction = "Non-Bullying"
            confidence = (1 - max_score) * 100
            if not reasons:
                reasons = ["No toxic patterns detected"]

        return {
            "prediction": prediction,
            "confidence": round(confidence, 2),
            "reason": reasons,
            "cleaned_text": cleaned,
            "model_status": self.model_status,
        }
