DROP TABLE IF EXISTS `dimas_e`.`submission`;
CREATE TABLE  `dimas_e`.`submission` (
  `ID` int(10) unsigned NOT NULL auto_increment,
  `ID_xray` varchar(45) default NULL,
  `InstituteID` int(11) default NULL,
  `SubmitterID` int(11) default NULL,
  `AccountID` int(11) NOT NULL default '0',
  `DateSubmission` datetime default NULL,
  `ChemicalName` varchar(255) character set utf8 default NULL,
  `FormulaSubmitted` varchar(255) character set utf8 default NULL,
  `CompoundCode` varchar(255) character set utf8 default NULL,
  `Smiles` varchar(255) character set utf8 default NULL,
  `Marvin` mediumtext,
  `ListSensitivities` varchar(255) character set utf8 default NULL,
  `ListToxicities` varchar(255) character set utf8 default NULL,
  `ListPreviousAnalyses` varchar(255) character set utf8 default NULL,
  `CommentPreparation` text,
  `Comment` mediumtext character set utf8,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  USING BTREE (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=100000 DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`submission` (`ID`) VALUES (0);

DROP TABLE IF EXISTS `dimas_e`.`submission_xray`;
CREATE TABLE  `dimas_e`.`submission_xray` (
  `ID` int(10) unsigned NOT NULL,
  `ID_service` varchar(10) character set utf8 NOT NULL,
  `AnalysisCode` varchar(255) character set utf8 default NULL,
  `DateSubmission` datetime default NULL,
  `OperatorID` int(11) default NULL,
  `MeasurementTemperature` varchar(10) character set utf8 default NULL,
  `Solvents` varchar(50) character set utf8 default NULL,
  `ListType` varchar(255) character set utf8 default NULL,
  `ListReasons` varchar(255) character set utf8 default NULL,
  `Comment` mediumtext character set utf8,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  USING BTREE (`ID_service`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`submission_xray` (`ID`,`ID_service`) VALUES (0, 'NEW');

DROP TABLE IF EXISTS `dimas_e`.`submission_nmr`;
CREATE TABLE  `dimas_e`.`submission_nmr` (
  `ID` int(10) unsigned NOT NULL,
  `ID_service` varchar(45) NOT NULL,
  `AnalysisCode` varchar(255) character set utf8 default NULL,
  `DateSubmission` datetime default NULL,
  `OperatorID` int(10) unsigned default NULL,
  `TypeID` int(10) unsigned NOT NULL default '0',
  `SolventID` int(10) unsigned NOT NULL default '0',
  `Comment` mediumtext character set utf8,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  USING BTREE (`ID_service`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`submission_nmr` (`ID`,`ID_service`) VALUES (0, 'NEW');