mysql -u root -p -e 'DROP TABLE IF EXISTS Items; DROP TABLE IF EXISTS Locations' SmartShelves
mysql -u root -p -e 'CREATE TABLE Locations(locationID int PRIMARY KEY AUTO_INCREMENT, name varchar(255), Led int); CREATE TABLE Items(itemID int PRIMARY KEY AUTO_INCREMENT, name varchar(255), locationID int, FOREIGN KEY (locationID) REFERENCES Locations(locationID))' SmartShelves
