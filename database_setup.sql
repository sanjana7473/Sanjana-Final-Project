-- For local db
CREATE DATABASE retail_db;

USE retail_db;


-- 

CREATE TABLE households (
    hshd_num INT PRIMARY KEY,
    loyalty_flag VARCHAR(20),
    age_range VARCHAR(50),
    marital_status VARCHAR(50),
    income_range VARCHAR(50),
    home_ownership VARCHAR(50),
    household_size INT,
    children INT
);

CREATE TABLE transactions (
    basket_num INT,
    hshd_num INT,
    purchase_date DATE,
    product_num INT,
    spend FLOAT,
    units INT,
    store_region VARCHAR(100)
);

CREATE TABLE products (
    product_num INT PRIMARY KEY,
    department VARCHAR(100),
    commodity VARCHAR(100),
    brand_type VARCHAR(50),
    organic_flag VARCHAR(5)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

