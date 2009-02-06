DROP TABLE IF EXISTS `dimas_e`.`xray_crystal`;
CREATE TABLE  `dimas_e`.`xray_crystal` (
  `Sort` smallint(6) NOT NULL auto_increment,
  `ID_service` varchar(10) NOT NULL,
  `ID` varchar(45) NOT NULL default '',
  `ColourAppearanceID` tinyint(1) default 0,
  `ColourIntensityID` tinyint(1) default 0,
  `ColourBaseID` tinyint(1) default 0,
  `exptl_crystal_colour` varchar(45) default 0,
  `exptl_crystal_size_min` float unsigned default NULL,
  `exptl_crystal_size_med` float default NULL,
  `exptl_crystal_size_max` float default NULL,
  `ShapeID` tinyint(1) default 0,
  `CifShape` varchar(45) default NULL,
  `NameSystematic` varchar(100) default NULL,
  `FormulaSum` varchar(255) default NULL,
  `Mass` float default NULL,
  `MeltingPoint_1` varchar(6) default NULL,
  `MeltingPoint_2` varchar(6) default NULL,
  `MeltingPoint_3` varchar(6) default NULL,
  `Density` float default NULL,
  `Comment` varchar(255) default NULL,
  `CommentCrystallisation` text,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`),
  KEY `Index_2` (`Sort`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`xray_crystal` (`ID`,`ID_service`) VALUES (0, 'NEW');


DROP TABLE IF EXISTS `dimas_e`.`xray_diffraction`;
CREATE TABLE  `dimas_e`.`xray_diffraction` (
  `ID_service` varchar(10) NOT NULL default 'xxxxxxx',
  `DiffractometerID` int(11) NOT NULL default '0',
  `data_HklID` varchar(10) NOT NULL default '',
  `Comment` mediumtext,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `data_P4pID` varchar(10) NOT NULL default '',
  `diffrn_ambient_temperature` varchar(10) default NULL,
  `ID` varchar(45) NOT NULL default '',
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`xray_diffraction` (`ID`,`ID_service`) VALUES (0, 'NEW');


DROP TABLE IF EXISTS `dimas_e`.`xray_reference`;
CREATE TABLE  `dimas_e`.`xray_reference` (
  `ID_service` varchar(10) NOT NULL,
  `CCDCNo` varchar(100) default '',
  `REFCODE` varchar(10) default '',
  `Reference` varchar(45) default NULL,
  `journal_name_full` varchar(45) default NULL,
  `journal_volume` varchar(45) default NULL,
  `journal_pages` varchar(45) default NULL,
  `journal_year` varchar(45) default NULL,
  `publ_authors` varchar(400) default NULL,
  `Comment` varchar(100) default NULL,
  `ID` varchar(45) NOT NULL,
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`xray_reference` (`ID`,`ID_service`) VALUES (0, 'NEW');


DROP TABLE IF EXISTS `dimas_e`.`xray_refinement`;
CREATE TABLE  `dimas_e`.`xray_refinement` (
  `ID_service` varchar(10) NOT NULL default 'xxxxxxx',
  `data_CifID` varchar(10) NOT NULL default '',
  `data_ResID` varchar(10) NOT NULL default '',
  `Comment` mediumtext,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `data_DocID` varchar(45) default NULL,
  `refine_ls_R_factor_gt` varchar(45) default NULL,
  `Smile` varchar(800) default NULL,
  `Inchi` varchar(800) default NULL,
  `Setting` varchar(45) default NULL,
  `SpaceGroup` varchar(45) default NULL,
  `ID` varchar(45) NOT NULL,
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`xray_refinement` (`ID`,`ID_service`) VALUES (0, 'NEW');

DROP TABLE IF EXISTS `dimas_e`.`xray_progress`;
CREATE TABLE  `dimas_e`.`xray_progress` (
  `ID_service` varchar(64) NOT NULL default 'xxxxxxx',
  `StatusID` int(11) NOT NULL default '0',
  `DateCollected` datetime default NULL,
  `DateCompleted` datetime default NULL,
  `HasHkl` tinyint(3) unsigned default NULL,
  `Comment` mediumtext,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `ID` varchar(45) NOT NULL default '',
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`xray_progress` (`ID`,`ID_service`) VALUES (0, 'NEW');


DROP TABLE IF EXISTS `dimas_e`.`xray_diffraction_cell`;
CREATE TABLE  `dimas_e`.`xray_diffraction_cell` (
  `ID_service` varchar(10) NOT NULL,
  `cell_a` varchar(8) default NULL,
  `cell_b` varchar(8) default NULL,
  `cell_c` varchar(8) default NULL,
  `cell_alpha` varchar(8) default NULL,
  `cell_beta` varchar(8) default NULL,
  `cell_gamma` varchar(8) default NULL,
  `cell_volume` varchar(8) default NULL,
  `cell_a_err` smallint(5) unsigned default NULL,
  `cell_b_err` smallint(5) unsigned default NULL,
  `cell_c_err` smallint(5) unsigned default NULL,
  `cell_alpha_err` smallint(5) unsigned default NULL,
  `cell_beta_err` smallint(5) unsigned default NULL,
  `cell_gamma_err` smallint(5) unsigned default NULL,
  `cell_volume_err` smallint(5) unsigned default NULL,
  `ID` varchar(45) NOT NULL,
  PRIMARY KEY  USING BTREE (`ID_service`,`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
INSERT INTO `dimas_e`.`xray_diffraction_cell` (`ID`,`ID_service`) VALUES (0, 'NEW');


DROP TABLE IF EXISTS `dimas_e`.`xray_crystal_colourbase`;
CREATE TABLE  `dimas_e`.`xray_crystal_colourbase` (
  `ID` int(3) unsigned NOT NULL default '0',
  `cif` varchar(100) default NULL,
  `display` varchar(15) default NULL,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`xray_crystal_colourintensity`;
CREATE TABLE  `dimas_e`.`xray_crystal_colourintensity` (
  `ID` int(3) unsigned NOT NULL default '0',
  `cif` varchar(100) default NULL,
  `display` varchar(15) default NULL,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`xray_crystal_colourappearance`;
CREATE TABLE  `dimas_e`.`xray_crystal_colourappearance` (
  `ID` int(3) unsigned NOT NULL default '0',
  `display` varchar(15) default NULL,
  `cif` varchar(100) default NULL,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`xray_crystal_shape`;
CREATE TABLE  `dimas_e`.`xray_crystal_shape` (
  `ID` int(3) unsigned NOT NULL default '0',
  `display` varchar(20) default NULL,
  `cif` varchar(100) default NULL,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`xray_diffraction_diffractometer`;
CREATE TABLE  `dimas_e`.`xray_diffraction_diffractometer` (
  `ID` int(3) unsigned NOT NULL default '0',
  `diffractometer_CIF` varchar(30) default '',
  `display` varchar(30) default NULL,
  `diffractometer_HLP` varchar(255) default '',
  `AreaResolution_DAT` smallint(6) default NULL,
  `Timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;

DROP TABLE IF EXISTS `dimas_e`.`xray_progress_status`;
CREATE TABLE  `dimas_e`.`xray_progress_status` (
  `ID` int(11) NOT NULL default '0',
  `help` varchar(100) NOT NULL default '',
  `display` varchar(100) NOT NULL default '',
  PRIMARY KEY  (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;