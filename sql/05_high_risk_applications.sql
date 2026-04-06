-- High risk applications
-- these are the ones with low credit score, high leverage, and prior defaults

SELECT
    COUNT(*)                                            AS high_risk_count,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS defaults_in_segment,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                                   AS segment_default_rate_pct,
    SUM(loan_amount_requested_eur)                      AS segment_exposure_eur,
    ROUND(AVG(loan_amount_requested_eur), 2)            AS avg_loan_amount_eur,
    ROUND(AVG(credit_bureau_score), 0)                  AS avg_credit_score,
    ROUND(AVG(debt_to_equity_ratio), 2)                 AS avg_debt_to_equity
FROM sme_loan_applications
WHERE credit_bureau_score < 550
  AND debt_to_equity_ratio > 3
  AND has_payment_defaults = 1;
