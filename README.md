# ica_to_cgw
An orchestration approach to monitor analyses from Illumina Connected Analytics (ICA) and ingest the analyses into Velsera's GCW

## approach

## helper functions

- [ica_analysis_monitor.py](https://github.com/keng404/ica_to_cgw/blob/main/ica_analysis_monitor.py)
	- API calls and functions to monitor a given analyses
- [ica_analysis_launch.py](https://github.com/keng404/ica_to_cgw/blob/main/ica_analysis_launch.py)
	- API calls and functions to identify a previously run analysis and craft an API template
- [samplesheet_utils.py](https://github.com/keng404/ica_to_cgw/blob/main/samplesheet_utils.py)
	- Functions to read and parse v2 samplesheet and craft CGW manifest file
- [ica_data_transfer.py](https://github.com/keng404/ica_to_cgw/blob/main/ica_data_transfer.py)
	- API calls and functions to aid in download and upload to ICA using BOTO3 (i.e. AWS s3)
## orchestrators

These are custom script(s) based on an end-user's use-case

## [fcs.ICA_to_CGW.orchestrator.py](https://github.com/keng404/ica_to_cgw/blob/main/fcs.ICA_to_CGW.orchestrator.py)

1) Monitor TSO500 v2.5.2 analysis
2) If analysis is running, queued, or in progress
	- analysis ids are printed out by default ```analyses_monitored_file.txt``` 
	- It is a list of analysis ids
	- This can filepath can be customized
	- No additional action is taken by orchestrator currently
3) If analysis is completed
	- Check if analysis is in a triggered analysis table ```analyses_launched_table.txt```
	- This can filepath can be customized
	- Format is ```analysis_id_monitored,analysis_id_triggered,run_id```
		- ```analysis_id_monitored``` = analysis_id of TSO500 v2.5.2 analysis
		- ```analysis_id_triggered``` = analysis_id of CGW upload
		- ```run_id``` = Sequencing Run ID and/or parent folder name 
			- The ```run_id``` will also determine the prefix ```(i.e. "{run_id}.sample_manifest.csv")``` of the CGW manifest file
   			- Script will create a 'simplified' ```run_id``` if the original analysis root folder name is ```> 150 characters```
      				- Script will try to identify the ```RunName``` from the ```SampleSheet.csv``` or ```input.json``` associated with the TSO500 analysis
        			- If this ```RunName``` is identified, then the new ```run_id``` will be "{RunName}_DRAGEN-R2-{EPOCH_TIME}"
        			- ```EPOCH_TIME``` is the UNIX time in seconds	 		
	- If analysis is not in the triggered analysis table
		- Download v2 samplesheet of belonging to the TSO500 v2.5.2 analysis results
  		- If your TSO500 analysis is in a BaseSpace-managed project in ICA
		    - The analysis is linked into a different project where your CGW upload pipeline exists
		    - Data link is monitored and reported out to screen
		    - Once completed, we proceed with next steps
		- Parse samplesheet and create CGW manifest file
		- Rename TSO500 v2.5.2 analysis results if the original analysis root folder name is ```> 150 characters```
			- Create folder based off of the ```run_id```. See above for more details
     			- Copy data from TSO500 v2.5.2 analysis results 
				- Data copy is monitored and reported out to screen
   				- Once completed, we proceed with next steps
		- Upload CGW manifest file to ICA
		- Craft API template for CGW upload pipeline
			- Launch CGW upload pipeline run
			- Record analysis id for this run = ```analysis_id_triggered```
		- Update triggered analysis table ```analyses_launched_table.txt```
			- With all the ```analysis_id_monitored```,```analysis_id_triggered```, and ```run_id``` we've collected

## fcs.ICA_to_CGW.orchestrator.py TODO list

- Add in code to pass the CGW manifest file to the CGW upload pipeline in ICA
- Add bash_wrapper to run orchestrator script every 5/10 minutes
- Give instructions for setting up Cron job
- Build and push official docker image based-off of this [Dockerfile](https://github.com/keng404/ica_to_cgw/blob/main/Dockerfile)
- [OPTIONAL] Add data management functionality to remove linked data or duplicate data?? 

## fcs.ICA_to_CGW.orchestrator.py FAQs

1) How do I generate an API key?
See this [ICA help page](https://help.ica.illumina.com/get-started/gs-getstarted#api-keys). You can either save during key generation or copy+paste to any text file of your choosing.
1) What if the pipeline input to ```CGW upload``` changes?
You will need to provide the ```--api_template_file``` to the orchestrator
Visit the script [here](https://github.com/keng404/bssh_parallel_transfer/blob/master/requeue.md#ica-api-template-generation)
or 
create an API template via the [ICA requeue template app](https://keneng87.pyscriptapps.com/ica-analysis-requeue/latest/)
You may also need to modify how the orchestrator launches your CGW upload via [this section](https://github.com/keng404/ica_to_cgw/blob/main/fcs.ICA_to_CGW.orchestrator.py#L435-L441) 
2) What if my CGW manifest file changes format?
Make updates to [samplesheet_utils.py](https://github.com/keng404/ica_to_cgw/blob/main/samplesheet_utils.py#L66-L117) 
in the appropriate sections
3) What happens if analysis fails (either TSO500 or CGW upload)?
Only the happy-path has been implemented. So the orchestrator has no retry logic.
You can use  the script [here](https://github.com/keng404/bssh_parallel_transfer/blob/master/requeue.md) or the [ICA requeue template app](https://keneng87.pyscriptapps.com/ica-analysis-requeue/latest/) if you don't have a template handy. Presuming you have the ICA CLI installed you should be able to copy+paste these templates.

## fcs.ICA_to_CGW.orchestrator.py command line examples

```bash
# TEST1 : analysis you monitor and trigger will be in the same ICA project
python fcs.ICA_to_CGW.orchestrator.py --api_key_file /opt/api_key.txt --source_project_name ken_debug --pipeline_name_to_monitor 'DRAGEN Somatic Enrichment 4-3-6 Clone' --pipeline_name_to_trigger 'DRAGEN_REPORTS_STANDALONE_CUSTOM'
 
 or

python fcs.ICA_to_CGW.orchestrator.py --api_key_file /opt/api_key.txt --source_project_name ken_debug --pipeline_name_to_monitor 'DRAGEN Somatic Enrichment 4-3-6 Clone' --pipeline_name_to_trigger 'DRAGEN_REPORTS_STANDALONE_CUSTOM' --api_template_file /Users/keng/ica_to_cgw/test.json

# TEST2 : analysis you monitor and trigger will be in the different ICA projects
python fcs.ICA_to_CGW.orchestrator.py --api_key_file /opt/api_key.txt --source_project_name ken_debug --destination_project_name Ken_demos  --pipeline_name_to_monitor 'DRAGEN Somatic Enrichment 4-3-6 Clone' --pipeline_name_to_trigger 'DRAGEN_REPORTS_STANDALONE_CUSTOM_v2'
```

## fcs.ICA_to_CGW.orchestrator.py command line options

- ```--api_key_file``` : path to text file containing API Key for ICA
- ```--source_project_name``` : Name of the ICA project where your TSO500 analysis resides
- ```--destination_project_name``` : [OPTIONAL] Name of the ICA project where your CGW upload pipeline resides --- only need to specify this if the projects are different
- ```--pipeline_name_to_monitor``` : Name of the ICA pipeline you want to monitor for completed analysis
- ```--pipeline_name_to_trigger``` : Name of the ICA pipeline you want to trigger downstream
- ```--api_template_file``` : [OPTIONAL] path to a JSON file containing ICA analysis template for requesting a pipeline run. Template should be generated by [this process](https://github.com/keng404/bssh_parallel_transfer/blob/master/requeue.md#ica-api-template-generation). By default the orchestrator script will identify the last successful pipeline run for the ```--pipeline_name_to_trigger`` and craft an API template within the script for use later.
