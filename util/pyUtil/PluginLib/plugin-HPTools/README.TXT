Database and Bulk Running of Files

WARNING: This tool has been developed by HP for my own use. I have attempted to make it more user friendly, but things are clearly not as useable as they might be. Please use at your own peril.

The Database tools and GUI are part of plugin-HPTools and requires plugin-SQLAlchemy; both plugins need to be registered from BaseDir()/plugins.xld.
The GUI needs to be linked from an index file, e.g  (BaseDir()/etc/gui/blocks/index-info.htm.

<!-- #include database BaseDir()/util/pyUtil/PluginLib/plugin-HPTools/db_graphs.htm;gui\blocks\tool-off.htm;image=Database;onclick=;1; -->

1) Before running anything, you need to establish a database by scaning a directory that contains structural data in the form of subfolders containing an ins and a hkl file. To do this, type some some prefix into the first box (e.g. "G:/HP/DS"), then the target directory in the second (e.g. "Data/") (The primary key used for the database will be the path of the structure _without_ the prefix). Not all structures will load correctly and these structures will be marked in the form of text files written in DataDir():

    exclude_FailedReap.txt
    exclude_NoReflectionFile.txt
    exclude_FailedR1.txt
    
Paths contained in these files will not be considered again.

To establish the database, enter the path information, select 'scan' for the action and select '--' for the database, which will create a new database with the name str(int(time.time())).sqlite. If an existing database is chosen, only files not already contained in the db will be scanned. The scan run will load each structure in turn, and revert it to its original state (if the structure has been 'seen' by Olex2 before).

2) Once the database is established, I recomend to rename this to something more meaningful.

The sets of structures to be used in bulk runs can be filtered using two sets of filters. The new database contains two filled tables:

"Structure":
      '--'
      'volume'
      'formula'
      'path'
      'atom_count'
      'z_prime'

"Reflections":
      '--'
      'r_int'
      'completeness'

There are also two unfilled tables:

"ac2":
      '--'
      'r1_original'
      'r1_ac2'
      'ata_original'
      'ata_ac2'
      'time_ac2'
      'solution_ac2'

"oda":
      '--'
      'r1_original'
      'r1_oda'
      'ata_original'
      'ata_oda'
      'time_oda'
      'solution_oda'

Other tables can be added in /plugin-SQLAlchemy/SQLAlchemy.py

For filtering, the following operators are available
--    Do not use this filter
<     Smaller than
=     Equal
>     Larger Than
!=    Not Equal
cont  Contains


Runs will be carried out on the filtered list; if the tickbox 'run new only' is ticked, files that have been run before will not be re-run. When it is not ticked, files will be run but the current entry in the db will not be modified. The GUI display comes from the file DataDir()/batch_list.htm, it might make sense to save that file under a different name if it contains information for later.

