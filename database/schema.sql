CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    password TEXT,
    location TEXT,
    language TEXT
);

CREATE TABLE farmers (
    id TEXT PRIMARY KEY,
    name TEXT,
    location TEXT,
    language TEXT
);

CREATE TABLE produce (
    id TEXT PRIMARY KEY,
    farmer_name TEXT,
    crop TEXT,
    quantity REAL,
    min_price REAL,
    shelf_life INTEGER,
    quality TEXT,
    location TEXT,
    language TEXT,
    status TEXT
);

CREATE TABLE negotiations (
    negotiation_id TEXT PRIMARY KEY,
    status TEXT,
    summary TEXT
);

CREATE TABLE offers (
    id TEXT PRIMARY KEY,
    negotiation_id TEXT,
    round INTEGER,
    agent TEXT,
    price REAL,
    decision TEXT
);

CREATE TABLE history (
    user_id TEXT,
    negotiation_id TEXT,
    crop TEXT,
    quantity REAL,
    status TEXT,
    final_price REAL,
    summary TEXT
);