# cni

## flannel

## calico

## hca

使用Mellanox的网卡，有两种工作模式，hca是其中的一种。这种工作模式基本就是将Mellanox网卡作为一块普通网卡来，需要配合calico来进行使用。

### 测试

```text
cat <<EOF |kubectl create -f -
apiVersion: v1
kind: Pod
metadata:
  name: mofed-test-pod-4
spec:
  restartPolicy: OnFailure
  containers:
  - image: 192.168.1.150:5000/mellanox/centos_7_4_mofed_4_2_1_2_0_0_60
    name: mofed-test-ctr-4
    securityContext:
      capabilities:
        add: [ "IPC_LOCK" ]
    resources:
      limits:
        rdma/hca: 1
    command:
    - sh
    - -c
    - |
      ls -l /dev/infiniband /sys/class/net
      sleep 1000000
EOF
```

使用hca模式时，要在container的配置中要增加`rdma/hca`，这时`Mellanox`的插件程序会将宿主机上的`/dev/infiniband` 作为`device`挂载到容器上。

```
docker inspect <container-id>
...
            "Devices": [
                {
                    "PathOnHost": "/dev/infiniband",
                    "PathInContainer": "/dev/infiniband",
                    "CgroupPermissions": "rwm"
                }
            ],
...
```

## sriov

使用Mellanox的网卡的另一种工作模式。它可以将一块物理网卡，虚拟出多块网卡，然后在物理网卡内部实现多块虚拟网卡的路由。

## multus

### 什么是multus

默认情况下，kuberenets只会从/etc/cni/conf中寻找一个插件使用，无法灵活使用多种CNI。同时，对于主机上有多块网卡的话，只能使用到其中一块。multus就是用来解决上述问题的。通过代理的方式，multus调用其他cni插件，在pod创建的过程中，为其创建多张网卡，每张网卡都属于一个CNI插件的网络。

### 支持范围

目前可以支持的CNI有 sriov、macvlan、flannel。calico暂时还在测试中。
其中flannel目前作为默认的网络。也就是说，默认的网络是由flannel提供的，其他的网络需要在创建pod的时候，通过annotation添加。

### CNI插件的配置

首先/etc/cni/conf 目录下只需要有multus的cni配置。或者说，multus的cni配置要有最高的优先级。
对于multus要使用的CNI插件，他们的CNI配置都通过configmap保存在kubernetes中。

例如：

```text
cat <<EOF | kubectl create -f -
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
spec:
  config: '{
      "cniVersion": "0.3.0",
      "type": "macvlan",
      "master": "eth0",
      "mode": "bridge",
      "ipam": {
        "dhcp"
      }
    }'
EOF
```

在config中比较重要的配置有

* type
  CNI类型，multus/kubernets会根据这个参数到/opt/cni/bin下去查找同名的CNI插件
* master
  CNI插件所使用的宿主机上的网卡
* ipam
  IP地址管理策略，默认有host-local，dhcp，static。

在实际使用过程中，sriov、macvlan要使用DHCP来动态获取地址。官方示例中使用的都是"host-local"。会导致不同节点上的容器有相同的IP地址。
flannel 使用默认配置就可以了。因为在flannel的设计中，不同的服务器上的容器属于不同的子网。不会有不同节点上出现相同IP地址的事情。

### 测试

#### macvlan 的测试

1. 重复创建多个使用macvlan的pod  
    ```text
    cat <<EOF | kubectl create -f -
    apiVersion: v1
    kind: Pod
    metadata:
      name: samplepod
      annotations:
        k8s.v1.cni.cncf.io/networks: macvlan-conf
    spec:
      containers:
      - name: samplepod
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        image: 192.168.1.150:5000/dougbtv/centos-network
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: samplepod2
      annotations:
        k8s.v1.cni.cncf.io/networks: macvlan-conf
    spec:
      containers:
      - name: samplepod2
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        image: 192.168.1.150:5000/dougbtv/centos-network
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: samplepod3
      annotations:
        k8s.v1.cni.cncf.io/networks: macvlan-conf
    spec:
      containers:
      - name: samplepod3
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        image: 192.168.1.150:5000/dougbtv/centos-network
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: samplepod4
      annotations:
        k8s.v1.cni.cncf.io/networks: macvlan-conf
    spec:
      containers:
      - name: samplepod4
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        image: 192.168.1.150:5000/dougbtv/centos-network
    EOF
    ```

2. 检查网卡  
    ```text
    kubectl exec -it samplepod -- ip a
    kubectl exec -it samplepod2 -- ip a
    kubectl exec -it samplepod3 -- ip a
    kubectl exec -it samplepod4 -- ip a
    ```
    每个pod应该有3块网卡
    * eth0  
      由默认网络flannel创建
    * lo
    * net1  
      由macvlan创建，ip地址由DHCP服务分配

#### sriov 的测试

1. 重复创建多个使用sriov的pod  
    ```text
    cat <<EOF |kubectl create -f -
    apiVersion: v1
    kind: Pod
    metadata:
      name: multus-multi-net-poc
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "flannel-conf" },
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: multus-multi-net-poc
        image: "192.168.1.150:5000/busybox"
        command: ["top"]
        stdin: true
        tty: true
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: multus-multi-net-poc-2
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "flannel-conf" },
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: multus-multi-net-poc-2
        image: "192.168.1.150:5000/busybox"
        command: ["top"]
        stdin: true
        tty: true
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: multus-multi-net-poc-3
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "flannel-conf" },
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: multus-multi-net-poc-3
        image: "192.168.1.150:5000/busybox"
        command: ["top"]
        stdin: true
        tty: true
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: multus-multi-net-poc-4
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "flannel-conf" },
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: multus-multi-net-poc-4
        image: "192.168.1.150:5000/busybox"
        command: ["top"]
        stdin: true
        tty: true
    EOF
    ```
2. 检查网卡  
    ```text
    kubectl exec -it multus-multi-net-poc -- ip a
    kubectl exec -it multus-multi-net-poc-2 -- ip a
    kubectl exec -it multus-multi-net-poc-3 -- ip a
    kubectl exec -it multus-multi-net-poc-4 -- ip a
    ```
    每个pod应该有3块网卡
    * eth0  
      由默认网络flannel创建
    * lo
    * net1  
      由flannel-conf创建
    * net2
      由sriov创建，ip地址由DHCP服务分配

