import os
import requests

SYSTEM_PROMPT = """You are FINSHIELD AI, an educational financial literacy assistant.
Answer in simple English or Tamil based on the user's language.
Topics: budgeting, saving, SIP, mutual funds, FDs, RDs, stocks, diversification, expenses.
Do not guarantee returns or give personalized financial advice. Encourage diversification and regulated providers.
Keep answers concise, practical, and add a disclaimer when discussing investments.
This is a simulated hackathon application; never ask for or process OTP, PIN, password, or banking credentials."""

FALLBACKS = {
    "budget": "A simple budget is the 50/30/20 approach: 50% for needs, 30% for wants, and 20% for savings and debt. Adjust the ratios to fit your income, but track expenses consistently.",
    "saving": "Start by setting a realistic goal, automate savings soon after income arrives, use a separate savings account, and review unnecessary subscriptions.",
    "sip": "A SIP is a regular investment in a mutual fund. It may encourage discipline and rupee-cost averaging, but market-linked returns are not guaranteed and capital can fall.",
    "mutual fund": "Mutual funds pool money and invest according to their scheme objective. Check category, expense ratio, fund history, risk level, and suitability; past performance does not guarantee future returns.",
    "fd": "A Fixed Deposit locks money for a fixed tenure at an agreed rate. It is generally lower risk than market-linked investments, but early withdrawal or taxation may reduce returns.",
    "rd": "A Recurring Deposit lets you save a fixed amount regularly for a tenure. It is useful for disciplined short-term goals, subject to bank or post office terms.",
    "stock": "Stocks represent ownership in companies. They can rise or fall sharply, so research, diversification, and only suitable risk levels are important.",
    "divers": "Diversification means spreading investments across asset types, sectors, and durations so that one negative event does not affect all investments equally.",
}


def fallback_answer(question):
    q = question.lower()
    if any(k in q for k in ("50/30", "budget", "budjet")):
        return FALLBACKS["budget"]
    if any(k in q for k in ("save", "savings", "சேம")):
        return FALLBACKS["saving"]
    if "sip" in q:
        return FALLBACKS["sip"]
    if "mutual" in q:
        return FALLBACKS["mutual fund"]
    if any(k in q for k in ("fd", "fixed deposit")):
        return FALLBACKS["fd"]
    if any(k in q for k in ("rd", "recurring")):
        return FALLBACKS["rd"]
    if any(k in q for k in ("stock", "share")):
        return FALLBACKS["stock"]
    if any(k in q for k in ("divers", "mix", "spread")):
        return FALLBACKS["divers"]
    return "A useful starting point is to list income, essential expenses, savings goals, and discretionary spending. For investments, understand risk, tenure, liquidity, and costs. Market-linked returns are not guaranteed. What would you like to explore?"


def ask_groq(question, history=None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return fallback_answer(question) + "\n\n_Offline fallback mode: add GROQ_API_KEY for live AI responses._"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in (history or [])[-8:]:
        role = "assistant" if item["role"] == "assistant" else "user"
        messages.append({"role": role, "content": item["content"]})
    messages.append({"role": "user", "content": question})
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.3, "max_tokens": 500},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return fallback_answer(question) + f"\n\n_Live AI unavailable. Offline fallback was used ({type(exc).__name__})._"
