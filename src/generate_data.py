# generate synthetic SME loan application data
# parameters calibrated against EBA Risk Assessment 2024, Eurostat Business
# Demography 2023, OECD Secured Lending 2022, and academic lending research

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

SEED = 42
N = 5_000

COUNTRIES = ['Netherlands', 'Belgium', 'Germany', 'France', 'Spain', 'Italy', 'Poland']
COUNTRY_W = [0.30, 0.12, 0.20, 0.12, 0.10, 0.10, 0.06]

SECTORS = [
    'Retail & E-commerce', 'Manufacturing', 'Professional Services',
    'Hospitality & Food', 'Construction', 'Technology', 'Healthcare',
    'Transportation & Logistics', 'Agriculture', 'Real Estate',
]
SECTOR_W = [0.15, 0.12, 0.14, 0.10, 0.09, 0.12, 0.08, 0.07, 0.06, 0.07]

# risk multiplier per sector
SECTOR_RISK = {
    'Retail & E-commerce': 1.2, 'Manufacturing': 0.9,
    'Professional Services': 0.7, 'Hospitality & Food': 1.5,
    'Construction': 1.3, 'Technology': 1.1,
    'Healthcare': 0.6, 'Transportation & Logistics': 1.0,
    'Agriculture': 1.4, 'Real Estate': 0.8,
}

rng = np.random.default_rng(SEED)

sizes = ['Micro (<10)', 'Small (10-49)', 'Medium (50-249)']
size_w = [0.58, 0.27, 0.15]  # Eurostat: 93% micro in population, but lending skews larger

emp_ranges = {'Micro (<10)': (1, 10), 'Small (10-49)': (10, 50), 'Medium (50-249)': (50, 250)}

df = pd.DataFrame({
    'application_id': [f'APP-{i:05d}' for i in range(1, N + 1)],
    'application_date': [
        datetime(2023, 1, 1) + timedelta(days=int(rng.integers(0, 730)))
        for _ in range(N)
    ],
    'country': rng.choice(COUNTRIES, N, p=COUNTRY_W),
    'sector': rng.choice(SECTORS, N, p=SECTOR_W),
    'company_size': rng.choice(sizes, N, p=size_w),
    'years_in_business': np.clip(rng.lognormal(2.0, 0.8, N).astype(int), 1, 50),
    'annual_revenue_eur': np.clip(rng.lognormal(12.5, 1.2, N).astype(int), 50_000, 50_000_000),
    'existing_bank_client': rng.choice([True, False], N, p=[0.4, 0.6]),
    'previous_loans': rng.choice([0, 1, 2, 3, 4, 5], N, p=[0.35, 0.25, 0.20, 0.10, 0.06, 0.04]),
    'loan_amount_requested_eur': np.clip(rng.lognormal(11.5, 0.8, N).astype(int), 10_000, 5_000_000),  # median ~EUR 100K per OECD
    'loan_term_months': rng.choice([12, 24, 36, 48, 60, 72, 84], N, p=[0.10, 0.15, 0.25, 0.20, 0.15, 0.10, 0.05]),
    'collateral_offered': rng.choice([True, False], N, p=[0.45, 0.55]),  # OECD: 40-50% secured
})

# number of employees based on company size
employees = []
for s in df['company_size']:
    lo, hi = emp_ranges[s]
    employees.append(int(rng.integers(lo, hi)))
df['num_employees'] = employees

df['debt_to_equity_ratio'] = np.clip(rng.lognormal(0.3, 0.6, N), 0.1, 8.0).round(2)
df['current_ratio'] = np.clip(rng.normal(1.4, 0.6, N), 0.3, 5.0).round(2)  # SME median ~1.3-1.5
df['profit_margin_pct'] = np.clip(rng.normal(6.0, 5.5, N), -15, 35).round(1)  # EU SME median ~5-8%
df['revenue_growth_yoy_pct'] = np.clip(rng.normal(5.0, 12.0, N), -30, 60).round(1)
df['loan_to_revenue_ratio'] = (df['loan_amount_requested_eur'] / df['annual_revenue_eur']).round(3)
df['credit_bureau_score'] = np.clip(rng.normal(650, 80, N).astype(int), 300, 850)
df['num_credit_inquiries_12m'] = rng.poisson(2, N)
df['has_payment_defaults'] = rng.choice([True, False], N, p=[0.12, 0.88])

# calculate default probability and assign target
def _default_probability(row):
    # base rate 3.5% - calibrated to EU SME annual default rate (EBA 2024)
    p = 0.035 * SECTOR_RISK.get(row['sector'], 1.0)

    if row['debt_to_equity_ratio'] > 3.0:
        p *= 1.5
    if row['current_ratio'] < 1.0:
        p *= 1.6
    if row['profit_margin_pct'] < 0:
        p *= 2.0
    if row['credit_bureau_score'] < 550:
        p *= 2.0
    elif row['credit_bureau_score'] > 750:
        p *= 0.5
    if row['has_payment_defaults']:
        p *= 2.5
    if row['collateral_offered']:
        p *= 0.7  # OECD: secured loans ~20-30% lower LGD
    if row['existing_bank_client']:
        p *= 0.8  # relationship lending reduces default 15-25%
    if row['years_in_business'] > 10:
        p *= 0.7  # established firms 30-40% lower default
    elif row['years_in_business'] < 3:
        p *= 1.4  # young firms have higher failure rates (Eurostat)
    return min(p, 0.95)

df['default_prob'] = df.apply(_default_probability, axis=1)
df['defaulted_12m'] = (rng.random(N) < df['default_prob']).astype(int)
df.drop(columns=['default_prob'], inplace=True)

# add some missing values (~3%)
idx = rng.choice(N, size=int(N * 0.03), replace=False)
df.loc[idx[:len(idx) // 2], 'profit_margin_pct'] = np.nan
df.loc[idx[len(idx) // 2:], 'revenue_growth_yoy_pct'] = np.nan

# save
out_path = os.path.join('..', 'data', 'sme_loan_applications.csv')
df.to_csv(out_path, index=False)
print(f"Generated {len(df)} records  |  Default rate: {df['defaulted_12m'].mean():.1%}")
