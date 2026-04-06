# credit risk scoring analysis - SME lending portfolio

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix, roc_curve
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# chart styling
import sys, os
sys.path.insert(0, '..')
from style_config import *

# helper to run sql files against our in-memory db
def run_sql(filepath, conn):
    with open(filepath) as f:
        return pd.read_sql(f.read(), conn)

plt.rcParams.update({
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': LIGHT,
    'axes.labelcolor': TEXT,
    'text.color': TEXT,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# load data
print("=" * 60)
print("CREDIT RISK SCORING - SME LENDING PORTFOLIO")
print("=" * 60)

df = pd.read_csv('../data/sme_loan_applications.csv')
df['application_date'] = pd.to_datetime(df['application_date'])

print(f"\nDataset: {len(df)} loan applications")
print(f"Default rate: {df['defaulted_12m'].mean():.1%}")
print(f"Period: {df['application_date'].min().date()} to {df['application_date'].max().date()}")

# clean missing values - just fill with median
df['profit_margin_pct'] = df['profit_margin_pct'].fillna(df['profit_margin_pct'].median())
df['revenue_growth_yoy_pct'] = df['revenue_growth_yoy_pct'].fillna(df['revenue_growth_yoy_pct'].median())

# load into sqlite so we can run our sql queries
conn = sqlite3.connect(':memory:')
df.to_sql('sme_loan_applications', conn, index=False)

# --- Exploratory Analysis (SQL) ---
# running queries from sql/ folder
print("\nEDA CHARTS")

# Figure 1 - default rate by sector (from SQL)
fig, ax = plt.subplots(figsize=(10, 5.5))

stats = run_sql('../sql/02_default_rate_by_sector.sql', conn)
stats = stats.sort_values('default_rate_pct')
avg = df['defaulted_12m'].mean()
colors = [ACCENT if r > avg * 100 else PRIMARY for r in stats['default_rate_pct']]
ax.barh(stats['sector'], stats['default_rate_pct'], color=colors, height=0.65, edgecolor='white')
ax.axvline(avg * 100, color=DANGER, ls='--', lw=1.2, alpha=0.7,
           label=f'Portfolio avg: {avg:.1%}')

for i, row in enumerate(stats.itertuples()):
    ax.text(row.default_rate_pct + 0.3, i, f'{row.default_rate_pct:.1f}%', va='center', fontsize=9)
ax.set_xlabel('Default Rate (%)')
ax.set_title('Default Rate by Industry Sector')
ax.legend(loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig('../outputs/figures/01_default_by_sector.png')
plt.close()
print("OK saved 01_default_by_sector.png")

# --- Python-only Analysis ---
# correlation matrix, distributions (need raw data)

# Figure 2 - correlation matrix
cols_corr = ['debt_to_equity_ratio', 'current_ratio', 'profit_margin_pct',
        'revenue_growth_yoy_pct', 'loan_to_revenue_ratio', 'credit_bureau_score',
        'num_credit_inquiries_12m', 'years_in_business', 'loan_amount_requested_eur',
        'annual_revenue_eur', 'defaulted_12m']
labels_corr = ['Debt/Equity', 'Current Ratio', 'Profit Margin', 'Rev Growth',
          'Loan/Revenue', 'Credit Score', 'Credit Inquiries', 'Years in Biz',
          'Loan Amount', 'Revenue', 'Defaulted']

fig, ax = plt.subplots(figsize=(9, 7))
corr = df[cols_corr].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, cmap=sns.diverging_palette(220, 20, as_cmap=True),
            center=0, annot=True, fmt='.2f', linewidths=0.8, linecolor='white',
            ax=ax, annot_kws={'size': 8}, cbar_kws={'shrink': 0.8})
ax.set_xticklabels(labels_corr, rotation=45, ha='right', fontsize=8)
ax.set_yticklabels(labels_corr, rotation=0, fontsize=8)
ax.set_title('Risk Factor Correlation Matrix')

plt.tight_layout()
plt.savefig('../outputs/figures/02_correlation_matrix.png')
plt.close()
print("OK saved 02_correlation_matrix.png")

# Figure 3 - country analysis (SQL for bar chart, pandas for pie)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# pie chart - just value_counts, keeping as pandas
cc = df['country'].value_counts()
wedges, texts, auto = axes[0].pie(
    cc, labels=cc.index, autopct='%1.0f%%', colors=PALETTE[:len(cc)],
    startangle=90, pctdistance=0.82,
    wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
for t in auto:
    t.set(fontsize=8, color='white', fontweight='bold')
axes[0].set_title('Applications by Country')

# bar chart from SQL
cd = run_sql('../sql/03_default_rate_by_country.sql', conn)
cd = cd.sort_values('default_rate_pct')
axes[1].barh(cd['country'], cd['default_rate_pct'], color=PRIMARY, height=0.55, edgecolor='white')
for i, row in enumerate(cd.itertuples()):
    axes[1].text(row.default_rate_pct + 0.2, i, f'{row.default_rate_pct:.1f}%', va='center', fontsize=9)
axes[1].set_xlabel('Default Rate (%)')
axes[1].set_title('Default Rate by Country')
axes[1].axvline(df['defaulted_12m'].mean() * 100, color=DANGER, ls='--', lw=1, alpha=0.6)

plt.tight_layout(w_pad=3)
plt.savefig('../outputs/figures/03_country_analysis.png')
plt.close()
print("OK saved 03_country_analysis.png")

# Figure 4 - risk factor distributions
# histograms stay as python (need raw data), age chart from SQL
fig, axes = plt.subplots(2, 2, figsize=(11, 8))

# credit score distribution
for lab, c, nm in [(0, PRIMARY, 'Non-Default'), (1, ACCENT, 'Default')]:
    sub = df[df['defaulted_12m'] == lab]
    axes[0, 0].hist(sub['credit_bureau_score'], bins=30, alpha=0.6, color=c, label=nm, edgecolor='white')
axes[0, 0].set_title('Credit Bureau Score')
axes[0, 0].legend(fontsize=9)

# debt to equity
for lab, c, nm in [(0, PRIMARY, 'Non-Default'), (1, ACCENT, 'Default')]:
    sub = df[df['defaulted_12m'] == lab]
    axes[0, 1].hist(sub['debt_to_equity_ratio'], bins=30, alpha=0.6, color=c, label=nm, edgecolor='white')
axes[0, 1].set_title('Debt-to-Equity Ratio')
axes[0, 1].legend(fontsize=9)

# loan to revenue
for lab, c, nm in [(0, PRIMARY, 'Non-Default'), (1, ACCENT, 'Default')]:
    sub = df[df['defaulted_12m'] == lab]
    vals = sub['loan_to_revenue_ratio'].clip(upper=sub['loan_to_revenue_ratio'].quantile(0.99))
    axes[1, 0].hist(vals, bins=30, alpha=0.6, color=c, label=nm, edgecolor='white')
axes[1, 0].set_title('Loan-to-Revenue Ratio')
axes[1, 0].legend(fontsize=9)

# company age bar chart from SQL
age_data = run_sql('../sql/04_risk_by_company_age.sql', conn)
# strip the numbering prefix for nice labels
age_labels = age_data['age_bucket'].str.replace(r'^\d+\.\s*', '', regex=True)
axes[1, 1].bar(age_labels, age_data['default_rate_pct'], color=ACCENT, edgecolor='white', width=0.55)
for i, row in enumerate(age_data.itertuples()):
    axes[1, 1].text(i, row.default_rate_pct + 0.3, f'{row.default_rate_pct:.1f}%', ha='center', fontsize=9)
axes[1, 1].set_title('Default Rate by Company Age')
axes[1, 1].set_ylabel('Default Rate (%)')

plt.suptitle('Key Risk Factor Distributions', fontsize=15, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('../outputs/figures/04_risk_distributions.png')
plt.close()
print("OK saved 04_risk_distributions.png")

# --- Machine Learning ---
# feature engineering, model training, evaluation
print("\nFEATURE ENGINEERING")

# encode categoricals
le_country = LabelEncoder()
df['country_enc'] = le_country.fit_transform(df['country'])

le_sector = LabelEncoder()
df['sector_enc'] = le_sector.fit_transform(df['sector'])

le_size = LabelEncoder()
df['size_enc'] = le_size.fit_transform(df['company_size'])

# booleans to int
df['existing_bank_client'] = df['existing_bank_client'].astype(int)
df['collateral_offered'] = df['collateral_offered'].astype(int)
df['has_payment_defaults'] = df['has_payment_defaults'].astype(int)

feature_cols = [
    'country_enc', 'sector_enc', 'size_enc', 'years_in_business',
    'existing_bank_client', 'previous_loans', 'loan_term_months',
    'collateral_offered', 'debt_to_equity_ratio', 'current_ratio',
    'profit_margin_pct', 'revenue_growth_yoy_pct', 'loan_to_revenue_ratio',
    'credit_bureau_score', 'num_credit_inquiries_12m', 'has_payment_defaults',
]

X = df[feature_cols]
y = df['defaulted_12m']

# ---- TRAIN MODELS ----
print("\nTRAINING MODELS")

seed = 42
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc = scaler.transform(X_test)

# logistic regression
lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=seed)
lr.fit(X_train_sc, y_train)
lr_pred = lr.predict(X_test_sc)
lr_proba = lr.predict_proba(X_test_sc)[:, 1]
lr_auc = roc_auc_score(y_test, lr_proba)
lr_f1 = f1_score(y_test, lr_pred)
print(f"  Logistic Regression        AUC={lr_auc:.4f}  F1={lr_f1:.4f}")

# random forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10, class_weight='balanced',
                            random_state=seed, n_jobs=-1)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_proba = rf.predict_proba(X_test)[:, 1]
rf_auc = roc_auc_score(y_test, rf_proba)
rf_f1 = f1_score(y_test, rf_pred)
print(f"  Random Forest              AUC={rf_auc:.4f}  F1={rf_f1:.4f}")

# gradient boosting
gb = GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=seed)
gb.fit(X_train, y_train)
gb_pred = gb.predict(X_test)
gb_proba = gb.predict_proba(X_test)[:, 1]
gb_auc = roc_auc_score(y_test, gb_proba)
gb_f1 = f1_score(y_test, gb_pred)
print(f"  Gradient Boosting          AUC={gb_auc:.4f}  F1={gb_f1:.4f}")

# collect results to find best model
results = {
    'Logistic Regression': {'model': lr, 'y_pred': lr_pred, 'y_proba': lr_proba, 'auc': lr_auc, 'f1': lr_f1, 'scaled': True},
    'Random Forest': {'model': rf, 'y_pred': rf_pred, 'y_proba': rf_proba, 'auc': rf_auc, 'f1': rf_f1, 'scaled': False},
    'Gradient Boosting': {'model': gb, 'y_pred': gb_pred, 'y_proba': gb_proba, 'auc': gb_auc, 'f1': gb_f1, 'scaled': False},
}

best_name = max(results, key=lambda k: results[k]['auc'])
best = results[best_name]
print(f"\nBest model: {best_name}")

# ---- MODEL CHARTS ----
print("\nMODEL CHARTS")

# Figure 5 - model comparison (ROC + bar)
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
color_map = {'Logistic Regression': PRIMARY, 'Random Forest': ACCENT, 'Gradient Boosting': SECONDARY}

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['y_proba'])
    axes[0].plot(fpr, tpr, color=color_map[name], lw=2, label=f"{name} (AUC={res['auc']:.3f})")
axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.3)
axes[0].set_xlabel('False Positive Rate')
axes[0].set_ylabel('True Positive Rate')
axes[0].set_title('ROC Curves')
axes[0].legend(fontsize=9, loc='lower right')

names = list(results.keys())
x = np.arange(len(names))
axes[1].bar(x - 0.18, [results[n]['auc'] for n in names], 0.35, label='AUC-ROC', color=ACCENT, edgecolor='white')
axes[1].bar(x + 0.18, [results[n]['f1'] for n in names], 0.35, label='F1 Score', color=PRIMARY, edgecolor='white')
axes[1].set_xticks(x)
axes[1].set_xticklabels([n.replace(' ', '\n') for n in names], fontsize=9)
axes[1].set_ylim(0, 1)
axes[1].set_title('Model Performance Metrics')
axes[1].legend(fontsize=9)

plt.tight_layout(w_pad=3)
plt.savefig('../outputs/figures/05_model_comparison.png')
plt.close()
print("OK saved 05_model_comparison.png")

# Figure 6 - feature importance for the best model
if hasattr(best['model'], 'feature_importances_'):
    imp = best['model'].feature_importances_
else:
    imp = np.abs(best['model'].coef_[0])

top_n = 12
s = pd.Series(imp, index=feature_cols).sort_values().tail(top_n)

fig, ax = plt.subplots(figsize=(9, 6))
s.plot(kind='barh', ax=ax, color=ACCENT, edgecolor='white', width=0.6)
ax.set_title(f'Top {top_n} Risk Factors - {best_name}')
ax.set_xlabel('Feature Importance')

plt.tight_layout()
plt.savefig('../outputs/figures/06_feature_importance.png')
plt.close()
print("OK saved 06_feature_importance.png")

# Figure 7 - confusion matrix for best model
fig, ax = plt.subplots(figsize=(6, 5))
cm = confusion_matrix(y_test, best['y_pred'])
sns.heatmap(cm, annot=True, fmt='d', cmap='Oranges', ax=ax,
            xticklabels=['Non-Default', 'Default'],
            yticklabels=['Non-Default', 'Default'],
            linewidths=2, linecolor='white')
ax.set_xlabel('Predicted')
ax.set_ylabel('Actual')
ax.set_title(f'Confusion Matrix - {best_name}')

plt.tight_layout()
plt.savefig('../outputs/figures/07_confusion_matrix.png')
plt.close()
print("OK saved 07_confusion_matrix.png")

# --- Risk Segmentation ---
# scoring portfolio with best model
print("\nRISK SEGMENTATION")

# score the full portfolio with the best model
if best['scaled']:
    df['risk_score'] = best['model'].predict_proba(scaler.transform(X))[:, 1]
else:
    df['risk_score'] = best['model'].predict_proba(X)[:, 1]

q25, q50, q75 = df['risk_score'].quantile([0.25, 0.50, 0.75])
df['risk_tier'] = pd.cut(df['risk_score'], bins=[-0.01, q25, q50, q75, 1.0],
                         labels=['Low', 'Medium', 'High', 'Very High'])

# Figure 8 - risk segmentation
tier_colors = [SUCCESS, ACCENT, DANGER, '#8B0000']
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

tc = df['risk_tier'].value_counts().sort_index()
axes[0].bar(tc.index.astype(str), tc.values, color=tier_colors[:len(tc)], edgecolor='white', width=0.55)
axes[0].set_title('Applications by Risk Tier')
axes[0].set_ylabel('Count')
for i, v in enumerate(tc):
    axes[0].text(i, v + 20, str(v), ha='center', fontsize=10)

td = df.groupby('risk_tier', observed=True)['defaulted_12m'].mean()
axes[1].bar(td.index.astype(str), td * 100, color=tier_colors[:len(td)], edgecolor='white', width=0.55)
axes[1].set_title('Actual Default Rate by Tier')
axes[1].set_ylabel('Default Rate (%)')
for i, v in enumerate(td):
    axes[1].text(i, v * 100 + 0.5, f'{v:.1%}', ha='center', fontsize=10)

te = df.groupby('risk_tier', observed=True)['loan_amount_requested_eur'].sum() / 1e6
axes[2].bar(te.index.astype(str), te, color=tier_colors[:len(te)], edgecolor='white', width=0.55)
axes[2].set_title('Total Exposure by Tier')
axes[2].set_ylabel('EUR millions')
for i, v in enumerate(te):
    axes[2].text(i, v + 3, f'{v:.0f}M', ha='center', fontsize=10)

plt.suptitle('Portfolio Risk Segmentation', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../outputs/figures/08_risk_segmentation.png')
plt.close()
print("OK saved 08_risk_segmentation.png")

# Figure 9 - monthly trend (from SQL)
fig, ax = plt.subplots(figsize=(11, 4.5))

monthly = run_sql('../sql/08_monthly_trend.sql', conn)
monthly['application_month'] = pd.to_datetime(monthly['application_month'])

ax2 = ax.twinx()
ax.bar(monthly['application_month'], monthly['total_applications'], width=25, color=PRIMARY, alpha=0.4, label='Applications')
ax2.plot(monthly['application_month'], monthly['default_rate_pct'], color=ACCENT, lw=2.5, marker='o', ms=4, label='Default Rate')
ax.set_ylabel('Applications', color=PRIMARY)
ax2.set_ylabel('Default Rate (%)', color=ACCENT)
ax.set_title('Monthly Application Volume & Default Rate')
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=9)
ax2.spines['right'].set_visible(True)
ax2.spines['right'].set_color(ACCENT)

plt.tight_layout()
plt.savefig('../outputs/figures/09_monthly_trend.png')
plt.close()
print("OK saved 09_monthly_trend.png")

# done with sql
conn.close()

# save summary
print("\nSUMMARY")

high_risk_exposure = df[df['risk_tier'].isin(['High', 'Very High'])]['loan_amount_requested_eur'].sum() / 1e6

summary = pd.DataFrame({
    'Metric': ['Total Applications', 'Default Rate', 'Best Model', 'AUC-ROC', 'F1 Score',
               'High-Risk Exposure (EUR M)'],
    'Value': [str(len(df)), f'{df["defaulted_12m"].mean():.1%}', best_name,
              f'{best["auc"]:.4f}', f'{best["f1"]:.4f}',
              f'{high_risk_exposure:.0f}M'],
})
summary.to_csv('../data/model_summary.csv', index=False)
print("OK saved model_summary.csv")
print("\nALL OUTPUTS GENERATED SUCCESSFULLY")
