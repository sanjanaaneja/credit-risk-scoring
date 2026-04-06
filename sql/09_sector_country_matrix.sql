-- Sector and country matrix
-- just group by both to see where risk concentrates

SELECT
    sector,
    country,
    COUNT(*)                                            AS total_applications,
    SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END) AS defaults,
    ROUND(
        100.0 * SUM(CASE WHEN defaulted_12m = 1 THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )                                                   AS default_rate_pct,
    SUM(loan_amount_requested_eur)                      AS total_exposure_eur
FROM sme_loan_applications
GROUP BY sector, country
ORDER BY default_rate_pct DESC;
