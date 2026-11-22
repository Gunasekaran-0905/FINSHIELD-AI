import os
from datetime import date

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv

import database as db
from scam_detector import ScamDetector
from expense_tracker import CATEGORIES, summarize, parse_statement, saving_tips
from ai_assistant import ask_groq
from investment import PRODUCTS, scenario_table

load_dotenv()

st.set_page_config(page_title="FINSHIELD AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
:root { --navy:#07111f; --panel:#0d1b2a; --panel2:#11243a; --emerald:#24d39a; --text:#edf6f3; --muted:#94a9a3; }
.stApp { background: radial-gradient(circle at 85% 8%, rgba(36,211,154,.08), transparent 24%), #07111f; color:var(--text); }
section[data-testid="stSidebar"] { background:#091725; border-right:1px solid rgba(255,255,255,.06); }
section[data-testid="stSidebar"] * { color:#dfeee9; }
.block-container { padding-top:1.7rem; max-width:1450px; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#10243a,#0d1b2a); border:1px solid rgba(36,211,154,.10); border-radius:18px; padding:17px 18px; box-shadow:0 10px 30px rgba(0,0,0,.12); }
[data-testid="stMetricLabel"] { color:#99aaa5; }
[data-testid="stMetricValue"] { color:#f7fffb; font-size:29px; }
.stTabs [data-baseweb="tab"] { background:#0d1b2a; border-radius:12px 12px 0 0; color:#b8c9c4; padding:10px 18px; }
.stTabs [aria-selected="true"] { color:#24d39a; border-bottom:2px solid #24d39a; }
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stNumberInput"] input { background:#0d1b2a; color:#edf6f3; border:1px solid #1c3a50; border-radius:11px; }
.stButton>button { background:#24d39a; color:#061711; border:0; border-radius:11px; font-weight:700; min-height:42px; padding:0 18px; }
.stButton>button:hover { background:#43e5b1; border:0; box-shadow:0 8px 22px rgba(36,211,154,.18); }
.card { background:linear-gradient(145deg,#10243a,#0c1928); border:1px solid rgba(255,255,255,.07); border-radius:18px; padding:20px; margin-bottom:12px; }
.brand { display:flex; align-items:center; gap:10px; font-size:21px; font-weight:800; letter-spacing:.3px; margin:8px 0 24px; }
.brand-mark { width:38px; height:38px; display:grid; place-items:center; border-radius:12px; background:linear-gradient(135deg,#24d39a,#148768); }
.risk-high { color:#ff5d73; } .risk-medium { color:#ffc45d; } .risk-low { color:#24d39a; }
.small-muted { color:#94a9a3; font-size:13px; }
.notice { background:rgba(36,211,154,.08); border-left:3px solid #24d39a; padding:12px 14px; border-radius:8px; }
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; }
hr { border-color:rgba(255,255,255,.07); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def currency(value):
    return f"₹{value:,.0f}"


def login_register():
    col1, col2, col3 = st.columns([1,1.25,1])
    with col2:
        st.markdown("<div class='brand' style='justify-content:center;margin-top:8vh'><div class='brand-mark'>🛡️</div><span>FINSHIELD AI</span></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#94a9a3'>Protect Your Money. Manage Your Future.</p>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])
        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign In", use_container_width=True):
                user = db.authenticate(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        with tab_register:
            name = st.text_input("Full name", key="reg_name")
            email2 = st.text_input("Email address", key="reg_email")
            password2 = st.text_input("Create password", type="password", key="reg_password")
            if st.button("Create Demo Account", use_container_width=True):
                if len(name.strip()) < 2:
                    st.error("Enter a valid name.")
                else:
                    ok, result = db.register_user(name, email2, password2)
                    if ok:
                        st.success("Account created. You can now sign in.")
                    else:
                        st.error(str(result))
        st.markdown("<div class='notice small-muted'>Demo prototype: use simulated data only. Never enter real OTPs, PINs, or banking credentials.</div>", unsafe_allow_html=True)


if not st.session_state.authenticated:
    login_register()
    st.stop()

user = st.session_state.user
transactions = db.get_transactions(user["id"])
summary = summarize(transactions)

with st.sidebar:
    st.markdown("<div class='brand'><div class='brand-mark'>🛡️</div><span>FINSHIELD AI</span></div>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Dashboard", "Scam Detection", "Expense Tracker", "AI Financial Assistant", "Investment Learning", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown(f"**{user['name']}**")
    st.markdown("<span class='small-muted'>Protected demo account</span>", unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.pop("user", None)
        st.rerun()


if page == "Dashboard":
    st.markdown("## Financial Command Center")
    st.markdown("<span class='small-muted'>Your simulated financial overview</span>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income", currency(summary["income"]), "Monthly inflow")
    c2.metric("Total Expenses", currency(summary["expenses"]), "Tracked spend")
    c3.metric("Total Savings", currency(summary["savings"]), "Income minus expenses")
    c4.metric("Monthly Budget", currency(user["monthly_budget"]), "Budget target")

    alerts = db.get_fraud_alerts(user["id"])
    high_alerts = sum(a["risk_level"] == "HIGH" for a in alerts)
    expense_ratio = summary["expenses"] / user["monthly_budget"] if user["monthly_budget"] else 0
    health = max(0, min(100, 100 - int(expense_ratio * 45) - high_alerts * 8 + (10 if summary["savings"] > 0 else 0)))

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Expense Distribution")
        cat = summary["expense_by_category"]
        if cat:
            fig = px.pie(values=list(cat.values()), names=list(cat.keys()), hole=.68,
                         color_discrete_sequence=["#24d39a","#1db3a1","#6de0bd","#397b80","#ffc45d","#ff7c86","#7f8cff","#486581"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd8d4", margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h"))
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add an expense to see its distribution.")
    with right:
        st.markdown("#### Financial Health")
        gauge = go.Figure(go.Indicator(mode="gauge+number", value=health, number={"suffix":" / 100"},
            gauge={"axis":{"range":[0,100]}, "bar":{"color":"#24d39a"}, "bgcolor":"#10243a",
            "steps":[{"range":[0,40],"color":"#4b2630"},{"range":[40,70],"color":"#55482b"},{"range":[70,100],"color":"#183f35"}] }))
        gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#edf6f3", height=250, margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(gauge, use_container_width=True)
        st.markdown(f"<div class='card'><b>Fraud Alerts:</b> {len(alerts)} &nbsp; | &nbsp; <b>High-risk:</b> {high_alerts}</div>", unsafe_allow_html=True)

    st.markdown("#### Monthly Savings Trend")
    monthly = summary["monthly_savings"]
    if monthly:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[m["month"] for m in monthly], y=[m["savings"] for m in monthly], name="Savings", marker_color="#24d39a", opacity=.9))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd8d4", height=300, margin=dict(l=0,r=0,t=15,b=0), bargap=.5)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Recent Transactions")
    if transactions:
        display = [{"Date":t["tx_date"], "Type":t["tx_type"].title(), "Category":t["category"], "Description":t["description"], "Amount":currency(t["amount"])} for t in transactions[:8]]
        st.dataframe(display, use_container_width=True, hide_index=True)

elif page == "Scam Detection":
    st.markdown("## AI Scam Detection")
    st.markdown("<span class='small-muted'>Rule-based + simulated ML screening with AI-style explanations</span>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.35,.65])
    with col1:
        loaded_text = st.session_state.pop("loaded_scam_text", "")
        text = st.text_area("Paste a suspicious SMS, UPI message, or email", value=loaded_text, height=210, placeholder="Example: Congratulations! Share OTP to claim your reward...")
        c1, c2 = st.columns([1,3])
        with c1:
            analyse = st.button("Analyse Risk", use_container_width=True)
        with c2:
            sample = st.selectbox("Try a realistic sample", ["Custom message", "UPI cashback scam", "Bank KYC scam", "OTP refund scam", "Normal transaction SMS"])
        if sample != "Custom message" and st.button("Load Sample", use_container_width=True):
            samples = {
                "UPI cashback scam":"Congratulations! You won a ₹5000 cashback reward. Open this link now and approve the UPI request to claim it.",
                "Bank KYC scam":"URGENT: Your bank account will be blocked today. Update KYC immediately by clicking http://kyc-verify.xyz and share OTP.",
                "OTP refund scam":"Customer support here. We need the OTP sent to your mobile to process the reversal of an extra charge.",
                "Normal transaction SMS":"Your debit card purchase of ₹850 was successful. If this was not you, contact the official number in the bank app.",
            }
            text = samples[sample]
            st.session_state.loaded_scam_text = text
            st.rerun()
        if analyse:
            try:
                detector = ScamDetector()
                result = detector.analyse(text)
                db.add_fraud_alert(user["id"], result["score"], result["level"], text)
                st.markdown("### Risk Result")
                level_class = result["level"].lower()
                st.markdown(f"<div class='card'><div style='font-size:38px;font-weight:800' class='risk-{level_class}'>{result['score']} / 100</div><b class='risk-{level_class}'>{result['level']} RISK</b></div>", unsafe_allow_html=True)
                st.warning("Detection assistance only: no automated result is 100% accurate.")
                st.markdown("#### Why it may be suspicious")
                for reason in result["reasons"]:
                    st.markdown(f"• {reason}")
                st.markdown("#### Safety recommendations")
                for tip in result["recommendations"]:
                    st.markdown(f"• {tip}")
            except ValueError as exc:
                st.error(str(exc))
    with col2:
        st.markdown("<div class='card'><b>Never Share</b><br><span class='small-muted'>OTP<br>PIN / password<br>UPI PIN<br>Card details</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'><b>Verify Safely</b><br><span class='small-muted'>Use official apps<br>Call known numbers<br>Check URLs manually</span></div>", unsafe_allow_html=True)
        st.markdown("#### Recent Alerts")
        for alert in db.get_fraud_alerts(user["id"])[:5]:
            cls = alert["risk_level"].lower()
            st.markdown(f"<span class='risk-{cls}'>● {alert['risk_level']} · {alert['risk_score']}</span><br><span class='small-muted'>{alert['message_preview'][:55]}...</span><hr>", unsafe_allow_html=True)

elif page == "Expense Tracker":
    st.markdown("## Smart Expense Tracker")
    tab1, tab2, tab3 = st.tabs(["Add Transaction", "Bank CSV Import", "Reports & Insights"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            tx_type = st.selectbox("Transaction type", ["expense", "income"])
            category = st.selectbox("Category", CATEGORIES if tx_type == "expense" else ["Others"])
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        with c2:
            tx_date = st.date_input("Date", value=date.today())
            description = st.text_input("Description")
            if st.button("Add Transaction", use_container_width=True):
                if amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    db.add_transaction(user["id"], tx_type, category, float(amount), description or tx_type.title(), tx_date.strftime("%Y-%m-%d"))
                    st.success("Transaction saved.")
                    st.rerun()
        st.markdown("#### Transactions")
        rows = [{"ID":t["id"], "Date":t["tx_date"], "Type":t["tx_type"].title(), "Category":t["category"], "Amount":currency(t["amount"]), "Description":t["description"]} for t in db.get_transactions(user["id"])]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        delete_id = st.number_input("Transaction ID to delete", min_value=0, step=1)
        if st.button("Delete Selected Transaction"):
            if delete_id:
                db.delete_transaction(int(delete_id), user["id"])
                st.success("Transaction deleted.")
                st.rerun()
    with tab2:
        st.markdown("Upload a CSV with `date`, `description`, and `amount` columns. Positive values are income; negative values are expenses.")
        upload = st.file_uploader("Choose CSV", type=["csv"])
        if upload:
            try:
                imported = parse_statement(upload)
                st.dataframe(imported.head(20), use_container_width=True, hide_index=True)
                if st.button("Import These Rows"):
                    for _, row in imported.iterrows():
                        db.add_transaction(user["id"], row["tx_type"], row["category"], float(row["amount"]), str(row["description"]), str(row["tx_date"]))
                    st.success(f"Imported {len(imported)} transactions.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not process CSV: {exc}")
    with tab3:
        c1,c2,c3 = st.columns(3)
        c1.metric("Income", currency(summary["income"])); c2.metric("Expenses", currency(summary["expenses"])); c3.metric("Savings", currency(summary["savings"]))
        st.markdown("#### Spending Pattern")
        cat = summary["expense_by_category"]
        if cat:
            fig = px.bar(x=list(cat.keys()), y=list(cat.values()), labels={"x":"Category","y":"Amount (₹)"}, color=list(cat.values()), color_continuous_scale=["#153d42","#24d39a"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd8d4")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### AI-Style Saving Suggestions")
        for tip in saving_tips(summary):
            st.markdown(f"• {tip}")

elif page == "AI Financial Assistant":
    st.markdown("## AI Financial Assistant")
    st.markdown("<span class='small-muted'>Ask in simple English or Tamil · Monthly budget · SIP · Mutual Funds · FD · RD</span>", unsafe_allow_html=True)
    history = db.get_chat_history(user["id"])
    if not history:
        st.markdown("<div class='card'>Try: <b>How should I create a monthly budget?</b><br>Or: <b>SIP என்றால் என்ன?</b></div>", unsafe_allow_html=True)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    question = st.chat_input("Ask a financial literacy question")
    if question:
        db.save_chat(user["id"], "user", question)
        answer = ask_groq(question, history + [{"role":"user","content":question}])
        db.save_chat(user["id"], "assistant", answer)
        st.rerun()

elif page == "Investment Learning":
    st.markdown("## Investment Learning Studio")
    tabs = st.tabs(["Learn", "Compare Scenarios"])
    with tabs[0]:
        cols = st.columns(2)
        for i, (name, details) in enumerate(PRODUCTS.items()):
            with cols[i % 2]:
                st.markdown(f"<div class='card'><h4>{name}</h4><span class='small-muted'>Risk: {details['risk']}</span><p>{details['description']}</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'><h4>Investment Risk & Diversification</h4><p>Risk is the possibility of returns differing from expectations. Diversification can reduce concentration risk, but it does not eliminate all risk. Match a product to your goal, time horizon, liquidity needs, and comfort with loss.</p></div>", unsafe_allow_html=True)
    with tabs[1]:
        c1,c2,c3 = st.columns(3)
        with c1: monthly = st.number_input("Monthly amount (₹)", min_value=500, value=5000, step=500)
        with c2: years = st.number_input("Period (years)", min_value=1, max_value=40, value=10)
        with c3:
            conservative = st.number_input("Conservative return %", min_value=0.0, max_value=30.0, value=6.0)
            moderate = st.number_input("Moderate return %", min_value=0.0, max_value=30.0, value=10.0)
            growth = st.number_input("Growth return %", min_value=0.0, max_value=30.0, value=12.0)
        rows = scenario_table(monthly, years, {"Conservative":conservative,"Moderate":moderate,"Growth":growth})
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[r["name"] for r in rows], y=[r["estimated_value"] for r in rows], text=[currency(r["estimated_value"])+" est." for r in rows], textposition="outside", marker_color=["#397b80","#24d39a","#6de0bd"]))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd8d4", height=380, yaxis_title="Estimated value (₹)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe([{ "Scenario":r["name"], "Illustrative rate":f'{r["rate"]}%', "Total contributed":currency(r["contributions"]), "Estimated value":currency(r["estimated_value"])} for r in rows], use_container_width=True, hide_index=True)
        st.warning("Illustrative calculations only. Returns are not guaranteed. Taxes, fees, inflation, and market volatility can change outcomes.")

elif page == "Settings":
    st.markdown("## Settings")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Profile")
        st.text_input("Name", value=user["name"], disabled=True)
        st.text_input("Email", value=user["email"], disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Monthly Budget")
        budget = st.number_input("Budget target (₹)", min_value=0.0, value=float(user["monthly_budget"]), step=1000.0)
        if st.button("Save Budget"):
            if budget < 0:
                st.error("Budget cannot be negative.")
            else:
                db.update_budget(user["id"], float(budget))
                st.session_state.user = db.get_user(user["id"])
                st.success("Monthly budget updated.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h4>Privacy & Safety</h4><p>This prototype stores only simulated account, transaction, and safety-alert data locally in SQLite. Never enter actual OTPs, PINs, passwords, or banking credentials.</p></div>", unsafe_allow_html=True)
