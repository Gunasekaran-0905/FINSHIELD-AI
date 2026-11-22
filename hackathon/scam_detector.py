import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

SAFE = [
    "your salary has been credited to your account",
    "your monthly statement is available in the official banking app",
    "payment received for your grocery purchase",
    "your debit card transaction was successful",
]
SCAM = [
    "share otp immediately to receive cashback",
    "your bank account is blocked update kyc now",
    "click this link verify account and enter card pin",
    "you won a lottery pay processing fee",
    "upi request pending approve to claim reward",
    "urgent pay tax or arrest will follow",
    "send otp for refund reversal",
    "kyc suspended click suspicious url",
]

class ScamDetector:
    def __init__(self):
        texts = SAFE + SCAM
        labels = [0] * len(SAFE) + [1] * len(SCAM)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(texts)
        self.model = MultinomialNB()
        self.model.fit(X, labels)

    def analyse(self, text):
        text = text.strip()
        if not text:
            raise ValueError("Enter a message to analyse.")
        lower = text.lower()
        score = 8
        reasons = []

        patterns = {
            r"\botp\b|one.?time.?password": 28,
            r"\bkyc\b|account.*(block|suspend)|verify.*account": 24,
            r"upi|imps|netbanking": 12,
            r"share.*(otp|pin)|send.*(otp|pin)|do not share": 22,
            r"click.*(link|url)|http[s]?://|bit\.ly|tinyurl|\.xyz|\.top": 20,
            r"cashback|reward|lottery|prize|won": 18,
            r"urgent|immediately|within.*(hour|minute)|last chance": 10,
            r"processing fee|pay.*fee|advance.*payment": 16,
            r"arrest|police|legal action|account.*seize": 18,
        }
        for pattern, points in patterns.items():
            if re.search(pattern, lower):
                score += points
                if "otp" in pattern:
                    reasons.append("Requests an OTP or verification code")
                elif "kyc" in pattern:
                    reasons.append("Uses account/KYC urgency or suspension threats")
                elif "link" in pattern:
                    reasons.append("Contains a suspicious or shortened URL")
                elif "cashback" in pattern:
                    reasons.append("Promises an unrealistic reward or prize")
                elif "fee" in pattern:
                    reasons.append("Requests a payment or processing fee")
                elif "arrest" in pattern:
                    reasons.append("Uses fear or legal-threat language")
                else:
                    reasons.append("Contains urgency or financial-action language")

        if re.search(r"\b[pP][aA][sS][sS]|pin\b", lower):
            score += 18
            reasons.append("Mentions a PIN or password secret")

        ml_score = int(self.model.predict_proba(self.vectorizer.transform([text]))[0][1] * 35)
        score += ml_score
        score = min(score, 100)

        if score >= 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        recommendations = []
        if level == "HIGH":
            recommendations = [
                "Do not click links or reply to the sender.",
                "Never share OTP, PIN, password, or banking credentials.",
                "Verify through the official bank app or a known phone number.",
            ]
        elif level == "MEDIUM":
            recommendations = [
                "Treat the message with caution and verify independently.",
                "Do not install apps or scan QR codes suggested by the sender.",
            ]
        else:
            recommendations = [
                "This appears less suspicious, but verify unexpected requests.",
                "Use official channels before taking action.",
            ]

        if not reasons:
            reasons = ["No strong scam indicators were found in the text"]
        return {
            "score": score,
            "level": level,
            "reasons": list(dict.fromkeys(reasons)),
            "recommendations": recommendations,
        }
