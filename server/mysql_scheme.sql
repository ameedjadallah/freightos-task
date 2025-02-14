-- Create market_rates table
CREATE TABLE market_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    origin VARCHAR(10) NOT NULL,
    destination VARCHAR(10) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- Create aggregated_market_rates table
CREATE TABLE aggregated_market_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    origin VARCHAR(10) NOT NULL,
    destination VARCHAR(10) NOT NULL,
    min_price DECIMAL(10,2),
    percentile_10_price DECIMAL(10,2),
    median_price DECIMAL(10,2),
    percentile_90_price DECIMAL(10,2),
    max_price DECIMAL(10,2)
);

-- Create users_rates table
CREATE TABLE users_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    origin VARCHAR(10) NOT NULL,
    destination VARCHAR(10) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    annual_volume DECIMAL(10,2) NOT NULL
);
