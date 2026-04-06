-- Risk by company age
-- bucket companies by how old they are and check default rates

SELECT
    CASE
        WHEN years_in_business < 2  THEN '1. Under 2 years'
        WHEN years_in_business < 5  THEN '2. 2 to 5 years'
        WHEN years_in_business < 10 THEN '3. 5 to 10 years'
        WHEN years_in_business < 20 THEN '4. 10 to 20 years'
        ELSE                             '5. 20+ years'
    END AS age_bucket,
    COUNT(*)                                            AS total_applications,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS defaults,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                                   AS default_rate_pct,
    ROUND(AVG(annual_revenue_eur), 2)                   AS avg_annual_revenue_eur,
    ROUND(AVG(loan_amount_requested_eur), 2)            AS avg_loan_amount_eur,
    ROUND(AVG(credit_bureau_score), 0)                  AS avg_credit_score
FROM sme_loan_applications
GROUP BY age_bucket
ORDER BY age_bucket;
