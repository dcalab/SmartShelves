mysql -u root -p -e 'CREATE DATABASE SmartShelves'
mysql -u root -p -e 'CREATE TABLE Items(itemID int PRIMARY KEY, name varchar(255), location varchar(255), led int)' SmartShelves