# ica_to_cgw
An orchestration approach to monitor analyses from Illumina Connected Analytics (ICA) and ingest the analyses into Velsera's GCW


## approach

### helper functions

- ica_analysis_monitor.py
	- API calls to monitor a given analyses
- ica_analysis_launch.py
	- API calls to identify a previously run analysis and craft an API template
- samplesheet_utils.py
	- functions to read and parse v2 samplesheet and craft CGW manifest file

### orchestrators

These are custom script(s) based on an end-user's use-case

#### fcs.ICA_to_CGW.orchestrator.py

- 1) monitor TSO500 v2.5.2 analysis
- 2) if analysis is running, queued, or in progress
	- Analysis ids are printed out by default ```analyses_monitored_file.txt``` 
	- It is a list of analysis ids
	- This can filepath can be customized
	- No additional action is taken by orchestrator currently
- 3) if analysis is completed
	- check if analysis is in a triggered analysis table ```analyses_launched_table.txt```
	- This can filepath can be customized
	- Format is ```analysis_id_monitored,analysis_id_triggered,run_id```
		- ```analysis_id_monitored``` = analysis_id of TSO500 v2.5.2 analysis
		- ```analysis_id_triggered``` = analysis_id of CGW upload
		- ```run_id``` = Sequencing Run ID and parent folder name 
			- the ```run_id``` will also determine the prefix ```(i.e. f"{folder_basename}.sample_manifest.csv")``` of the CGW manifest file
	- if analysis is not in the triggered analysis table
		- download v2 samplesheet of belonging to the TSO500 v2.5.2 analysis results 
		- parse samplesheet and create CGW manifest file
		- rename TSO500 v2.5.2 analysis results (i.e. create folder based off of the ```run_id```)
			- upload manifest file
			- copy data from TSO500 v2.5.2 analysis results 
				- data copy is monitored and reported out to screen
		- craft API template for CGW upload
			- launch CGW upload pipeline run
			- record analysis id for this run = ```analysis_id_triggered```
		- update triggered analysis table ```analyses_launched_table.txt```
			- with all the ```analysis_id_monitored```,```analysis_id_triggered```, and ```run_id``` we've collected

#### fcs.ICA_to_CGW.orchestrator.py [TODO]
- add bash_wrapper to run orchestrator script every 5/10 minutes
- give instructions for setting up Cron job
- build and push official docker image based-off of this Dockerfile

#### fcs.ICA_to_CGW.orchestrator.py command line examples
# TEST1 : analysis you monitor and trigger will be in the same ICA project
bash```
python fcs.ICA_to_CGW.orchestrator.py --api_key_file /opt/api_key.txt --source_project_name ken_debug --pipeline_name_to_monitor 'DRAGEN Somatic Enrichment 4-3-6 Clone' --pipeline_name_to_trigger 'DRAGEN_REPORTS_STANDALONE_CUSTOM'
 
 or

python fcs.ICA_to_CGW.orchestrator.py --api_key_file /opt/api_key.txt --source_project_name ken_debug --pipeline_name_to_monitor 'DRAGEN Somatic Enrichment 4-3-6 Clone' --pipeline_name_to_trigger 'DRAGEN_REPORTS_STANDALONE_CUSTOM' --api_template_file /Users/keng/ica_to_cgw/test.json

# TEST2 : analysis you monitor and trigger will be in the different ICA projects
python fcs.ICA_to_CGW.orchestrator.py --api_key_file /opt/api_key.txt --source_project_name ken_debug --destination_project Ken_demos  --pipeline_name_to_monitor 'DRAGEN Somatic Enrichment 4-3-6 Clone' --pipeline_name_to_trigger 'DRAGEN_REPORTS_STANDALONE_CUSTOM_v2'
```
