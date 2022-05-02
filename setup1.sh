printf "Seteando variables AOK_AWS_REGION AOK_ACCOUNT_ID AOK_EKS_CLUSTER_NAME...\n"
AOK_AWS_REGION=us-east-1 #<-- Change this to match your region
AOK_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
AOK_EKS_CLUSTER_NAME=Airflow-on-Kubernetes

#printf "Asignando AmazonEKSClusterPolicy...\n"
#aws iam attach-role-policy \
#  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy \
#  --role-name LabRole

printf "Asignando AmazonEKS_CNI_Policy...\n"
aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy \
  --role-name LabRole
  
#printf "Asignando AmazonSSMManagedInstanceCore...\n"
#aws iam attach-role-policy \
#  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore \
#  --role-name LabRole
  
#printf "Asignando AmazonEC2ContainerRegistryReadOnly...\n"
#aws iam attach-role-policy \
#  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly\
#  --role-name LabRole

printf "Asignando AmazonEKS_CNI_Policy...\n"
aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy \
  --role-name LabRole
  
cat << EOF > EKSPassRole-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "eks:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "iam:PassedToService": "eks.amazonaws.com"
                }
            }
        }
    ]
}  
EOF

printf "Creando EKSPassRole-policy...\n"
aws iam put-role-policy --role-name LabRole --policy-name EKSPassRole-policy --policy-document file://EKSPassRole-policy.json

printf "Asignando AmazonEKS_CNI_Policy...\n"
aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy \
  --role-name LabRole

printf "Asignando AmazonElasticFileSystemFullAccess...\n"
aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess \
  --role-name LabRole
  
cat << EOF > CreateDBInstance-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInternetGateways",
                "rds:Describe*",
                "rds:ListTagsForResource",
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeVpcs",
                "rds:CreateDBInstance",
                "ec2:DescribeAccountAttributes",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcAttribute",
                "rds:CreateDBSubnetGroup",
                "ec2:DescribeSecurityGroups"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "rds:CreateDBInstance",
            "Resource": [
                "arn:aws:rds:*:841487132122:db:*",
                "arn:aws:rds:*:841487132122:og:*",
                "arn:aws:rds:*:841487132122:subgrp:*",
                "arn:aws:rds:*:841487132122:cluster:*",
                "arn:aws:rds:*:841487132122:secgrp:*",
                "arn:aws:rds:*:841487132122:pg:*"
            ]
        },
        {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": "rds:DescribeDBEngineVersions",
            "Resource": "*"
        }
    ]
}
EOF
    
aws iam put-role-policy --role-name LabRole --policy-name CreateDBInstance-policy --policy-document file://CreateDBInstance-policy.json    

aws iam put-role-policy --role-name LabRole --policy-name API-policy-policy --policy-document file://API-policy.json    


cat << EOF > s3_QuickSight-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::s3-analytics-export-shared-*"
            ]
        },
        {
            "Action": [
                "s3:GetAnalyticsConfiguration",
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}  
EOF

aws iam put-role-policy --role-name LabRole --policy-name s3_QuickSight-policy --policy-document file://s3_QuickSight-policy.json


printf "Asignando AmazonSageMakerFullAccess_Policy...\n"
aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess \
  --role-name LabRole
      
printf "Creando bucket en S3 y Folder ...\n"  
aws s3api create-bucket \
    --bucket friccomi \
    --region us-east-1

aws s3api put-object \
    --bucket friccomi \
    --key templates/  
 
aws s3api put-object \
    --bucket friccomi \
    --key tp/tp_avgs/
     
    
aws s3api put-object \
    --bucket friccomi \
    --key Airflow/
    
 aws s3api put-object \
    --bucket friccomi \
    --key Airflow/logs/ 
    






