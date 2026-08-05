\set ON_ERROR_STOP on

DO $$
DECLARE
    target_station_id integer;
    canonical_price numeric(12,3);
    min_price numeric(12,3);
    max_price numeric(12,3);
    matching_nozzles integer;
    effective_time timestamptz;
    target_currency varchar(10);
BEGIN
    SELECT id INTO STRICT target_station_id
    FROM stations
    WHERE station_id = 'STATION-HAIL-001' AND deleted_at IS NULL;

    IF EXISTS (
        SELECT 1 FROM fuel_prices
        WHERE station_id = target_station_id
          AND active IS TRUE
          AND lower(regexp_replace(fuel_code, '[^a-zA-Z0-9]', '', 'g')) IN ('gasoline95', '95')
          AND effective_at <= now()
    ) THEN
        RAISE NOTICE 'Active Gasoline 95 price already exists; no insert required';
        RETURN;
    END IF;

    SELECT min(unit_price), max(unit_price), count(*)
    INTO min_price, max_price, matching_nozzles
    FROM nozzles
    WHERE station_id = target_station_id
      AND enabled IS TRUE
      AND deleted_at IS NULL
      AND unit_price IS NOT NULL
      AND lower(regexp_replace(fuel_code, '[^a-zA-Z0-9]', '', 'g')) IN ('gasoline95', '95');

    IF matching_nozzles = 0 OR min_price IS DISTINCT FROM max_price THEN
        RAISE EXCEPTION 'Cannot repair Gasoline 95: enabled nozzle prices are missing or inconsistent';
    END IF;
    canonical_price := min_price;

    SELECT created_at INTO effective_time
    FROM price_change_logs
    WHERE station_id = target_station_id
      AND lower(regexp_replace(fuel_code, '[^a-zA-Z0-9]', '', 'g')) IN ('gasoline95', '95')
      AND new_price = canonical_price
    ORDER BY created_at DESC
    LIMIT 1;

    IF effective_time IS NULL THEN
        RAISE EXCEPTION 'Cannot repair Gasoline 95: no matching authoritative price ACK exists';
    END IF;

    SELECT currency INTO target_currency
    FROM fuel_prices
    WHERE station_id = target_station_id AND active IS TRUE
    ORDER BY effective_at DESC LIMIT 1;

    INSERT INTO fuel_prices (
        station_id, fuel_code, fuel_name_ar, fuel_name_en, price, currency,
        effective_at, active, created_at, updated_at
    ) VALUES (
        target_station_id, 'gasoline95', 'بنزين 95', 'Gasoline 95',
        canonical_price, coalesce(target_currency, 'SAR'), effective_time,
        TRUE, now(), now()
    );

    INSERT INTO fuel_products (
        station_id, code, name_ar, name_en, color, enabled, created_at, updated_at
    )
    SELECT target_station_id, values.code, values.name_ar, values.name_en,
           values.color, TRUE, now(), now()
    FROM (VALUES
        ('gasoline91', 'بنزين 91', 'Gasoline 91', '#22a06b'),
        ('gasoline95', 'بنزين 95', 'Gasoline 95', '#d64545'),
        ('diesel', 'ديزل', 'Diesel', '#d2a51d')
    ) AS values(code, name_ar, name_en, color)
    WHERE EXISTS (
        SELECT 1 FROM fuel_prices price
        WHERE price.station_id = target_station_id
          AND price.active IS TRUE
          AND lower(regexp_replace(price.fuel_code, '[^a-zA-Z0-9]', '', 'g')) = values.code
    )
    ON CONFLICT (station_id, code) DO UPDATE SET
        name_ar = excluded.name_ar,
        name_en = excluded.name_en,
        color = excluded.color,
        enabled = TRUE,
        updated_at = now();
END $$;

