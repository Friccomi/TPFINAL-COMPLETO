# ITBA: Final Proyect, Data Cloud Engineer

## Problem to resolve:
   - We need to know whitch airports had days with anormal delays.
   - The data sets has rows with only the airport and no data. Those rows where delete.
   - The column that has delay time with negative numbers, means the flight took off before the departure time, those number were considered
     as zero delay.
   
## Architecture:
   - VPC.
   - Two Availabe zones
   - For each zones: one public subnets, one private subnets, a Nat Gayway, an Elastic IP,a private route table
   - Policys: needed to run all
   - Security groups: ClusterSharedNodeSecurity Group,  ControlPlanelSecurity Group
   - EFS
   - ECR: for the airflow image that will be using EKS
   - EKS: with two nodes, one on demand, the other on spot
   - Auto scaling group for the cluster
   - RDS: a postgres DB to save results. It will contain a table for each year.
   - RDS security group 
   - authorize-security-group-ingress: to have access to DB
   - s3: to save, Cloudformation template, Airflow files, files to be processed and results
   - Git sidecar (https://github.com/Friccomi/ITBA-TPFINAL.git)

## Limits: 
   Sagemaker has e limit, so it was not possible to process all airports for a year. To be able to run the others jobs, the job Search_unnormals
   was mark as succeded, even thought it only processed six airports.
   
## Architecture Diagram:
![Esta es una imagen](https://github.com/Friccomi/TPFINAL-COMPLETO/blob/master/Infra.jpg)

## Others:
   A video showing the infrastructure deploy is included
      

## Install Airflow on EKS.

1- Clone https://github.com/Friccomi/TPFINAL-COMPLETO.git on your linux.

2- You need to have the aws client install. https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

3- Copy and paste credentials (from AWS page) to .aws/credentials on your computer. 

4- As we are using a student account, we don’t have permison to create roles, so we are going to be asiggning permison to the LabRole (role asigne to students)

5- You need know your account number.

6- Replaciong account number: you have to edit this files and replace the account number with your account number.
	Setup1.sh
	CreateDBInstance-policy.json
	EKSDescribeCluster-policy.json
	API-policy.json
	Airflow-EKS.yaml
	Setup2.sh

7- Run : sh setup1.sh

8- Run: sh setup2.sh. If you go to CloudFormation you can see its progress. It takes some time to finish.

9- Go to aws EKS, and create the followings Nodes Groups. (EKS>Clusters>Airflow-on-Kubernetes. -→Configuration -→Compute: Add Node Group)

	name: ng-on-demand
	Node IAN Role: LabRole
	Kubernet Labels: 
	  key: lifecycle
	  value: OnDemand 
	Capacity type: ON-Demand
	  minSize: 2
	  maxSize: 4 
	  desiredCapacity: 2 
        iam: withAddonPolicies: autoScaler: true 
	subnets: select only the public subnets
	   
	name: ng-spot1
	Node IAN Role: LabRole
	Kubernet Labels: 
	   Key: lifecycle
	   value: Ec2Spot 
	Kubernetes taints: 
	   Key: spotInstance
	   value: true 
	   Effect: PreferNoSchedule
	Capacity type: Spot
	instanceTypes: ["m5.large","m4.large","m5a.large"] (select one)
	minSize: 1
	maxSize: 4 
	desiredCapacity: 2 
	subnets: select only the public subnets

10- Wait until the two nodes are Active.

11- Run: sh setup3.sh

12- Now the infra is ready. You can verify by taking a look on AWS.

13- We need to push a customize docker image of airflow for Kubernetes to an ERC, to be used during Airflow instalation. 
	Run: sh setup4.sh

14- cd aws-airflow-helm

15- Edit values.yaml
 	a) Find: airflow--> container image -→respository and replace it with the new ERC repositorie
	b) Find: "s3://friccomi/Airflow/logs/" and replace name bucket ‘friccomi’ with yout bucket name.
	b) Find: connections: 
    	  - id: s3_conn
            type: aws
            description: my AWS 	connection
	    extra: |-
	    { "aws_access_key_id": ASIAWVVOBTBDG75GF4NB,
	      "aws_secret_access_key": Wgv/iTQVBYLqI9M043XGojl8Va6Jd17FLprJD9FK,
	      "region_name":us-east-1" 
            }
	  Replace:
             aws_access_key_id, with your own aws_access_key_id
             aws_secret_access_key  with your own  aws_secret_access_key

16- Edit efs-pvc.yml. Replace server: fs-03d62e30c69113974.efs.us-east-1.amazonaws.com   with 	DNS name of your new EFS.

17- We have to modifiy in git sidecar the DB-HOST in .env and de s3 connection in convert_train/s3_conn.py, replace aws_access_key_id, aws_secret_access_key,aws_session_tokenwith the ones of your account. 

18- cd ..

19- Run: sh setup5.sh. It takes a while, you can see its progress at AWS EKS → Workloads → default

20- Run: aws s3 sync raw/ s3://friccomi/tp/ 

21- Run: 
        export POD_NAME=$(kubectl get pods --namespace default -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")
	kubectl port-forward --namespace default $POD_NAME 8080:8080

22- Copy and paste de url showed, to your browser (eg:127.0.0.1:8080)
      user: admin
      password: admin	






