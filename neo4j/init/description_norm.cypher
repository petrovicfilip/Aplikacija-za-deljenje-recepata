MATCH (r:Recipe)
WHERE r.description IS NOT NULL AND (r.description_norm IS NULL OR r.description_norm = "")
SET r.description_norm = toLower(r.description);