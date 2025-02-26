use swgresource;

ALTER TABLE tResourceType ADD COLUMN elective TINYINT DEFAULT 0;

CREATE TABLE `tGalaxyResourceType` (
  `galaxyID` int(11) NOT NULL,
  `resourceType` varchar(63) NOT NULL,
  PRIMARY KEY (`galaxyID`,`resourceType`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO
  `tResourceType`
    (`resourceTypeName`, `resourceCategory`, `resourceGroup`, `maxTypes`, `enterable`, `resourceType`, `CRmin`, `CRmax`, `CDmin`, `CDmax`, `DRmin`, `DRmax`, `FLmin`, `FLmax`, `HRmin`, `HRmax`, `MAmin`, `MAmax`, `PEmin`, `PEmax`, `OQmin`, `OQmax`, `SRmin`, `SRmax`, `UTmin`, `UTmax`, `ERmin`, `ERmax`, `specificPlanet`, `inventoryType`, `containerType`, `elective`)
  VALUES
    ('Mandalorian Type 1 Crystal Amorphous Gem', 'mineral', 'gemstone_armophous', 2, 1, 'amorphous_mandalore_1', 600, 1000, 0, 0, 600, 1000, 0, 0, 600, 1000, 300, 700, 0, 0, 1, 1000, 600, 1000, 600, 1000, 1, 900, 0, 'gemstone', 'gemstone', 1),
    ('Mandalorian Type 2 Crystal Amorphous Gem', 'mineral', 'gemstone_armophous', 2, 1, 'amorphous_mandalore_2', 600, 1000, 0, 0, 600, 1000, 0, 0, 600, 1000, 300, 700, 0, 0, 1, 1000, 600, 1000, 600, 1000, 1, 900, 0, 'gemstone', 'gemstone', 1),
    ('Mandalorian Type 1 Crystalline Gem', 'mineral', 'gemstone_crystalline', 2, 1, 'crystalline_mandalore_1', 600, 1000, 0, 0, 500, 1000, 0, 0, 600, 1000, 1, 500, 0, 0, 300, 1000, 600, 1000, 600, 1000, 700, 1000, 0, 'gemstone', 'gemstone', 1),
    ('Mandalorian Type 2 Crystalline Gem', 'mineral', 'gemstone_crystalline', 2, 1, 'crystalline_mandalore_2', 600, 1000, 0, 0, 500, 1000, 0, 0, 600, 1000, 1, 500, 0, 0, 300, 1000, 600, 1000, 600, 1000, 700, 1000, 0, 'gemstone', 'gemstone', 1);

INSERT INTO
  `tResourceTypeGroup`
    (`resourceType`, `resourceGroup`)
  VALUES
    ('amorphous_mandalore_1', 'inorganic'),
    ('amorphous_mandalore_1', 'mineral'),
    ('amorphous_mandalore_1', 'gemstone'),
    ('amorphous_mandalore_1', 'gemstone_armophous'),
    ('amorphous_mandalore_2', 'inorganic'),
    ('amorphous_mandalore_2', 'mineral'),
    ('amorphous_mandalore_2', 'gemstone'),
    ('amorphous_mandalore_2', 'gemstone_armophous'),
    ('crystalline_mandalore_1', 'inorganic'),
    ('crystalline_mandalore_1', 'mineral'),
    ('crystalline_mandalore_1', 'gemstone'),
    ('crystalline_mandalore_1', 'gemstone_crystalline'),
    ('crystalline_mandalore_2', 'inorganic'),
    ('crystalline_mandalore_2', 'mineral'),
    ('crystalline_mandalore_2', 'gemstone'),
    ('crystalline_mandalore_2', 'gemstone_crystalline');
