export AIRFLOW_NAME="Airflow-on-Kubernetes"
export AIRFLOW_NAMESPACE="airflow"
export RELEASE_NAME=airflow-on-kubernetes
export CHART_VERSION=8.5.3
export VALUES_FILE=./values.yaml
export AOK_AWS_REGION=us-east-1 #<-- Change this to match your region
export AOK_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export AOK_EKS_CLUSTER_NAME=Airflow-on-Kubernetes

cd aws-airflow-helm
cat << EOF > NodeInstanceRole-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:BatchCheckLayerAvailability",
                "ecr:BatchGetImage",
                "ecr:GetDownloadUrlForLayer",
                "ecr:GetAuthorizationToken"
            ],
            "Resource": "*"
        }
    ]
}
EOF
printf "Creando NodeInstanceRole-policy...\n"
aws iam put-role-policy --role-name LabRole --policy-name NodeInstanceRole-policy --policy-document file://NodeInstanceRole-policy.json


export AOK_AIRFLOW_REPOSITORY=$(aws ecr create-repository \
  --repository-name airflow-eks \
  --region $AOK_AWS_REGION \
  --query 'repository.repositoryUri' \
  --output text)
  
printf  "Loggin  ECR.. \n"  
aws ecr get-login-password \
  --region $AOK_AWS_REGION | \
  docker login \
  --username AWS \
  --password-stdin \
  $AOK_AIRFLOW_REPOSITORY

printf  "Building image of Airflow.. \n"  

docker build -t ${AOK_AIRFLOW_REPOSITORY}:airflow .
docker push ${AOK_AIRFLOW_REPOSITORY}:airflow


