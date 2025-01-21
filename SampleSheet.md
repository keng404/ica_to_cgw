## v2 SampleSheet Assumptions

- It is a V2 samplesheet that follows the conventions listed [here](https://support-docs.illumina.com/SW/DRAGEN_TSO500_v2.5/Content/SW/Apps/SampleSheetReqs_fDRAG_mTSO500v2.htm)
- Additional links of interest are as follows. Note that these are specific instructions for configuring your v2 samplesheet for TSO500 analyses and note other analyses you may be interested in running.
Please refer to help documentation for examples and guidance on v2 samplesheets for those applications:
  - [SampleSheet Introduction](https://help.tso500software.illumina.com/run-set-up/sample-sheet-introduction)
  - [SampleSheet Requirements](https://help.tso500software.illumina.com/run-set-up/sample-sheet-requirements)
  - [SampleSheet Generation in BaseSpace](https://help.tso500software.illumina.com/run-set-up/sample-sheet-creation-in-basespace-run-planning-tool)
  - [SampleSheet Introduction Templates](https://help.tso500software.illumina.com/run-set-up/sample-sheet-templates)

## CGW manifest assumptions

- assume ```LANE``` is always ```'1'```
- ```SPECIMEN LABEL``` is  ```SPECIMEN_LABEL```
- ```RUN ID``` is folder name of the analysis
- ```BARCODE``` is ```f"{Index}-{Index2}```
- assume ```SEQUENCING TYPE``` is ```'PAIRED END'```
- ```ACCESSION NUMBER``` is ```ACCESSION_NUMBER```
- ```SAMPLE TYPE``` is ```Sample_Type```
- ```SAMPLE ID``` is ```Sample_ID```
- ```PAIR ID``` is ```PAIR ID```  


### SampleSheet v2 TSO Data header assumption

- ```ACCESSION_NUMBER``` and ```SPECIMEN_LABEL``` fields are present in the TSO Data section of the v2 samplesheet
- If these headers are not found, the script will look for headers that match the following:
  - ```ACCESSION_NUMBER```  will match to ```ACCESSION NUMBER```, ```ACCESSION_NUMBER```, ```ACCESSION-NUMBER```
  - ```SPECIMEN_LABEL``` will match to ```SPECIMEN LABEL```, ```SPECIMEN_LABEL```, ```SPECIMEN-LABEL```
- Additionally the parser will match ignoring lower or upper casing of the headers

## The following TSO Data headers are examples of valid headers
- ```Sample_ID,Sample_Type,Pair_ID,Sample_Feature,Index_ID,Index,Index2,ACCESSION_NUMBER,SPECIMEN_LABEL```
- ```Sample_ID,Sample_Type,Pair_ID,Sample_Feature,Index_ID,Index,Index2,ACCESSION_NUMBER,```***SPECIMEN LABEL***
- ```Sample_ID,Sample_Type,Pair_ID,Sample_Feature,Index_ID,Index,Index2,```***ACCESSION NUMBER***```,SPECIMEN_LABEL```
- ```Sample_ID,Sample_Type,Pair_ID,Sample_Feature,Index_ID,Index,Index2,```***ACCESSION-NUMBER***```,SPECIMEN_LABEL```
- ```Sample_ID,Sample_Type,Pair_ID,Sample_Feature,Index_ID,Index,Index2,ACCESSION_NUMBER,```***SPECIMEN-LABEL***
- ```Sample_ID,Sample_Type,Pair_ID,Sample_Feature,Index_ID,Index,Index2,ACCESSION_NUMBER,```***SPECIMEN_LABEl***