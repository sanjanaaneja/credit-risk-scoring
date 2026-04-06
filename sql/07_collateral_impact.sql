-- Does collateral reduce defaults? Break it down by loan size bucket

SELECT
    CASE
        WHEN loan_amount_requested_eur < 50000   THEN '1. Under 50K'
        WHEN loan_amount_requested_eur < 150000  THEN '2. 50K to 150K'
        WHEN loan_amount_requested_eur < 500000  THEN '3. 150K to 500K'
        WHEN loan_amount_requested_eur < 1000000 THEN '4. 500K to 1M'
        ELSE                                          '5. Over 1M'
    END AS loan_size_bucket,
    collateral_offered,
    COUNT(*)                                            AS total_applications,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS defaults,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                                   AS default_rate_pct,
    SUM(loan_amount_requested_eur)                      AS total_exposure_eur
FROM sme_loan_applications
GROUP BY loan_size_bucket, collateral_offered
ORDER BY loan_size_bucket, collateral_offered;
