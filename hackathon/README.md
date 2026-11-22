# FINSHIELD AI

A Streamlit fintech hackathon prototype for scam screening, expense tracking, financial learning, and simulated investment comparisons.

## Run locally

```powershell
cd c:\Users\acer\hackathon
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Add your Groq API key to .env if desired
streamlit run app.py
```

Open the local URL shown by Streamlit. Create a demo account or use the registration form.

## Optional Groq AI

Set `GROQ_API_KEY` in `.env`. Without it, the assistant provides a built-in offline financial knowledge fallback.

## Safety

- Use simulated data only.
- Never enter real OTPs, PINs, passwords, card details, or banking credentials.
- Scam detection is assistive and may produce false positives or negatives.
- Investment calculations are illustrative; returns are not guaranteed.

## Structure

- `app.py` — Streamlit interface
- `database.py` — SQLite users, transactions, alerts, chat
- `scam_detector.py` — rules and scikit-learn screening
- `expense_tracker.py` — summaries, CSV import, tips
- `ai_assistant.py` — Groq and offline assistant
- `investment.py` — educational scenarios
- `data/` — SQLite database and sample CSV
