## SampleSheet Assumptions

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
