# azureml-online-endpoints-aks

This repo shows how to deploy models to AKS using Azure Machine Learning Online Endpoints. More details can be found in [Azure/AML-Kubernetes](https://github.com/Azure/AML-Kubernetes). Thanks to [René Bremer](https://github.com/rebremer) for providing the [original steps](https://github.com/rebremer/blog-mlopsapim-git/blob/master/other/mlv2clitest/cli_script.txt).

## Install extensions

```console
az extension add --name ml
az extension add --name connectedk8s
az extension add --name k8s-extension
sudo az aks install-cli
```

## Variable definitinos

```console
# Resource group name
rg='aml-moe'

# VNET details
vnet_name='vnet'
vnet_address_range='10.0.0.0/16'

# AKS clustername
aks_cluster_name='aks-dev'

# AKS networking details
aks_subnet_address_range='10.0.2.0/24'
aks_service_address_range='10.100.0.0/24'
aks_dns_service_ip='10.100.0.10'

# AML details
workspace_name='aml-moetest'
aml_subnet_address_range='10.0.1.0/24'

# AML deployment name
endpoint='model-endpoint'
```

## Create network resources

```console
az group create -l westeurope -n $rg
az network vnet create -g $rg -n $vnet_name --address-prefix $vnet_address_range
az network vnet subnet create -g $rg --vnet-name $vnet_name -n aml --address-prefixes $aml_subnet_address_range
az network vnet subnet create -g $rg --vnet-name $vnet_name -n aks --address-prefixes $aks_subnet_address_range
aks_subnet_id=`az network vnet subnet show -g $rg -n aks --vnet-name $vnet_name --query 'id' | sed 's/\"//g'`
```

## Create workspace

This repo assumes the workspace is already here and is named `$workspace_name`

## Create jumphost VM/Compute Instance in aml-subnet

Not covered in this repo right now...and potentially not needed (needs to be validated).

## Make sure public access is enabled for your AzureML workspace

Allow public access to workspace via this Python snippet, or alternatively just change the setting under the Networking tab on your AML Workspace:

```python
from azureml.core import Workspace
ws = Workspace(subscription_id='...', resource_group='...', workspace_name='...')
ws.update(allow_public_access_when_behind_vnet=True)
```

## Create AKS cluster

```console
az aks create --resource-group $rg --name $aks_cluster_name --network-plugin azure --vnet-subnet-id $aks_subnet_id --docker-bridge-address 172.17.0.1/16 --dns-service-ip $aks_dns_service_ip --service-cidr $aks_service_address_range --generate-ssh-keys --enable-managed-identity -y --enable-private-cluster
az aks get-credentials --resource-group $rg --name $aks_cluster_name --overwrite-existing
```

## Make sure AKS MI has network contributor rights on Network in which internal load balancer is deployed

```console
aks_object_id=`az aks show -g $rg -n $aks_cluster_name --query 'identity.principalId' | sed 's/\"//g'`
vnet_id=`az network vnet show -g $rg -n $vnet_name --query 'id' | sed 's/\"//g'`
az role assignment create --assignee-object-id $aks_object_id --role "Network Contributor" --scope $vnet_id
```

# Install AML AKS extension on AKS cluster

```console
az feature register --namespace Microsoft.ContainerService -n AKS-ExtensionManager
az provider register -n Microsoft.ContainerService
az k8s-extension create --name arcml-inference --extension-type Microsoft.AzureML.Kubernetes --cluster-type managedClusters --cluster-name $aks_cluster_name --config enableInference=True privateEndpointILB=True allowInsecureConnections=True --resource-group $rg --scope cluster --auto-upgrade-minor-version False
az k8s-extension show --name arcml-inference --cluster-type managedClusters --cluster-name $aks_cluster_name --resource-group $rg
```

# Attach cluster to workspace

```console
aks_id=`az aks show -g $rg -n $aks_cluster_name --query 'id' | sed 's/\"//g'`
az ml compute attach -g $rg -w $workspace_name -n $aks_cluster_name -t Kubernetes --resource-id $aks_id --namespace $workspace_name
```

# Create endpoints and deployments using yml files

```console
az ml online-endpoint create -g $rg -w $workspace_name -n $endpoint -f endpoint/endpoint.yml
az ml online-deployment create --name deployment --endpoint $endpoint -f endpoint/deployment.yml --all-traffic -g $rg -w $workspace_name
```
