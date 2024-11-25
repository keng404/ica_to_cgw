#!/usr/bin/bash

usage()
{
        echo "fcs_orchestration_wrapper.sh"
        echo "Ken Eng 25-Nov-2024"
        echo
        echo "Runs fcs.ICA_to_CGW.orchestrator.py"
        echo "An orchestration approach to monitor analyses from Illumina Connected Analytics (ICA)"
        echo "and ingest the analyses into Velsera's Clinical Genomics Workspace (CGW)"
        echo
        echo "Usage: $0 [-a api_key_file] [-s source_project_name] [-m pipeline_name_to_monitor] \ "
        echo "                           [-t pipeline_name_to_trigger]  \ "
        echo "                           [OPTIONAL] [-d destination_project_name] [-f api_template_file] \ "
        echo
        echo "  [-a api_key_file]            	- path to text file containing API Key for ICA"
        echo "  [-s source_project_name]  		- Name of the ICA project where your TSO500 analysis resides"
        echo "  [-d destination_project_name]   - [OPTIONAL] Name of the ICA project where your CGW upload pipeline resides "
        echo " --- only need to specify this if the projects are different"
        echo "  [-m pipeline_name_to_monitor]   - Name of the ICA pipeline you want to monitor for completed analysis"
        echo "  [-t pipeline_name_to_trigger]   - Name of the ICA pipeline you want to trigger downstream"
        echo "  [-f api_template_file] 			- [OPTIONAL] path to a JSON file containing ICA analysis template for requesting a pipeline run. "
        echo "Template should be generated by this process. [https://github.com/keng404/bssh_parallel_transfer/blob/master/requeue.md#ica-api-template-generation] "
        echo "By default the orchestrator script will identify the last successful pipeline run for the 'pipeline_name_to_trigger' and craft an API template "
        echo "within the script for use later."
        echo "  [-h help]                 		- Display this page"
        exit
}

#--api_key_file : path to text file containing API Key for ICA
#--source_project_name : Name of the ICA project where your TSO500 analysis resides
#--destination_project_name : [OPTIONAL] Name of the ICA project where your CGW upload pipeline resides --- only need to specify this if the projects are different
#--pipeline_name_to_monitor : Name of the ICA pipeline you want to monitor for completed analysis
#--pipeline_name_to_trigger : Name of the ICA pipeline you want to trigger downstream
#--api_template_file : [OPTIONAL] path to a JSON file containing ICA analysis template for requesting a pipeline run. Template should be generated by this process [https://github.com/keng404/bssh_parallel_transfer/blob/master/requeue.md#ica-api-template-generation]. By default the orchestrator script will identify the last successful pipeline run for the ```--pipeline_name_to_trigger`` and craft an API template within the script for use later.
api_key_file=""
source_project_name=""
destination_project_name=""
pipeline_name_to_monitor=""
pipeline_name_to_trigger=""
api_template_file=""
# Seconds between checks
update_delay_sec=600 # Candence between each trigger of the fcs.ICA_to_CGW.orchestrator.py script
while getopts ":a:s:d:m:t:f:h" Option
        do
        case $Option in
                a ) api_key_file="$OPTARG" ;;
                s ) source_project_name="$OPTARG" ;;
                d ) destination_project_name="$OPTARG" ;;
                m ) pipeline_name_to_monitor="$OPTARG" ;;
                t ) pipeline_name_to_trigger="$OPTARG" ;;
                f ) api_template_file="$OPTARG" ;;
                h ) usage ;;
                * ) echo "Unrecognized argument. Use '-h' for usage information."; exit 255 ;;
        esac
done
shift $(($OPTIND - 1))


if [[ "$api_key_file" == "" || "$pipeline_name_to_monitor" == "" || "$pipeline_name_to_trigger" == ""   || "$source_project_name" == "" ]]
then
        usage
fi

if [ ! -r "$api_key_file" ]
then
        echo "Error: can't open API KEY FILE ($1)." >&2
        exit 1
fi

if [ ! -z "$api_template_file" ]
	if [ ! -r "$api_template_file" ]
	then
        echo "Error: can't open API TEMPLATE FILE ($1)." >&2
        exit 1
    fi
fi



# Loop until control-C'ed out
while : ; do
	clear
	if [[ "$destination_project_name" == "" ]] ;; then
		if [[ "$api_template_file" != "" ]] ;; then
			python fcs.ICA_to_CGW.orchestrator.py --api_key_file "$api_key_file" --source_project_name "$source_project_name" --pipeline_name_to_monitor "$pipeline_name_to_monitor" --pipeline_name_to_trigger "$pipeline_name_to_trigger" 
		else
			python fcs.ICA_to_CGW.orchestrator.py --api_key_file "$api_key_file" --source_project_name "$source_project_name" --pipeline_name_to_monitor "$pipeline_name_to_monitor" --pipeline_name_to_trigger "$pipeline_name_to_trigger"  --api_template_file "$api_template_file"
		fi
	else
		if [[ "$api_template_file" != "" ]] ;; then
			python fcs.ICA_to_CGW.orchestrator.py --api_key_file "$api_key_file" --source_project_name "$source_project_name" --destination_project_name "$destination_project_name" --pipeline_name_to_monitor "$pipeline_name_to_monitor" --pipeline_name_to_trigger "$pipeline_name_to_trigger" 
		else
			python fcs.ICA_to_CGW.orchestrator.py --api_key_file "$api_key_file" --source_project_name "$source_project_name" --destination_project_name "$destination_project_name" --pipeline_name_to_monitor "$pipeline_name_to_monitor" --pipeline_name_to_trigger "$pipeline_name_to_trigger"  --api_template_file "$api_template_file"
		fi
	fi
sleep $update_delay_sec
done  
