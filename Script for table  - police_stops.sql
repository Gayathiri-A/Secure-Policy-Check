Use police;
CREATE TABLE police_stops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stop_datetime DATETIME,
    country_name VARCHAR(100),
    driver_gender VARCHAR(10),
    driver_age_raw INT,
    driver_age INT,
    driver_race VARCHAR(50),
    violation_raw VARCHAR(255),
    violation VARCHAR(255),
    search_conducted BOOLEAN,
    search_type VARCHAR(255),
    stop_outcome VARCHAR(100),
    is_arrested BOOLEAN,
    stop_duration VARCHAR(50),
    drugs_related_stop BOOLEAN,
    vehicle_number VARCHAR(50)
);
