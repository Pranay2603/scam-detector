import re

def generate_explanation(text):
    text = text.lower()
    reasons = []

    if "otp" in text:
        reasons.append("It asks for an OTP, which legitimate services never request via messages.")

    if "bank" in text or "account" in text:
        reasons.append("It mentions financial details, which scammers often target.")

    if "click" in text or "link" in text:
        reasons.append("It asks you to click a link, which could lead to phishing sites.")

    if "urgent" in text or "immediately" in text or "act now" in text:
        reasons.append("It creates urgency to pressure quick action, a common scam tactic.")

    if "win" in text or "lottery" in text or "prize" in text or "congratulations" in text:
        reasons.append("It promises rewards or prizes, which is a common scam pattern.")

    if not reasons:
        return "✅ This message appears safe and does not contain common scam patterns."

    return "⚠️ " + " ".join(reasons)


def analyze_text(text):
    scam_keywords = [
        "win", "lottery", "urgent", "prize", "click",
        "offer", "free", "money", "reward", "cash",
        "limited", "act now", "verify", "otp", "bank",
        "account", "link", "gift", "congratulations"
    ]

    score = 0
    found_words = []
    highlighted_text = text

    for word in scam_keywords:
        if word in text.lower():

            if word in ["otp", "bank", "account"]:
                score += 20   # high-risk keywords
            else:
                score += 10

            found_words.append(word)

            highlighted_text = re.sub(
                f"({word})",
                r'<span class="highlight">\1</span>',
                highlighted_text,
                flags=re.IGNORECASE
            )

            highlighted_text = re.sub(
                f"({word})",
                r'<span class="highlight">\1</span>',
                highlighted_text,
                flags=re.IGNORECASE
            )

    if score <= 20:
        risk_level = "Safe"
    elif score <= 50:
        risk_level = "Suspicious"
    else:
        risk_level = "High"

    explanation = generate_explanation(text)

    return {
        "score": min(score, 100),
        "risk": risk_level,
        "label": risk_level,
        "keywords": found_words,
        "highlighted": highlighted_text,
        "explanation": explanation
    }