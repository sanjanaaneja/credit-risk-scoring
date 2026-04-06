-- Do existing bank clients default less?

SELECT
    existing_bank_client,
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
FROM sme_loan_applications
GROUP BY existing_bank_client
ORDER BY existing_bank_client DESC;
