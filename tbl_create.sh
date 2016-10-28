mysql -u root -p -e 'CREATE DATABASE SmartShelves'
mysql -u root -p -e 'CREATE TABLE Locations(locationID int PRIMARY KEY AUTO_INCREMENT, name varchar(255), Led int)' SmartShelves
mysql -u root -p -e 'CREATE TABLE Items(itemID int PRIMARY KEY AUTO_INCREMENT, name varchar(255), locationID int, FOREIGN KEY (locationID) REFERENCES Locations(locationID))' SmartShelves
