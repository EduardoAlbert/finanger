DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS transaction_type;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount NUMERIC,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE transaction_type(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL
);

INSERT INTO transaction_type (id, type) VALUES (1, "incomes");
INSERT INTO transaction_type (id, type) VALUES (2, "expenses");
INSERT INTO transaction_type (id, type) VALUES (3, "transfers");

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount NUMERIC,
    date TEXT,
    type_id INTEGER,
    account_id_origin INTEGER,
    account_id_destination INTEGER,
    FOREIGN KEY (type_id) REFERENCES transaction_type(id),
    FOREIGN KEY (account_id_origin) REFERENCES account(id),
    FOREIGN KEY (account_id_destination) REFERENCES account(id)
);