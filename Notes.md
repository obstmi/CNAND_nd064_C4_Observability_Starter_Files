
## Helm installation
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
see: https://helm.sh/docs/intro/install/#from-script

## Create the Monitoring Namespace
* kubectl create namespace monitoring


## Prometheus installation
# preparation
* helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
* helm repo add stable https://charts.helm.sh/stable
* helm repo update

# Install Prometheus and Grafana using Helm
* helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --kubeconfig /etc/rancher/k3s/k3s.yaml
NAME: prometheus
LAST DEPLOYED: Mon Apr 14 12:03:28 2025
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
NOTES:
kube-prometheus-stack has been installed. Check its status by running:
  kubectl --namespace monitoring get pods -l "release=prometheus"

Get Grafana 'admin' user password by running:

  kubectl --namespace monitoring get secrets prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

Access Grafana local instance:

  export POD_NAME=$(kubectl --namespace monitoring get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=prometheus" -oname)
  kubectl --namespace monitoring port-forward $POD_NAME 3000

Visit https://github.com/prometheus-operator/kube-prometheus for instructions on how to create & configure Alertmanager and Prometheus instances using the Operator.

## Pods running
root@vagrant:/home/vagrant# kubectl get pods,svc --namespace=monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running   0          31m
pod/prometheus-grafana-79fc997c7-lj5p5                       3/3     Running   0          31m
pod/prometheus-kube-prometheus-operator-57d9889bf-m5lzl      1/1     Running   0          31m
pod/prometheus-kube-state-metrics-f699c577d-tpdxn            1/1     Running   0          31m
pod/prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running   0          31m
pod/prometheus-prometheus-node-exporter-pg6qc                1/1     Running   0          31m

NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                     ClusterIP   None            <none>        9093/TCP,9094/TCP,9094/UDP   31m
service/prometheus-grafana                        ClusterIP   10.43.38.10     <none>        80/TCP                       31m
service/prometheus-kube-prometheus-alertmanager   ClusterIP   10.43.100.214   <none>        9093/TCP,8080/TCP            31m
service/prometheus-kube-prometheus-operator       ClusterIP   10.43.87.239    <none>        443/TCP                      31m
service/prometheus-kube-prometheus-prometheus     ClusterIP   10.43.192.100   <none>        9090/TCP,8080/TCP            31m
service/prometheus-kube-state-metrics             ClusterIP   10.43.175.226   <none>        8080/TCP                     31m
service/prometheus-operated                       ClusterIP   None            <none>        9090/TCP                     31m
service/prometheus-prometheus-node-exporter       ClusterIP   10.43.33.170    <none>        9100/TCP                     31m
root@vagrant:/home/vagrant# kubectl get pods,svc

## Forward Grafana service
# Option 1 - Port-forward the Grafana service
kubectl port-forward service/prometheus-grafana --address 0.0.0.0 3000:80 --namespace monitoring

# Option 2 - Port forward the specific pod
kubectl port-forward pod/prometheus-grafana-6bcd69b9f6-fmdxj --address 0.0.0.0 3000 --namespace monitoring

username: admin 
password: prom-operator

## Forward Prometheus service
kubectl port-forward service/prometheus-kube-prometheus-prometheus --address 0.0.0.0 9090:9090 --namespace monitoring

## Install Jaeger
(using apply instead of create, since it updates existing ressources instead of trying to renew them - but with error if existing)
# Create observalibilty namespace
* kubectl create namespace observability
# install cert.manager:
* kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.1/cert-manager.yaml
# deploy the Ingress Controller:
* kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
# Install the Jaeger Operator:
* kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.62.0/jaeger-operator.yaml -n observability
# Deploy a Jaeger Agent Sidecar:
* kubectl apply -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/v1.62.0/examples/business-application-injected-sidecar.yaml  
("myapp")
# Create an Ingress Resource for Jaeger:
* touch jaeger-ingress.yaml
* vi jaeger-ingress.yaml
* kubectl apply -n observability -f jaeger-ingress.yaml
# Configure Hosts File for Local Access
* kubectl get nodes -o wide
* echo "10.0.2.15 jaeger.local" | sudo tee -a /etc/hosts
# Verify Application Logs and Services
* Check logs of the sample application:  
kubectl logs -l app=myapp -n observability
# List Ingress and Service details:
* kubectl get ingress -n observability
* kubectl get svc -n ingress-nginx
# If the EXTERNAL-IP is <pending>, change the service type to NodePort:
* kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec": {"type": "NodePort"}}'
# Deploy a Jaeger Instance
* touch jaeger.yaml
* vi jaeger.yaml
* kubectl apply -f jaeger.yaml -n observability
# Access the Jaeger UI
* locally: curl -v http://jaeger.local
* To access from the host machine, set up port forwarding:  :
kubectl port-forward -n observability svc/jaeger-query 16686:16686 --address 0.0.0.0

## Add Jaeger Data Source in Prometheus
# In the Grafana UI (running on localhost:3000 from the previous exercise), go to Connections > Data sources > Add data source > Type: Jaeger and use the following URL:
* http://jaeger-query.observability.svc.cluster.local:16686



## Install Jaeger - OLD VERSION!!! 
(using apply instead of create, since it updates existing ressources instead of trying to renew them - but with error if existing)
# install cert.manager:
* kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
# install latest Jaeger:
* kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.65.0/jaeger-operator.yaml -n observability  
"all-in-one", see: https://www.jaegertracing.io/docs/1.65/operator/
# auto-injecting Jaeger Agent Sidecars, a sample application, into every worker:
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/v1.65.0/examples/business-application-injected-sidecar.yaml

## Deploy an ingress-controller:
* kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.1/deploy/static/provider/cloud/deploy.yaml  
See:
* https://kubernetes.github.io/ingress-nginx/deploy  
* https://github.com/kubernetes/ingress-nginx

## Create “all-in-one” Jaeger instance (see: https://github.com/jaegertracing/jaeger-operator#getting-started)
kubectl apply -n observability -f - <<EOF
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: simplest
EOF

### This does:
* creates a Jaeger Instance with name "simplest"
* the Jaeger operator creates an Ingress-object. Because it recognizes, that an Ingress-conroller (here: NGINX Ingress-Controller) is installed in the Kubernetes cluster


## Forward the local port to the service/simplest-query port 
* kubectl port-forward -n observability  service/simplest-query --address 0.0.0.0 16686:16686  


## Stop port forwarding
* lsof -ti:16686 | xargs kill -9

## Delete a Jaeger instance
* kubectl delete jaeger simplest -n observability  
Dieser Befehl löscht die benutzerdefinierte Ressource (CRD) simplest. Der Jaeger Operator erkennt dies und entfernt automatisch alle zugehörigen Ressourcen wie:
* Deployments (simplest)
* Pods (simplest-*)
* Services (simplest-*)
* Ingress-Objekte (falls vorhanden)

check: kubectl get deployment,pods,svc -n observability

Oder einzeln:
* kubectl delete deployment simplest -n observability
* kubectl delete pod -l app.kubernetes.io/instance=simplest -n observability
* kubectl delete svc -l app.kubernetes.io/instance=simplest -n observability
* kubectl delete ingress -l app.kubernetes.io/instance=simplest -n observability

Check Jaeger operator (remains active)
* kubectl get deployment jaeger-operator -n observability
* kubectl get pods -n observability -l name=jaeger-operator (the operator runs as a pod)
* kubectl logs -n observability <jaeger-operator-pod-name>
* kubectl get crds | grep jaeger (the operator manages CRDs) => "jaegers.jaegertracing.io"
* kubectl get jaeger -n observability (shows the Jaeger instances)  

Delete Jaeger operator:
* kubectl delete deployment jaeger-operator -n observability


## Summary
* Installation Cert Manager and Jaeger Operator  
see: https://www.jaegertracing.io/docs/1.65/operator/
* Deploy Ingress Controller  
see: https://kubernetes.github.io/ingress-nginx/deploy and https://github.com/kubernetes/ingress-nginx and https://kubernetes.github.io/ingress-nginx/deploy/#provider-specific-steps and https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
* Create Jaeger Instance together with an Ingress object  
see: https://github.com/jaegertracing/jaeger-operator#getting-started
* Forward the local port to the service/simplest-query port  
see: https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/#forward-a-local-port-to-a-port-on-the-pod





## Performancy / technical SLOs / four golden signals
* Latency (the time taken to serve a request)
* Traffic (the amount of stress on a system e.g. the number of HTTP requests/second)
* Error rate (the number of requests that are failing e.g. the number of HTTP 500 responses)
* Saturation (the overall capacity of a service e.g. the percentage of memory or CPU used)  
and further:
* Network capacity
* Uptime

Terms:
* bounce rate: number of users how are exciting an app without using it



