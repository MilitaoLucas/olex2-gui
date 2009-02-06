DROP TABLE IF EXISTS `OlexGui`.`translation`;
CREATE TABLE  `OlexGui`.`translation` (
  `ID` int(10) unsigned NOT NULL auto_increment,
  `OXD` varchar(200) default NULL,
  `English` varchar(2000) character set latin1 default "",
  `German` varchar(2000) character set latin1 default "",
  `Spanish` varchar(2000) character set latin1 default "",
  `Chinese` varchar(2000) character set latin1 default "",
  `Russian` varchar(2000) character set latin1 default "",
  `French` varchar(2000) character set latin1 default "",
  `Greek` varchar(2000) character set latin1 default "",
  `Arabic` varchar(2000) character set latin1 default "",
  `Japanese` varchar(2000) character set latin1 default "",
  `context` varchar(200) default "",
  `translationtypeID` int(10) unsigned default NULL,
  `last_modified_by` varchar(45) character set latin1 default NULL,
  `last_modified_on` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=gb2312;