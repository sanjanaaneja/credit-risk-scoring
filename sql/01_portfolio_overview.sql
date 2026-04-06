-- Portfolio overview: headline metrics for the SME loan book

SELECT
    COUNT(*)                                        AS total_applications,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS total_defaults,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                               AS default_rate_pct,
    ROUND(AVG(loan_amount_requested_eur), 2)        AS avg_loan_amount_eur,
    SUM(loan_amount_requested_eur)                  AS total_exposure_eur,
    ROUND(AVG(loan_term_months), 1)                 AS avg_loan_term_months,
    ROUND(AVG(credit_bureau_score), 0)              AS avg_credit_bureau_score
FROM sme_loan_applications;
