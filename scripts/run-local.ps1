Write-Output "Fetching cluster information"
$ip = kubectl cluster-info | Select-String -Pattern "\d{5}$" | Select-Object -ExpandProperty Matches | Select-Object -ExpandProperty Value

Write-Output "Adding roles"
kubectl create clusterrolebinding default-view `
    --clusterrole=edit `
    --serviceaccount=default:default

Write-Output "Starting minikube dashboard"
$job = Start-Job -ScriptBlock { minikube dashboard } |  Select-Object -Property Name -Unique

Write-Output "Execute example"
$instances = 3
./bin/spark-submit `
    --master k8s://https://127.0.0.1:$ip `
    --deploy-mode cluster `
    --name spark-pi `
    --class org.apache.spark.examples.SparkPi `
    --conf spark.executor.instances=$instances `
    --conf spark.kubernetes.container.image=spark:3.5.1 `
    local:///opt/spark/examples/jars/spark-examples_2.12-3.5.1.jar

Write-Output "Stopping minikube dashboard"
Stop-Job $job
