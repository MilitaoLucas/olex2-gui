DROP VIEW IF EXISTS `dimas_plone`.`people_fullnames`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost`
SQL SECURITY DEFINER VIEW  `dimas_plone`.`people_fullnames` AS
select concat(`people`.`GivenName`,_latin1' ',`people`.`Surname`)
  AS `display`,`people`.`ID`
  AS `ID`
from `people`;