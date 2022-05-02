printf "Para correr este script debe tener creado el cluster y los nodos, uno en spot el otro on-demand \n"
printf " ASEGURARSE QUE LABROLE TENGA los SIGUIENTES PERMISOS \n"
printf " iam::aws:policy/AmazonEC2ContainerRegistryReadOnly \n"
printf " iam::aws:policy/AmazonEKSWorkerNodePolicy' \n"
printf " iam::aws:policy/AmazonEKS_CNI_Policy' \n"
printf " iam::aws:policy/AmazonSSMManagedInstanceCore' \n"
printf "\n"
printf "Cuando pregunte subredes, asignar solo las publicas \n"
printf "\n"
printf "\n"
printf "- name: ng-on-demand \n"
printf "	  Node IAN Role: LabRole \n"
printf "        Kubernet Labels: \n"
printf "		key: lifecycle \n"
printf "               value: OnDemand \n"
printf "        Capacity type: ON-Demand \n"
printf "	 MinSize: 2 \n"
printf "	 MaxSize: 4  \n"
printf "	 DesiredCapacity: 2 \n"
printf "        iam: withAddonPolicies: autoScaler: true \n"
printf "	 subnets: select only the public subnets \n"
printf "- name: ng-spot1 \n"
printf "        Node IAN Role: LabRole \n"
printf "        Kubernet Labels: \n"
printf "		key: lifecycle \n"
printf "               value: Ec2Spot  \n"
printf "        Kubernetes taints: \n"
printf "		key: spotInstance \n"
printf "               value: true  \n"
printf "		Effect: PreferNoSchedule \n"
printf "        Capacity type: Spot \n"
printf "	 InstanceTypes: ["m5.large","m4.large","m5a.large"] (select one) \n"
printf "	 MinSize: 1 \n"
printf "	 MaxSize: 4 \n"
printf "	 DesiredCapacity: 2 \n"
printf "	 Subnets: select only the public subnets \n"
printf "\n"
wait

printf "Seteando variables AOK_AWS_REGION AOK_ACCOUNT_ID AOK_EKS_CLUSTER_NAME...\n"
AOK_AWS_REGION=us-east-1 #<-- Change this to match your region
AOK_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
AOK_EKS_CLUSTER_NAME=Airflow-on-Kubernetes

echo $AOK_AWS_REGION
echo $AOK_ACCOUNT_ID
echo $AOK_EKS_CLUSTER_NAME

kubectl get nodes
kubectl get nodes --label-columns=lifecycle --selector=lifecycle=Ec2Spot
  

printf "Getting the VPC of the EKS cluster and its CIDR block...\n"
export AOK_VPC_ID=$(aws eks describe-cluster --name $AOK_EKS_CLUSTER_NAME \
  --region $AOK_AWS_REGION \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)
  
printf "\n"      		
printf "Creating an IAM policy document for cluster autoscaler...\n"
cat << EOF > cluster-autoscaler-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeTags",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "ec2:DescribeLaunchTemplateVersions"
            ],
            "Resource": "*"
        }
    ]
}
EOF

#export AOK_AmazonEKSClusterAutoscalerPolicy=$(aws iam create-policy \
#    --policy-name EKSClusterAutoscPolicy \
#    --policy-document file://cluster-autoscaler-policy.json)
    
aws iam put-role-policy --role-name LabRole --policy-name EKSClusterAutoscPolicy \
--policy-document file://cluster-autoscaler-policy.json
    
    
    
    
#printf "Si no funciona, generarlo a mano"       
    
 # printf "Creating service account for cluster autoscaler...\n"
 # (NO TENGO PERMISOS PARA ESTE PUNTO)
 # eksctl create iamserviceaccount \
 #	 --cluster=$AOK_EKS_CLUSTER_NAME \
 #	 --namespace=kube-system \
 #	 --name=cluster-autoscaler \
 #	 --attach-policy-arn=arn:aws:iam::$AOK_ACCOUNT_ID:policy/AmazonEKSClusterAutoscalerPolicy \
 #	 --override-existing-serviceaccounts \
 #	 --region $AOK_AWS_REGION \
 #	 --approve  
 
  # cd airflow-for-amazon-eks-blog/scripts
   	 
   printf "Adding cluster autoscaler helm repo....\n"
   helm repo add autoscaler https://kubernetes.github.io/autoscaler
   helm repo update

   printf "Installing cluster autoscaler....\n"
    helm install cluster-autoscaler \
      autoscaler/cluster-autoscaler \
     --namespace kube-system \
     --set 'autoDiscovery.clusterName'=$AOK_EKS_CLUSTER_NAME \
     --set awsRegion=$AOK_AWS_REGION \
     --set cloud-provider=aws \
     --set extraArgs.balance-similar-node-groups=true \
     --set extraArgs.skip-nodes-with-system-pods=true \
     --set rbac.serviceAccount.create=false \
     --set rbac.serviceAccount.name=cluster-autoscaler

  printf "Deploy the EFS CSI driver and create EFS filesystem and Access Point.\n"
  printf "Deploying EFS Driver...\n"
 
 
 
  helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver/
  helm repo update
  helm upgrade --install aws-efs-csi-driver \
    aws-efs-csi-driver/aws-efs-csi-driver \
    --namespace kube-system
   
printf "Getting the VPC of the EKS cluster and its CIDR block...\n"
export AOK_VPC_ID=$(aws eks describe-cluster --name $AOK_EKS_CLUSTER_NAME \
  --region $AOK_AWS_REGION \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)
export AOK_CIDR_BLOCK=$(aws ec2 describe-vpcs --vpc-ids $AOK_VPC_ID \
  --query "Vpcs[].CidrBlock" \
  --region $AOK_AWS_REGION \
  --output text)

printf "Creating a security group for EFS, and allow inbound NFS traffic (port 2049):...\n"
export AOK_EFS_SG_ID=$(aws ec2 create-security-group \
  --region $AOK_AWS_REGION \
  --description Airflow-on-EKS \
  --group-name Airflow-on-EKS \
  --vpc-id $AOK_VPC_ID \
  --query 'GroupId' \
  --output text)
  
aws ec2 authorize-security-group-ingress \
  --group-id $AOK_EFS_SG_ID \
  --protocol tcp \
  --port 2049 \
  --cidr $AOK_CIDR_BLOCK \
  --region $AOK_AWS_REGION

printf "Creating an EFS file system...\n"
export AOK_EFS_FS_ID=$(aws efs create-file-system \
  --creation-token Airflow-on-EKS \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --region $AOK_AWS_REGION \
  --tags Key=Name,Value=AirflowVolume \
  --encrypted \
  --output text \
  --query "FileSystemId")

printf "Waiting for 10 seconds...\n"
sleep 10

printf "Creating EFS mount targets in each subnet attached to on-demand nodes...\n"
for subnet in $(aws eks describe-nodegroup \
  --cluster-name $AOK_EKS_CLUSTER_NAME \
  --nodegroup-name ng-on-demand \
  --region $AOK_AWS_REGION \
  --output text \
  --query "nodegroup.subnets"); \
do (aws efs create-mount-target \
  --file-system-id $AOK_EFS_FS_ID \
  --subnet-id $subnet \
  --security-group $AOK_EFS_SG_ID \
  --region $AOK_AWS_REGION); \
done

printf "Creating an EFS access point...\n"
export AOK_EFS_AP=$(aws efs create-access-point \
  --file-system-id $AOK_EFS_FS_ID \
  --posix-user Uid=1000,Gid=1000 \
  --root-directory "Path=/airflow,CreationInfo={OwnerUid=1000,OwnerGid=1000,Permissions=777}" \
  --region $AOK_AWS_REGION \
  --query 'AccessPointId' \
  --output text)
  

printf "Seteando variables AOK_AWS_REGION AOK_ACCOUNT_ID AOK_EKS_CLUSTER_NAME...\n"
AOK_AWS_REGION=us-east-1 #<-- Change this to match your region
AOK_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
AOK_EKS_CLUSTER_NAME=Airflow-on-Kubernetes

echo $AOK_AWS_REGION
echo $AOK_ACCOUNT_ID
echo $AOK_EKS_CLUSTER_NAME


printf "Getting the VPC of the EKS cluster and its CIDR block...\n"
export AOK_VPC_ID=$(aws eks describe-cluster --name $AOK_EKS_CLUSTER_NAME \
  --region $AOK_AWS_REGION \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)
  

printf "\n"
printf "\n"
printf "Deploy an Amazon RDS PostgreSQL database.\n"

printf "Obtaining the list of Private Subnets in Env variables...\n"
export AOK_PRIVATE_SUBNETS=$(aws eks describe-nodegroup \
  --cluster-name $AOK_EKS_CLUSTER_NAME \
  --nodegroup-name ng-on-demand \
  --region $AOK_AWS_REGION \
  --output text \
  --query "nodegroup.subnets" | awk -v OFS="," '{for(i=1;i<=NF;i++)if($i~/subnet/)$i="\"" $i "\"";$1=$1}1')
printf $AOK_PRIVATE_SUBNETS


printf "Creating a DB Subnet group...\n"
aws rds create-db-subnet-group \
   --db-subnet-group-name airflow-postgres-subnet1 \
   --subnet-ids "[$AOK_PRIVATE_SUBNETS]" \
   --db-subnet-group-description "Subnet group for Postgres RDS" \
   --region $AOK_AWS_REGION

printf "Creating the RDS Postgres Instance...\n"
#OJO POR AHORA LA CREO PUBLICA PARA VER QUE TODO ANDE
aws rds create-db-instance \
  --db-instance-identifier airflow \
  --db-instance-class db.t3.micro \
  --db-name airflow \
  --engine postgres \
  --master-username airflow \
  --master-user-password supersecretpassword \
  --allocated-storage 20 \
  --region $AOK_AWS_REGION \
  --publicly-accessible \
  --db-subnet-group-name airflow-postgres-subnet1
  
printf "Checking if the RDS Instance is up ....\n"
aws rds describe-db-instances \
  --db-instance-identifier airflow \
  --region $AOK_AWS_REGION \
  --query "DBInstances[].DBInstanceStatus"   
   
printf "Creating RDS security group...\n"
export AOK_RDS_SG=$(aws rds describe-db-instances \
   --db-instance-identifier airflow \
   --region $AOK_AWS_REGION \
   --query "DBInstances[].VpcSecurityGroups[].VpcSecurityGroupId" \
   --output text)  

export AOK_VPC_ID=$(aws eks describe-cluster --name $AOK_EKS_CLUSTER_NAME \
  --region $AOK_AWS_REGION \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)
export AOK_CIDR_BLOCK=$(aws ec2 describe-vpcs --vpc-ids $AOK_VPC_ID \
  --query "Vpcs[].CidrBlock" \
  --region $AOK_AWS_REGION \
  --output text)
 
#NO ACTIVAR SI QUIERO VER LOS DATOS DESDE MI PC    
printf "Authorizing traffic...\n"
aws ec2 authorize-security-group-ingress \
  --group-id $AOK_RDS_SG \
  --cidr $AOK_CIDR_BLOCK  \
  --port 5432 \
  --protocol tcp \
  --region $AOK_AWS_REGION

   
printf "Waiting for 5 minutes...\n"
sleep 300 
   
printf "Checking if the RDS Instance is up ....\n"
aws rds describe-db-instances \
  --db-instance-identifier airflow \
  --region $AOK_AWS_REGION \
  --query "DBInstances[].DBInstanceStatus"   
  
printf "Creating an RDS endpoint....\n"
export AOK_RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier airflow \
  --query 'DBInstances[0].Endpoint.Address' \
  --region $AOK_AWS_REGION \
  --output text) 
  
printf "Waiting for 5 minutes...\n"
sleep 300 
   
printf "Checking if the RDS Instance is up ....\n"
aws rds describe-db-instances \
  --db-instance-identifier airflow \
  --region $AOK_AWS_REGION \
  --query "DBInstances[].DBInstanceStatus"   
  
printf "Creating an RDS endpoint....\n"
export AOK_RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier airflow \
  --query 'DBInstances[0].Endpoint.Address' \
  --region $AOK_AWS_REGION \
  --output text) 
 
   



