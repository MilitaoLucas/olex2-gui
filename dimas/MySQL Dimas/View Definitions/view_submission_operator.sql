DROP VIEW IF EXISTS `dimas_plone`.`submision_operator`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW
`dimas_plone`.`submision_operator` AS
select concat(`people`.`GivenName`,_latin1' ',`people`.`Surname`)
AS `display`,`people_status`.`IsAccount`
AS `IsAccount`,`people`.`ID`
AS `ID`
from
(`people` join `people_status`
on((`people`.`ID` = `people_status`.`ID`)))
where (`people_status`.`IsDiffraction`
like _latin1'Yes');