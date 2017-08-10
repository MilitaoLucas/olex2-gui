# Report
Here is a collection of tools that can help you to form a report about your structure.

# Collection 
Here you can enter any information you might have concerning the Data Collection of your structure.

**Information entered in these boxes will take precedence over information provided in files**. If you edit the CIF information using the 'Edit Cif Info' button above, then that will take precedence over what you entered here (and the new values will be displayed in these boxes). 

# Crystal 
Here you can enter any information you might have concerning the Crystal itself. 

**Information  entered in these boxes will take precedence over information provided in files**. If you edit the CIF information using the 'Edit Cif Info' button above, then that will take precedence over what you entered here (and the new values will be displayed in these boxes). 

# Diffraction 
Here you can enter any information you might have concerning the Diffraction Experiment. 

**Information entered in these boxes will take precedence over information provided in files**. If you edit the CIF information using the 'Edit Cif Info' button above, then that will take precedence over what you entered here (and the new values will be displayed in these boxes). 

# Absorption Correction 
XXX

# Publication 
Here you can enter any information you might have concerning the Publication details of your structure. 

**Information entered in these boxes will take precedence over information provided in files**. If you edit the CIF information using the 'Edit Cif Info' button above, then that will take precedence over what you entered here (and the new values will be displayed in these boxes). 

# Citations 
XXX

# Reference 
Here you can enter any information about publication of your structure. 

**Information  entered in these boxes will take precedence over information provided in files**. If you edit the CIF information using the 'Edit Cif Info' button above, then that will take precedence over what you entered here (and the new values will be displayed in these boxes). 

# Source Files 
XXX

# CIF Part 1 
This section deals with your CIF file. The CIF file contains everything that is known about your structure in a format that has been defined by the IUCr. Getting a complete and correct cif file is vital for the successful publication of your structures in any peer reviewed journals.

Ideally, the creation of the CIF file should be completely automatic and you won't have to worry about it. But just in case, we povide a number of tools here to help you with your CIF files.

## Edit CIF Info 
Pressing this button will bring up a text editor, in which all the information that is known about your structure is shown. You can modify the contents of this file and even add and remove items. Your edits will take precedence over any previous values. 

## Merge CIF 
This will open the current CIF of your structure - a file in which the 'meta-data' has been merged with the CIF that originated from your last refinement. 

## Include/Exclude HKL and RES in your CIF 
Here you can determine whether you want to include the HKL/RES files in your final CIF or not. Please note: If you choose 'ignore', then nothing will be done to your CIF - the HKL/RES part will be included **exactly** as it was returned by the refinement program. ShelXL-2013 includes the HKL and RES information as plain text by default. If you select 'exclude', no HKL and res information will be included. If you choose 'include', the RES and HKL information will be included in the official IUCr/CIF definition format: as a loop.

# CIF Part 2 
The IUCr offer a free checking service for your CIF files.

## The CheckCif report 
This will help you to identify potential problems with your structure. Click the 'CheckCif Report' button to send your CIF file to the IUCr server and obtain your report in either html or pdf format. For a full report, you will also have to send your 'structure factors', which are contained in the fcf file. Tick the box if you want a full report.

## Update Meta Info (Can't actually find this!!)  
This tick-box is included here only for the very rare case where you might experience problems with the merging of the CIF created by the refinement program and the information contained within Olex2. If you ever feel the need to untick this box, please make sure to let us know what the problem was and we will try and fix it for everyone. Thanks!

## CCDC Number 
The first step in the submission to the CSD is to obtain a CCDC number. Pressing this button will do that for you: it will send your CIF file and your structure factor file (optional) to the CCDC. After a few days of processing in Cambridge, you will obtain an e-mail containing your CCDC submission number. A number will only be requested if **all** the required data is provided - so make sure you fill in all the forms as much as you can! 


# CIF Part 3 
One of the really strong points of Olex2 is that it will keep your CIF information synchronised throughout the entire solution and refinement process. This is quite a tricky thing to do, but if it all works the way it should, you will never need to edit a CIF by hand again. 

## Merge CIF  
If this box is ticked, the files that are listed in this line will all be merged with your CIF information. 'metacif' is the builtin-file where Olex2 collects all the information about your structure it can. You can edit this file using the 'Edit Cif Info' button above, and **your edits will take precedence over all other sources of information**. If something goes dreadfully wrong here, you may choose to untick this box. However, we really don't recommend this and if you feel that you need to do this, please contact us and we will try and find a solution to your problem. Thank you! 
