import numpy as np

PRODUCTS = {
    "SIP / Mutual Fund": {"risk": "Moderate to High", "description": "A systematic investment plan invests regularly in a mutual fund. Fund value depends on market performance and fund choice."},
    "Fixed Deposit (FD)": {"risk": "Low", "description": "Money is deposited for a fixed tenure at a stated interest rate, subject to bank rules and taxation."},
    "Recurring Deposit (RD)": {"risk": "Low", "description": "A fixed amount is deposited regularly for a chosen tenure at a defined rate."},
    "Stocks": {"risk": "High", "description": "Ownership in a company with exposure to market volatility and possible loss of capital."},
}


def project_investment(monthly_amount, annual_rate, years):
    monthly_rate = annual_rate / 100 / 12
    months = years * 12
    if monthly_rate == 0:
        return monthly_amount * months
    return monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)


def scenario_table(monthly_amount, years, rates):
    return [{"name": name, "rate": rate, "estimated_value": project_investment(monthly_amount, rate, years),
             "contributions": monthly_amount * years * 12}
            for name, rate in rates.items()]
