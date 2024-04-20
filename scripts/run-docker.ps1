Write-Output "Starting spark container"
docker compose -f .\docker\docker-compose.yml up -d

Write-Output "Adding roles"
kubectl create clusterrolebinding default-view `
    --clusterrole=edit `
    --serviceaccount=default:default

Write-Output "Starting minikube dashboard"
$job = Start-Job -ScriptBlock { minikube dashboard } | Select-Object -Property Name -Unique

Write-Output "Execute example"
$instances = 3
docker exec -it spark /opt/spark/bin/spark-submit `
    --master k8s://http://minikube:8443 `
    --deploy-mode cluster --name spark-pi `
    --class org.apache.spark.examples.SparkPi `
    --conf spark.executor.instances=$instances `
    --conf spark.kubernetes.container.image=bde2020/spark-base:3.3.0-hadoop3.3 `
    local:///opt/spark/examples/jars/spark-examples_2.12-3.5.1.jar

Write-Output "Stopping minikube dashboard"
Stop-Job $job
