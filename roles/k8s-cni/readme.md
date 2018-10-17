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

### 性能测试

#### 测试环境

##### 硬件

##### 软件

#### 使用 iperf 测试 sriov

1. 镜像准备
    因为`mellanox/centos_7_4_mofed_4_2_1_2_0_0_60`里只有`perftest` 没有`iperf3`所以需要自己制作镜像
    ```text
    git clone https://github.com/starcloud-ai/mofed_dockerfiles.git
    cd mofed_dockerfiles
    cp Dockerfile.centos7.2.mofed-4.4 Dockerfile
    docker build -t mofed_test .
    docker save mofed_test|gzip -c > mofed_test.tar.gz
    scp mofed_test.tar.gz ubuntu@192.168.1.150:/tmp
    ssh ubuntu@192.168.1.150 "docker load < /tmp/mofed_test.tar.gz"
    ssh ubuntu@192.168.1.160 "docker tag mofed_test 192.168.1.150:5000/mofed_test"
    ssh ubuntu@192.168.1.160 "docker push 192.168.1.150:5000/mofed_test"
    ```

2. 使用`mofed_test`创建4个pod

    ```text
    apiVersion: v1
    kind: Pod
    metadata:
      name: iperf-server
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: iperf-server
        image: "192.168.1.150:5000/mofed_test"
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        stdin: true
        tty: true
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: iperf-client-1
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: iperf-client-1
        image: "192.168.1.150:5000/mofed_test"
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        stdin: true
        tty: true
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: iperf-client-2
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: iperf-client-2
        image: "192.168.1.150:5000/mofed_test"
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        stdin: true
        tty: true
    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: iperf-client-3
      annotations:
        k8s.v1.cni.cncf.io/networks: '[
                { "name": "sriov-conf" }
        ]'
    spec:  # specification of the pod's contents
      containers:
      - name: iperf-client-3
        image: "192.168.1.150:5000/mofed_test"
        command: ["/bin/bash", "-c", "sleep 2000000000000"]
        stdin: true
        tty: true
    ```

3. 在sriov网卡上启动iperf server
    ```text
    # 查看网卡
    kubectl exec -it iperf-server ip a

    # 在sriov网卡上启动iperf server
    kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.0.0.89 -s
    ```

4. 选取client pod执行测试
    ```text
    # 单线程测试tcp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.0.89
    ......
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  21.3 GBytes  18.3 Gbits/sec  436             sender
    [  5]   0.00-10.04  sec  21.3 GBytes  18.2 Gbits/sec                  receiver

    # 多线程测试tcp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.0.89 -P 4
    ......
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  5.58 GBytes  4.80 Gbits/sec    0             sender
    [  5]   0.00-10.03  sec  5.58 GBytes  4.78 Gbits/sec                  receiver
    [  7]   0.00-10.00  sec  5.62 GBytes  4.83 Gbits/sec    0             sender
    [  7]   0.00-10.03  sec  5.61 GBytes  4.81 Gbits/sec                  receiver
    [  9]   0.00-10.00  sec  5.62 GBytes  4.83 Gbits/sec    0             sender
    [  9]   0.00-10.03  sec  5.61 GBytes  4.81 Gbits/sec                  receiver
    [ 11]   0.00-10.00  sec  5.58 GBytes  4.80 Gbits/sec    0             sender
    [ 11]   0.00-10.03  sec  5.58 GBytes  4.78 Gbits/sec                  receiver
    [SUM]   0.00-10.00  sec  22.4 GBytes  19.2 Gbits/sec    0             sender
    [SUM]   0.00-10.03  sec  22.4 GBytes  19.2 Gbits/sec                  receiver

    # 单线程测试udp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.0.89
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  5]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.006 ms  0/906 (0%)  receiver

    # 多线程测试udp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.0.89 -P 4
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  5]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.005 ms  0/906 (0%)  receiver
    [  7]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  7]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.005 ms  0/906 (0%)  receiver
    [  9]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  9]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.002 ms  0/906 (0%)  receiver
    [ 11]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [ 11]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.005 ms  0/906 (0%)  receiver
    [SUM]   0.00-10.00  sec  5.00 MBytes  4.20 Mbits/sec  0.000 ms  0/3624 (0%)  sender
    [SUM]   0.00-10.04  sec  5.00 MBytes  4.18 Mbits/sec  0.004 ms  0/3624 (0%)  receiver

    # 单线程测试udp，增加带宽参数
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.0.89 -b 100G
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  2.94 GBytes  2.53 Gbits/sec  0.000 ms  0/2179770 (0%)  sender
    [  5]   0.00-10.04  sec  2.27 GBytes  1.94 Gbits/sec  0.009 ms  494436/2179699 (23%)  receiver

    # 多线程测试udp，增加带宽参数
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.0.89 -P 4 -b 100G
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.12 GBytes   961 Mbits/sec  0.000 ms  0/829989 (0%)  sender
    [  5]   0.00-10.04  sec   959 MBytes   801 Mbits/sec  0.002 ms  135476/829923 (16%)  receiver
    [  7]   0.00-10.00  sec  1.12 GBytes   961 Mbits/sec  0.000 ms  0/829993 (0%)  sender
    [  7]   0.00-10.04  sec   960 MBytes   802 Mbits/sec  0.002 ms  134535/829926 (16%)  receiver
    [  9]   0.00-10.00  sec  1.12 GBytes   961 Mbits/sec  0.000 ms  0/829993 (0%)  sender
    [  9]   0.00-10.04  sec   958 MBytes   801 Mbits/sec  0.002 ms  135872/829926 (16%)  receiver
    [ 11]   0.00-10.00  sec  1.12 GBytes   961 Mbits/sec  0.000 ms  0/829853 (0%)  sender
    [ 11]   0.00-10.04  sec   976 MBytes   815 Mbits/sec  0.002 ms  123237/829787 (15%)  receiver
    [SUM]   0.00-10.00  sec  4.48 GBytes  3.85 Gbits/sec  0.000 ms  0/3319828 (0%)  sender
    [SUM]   0.00-10.04  sec  3.76 GBytes  3.22 Gbits/sec  0.002 ms  529120/3319562 (16%)  receiver

    ```

#### 使用 perftest 测试 hca

1. 镜像准备
    使用上面生成的`mofed_test`镜像

2. 使用`mofed_test`创建4个pod
    使用上面的yaml创建4个pod

3. 使用iperf测试ip2ib网卡性能
   1. 启动iperf server
   2. 选取client pod执行测试
4. 使用perftest测试hca

参考：

https://www.iyunv.com/thread-274855-1-1.html  
https://www.cnblogs.com/yingsong/p/5682080.html  