import pandas as pd

CATEGORIES = ["Food", "Travel", "Shopping", "Education", "Entertainment", "Medical", "Bills", "Others"]


def summarize(transactions):
    df = pd.DataFrame(transactions)
    if df.empty:
        return {"income": 0.0, "expenses": 0.0, "savings": 0.0, "expense_by_category": {}, "monthly_savings": []}
    df["amount"] = pd.to_numeric(df["amount"])
    income = df.loc[df["tx_type"] == "income", "amount"].sum()
    expenses = df.loc[df["tx_type"] == "expense", "amount"].sum()
    grouped = df[df["tx_type"] == "expense"].groupby("category")["amount"].sum()

    df["month"] = pd.to_datetime(df["tx_date"], errors="coerce").dt.strftime("%Y-%m")
    monthly = df.groupby(["month", "tx_type"])["amount"].sum().unstack(fill_value=0)
    monthly_savings = []
    for month, row in monthly.iterrows():
        inc = float(row.get("income", 0))
        exp = float(row.get("expense", 0))
        monthly_savings.append({"month": month, "income": inc, "expense": exp, "savings": inc - exp})

    return {
        "income": float(income), "expenses": float(expenses), "savings": float(income - expenses),
        "expense_by_category": grouped.to_dict(), "monthly_savings": monthly_savings,
    }


def parse_statement(uploaded_file):
    df = pd.read_csv(uploaded_file)
    cols = {c.lower().strip(): c for c in df.columns}
    amount_col = next((cols[c] for c in ("amount", "transaction amount", "debit", "credit") if c in cols), None)
    date_col = next((cols[c] for c in ("date", "transaction date", "tx date") if c in cols), None)
    if not amount_col:
        raise ValueError("CSV needs an 'amount' or 'debit/credit' column.")
    result = pd.DataFrame()
    result["amount"] = pd.to_numeric(df[amount_col], errors="coerce")
    result["tx_date"] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d") if date_col else pd.Timestamp.today().strftime("%Y-%m-%d")
    description_col = next((cols[c] for c in ("description", "narration", "details", "particular") if c in cols), None)
    result["description"] = df[description_col].fillna("Imported statement") if description_col else "Imported statement"
    result = result.dropna(subset=["amount"])
    result["tx_type"] = result["amount"].apply(lambda x: "income" if x >= 0 else "expense")
    result["amount"] = result["amount"].abs()
    result["category"] = "Others"
    # Lightly infer categories from descriptions.
    keyword_map = {"Food": ["food", "restaurant", "grocery", "café"], "Travel": ["uber", "metro", "fuel", "rail"], "Bills": ["bill", "electric", "mobile", "internet"], "Shopping": ["amazon", "shop", "store"], "Entertainment": ["movie", "netflix", "game"], "Medical": ["medical", "pharmacy", "hospital"], "Education": ["course", "school", "college"]}
    for i, desc in enumerate(result["description"].astype(str).str.lower()):
        for cat, words in keyword_map.items():
            if any(word in desc for word in words):
                result.iloc[i, result.columns.get_loc("category")] = cat
                break
    return result


def saving_tips(summary):
    if summary["expenses"] == 0:
        return ["Start with a monthly budget and record every expense."]
    categories = summary["expense_by_category"]
    tips = []
    if categories.get("Shopping", 0) > categories.get("Food", 0):
        tips.append("Shopping is high. Apply a 24-hour waiting rule for non-essential purchases.")
    if categories.get("Entertainment", 0) > 0:
        tips.append("Review subscriptions and cancel services you use less than twice a month.")
    if categories.get("Food", 0) > 0:
        tips.append("Plan groceries weekly and set a dining-out limit.")
    tips.append("Automate a savings transfer on the day income is received.")
    return tips[:4]
