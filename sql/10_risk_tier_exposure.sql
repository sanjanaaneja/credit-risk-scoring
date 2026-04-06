-- Risk tier exposure using NTILE
-- Split the portfolio into 4 tiers based on credit bureau score

WITH tiered AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY credit_bureau_score DESC) AS risk_tier
    FROM sme_loan_applications
)

SELECT
    risk_tier,
    CASE risk_tier
        WHEN 1 THEN 'Low Risk'
        WHEN 2 THEN 'Moderate Risk'
        WHEN 3 THEN 'Elevated Risk'
        WHEN 4 THEN 'High Risk'
    END AS tier_label,
    COUNT(*)                                            AS total_applications,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS defaults,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                                   AS default_rate_pct,
    SUM(loan_amount_requested_eur)                      AS total_exposure_eur,
    ROUND(AVG(loan_amount_requested_eur), 2)            AS avg_loan_amount_eur,
    ROUND(AVG(credit_bureau_score), 0)                  AS avg_credit_score,
    ROUND(AVG(debt_to_equity_ratio), 2)                 AS avg_debt_to_equity
FROM tiered
GROUP BY risk_tier
ORDER BY risk_tier;
