DROP TABLE IF EXISTS `dimas_e`.`nmr_solvent`;
CREATE TABLE  `dimas_e`.`nmr_solvent` (
  `ID` int(10) unsigned NOT NULL,
  `display` varchar(45) NOT NULL,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (0, '--');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (1, 'CDCl3');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (2, 'D2O');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (3, 'DMSO');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (4, 'CD3OD');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (5, 'CD2Cl2');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (6, 'CD3CN');
INSERT INTO `dimas_e`.`nmr_solvent` (`ID`, `display`) VALUES (7, 'CD3OD');


DROP TABLE IF EXISTS `dimas_e`.`nmr_type`;
CREATE TABLE  `dimas_e`.`nmr_type` (
  `ID` int(10) unsigned NOT NULL,
  `display` varchar(45) NOT NULL,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`nmr_type` (`ID`, `display`) VALUES (0, '--');
INSERT INTO `dimas_e`.`nmr_type` (`ID`, `display`) VALUES (1, 'Proton');
INSERT INTO `dimas_e`.`nmr_type` (`ID`, `display`) VALUES (2, 'Carbon');
INSERT INTO `dimas_e`.`nmr_type` (`ID`, `display`) VALUES (3, 'Fluorine');
INSERT INTO `dimas_e`.`nmr_type` (`ID`, `display`) VALUES (4, 'Phosphorus');

DROP TABLE IF EXISTS `dimas_e`.`nmr_progress`;
CREATE TABLE  `dimas_e`.`nmr_progress` (
  `ID_service` varchar(64) NOT NULL default 'xxxxxxx',
  `StatusID` int(11) NOT NULL default '0',
  `DateMeasured` datetime default NULL,
  `DateCompleted` datetime default NULL,
  `Comment_nmr_progress` mediumtext,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `ID` varchar(45) NOT NULL default '',
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;