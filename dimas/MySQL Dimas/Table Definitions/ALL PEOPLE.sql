DROP TABLE IF EXISTS `dimas_e`.`people`;
CREATE TABLE  `dimas_e`.`people` (
  `ID` int(11) NOT NULL auto_increment,
  `Surname` varchar(20) default NULL,
  `GivenName` varchar(15) default NULL,
  `OtherNames` varchar(45) default NULL,
  `Username` varchar(45) NOT NULL default '',
  PRIMARY KEY  (`ID`,`Username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`people_contact`;
CREATE TABLE  `dimas_e`.`people_contact` (
  `IDlocal` int(11) NOT NULL auto_increment,
  `ID` int(11) NOT NULL default '0',
  `Phone` varchar(20) default NULL,
  `Office` varchar(20) default NULL,
  `Lab` varchar(45) default NULL,
  `eMail` varchar(50) default NULL,
  `IsCurrent` varchar(3) default NULL,
  `DateBegin` datetime default '0000-00-00 00:00:00' COMMENT 'begin of validity of entry',
  `DateEnd` datetime default '0000-00-00 00:00:00' COMMENT 'end of validity of entry',
  `OldRecord` varchar(3) default NULL,
  PRIMARY KEY  (`IDlocal`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`people_status`;
CREATE TABLE  `dimas_e`.`people_status` (
  `IDlocal` int(11) NOT NULL auto_increment,
  `ID` int(11) NOT NULL default '0',
  `AccountID` int(11) default NULL,
  `Nickname` varchar(100) default NULL,
  `InstituteID` int(11) default NULL,
  `IsIR` char(3) default NULL,
  `IsCHN` char(3) default NULL,
  `IsNMR` varchar(10) default NULL,
  `IsMS` char(3) default NULL,
  `IsDiffraction` char(3) default NULL,
  `IsAccount` char(3) default NULL,
  `DateFirst` date default NULL,
  `DateLast` date default NULL,
  `Roles` varchar(255) default NULL,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `IsCurrent` char(3) default NULL,
  `DateBegin` datetime default NULL,
  `DateEnd` datetime default NULL,
  `OldRecord` varchar(3) default NULL,
  PRIMARY KEY  (`IDlocal`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`people_status_institution`;
CREATE TABLE  `dimas_e`.`people_status_institution` (
  `ID` int(10) unsigned NOT NULL auto_increment,
  `display` varchar(100) NOT NULL default '',
  `LabName` varchar(64) NOT NULL default '',
  `DepartmentName` varchar(64) default NULL,
  `InstitutionName` varchar(64) default NULL,
  `Address1` varchar(64) default NULL,
  `Address2` varchar(64) default NULL,
  `City` varchar(16) NOT NULL default '',
  `Postcode` varchar(8) NOT NULL default '',
  `Country` varchar(16) NOT NULL default '',
  `Phone` varchar(16) default NULL,
  `Email` varchar(32) default NULL,
  `CrystallographyManager` int(11) NOT NULL default '0',
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;