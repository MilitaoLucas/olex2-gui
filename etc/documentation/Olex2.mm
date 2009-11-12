<map version="0.8.1">
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->
<node COLOR="#33cc00" CREATED="1246481935391" ID="Freemind_Link_1945128606" MODIFIED="1258017392209" STYLE="bubble" TEXT="Olex2">
<edge STYLE="bezier"/>
<font BOLD="true" NAME="SansSerif" SIZE="14"/>
<node CREATED="1246482224868" ID="_" MODIFIED="1258017336775" POSITION="right" TEXT="Solving  Structures">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#ff0000" CREATED="1246482232543" ID="Freemind_Link_1780118016" MODIFIED="1258017370707" TEXT="With ShelX">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482365468" ID="Freemind_Link_420495388" MODIFIED="1258017336771" TEXT="ShelXS">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482388347" ID="Freemind_Link_372544166" MODIFIED="1258017336769" TEXT="Direct Methods">
<font NAME="Gill Sans MT" SIZE="12"/>
</node>
<node CREATED="1246482393907" ID="Freemind_Link_1107238741" MODIFIED="1258017336768" TEXT="Patterson"/>
</node>
<node CREATED="1246482373764" ID="Freemind_Link_97112547" MODIFIED="1258017336767" TEXT="ShelXM">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node COLOR="#990000" CREATED="1253792161685" ID="Freemind_Link_1342539768" MODIFIED="1258017336765" TEXT="With Superflip">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792172213" ID="Freemind_Link_1030614921" MODIFIED="1258017336763" TEXT="With SIR">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1246482235479" ID="Freemind_Link_779597585" MODIFIED="1258017336761" TEXT="With smtbx">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482406451" ID="Freemind_Link_1594921558" MODIFIED="1258017336759" TEXT="Charge Flipping">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#990000" CREATED="1253792262563" ID="Freemind_Link_1611571922" MODIFIED="1258017336757" TEXT="Direct Methods">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#990000" CREATED="1253792271234" ID="Freemind_Link_1464562476" MODIFIED="1258017336756" TEXT="Patterson">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
<node CREATED="1256721547419" ID="Freemind_Link_1507516291" MODIFIED="1258017336754" POSITION="right" TEXT="Model Building">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256721615513" ID="Freemind_Link_1858296237" MODIFIED="1258017336752" TEXT="Fix/Free Parameters">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256721622489" ID="Freemind_Link_551440189" MODIFIED="1258017336751" TEXT="occu">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256721627848" ID="Freemind_Link_487087225" MODIFIED="1258017336749" TEXT="xyz">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256721631640" ID="Freemind_Link_1843287449" MODIFIED="1258017336747" TEXT="Uiso">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1256721663671" ID="Freemind_Link_255534313" MODIFIED="1258017336745" TEXT="Connectivity Table">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256721674183" FOLDED="true" ID="Freemind_Link_65227912" MODIFIED="1258017336743" TEXT="Set max/min connectivity">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256724139114" ID="Freemind_Link_32629505" MODIFIED="1258017336741" TEXT="conn n [r]  atoms">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256724169657" ID="Freemind_Link_1300864142" MODIFIED="1258017336741" TEXT="Sets the maximum number of bonds for the specified  atoms to n and changes the default bond radius for the given atom type to r.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#0033ff" CREATED="1256724179081" ID="Freemind_Link_761497543" MODIFIED="1258017336741" TEXT="Examples: conn 5 $C sets the maximum number of bonds all C atoms can have to 5, conn 1.3 $C changes the bonding radius for C atoms to 1.3 (the floating point is used to distinguish between n and r in this case!), conn 5 1.3 $C combines the two commands above"/>
</node>
</node>
<node CREATED="1256721690247" FOLDED="true" ID="Freemind_Link_834937290" MODIFIED="1258017336741" TEXT="Assemble Fragments">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256724198872" FOLDED="true" ID="Freemind_Link_209403351" MODIFIED="1258017336739" TEXT="compaq">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256724219912" ID="Freemind_Link_1829471196" MODIFIED="1258017336739" TEXT="Moves all atoms or fragments of the asymmetric unit as close to each other as possible. If no options are provided, all fragments are assembled around the largest one.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256724223576" ID="Freemind_Link_1808848997" MODIFIED="1258017336739" TEXT="-a - assembles broken fragments"/>
<node CREATED="1256724230456" ID="Freemind_Link_617482285" MODIFIED="1258017336739" TEXT="-c - similar as with no options, but considers atom-to-atom distances and will move all atoms to the closest possible position to the largest fragment in the structure."/>
</node>
</node>
<node CREATED="1256721702167" FOLDED="true" ID="Freemind_Link_671266115" MODIFIED="1258017336738" TEXT="Add Bonds">
<arrowlink DESTINATION="Freemind_Link_671266115" ENDARROW="Default" ENDINCLINATION="0;0;" ID="Freemind_Arrow_Link_625694775" STARTARROW="None" STARTINCLINATION="0;0;"/>
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256724259815" FOLDED="true" ID="Freemind_Link_443044905" MODIFIED="1258017336737" TEXT="addbond A1 A2 or atoms">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256724272935" ID="Freemind_Link_635677716" MODIFIED="1258017336737" TEXT="Adds a bond to the connectivity list for the specified atoms. This operation will also be successful if symmetry equivalent atoms are specified."/>
</node>
</node>
<node CREATED="1256721702167" FOLDED="true" ID="Freemind_Link_1862961712" MODIFIED="1258017336736" TEXT="Delete Bonds">
<arrowlink DESTINATION="Freemind_Link_1862961712" ENDARROW="Default" ENDINCLINATION="0;0;" ID="Freemind_Arrow_Link_1274638195" STARTARROW="None" STARTINCLINATION="0;0;"/>
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256724259815" ID="Freemind_Link_578431107" MODIFIED="1258017336735" TEXT="delbond A1 A2 or atoms">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256724272935" ID="Freemind_Link_1561065304" MODIFIED="1258017336735" TEXT="Deletes a bond to the connectivity list for the specified atoms. This operation will also be successful if symmetry equivalent atoms are specified."/>
</node>
</node>
</node>
<node CREATED="1256723088164" ID="Freemind_Link_1788012562" MODIFIED="1258017336734" TEXT="Constraints">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723098756" FOLDED="true" ID="Freemind_Link_1142527584" MODIFIED="1258017336733" TEXT="Share atom site">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723117651" ID="Freemind_Link_600492135" MODIFIED="1258017336732" TEXT="EXYZ atom types">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723124387" ID="Freemind_Link_763755898" MODIFIED="1258017336732" TEXT="Makes the selected site shared by atoms of several atom types.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723179026" ID="Freemind_Link_906772420" MODIFIED="1258017336731" TEXT="-EADP adds the equivalent ADPs command for all atoms sharing one site."/>
<node CREATED="1256723182082" ID="Freemind_Link_1321649547" MODIFIED="1258017336731" TEXT="-lo links the occupancy of the atoms sharing the site through a free variable."/>
</node>
</node>
<node CREATED="1256723197985" FOLDED="true" ID="Freemind_Link_12406295" MODIFIED="1258017336731" TEXT="Same ADP">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723207521" ID="Freemind_Link_810714223" MODIFIED="1258017336730" TEXT="EADP atoms">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723215025" ID="Freemind_Link_845807620" MODIFIED="1258017336729" TEXT="Makes the ADP of the specified atoms equivalent.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
<node CREATED="1256723251408" FOLDED="true" ID="Freemind_Link_1557710809" MODIFIED="1258017336729" TEXT="AFIX Constraints">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723259072" ID="Freemind_Link_1320129083" MODIFIED="1258017336728" TEXT="AFIX mn">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723277055" ID="Freemind_Link_103487816" MODIFIED="1258017336727" TEXT=""/>
</node>
</node>
</node>
<node CREATED="1256723093636" ID="Freemind_Link_95661317" MODIFIED="1258017336726" TEXT="Restraints">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723298255" FOLDED="true" ID="Freemind_Link_373542253" MODIFIED="1258017336724" TEXT="Same Distance">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723342094" FOLDED="true" ID="Freemind_Link_1573581060" MODIFIED="1258017336723" TEXT="SADI atoms or bonds">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723358701" ID="Freemind_Link_706126956" MODIFIED="1258017336723" TEXT="For selected bonds or atom pairs SADI makes the distances specified by selecting bonds or atom pairs similar within the esd.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723589672" ID="Freemind_Link_916201888" MODIFIED="1258017336723" TEXT="[esd=0.02]"/>
<node COLOR="#0033ff" CREATED="1256723370669" ID="Freemind_Link_1124223019" MODIFIED="1258017336723" TEXT="If only one atom is selected it is considered to belong to a regular molecule (like PF6) and adds similarity restraints for P-F and F-F distances. For three selected atoms (A1,A2,A3) it creates similarity restraint for A1-A2 and A2-A3 distances."/>
</node>
</node>
<node CREATED="1256723308767" FOLDED="true" ID="Freemind_Link_1361483425" MODIFIED="1258017336722" TEXT="Fixed Distance">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723385613" FOLDED="true" ID="Freemind_Link_1948293049" MODIFIED="1258017336721" TEXT="DFIX d atom pairs">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723403772" ID="Freemind_Link_1174528820" MODIFIED="1258017336721" TEXT="For selected bonds or atom pairs DFIX will generate length fixing restraint with the given esd.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#0033ff" CREATED="1256723416844" ID="Freemind_Link_880174548" MODIFIED="1258017336721" TEXT="If only one atom is selected, all outgoing bonds of that atom will be fixed to the given length with provided esd. For three selected atoms (A1,A2,A3) the A1-A2 and A2-A3 restraints will be generated."/>
<node CREATED="1256723557976" ID="Freemind_Link_1485045895" MODIFIED="1258017336721" TEXT="[esd=0.02]"/>
</node>
</node>
<node CREATED="1256723316398" FOLDED="true" ID="Freemind_Link_1485975797" MODIFIED="1258017336720" TEXT="Flat Group">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723434524" FOLDED="true" ID="Freemind_Link_290913313" MODIFIED="1258017336719" TEXT="FLAT atoms">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723443963" ID="Freemind_Link_45910794" MODIFIED="1258017336719" TEXT="Restrains given fragment to be flat (can be used on the grown structure) within given esd.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723625783" ID="Freemind_Link_226625339" MODIFIED="1258017336719" TEXT=" [esd=0.1]"/>
</node>
</node>
<node CREATED="1256723334062" FOLDED="true" ID="Freemind_Link_1073154384" MODIFIED="1258017336718" TEXT="Chiral Volume">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723466283" FOLDED="true" ID="Freemind_Link_301978901" MODIFIED="1258017336717" TEXT="CHIV atoms [val=0]">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723476170" ID="Freemind_Link_1455654677" MODIFIED="1258017336717" TEXT="Restrains the chiral volume of the provided group to be val within given esd">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723640774" ID="Freemind_Link_904065883" MODIFIED="1258017336717" TEXT=" [esd=0.02]"/>
</node>
</node>
<node CREATED="1256723687781" FOLDED="true" ID="Freemind_Link_863651240" MODIFIED="1258017336716" TEXT="Similar ADPs">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723702117" ID="Freemind_Link_1226061410" MODIFIED="1258017336715" TEXT="SIMU [d=1.7]">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723722020" ID="Freemind_Link_617590029" MODIFIED="1258017336715" TEXT="Restrains the ADPs of all 1,2 and 1,3 pairs within the given atoms to be similar with the given esd.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723739428" ID="Freemind_Link_1581141746" MODIFIED="1258017336715" TEXT="[esd12=0.04] "/>
<node CREATED="1256723746564" ID="Freemind_Link_1916254229" MODIFIED="1258017336715" TEXT="[esd13=0.08]"/>
</node>
</node>
<node CREATED="1256723761091" FOLDED="true" ID="Freemind_Link_57731194" MODIFIED="1258017336714" TEXT="Rigid Bond">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723783619" ID="Freemind_Link_192983882" MODIFIED="1258017336713" TEXT="DELU">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723792787" ID="Freemind_Link_1139087746" MODIFIED="1258017336713" TEXT="&apos;rigid bond&apos; restraint">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723802994" ID="Freemind_Link_1937165344" MODIFIED="1258017336713" TEXT="[esd12=0.01]"/>
<node CREATED="1256723815794" ID="Freemind_Link_202633960" MODIFIED="1258017336713" TEXT="[esd13=0.01]"/>
</node>
</node>
<node CREATED="1256723825474" FOLDED="true" ID="Freemind_Link_876341530" MODIFIED="1258017336712" TEXT="Aprrox Isotropic ADP">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723853473" ID="Freemind_Link_834817342" MODIFIED="1258017336711" TEXT="ISOR">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723864881" ID="Freemind_Link_1529681554" MODIFIED="1258017336711" TEXT="Restrains the ADP of the given atom(s) to be approximately isotropic">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256723877024" ID="Freemind_Link_425187372" MODIFIED="1258017336711" TEXT="[esd=0.1]"/>
<node CREATED="1256723888208" ID="Freemind_Link_1816912545" MODIFIED="1258017336711" TEXT="[esd_terminal=0.2]"/>
</node>
</node>
<node CREATED="1256723905952" FOLDED="true" ID="Freemind_Link_1412477518" MODIFIED="1258017336710" TEXT="Same Groups">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256723931743" ID="Freemind_Link_791762720" MODIFIED="1258017336708" TEXT="SAME n">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
<node CREATED="1256723945439" ID="Freemind_Link_321771083" MODIFIED="1258017336708" TEXT="Splits the selected atoms into the N groups and applies the SAME restraint to them.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#0033ff" CREATED="1256723961742" ID="Freemind_Link_153638920" MODIFIED="1258017336708" TEXT="Olex2 will manage the order of atoms within the in file, however mixing rigid group constraints and the &apos;same&apos; instructions might lead to an erroneous instruction file.">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
</node>
</node>
<node CREATED="1246482419739" ID="Freemind_Link_1055925113" MODIFIED="1258017336707" POSITION="right" TEXT="Refining  Structures">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482432714" ID="Freemind_Link_1799855020" MODIFIED="1258017336705" TEXT="With ShelXL">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792294098" ID="Freemind_Link_837232422" MODIFIED="1258017336704" TEXT="Full Matrix LS">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792304817" ID="Freemind_Link_126632794" MODIFIED="1258017336702" TEXT="CGLS">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1246482437722" ID="Freemind_Link_1100535887" MODIFIED="1258017336700" TEXT="With smtbx">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482445050" ID="Freemind_Link_942852928" MODIFIED="1258017336698" TEXT="LBFGS minimizer">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792281410" ID="Freemind_Link_281479260" MODIFIED="1258017336697" TEXT="Full Matrix LS">
<edge WIDTH="thin"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1253792191748" ID="Freemind_Link_707304456" MODIFIED="1258017336695" TEXT="With Crystals">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1256721756453" ID="Freemind_Link_485086975" MODIFIED="1258017336692" POSITION="right" TEXT="Symmetry Operations">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256721810724" FOLDED="true" ID="Freemind_Link_1629025059" MODIFIED="1258017336691" TEXT="List symmetry operations">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256722150699" ID="Freemind_Link_72366959" MODIFIED="1258017336690" TEXT="lstsymm">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722191738" ID="Freemind_Link_1312694964" MODIFIED="1258017336690" TEXT="Prints symmetry operations and their codes for current structure."/>
</node>
</node>
<node CREATED="1256721837507" FOLDED="true" ID="Freemind_Link_1330907143" MODIFIED="1258017336689" TEXT="Environmnet of an atom">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256722164347" ID="Freemind_Link_571791170" MODIFIED="1258017336688" TEXT="envi">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#338800" CREATED="1256722262473" ID="Freemind_Link_254439975" MODIFIED="1258017336688" TEXT="r [2.7 &#xc5;] A1 or one selected atom [-h] [-q]">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256722287448" ID="Freemind_Link_976487345" MODIFIED="1258017336688" TEXT="Prints a list of those atoms within a sphere of radius r around the specified atom."/>
<node CREATED="1256722296664" ID="Freemind_Link_1842208867" MODIFIED="1258017336688" TEXT="-h: adds hydrogen atoms to the list -q: option adds Q-peaks to the list"/>
</node>
</node>
<node CREATED="1256722396773" FOLDED="true" ID="Freemind_Link_252245511" MODIFIED="1258017336687" TEXT="Generate missing atoms">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256722422357" FOLDED="true" ID="Freemind_Link_100072111" MODIFIED="1258017336686" TEXT="mode grow">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722670830" ID="Freemind_Link_101123068" MODIFIED="1258017336686" TEXT="Generates atoms that are not shown because they are symmetry equivalents">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256722428053" ID="Freemind_Link_899058886" MODIFIED="1258017336686" TEXT="-s also shows the short interaction directions"/>
<node CREATED="1256722452132" ID="Freemind_Link_1194891333" MODIFIED="1258017336685" TEXT="-v [2.0 &#xc5;] shows directions to the molecules within &apos;v&apos; value of the Van der Waals radii of the shown or provided atoms which can be generated by clicking on the direction representations, only unique symmetry operations (producing shortest contacts are displayed)"/>
<node CREATED="1256722461892" ID="Freemind_Link_1853700974" MODIFIED="1258017336685" TEXT="-r shows directions to all atoms as the selected one(s) within 15 &#xc5;; shortcut &apos;Ctrl+G&apos; is used to enter the &apos;mode grow&apos;"/>
</node>
<node COLOR="#669900" CREATED="1256722931528" FOLDED="true" ID="Freemind_Link_1781331906" MODIFIED="1258017336685" TEXT="grow [atoms]">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722937320" ID="Freemind_Link_1507070235" MODIFIED="1258017336685" TEXT="Grows all possible/given atoms; for the polymeric structures or structures requiring several grows Olex2 will continue grow until the comes to already used symmetry element">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256722954631" ID="Freemind_Link_1306387007" MODIFIED="1258017336685" TEXT="-w allows to apply already used symmetry  operations to other fragments of the asymmetric unit"/>
<node COLOR="#0033ff" CREATED="1256723007302" ID="Freemind_Link_1634494681" MODIFIED="1258017336685" TEXT="Example: if the main molecule is grown, but only one solvent molecule is shown, using &apos;grow -w&apos; will produce other solvent molecules using symmetry operators used to grow the main molecule">
<arrowlink DESTINATION="Freemind_Link_1634494681" ENDARROW="Default" ENDINCLINATION="0;0;" ID="Freemind_Arrow_Link_1160532354" STARTARROW="None" STARTINCLINATION="0;0;"/>
</node>
</node>
</node>
<node CREATED="1256722524434" FOLDED="true" ID="Freemind_Link_1521151110" MODIFIED="1258017336684" TEXT="Pack the structure">
<font NAME="SansSerif" SIZE="12"/>
<node COLOR="#669900" CREATED="1256722535794" FOLDED="true" ID="Freemind_Link_1657218526" MODIFIED="1258017336683" TEXT="mode pack">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722541426" ID="Freemind_Link_1753261372" MODIFIED="1258017336683" TEXT="Displays the position of symmetry equivalent asymmetric units as tetrahedra. These asymmetric units can be generated by clicking on the corresponding tetrahedron.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node COLOR="#669900" CREATED="1256722564913" FOLDED="true" ID="Freemind_Link_1624628985" MODIFIED="1258017336683" TEXT="pack -a a -b b -c c">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722570353" ID="Freemind_Link_1153615177" MODIFIED="1258017336683" TEXT="Packs all or specified atoms within given dimensions">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256722588688" ID="Freemind_Link_1698291799" MODIFIED="1258017336683" TEXT="-c option prevents clearing existing model"/>
<node COLOR="#0033ff" CREATED="1256722643871" ID="Freemind_Link_707516004" MODIFIED="1258017336683" TEXT="Example:  pack $O will pack all O atoms with the default of -1.5 to 1.5 cells range."/>
</node>
<node COLOR="#669900" CREATED="1256722868282" FOLDED="true" ID="Freemind_Link_870557613" MODIFIED="1258017336683" TEXT="pack cell">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722875017" ID="Freemind_Link_1044493897" MODIFIED="1258017336683" TEXT="Shows content of the unit cell.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node COLOR="#669900" CREATED="1256722892825" FOLDED="true" ID="Freemind_Link_209744511" MODIFIED="1258017336683" TEXT="pack r">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256722898025" ID="Freemind_Link_17946441" MODIFIED="1258017336683" TEXT="Packs fragments within radius r of the selected atom(s) or the centre of gravity of the asymmetric unit.">
<font BOLD="true" NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
</node>
<node CREATED="1246482848416" ID="Freemind_Link_525766439" MODIFIED="1258017336682" POSITION="left" TEXT="Analyse Raw Data">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482856032" ID="Freemind_Link_1069405328" MODIFIED="1258017336679" TEXT="Space Group Determination">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1258016952317" ID="Freemind_Link_1094141680" MODIFIED="1258017336677" TEXT="Reflection Statistics">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#990000" CREATED="1258016958522" ID="Freemind_Link_1737977173" MODIFIED="1258017336675" TEXT="From Charge Flipping Solution">
<edge COLOR="#ff0033" WIDTH="thin"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1246482870927" ID="Freemind_Link_567691244" MODIFIED="1258017336674" TEXT="Reflection Statistics">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792121094" FOLDED="true" ID="Freemind_Link_47207096" MODIFIED="1258017336672" TEXT="Wilson Plot (Olex2)">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792531532" ID="Freemind_Link_1459892916" MODIFIED="1258017336671" STYLE="fork" TEXT="helps with">
<font ITALIC="true" NAME="SansSerif" SIZE="11"/>
<node CREATED="1253792536668" ID="Freemind_Link_326917991" MODIFIED="1258017336671" STYLE="bubble" TEXT="centrosymmetric vs non.c"/>
<node CREATED="1253792561675" ID="Freemind_Link_1426879109" MODIFIED="1258017336671" STYLE="bubble" TEXT="detection of twinning"/>
</node>
</node>
<node CREATED="1253792438030" FOLDED="true" ID="Freemind_Link_773591381" MODIFIED="1258017336670" TEXT="Wilson Plot (cctbx)">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792531532" ID="Freemind_Link_1597325383" MODIFIED="1258017336669" STYLE="fork" TEXT="helps with">
<font ITALIC="true" NAME="SansSerif" SIZE="11"/>
<node CREATED="1253792536668" ID="Freemind_Link_1433041297" MODIFIED="1258017336669" STYLE="bubble" TEXT="centrosymmetric vs non.c" VSHIFT="-13"/>
<node CREATED="1253792561675" ID="Freemind_Link_885227292" MODIFIED="1258017336669" STYLE="bubble" TEXT="detection of twinning"/>
</node>
<node CREATED="1253792468605" ID="Freemind_Link_180474956" MODIFIED="1258017336669" TEXT="Cumulative">
<node CREATED="1253792531532" ID="Freemind_Link_66042337" MODIFIED="1258017336669" STYLE="fork" TEXT="helps with">
<font ITALIC="true" NAME="SansSerif" SIZE="11"/>
<node CREATED="1253792536668" ID="Freemind_Link_515687520" MODIFIED="1258017336668" STYLE="bubble" TEXT="centrosymmetric vs non.c"/>
<node CREATED="1253792561675" ID="Freemind_Link_386417000" MODIFIED="1258017336668" STYLE="bubble" TEXT="detection of twinning"/>
</node>
</node>
</node>
<node CREATED="1253792468605" FOLDED="true" ID="Freemind_Link_322305670" MODIFIED="1258017336668" TEXT="Cumulative">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792531532" ID="Freemind_Link_1791651389" MODIFIED="1258017336667" TEXT="helps with">
<node CREATED="1253792536668" ID="Freemind_Link_531179912" MODIFIED="1258017336667" TEXT="centrosymmetric vs non.c"/>
<node CREATED="1253792561675" ID="Freemind_Link_518616239" MODIFIED="1258017336666" TEXT="detection of twinning"/>
</node>
</node>
<node CREATED="1253792483677" FOLDED="true" ID="Freemind_Link_1051604002" MODIFIED="1258017336666" TEXT="Systematic Absences">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792637113" ID="Freemind_Link_939270776" MODIFIED="1258017336665" TEXT="helps with">
<node CREATED="1253792646633" ID="Freemind_Link_36609314" MODIFIED="1258017336665" TEXT="spce group determination"/>
</node>
</node>
<node CREATED="1253792496893" ID="Freemind_Link_1790992940" MODIFIED="1258017336664" TEXT="Fobs vs Fcalc">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
<node CREATED="1246482840600" ID="Freemind_Link_184600100" MODIFIED="1258017336662" POSITION="left" TEXT="Analyse Structures">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1246482931542" ID="Freemind_Link_222100363" MODIFIED="1258017336660" TEXT="Electron Density Maps">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1246482936790" ID="Freemind_Link_1646470906" MODIFIED="1258017336659" TEXT="Void Analysis">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1246482919326" ID="Freemind_Link_1226299369" MODIFIED="1258017336657" POSITION="right" TEXT="Automate Tasks">
<arrowlink DESTINATION="Freemind_Link_1226299369" ENDARROW="Default" ENDINCLINATION="0;0;" ID="Freemind_Arrow_Link_1489599013" STARTARROW="None" STARTINCLINATION="0;0;"/>
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792323649" FOLDED="true" ID="Freemind_Link_1852062130" MODIFIED="1258017336655" TEXT="Structure Checking">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792332305" ID="Freemind_Link_207314099" MODIFIED="1258017336654" TEXT="Chirality (Flack)">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792343344" ID="Freemind_Link_194073526" MODIFIED="1258017336654" TEXT="Chirality (Hooft)">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1253792368736" FOLDED="true" ID="Freemind_Link_852789970" MODIFIED="1258017336653" TEXT="Program Setup">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253869357116" ID="Freemind_Link_986218465" MODIFIED="1258017336652" TEXT="Initial Setup">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253869361836" ID="Freemind_Link_1036383578" MODIFIED="1258017336652" TEXT="Automatic Weighting Scheme Updating">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1253875899722" FOLDED="true" ID="Freemind_Link_193222164" MODIFIED="1258017336651" TEXT="Model Building">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253875915817" ID="Freemind_Link_1183091509" MODIFIED="1258017336650" TEXT="VSS">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253875918473" ID="Freemind_Link_1633604094" MODIFIED="1258017336650" TEXT="ATA">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253883452590" ID="Freemind_Link_417410101" MODIFIED="1258017336649" TEXT="FATA">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1253792378032" FOLDED="true" ID="Freemind_Link_1055216656" MODIFIED="1258017336649" TEXT="Multiple Structures">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792397263" ID="Freemind_Link_1785751306" MODIFIED="1258017336648" TEXT="Creation of Tables">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792402335" ID="Freemind_Link_124816793" MODIFIED="1258017336647" TEXT="Creation of Images">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
<node CREATED="1253868057261" ID="Freemind_Link_152149540" MODIFIED="1258017336646" POSITION="right" TEXT="Visual Feedback">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253868068764" FOLDED="true" ID="Freemind_Link_381464472" MODIFIED="1258017336645" TEXT="Refinement Parameters">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253868078460" ID="Freemind_Link_328255405" MODIFIED="1258017336644" TEXT="Weighting Scheme">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253869300942" ID="Freemind_Link_1199018903" MODIFIED="1258017336644" TEXT="R History">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1253883224148" FOLDED="true" ID="Freemind_Link_773121223" MODIFIED="1258017336643" TEXT="Model">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253883228915" ID="Freemind_Link_705457759" MODIFIED="1258017336642" TEXT="Transparent Electron Density Peaks">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253883242499" ID="Freemind_Link_1523703630" MODIFIED="1258017336642" TEXT="Ueq reflected by size of the sphere">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253883335953" ID="Freemind_Link_103183674" MODIFIED="1258017336642" TEXT="N.P.D Atoms distinctive">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253883351488" ID="Freemind_Link_1870075446" MODIFIED="1258017336641" TEXT="Constraints/Restraints Visible">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
<node CREATED="1253869330493" ID="Freemind_Link_1843363258" MODIFIED="1258017336640" POSITION="right" TEXT="Workflow">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253869334541" ID="Freemind_Link_1492395886" MODIFIED="1258017336638" TEXT="History Generation">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253875365639" ID="Freemind_Link_238635034" MODIFIED="1258017336636" TEXT="Choose Reflection File">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1246482828152" ID="Freemind_Link_1713214437" MODIFIED="1258017336635" POSITION="left" TEXT="Make Images">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792046056" ID="Freemind_Link_1940584147" MODIFIED="1258017336633" TEXT="Rendered Images">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792076999" ID="Freemind_Link_1023391697" MODIFIED="1258017336631" TEXT="JPEG">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792080055" ID="Freemind_Link_84280513" MODIFIED="1258017336629" TEXT="BMP">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1253792083335" ID="Freemind_Link_1820704560" MODIFIED="1258017336628" TEXT="PNG">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1253792064280" ID="Freemind_Link_1391908905" MODIFIED="1258017336626" TEXT="ADP Plots">
<edge WIDTH="thin"/>
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1253792089799" ID="Freemind_Link_1147485245" MODIFIED="1258017336623" TEXT="EPS">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node COLOR="#990000" CREATED="1253792100871" ID="Freemind_Link_594780578" MODIFIED="1258017336621" TEXT="PS">
<edge COLOR="#ff0033"/>
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
<node CREATED="1256724088507" FOLDED="true" ID="Freemind_Link_548225843" MODIFIED="1258017336620" TEXT="Image Series">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256724096075" ID="Freemind_Link_1127253988" MODIFIED="1258017336619" TEXT="bmp">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
<node CREATED="1246482911726" ID="Freemind_Link_1987612111" MODIFIED="1258017336618" POSITION="left" TEXT="Create Reports">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1256724065564" ID="Freemind_Link_1112196389" MODIFIED="1258017336617" TEXT="Customise Templates">
<font NAME="SansSerif" SIZE="12"/>
</node>
<node CREATED="1256724070764" ID="Freemind_Link_957116259" MODIFIED="1258017336615" TEXT="Customise Styles">
<font NAME="SansSerif" SIZE="12"/>
</node>
</node>
</node>
</map>
