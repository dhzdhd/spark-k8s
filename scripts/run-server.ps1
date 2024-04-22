Write-Output "Starting spark container"
docker compose -f .\docker\docker-compose-server.yml up -d

Write-Output "Execute example"
docker exec -it spark /opt/spark/bin/spark-submit `
    --master k8s://https://<ip>:6443 `
    --deploy-mode cluster `
    --name spark-pi `
    --class org.apache.spark.examples.SparkPi `
    --conf spark.executor.instances=2 `
    --conf spark.kubernetes.container.image=spark `
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark `
    --conf spark.kubernetes.authenticate.submission.oauthToken= `
    --conf spark.kubernetes.authenticate.submission.caCertFile=/workdir/client-ca.crt `
    --conf spark.kubernetes.authenticate.submission.clientCertFile=/workdir/client-ca.crt `
    local:///opt/spark/examples/jars/spark-examples_2.12-3.5.1.jar
