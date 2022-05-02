    
printf "Subiendo template Infra Basica a S3 ...\n"
aws s3 cp Airflow-EKS.yaml \
    s3://friccomi/templates/
   

 printf  "\n"
 printf  "\n"
 printf  "Creando key-pair.. \n"
 aws ec2 create-key-pair --key-name Airflow
 printf  "\n"
 printf  "\n"
 printf "Creando Stack de CloudFormation para generar infra basica y Cluster (VPC,Subnets, NAT,  ...\n"    
aws cloudformation create-stack \
  --region us-east-1 \
  --stack-name Airflow-Kubernetes\
  --template-url  https://friccomi.s3.amazonaws.com/templates/Airflow-EKS.yaml   \
  --capabilities CAPABILITY_IAM
 
aws cloudformation wait stack-create-complete \--stack-name Airflow-Kubernetes
  
printf  "Registrando Cluster.. \n"
 aws eks update-kubeconfig \
  --region us-east-1 \
  --name Airflow-on-Kubernetes
  
 kubectl get svc

cat << EOF > EKSDescribeCluster-policy.json 
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "eks:DescribeCluster",
            "Resource": "arn:aws:eks:*:841487132122:cluster/*"
        }
    ]
}
EOF
aws iam put-role-policy --role-name LabRole --policy-name EKSDescribeCluster-policy \
--policy-document file://EKSDescribeCluster-policy.json


#printf  "Subiendo templates nodos.. \n"
#aws s3 cp amazon-eks-nodegroup.yaml  \
#    s3://friccomi/templates/
    

#aws cloudformation create-stack \
#  --region us-east-1 \
#  --stack-name Nodos \
#  --template-url  https://friccomi.s3.amazonaws.com/templates/amazon-eks-nodegroup.yaml  \
#  --parameters ParameterKey=KeyPairName,ParameterValue=TestKey ParameterKey=SubnetIDs,ParameterValue=SubnetID1\\,SubnetID2
#  --capabilities CAPABILITY_IAM
 

#aws cloudformation wait stack-create-complete \--stack-name amazon-eks-nodegroup.yaml

