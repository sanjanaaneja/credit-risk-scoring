-- Default rate by sector
-- shows which sectors are riskiest

SELECT
    sector,
    COUNT(*)                                            AS total_applications,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS defaults,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                                   AS default_rate_pct,
    SUM(loan_amount_requested_eur)                      AS total_exposure_eur,
    ROUND(AVG(loan_amount_requested_eur), 2)            AS avg_loan_amount_eur,
    ROUND(AVG(credit_bureau_score), 0)                  AS avg_credit_score
FROM sme_loan_applications
GROUP BY sector
ORDER BY default_rate_pct DESC;
