create table userdetails (
	name varchar(50),
    mailid varchar(100) unique,
    password varchar(100),
    userid varchar(50) unique primary key,
    creditcardno varchar(100),
    cvv varchar(50),
    pinno varchar(6),
    expdate varchar(50),
    amount decimal(10,2)
);

CREATE TABLE transactions (
    transaction_id varchar(50) PRIMARY KEY,
    userid varchar(50),
    amount DECIMAL(10, 2),
    tdesc text,
    transaction_date varchar(50),
    FOREIGN KEY (userid) REFERENCES userdetails(userid)
);

