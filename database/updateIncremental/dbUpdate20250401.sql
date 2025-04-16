use swgresource;

CREATE TABLE `tResourceTypeOverrides` (
  `galaxyID` int(11) NOT NULL,
  `resourceType` varchar(63) NOT NULL,
  `specificPlanet` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`galaxyID`,`resourceType`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
