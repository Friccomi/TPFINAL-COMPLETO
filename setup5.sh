export AIRFLOW_NAME="Airflow-on-Kubernetes"
export AIRFLOW_NAMESPACE="airflow"
export RELEASE_NAME=airflow-on-kubernetes
export CHART_VERSION=8.5.3
export VALUES_FILE=./values.yaml
export AOK_AWS_REGION=us-east-1 #<-- Change this to match your region
export AOK_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export AOK_EKS_CLUSTER_NAME=Airflow-on-Kubernetes

cd aws-airflow-helm

printf  "Traer helm airflow p/Kubernetes.. \n"     
helm repo add airflow-stable https://airflow-helm.github.io/charts
helm repo update


export AIRFLOW_NAME="Airflow-on-Kubernetes"
export AIRFLOW_NAMESPACE="airflow"
export RELEASE_NAME=airflow-on-kubernetes
export CHART_VERSION=8.5.3
export VALUES_FILE=./values.yaml


#kubectl create secret generic \
#  airflow-http-git-secret \
#  --from-literal=username=MY_GIT_USERNAME \
#  --from-literal=password=MY_GIT_TOKEN \
#  --namespace my-airflow-namespace
   
kubectl create secret generic \
  airflow-http-git-secret \
  --from-literal=username=Friccomi \
  --from-literal=password=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 \
  --namespace default
 
#kubectl apply -f airflow-db-secret.yml #--namespace=airflow
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.3"
helm repo add airflow-stable https://airflow-helm.github.io/charts
helm repo update
source set_env.sh
kubectl apply -f efs-pvc.yml
helm install airflow-on-kubernetes airflow-stable/airflow  --version 8.5.3 --values values.yaml

printf "Waiting for 3 minutes...\n"
sleep 180 

export POD_NAME=$(kubectl get pods --namespace default -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")
kubectl port-forward --namespace default $POD_NAME 8080:8080

#Hay que actualizar el DNS del EFS
#kubectl delete -f efs-pvc.yml  
#helm uninstall airflow-on-kubernetes airflow-stable/airflow
#kubectl delete secret  airflow-http-git-secret

#SI hay que corregir algo:
#helm upgrade airflow-on-kubernetes airflow-stable/airflow --namespace airflow --version 8.5.3 --values values.yaml

