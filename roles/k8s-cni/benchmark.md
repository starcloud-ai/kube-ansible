# 性能测试

## 测试环境

### 硬件

### 软件

## sriov 网络测试

### 1. 镜像准备

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

使用mofed的安装包，会使用rpm安装perftest，包含以下内容
| 名称 | 路径 | 说明 |
| --- | --- | --- |
| ib_atomic_bw | /usr/bin/ib_atomic_bw | --- |
| ib_atomic_lat | /usr/bin/ib_atomic_lat | --- |
| ib_read_bw | /usr/bin/ib_read_bw | --- |
| ib_read_lat | /usr/bin/ib_read_lat | --- |
| ib_send_bw | /usr/bin/ib_send_bw | --- |
| ib_send_lat | /usr/bin/ib_send_lat | --- |
| ib_write_bw | /usr/bin/ib_write_bw | --- |
| ib_write_lat | /usr/bin/ib_write_lat | --- |
| raw_ethernet_burst_lat | /usr/bin/raw_ethernet_burst_lat | --- |
| raw_ethernet_bw | /usr/bin/raw_ethernet_bw | --- |
| raw_ethernet_fs_rate | /usr/bin/raw_ethernet_fs_rate | --- |
| raw_ethernet_lat | /usr/bin/raw_ethernet_lat | --- |
| run_perftest_loopback | /usr/bin/run_perftest_loopback | --- |
| run_perftest_multi_devices | /usr/bin/run_perftest_multi_devices | --- |

### 2. 使用`mofed_test`创建pod

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
    resources:
      limits:
        rdma/vhca: 1
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
    resources:
      limits:
        rdma/vhca: 1
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
    resources:
      limits:
        rdma/vhca: 1
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
    resources:
      limits:
        rdma/vhca: 1
    stdin: true
    tty: true
```

### 3. 在sriov网卡上启动iperf server

```text
# 查看网卡
kubectl exec -it iperf-server ip a

# 在sriov网卡上启动iperf server
kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.0.0.89 -s
```

### 4. 选取client pod执行测试

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

### 5. 测试RDMA连通性



## hca 网络测试

### 1. 镜像准备

使用上面生成的`mofed_test`镜像

### 2. 使用`mofed_test`创建4个pod

```text
apiVersion: v1
kind: Pod
metadata:
  name: iperf-server
spec:  # specification of the pod's contents
  containers:
  - name: iperf-server
    image: "192.168.1.150:5000/mofed_test"
    securityContext:
      capabilities:
        add: [ "IPC_LOCK" ]
    resources:
      limits:
        rdma/hca: 1
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    stdin: true
    tty: true
---
apiVersion: v1
kind: Pod
metadata:
  name: iperf-client-1
spec:  # specification of the pod's contents
  containers:
  - name: iperf-client-1
    image: "192.168.1.150:5000/mofed_test"
    securityContext:
      capabilities:
        add: [ "IPC_LOCK" ]
    resources:
      limits:
        rdma/hca: 1
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    stdin: true
    tty: true
---
apiVersion: v1
kind: Pod
metadata:
  name: iperf-client-2
spec:  # specification of the pod's contents
  containers:
  - name: iperf-client-2
    image: "192.168.1.150:5000/mofed_test"
    securityContext:
      capabilities:
        add: [ "IPC_LOCK" ]
    resources:
      limits:
        rdma/hca: 1
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    stdin: true
    tty: true
---
apiVersion: v1
kind: Pod
metadata:
  name: iperf-client-3
spec:  # specification of the pod's contents
  containers:
  - name: iperf-client-3
    image: "192.168.1.150:5000/mofed_test"
    securityContext:
      capabilities:
        add: [ "IPC_LOCK" ]
    resources:
      limits:
        rdma/hca: 1
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    stdin: true
    tty: true
```

### 3.使用iperf测试ip2ib网卡性能

hca使用calico来进行ip地址的管理

1. 启动iperf server

    ```text
    # 查看网卡
    kubectl exec -it iperf-server ip a

    # 在sriov网卡上启动iperf server
    kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.244.3.3 -s
    ```

2. 选取跨主机的client pod执行测试

    ```text
    # 单线程测试tcp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.244.3.3
    ......
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  10.6 GBytes  9.13 Gbits/sec  1077             sender
    [  5]   0.00-10.04  sec  10.6 GBytes  9.09 Gbits/sec                  receiver

    # 多线程测试tcp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.244.3.3 -P 4
    ......
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  2.67 GBytes  2.30 Gbits/sec  358             sender
    [  5]   0.00-10.03  sec  2.67 GBytes  2.28 Gbits/sec                  receiver
    [  7]   0.00-10.00  sec  2.78 GBytes  2.39 Gbits/sec  151             sender
    [  7]   0.00-10.03  sec  2.77 GBytes  2.37 Gbits/sec                  receiver
    [  9]   0.00-10.00  sec  2.78 GBytes  2.39 Gbits/sec  795             sender
    [  9]   0.00-10.03  sec  2.77 GBytes  2.37 Gbits/sec                  receiver
    [ 11]   0.00-10.00  sec  2.67 GBytes  2.29 Gbits/sec   90             sender
    [ 11]   0.00-10.03  sec  2.66 GBytes  2.28 Gbits/sec                  receiver
    [SUM]   0.00-10.00  sec  10.9 GBytes  9.36 Gbits/sec  1394             sender
    [SUM]   0.00-10.03  sec  10.9 GBytes  9.31 Gbits/sec                  receiver

    # 单线程测试udp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.3.3
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/945 (0%)  sender
    [  5]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.012 ms  0/945 (0%)  receiver

    # 多线程测试udp
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.3.3 -P 4
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/945 (0%)  sender
    [  5]   0.00-10.04  sec  1.25 MBytes  1.04 Mbits/sec  0.008 ms  0/945 (0%)  receiver
    [  7]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/945 (0%)  sender
    [  7]   0.00-10.04  sec  1.25 MBytes  1.04 Mbits/sec  0.013 ms  0/945 (0%)  receiver
    [  9]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/945 (0%)  sender
    [  9]   0.00-10.04  sec  1.25 MBytes  1.04 Mbits/sec  0.011 ms  0/945 (0%)  receiver
    [ 11]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/945 (0%)  sender
    [ 11]   0.00-10.04  sec  1.25 MBytes  1.04 Mbits/sec  0.011 ms  0/945 (0%)  receiver
    [SUM]   0.00-10.00  sec  5.00 MBytes  4.20 Mbits/sec  0.000 ms  0/3780 (0%)  sender
    [SUM]   0.00-10.04  sec  5.00 MBytes  4.18 Mbits/sec  0.011 ms  0/3780 (0%)  receiver

    # 单线程测试udp，增加带宽参数
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.3.3 -b 100G
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.31 GBytes  1.13 Gbits/sec  0.000 ms  0/1016529 (0%)  sender
    [  5]   0.00-10.05  sec   734 MBytes   613 Mbits/sec  0.015 ms  461950/1016448 (45%)  receiver

    # 多线程测试udp，增加带宽参数
    $ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.3.3 -P 4 -b 100G
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec   400 MBytes   336 Mbits/sec  0.000 ms  0/302373 (0%)  sender
    [  5]   0.00-10.04  sec   399 MBytes   333 Mbits/sec  0.032 ms  932/302362 (0.31%)  receiver
    [  7]   0.00-10.00  sec   400 MBytes   336 Mbits/sec  0.000 ms  0/302373 (0%)  sender
    [  7]   0.00-10.04  sec   399 MBytes   333 Mbits/sec  0.032 ms  933/302362 (0.31%)  receiver
    [  9]   0.00-10.00  sec   400 MBytes   336 Mbits/sec  0.000 ms  0/302373 (0%)  sender
    [  9]   0.00-10.04  sec   399 MBytes   333 Mbits/sec  0.032 ms  933/302362 (0.31%)  receiver
    [ 11]   0.00-10.00  sec   400 MBytes   336 Mbits/sec  0.000 ms  0/302373 (0%)  sender
    [ 11]   0.00-10.04  sec   399 MBytes   333 Mbits/sec  0.032 ms  932/302362 (0.31%)  receiver
    [SUM]   0.00-10.00  sec  1.56 GBytes  1.34 Gbits/sec  0.000 ms  0/1209492 (0%)  sender
    [SUM]   0.00-10.04  sec  1.56 GBytes  1.33 Gbits/sec  0.032 ms  3730/1209448 (0.31%)  receiver
    ```

3. 选取同主机的client pod执行测试

    ```text
    # 单线程测试tcp
    $ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.244.3.3
    ......
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  36.4 GBytes  31.3 Gbits/sec  1042             sender
    [  5]   0.00-10.04  sec  36.4 GBytes  31.2 Gbits/sec                  receiver

    # 多线程测试tcp
    $ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.244.3.3 -P 4
    ......
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  9.71 GBytes  8.34 Gbits/sec    0             sender
    [  5]   0.00-10.03  sec  9.71 GBytes  8.32 Gbits/sec                  receiver
    [  7]   0.00-10.00  sec  9.71 GBytes  8.34 Gbits/sec    0             sender
    [  7]   0.00-10.03  sec  9.71 GBytes  8.32 Gbits/sec                  receiver
    [  9]   0.00-10.00  sec  9.71 GBytes  8.34 Gbits/sec    0             sender
    [  9]   0.00-10.03  sec  9.71 GBytes  8.32 Gbits/sec                  receiver
    [ 11]   0.00-10.00  sec  9.71 GBytes  8.34 Gbits/sec    0             sender
    [ 11]   0.00-10.03  sec  9.71 GBytes  8.32 Gbits/sec                  receiver
    [SUM]   0.00-10.00  sec  38.8 GBytes  33.4 Gbits/sec    0             sender
    [SUM]   0.00-10.03  sec  38.8 GBytes  33.3 Gbits/sec                  receiver

    # 单线程测试udp
    $ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.3.3
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  5]   0.00-10.04  sec  1.25 MBytes  1.04 Mbits/sec  0.006 ms  0/906 (0%)  receiver

    # 多线程测试udp
    $ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.3.3 -P 4
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  5]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.003 ms  0/906 (0%)  receiver
    [  7]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  7]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.002 ms  0/906 (0%)  receiver
    [  9]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [  9]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.005 ms  0/906 (0%)  receiver
    [ 11]   0.00-10.00  sec  1.25 MBytes  1.05 Mbits/sec  0.000 ms  0/906 (0%)  sender
    [ 11]   0.00-10.04  sec  1.25 MBytes  1.05 Mbits/sec  0.005 ms  0/906 (0%)  receiver
    [SUM]   0.00-10.00  sec  5.00 MBytes  4.20 Mbits/sec  0.000 ms  0/3624 (0%)  sender
    [SUM]   0.00-10.04  sec  5.00 MBytes  4.18 Mbits/sec  0.004 ms  0/3624 (0%)  receiver

    # 单线程测试udp，增加带宽参数
    $ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.3.3 -b 100G
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec  1.45 GBytes  1.25 Gbits/sec  0.000 ms  0/1077749 (0%)  sender
    [  5]   0.00-10.05  sec  1.45 GBytes  1.24 Gbits/sec  0.000 ms  5531/1077749 (0.51%)  receiver

    # 多线程测试udp，增加带宽参数
    $ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.3.3 -P 4 -b 100G
    ......
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec   500 MBytes   419 Mbits/sec  0.000 ms  0/361833 (0%)  sender
    [  5]   0.00-10.04  sec   495 MBytes   414 Mbits/sec  0.002 ms  3074/361833 (0.85%)  receiver
    [  7]   0.00-10.00  sec   500 MBytes   419 Mbits/sec  0.000 ms  0/361833 (0%)  sender
    [  7]   0.00-10.04  sec   495 MBytes   414 Mbits/sec  0.002 ms  3074/361833 (0.85%)  receiver
    [  9]   0.00-10.00  sec   500 MBytes   419 Mbits/sec  0.000 ms  0/361833 (0%)  sender
    [  9]   0.00-10.04  sec   495 MBytes   414 Mbits/sec  0.002 ms  3074/361833 (0.85%)  receiver
    [ 11]   0.00-10.00  sec   500 MBytes   419 Mbits/sec  0.000 ms  0/361833 (0%)  sender
    [ 11]   0.00-10.04  sec   495 MBytes   414 Mbits/sec  0.002 ms  3075/361833 (0.85%)  receiver
    [SUM]   0.00-10.00  sec  1.95 GBytes  1.68 Gbits/sec  0.000 ms  0/1447332 (0%)  sender
    [SUM]   0.00-10.04  sec  1.94 GBytes  1.66 Gbits/sec  0.002 ms  12297/1447332 (0.85%)  receiver
    ```

### 4. 在宿主机上使用perftest测试

1. 连通性测试

    ```text
    # 在cu05上执行
    $ ifconfig enp175s0
    enp175s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
           inet 10.0.0.155  netmask 255.255.255.0  broadcast 10.0.0.255
           inet6 fe80::526b:4bff:fe28:4df8  prefixlen 64  scopeid 0x20<link>
           ether 50:6b:4b:28:4d:f8  txqueuelen 1000  (Ethernet)
           RX packets 902715  bytes 58246978 (58.2 MB)
           RX errors 0  dropped 0  overruns 0  frame 0
           TX packets 90088  bytes 6375868 (6.3 MB)
           TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

    $ rdma_server

    # 在cu07上执行
    $ rdma_client -s 10.0.0.155
    rdma_client: start
    rdma_client: end 0
    ```

2. 性能测试

    ```text
    # 在cu05上执行
    $ ib_write_bw

    # 在cu07上执行
    $ ib_write_bw -d mlx5_0 10.0.0.155
    ---------------------------------------------------------------------------------------
                        RDMA_Write BW Test
     Dual-port       : OFF          Device         : mlx5_0
     Number of qps   : 1            Transport type : IB
     Connection type : RC           Using SRQ      : OFF
     TX depth        : 128
     CQ Moderation   : 100
     Mtu             : 1024[B]
     Link type       : Ethernet
     GID index       : 3
     Max inline data : 0[B]
     rdma_cm QPs     : OFF
     Data ex. method : Ethernet
    ---------------------------------------------------------------------------------------
     local address: LID 0000 QPN 0x00b7 PSN 0xda4e0c RKey 0x0057c3 VAddr 0x007f1d9feb0000
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:157
     remote address: LID 0000 QPN 0x00b7 PSN 0x2c7174 RKey 0x009450 VAddr 0x007f286d020000
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:155
    ---------------------------------------------------------------------------------------
     #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
    Conflicting CPU frequency values detected: 1003.892000 != 1940.696000. CPU Frequency is not max.
     65536      5000             11044.38            11043.78                  0.176700
    ---------------------------------------------------------------------------------------
    ```

    ```text
    # 在cu05上执行
    $ ib_atomic_bw

    # 在cu07上执行
    $ ib_atomic_bw -d mlx5_0 10.0.0.155
    ---------------------------------------------------------------------------------------
                        Atomic FETCH_AND_ADD BW Test
     Dual-port       : OFF          Device         : mlx5_0
     Number of qps   : 1            Transport type : IB
     Connection type : RC           Using SRQ      : OFF
     TX depth        : 128
     CQ Moderation   : 100
     Mtu             : 1024[B]
     Link type       : Ethernet
     GID index       : 3
     Outstand reads  : 16
     rdma_cm QPs     : OFF
     Data ex. method : Ethernet
    ---------------------------------------------------------------------------------------
     local address: LID 0000 QPN 0x00b8 PSN 0x9a0df2
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:155
     remote address: LID 0000 QPN 0x00b9 PSN 0x5db9ac
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:155
    ---------------------------------------------------------------------------------------
     #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
    Conflicting CPU frequency values detected: 1000.005000 != 3060.420000. CPU Frequency is not max.
     8          1000             16.28              16.17              2.119821
    ---------------------------------------------------------------------------------------
    ```

    ```text
    # 在cu05上执行
    $ ib_read_bw

    # 在cu07上执行
    $ ib_read_bw -d mlx5_0 10.0.0.155
    ---------------------------------------------------------------------------------------
                        RDMA_Read BW Test
     Dual-port       : OFF          Device         : mlx5_0
     Number of qps   : 1            Transport type : IB
     Connection type : RC           Using SRQ      : OFF
     TX depth        : 128
     CQ Moderation   : 100
     Mtu             : 1024[B]
     Link type       : Ethernet
     GID index       : 3
     Outstand reads  : 16
     rdma_cm QPs     : OFF
     Data ex. method : Ethernet
    ---------------------------------------------------------------------------------------
     local address: LID 0000 QPN 0x00b9 PSN 0x1b5fa OUT 0x10 RKey 0x007435 VAddr 0x007fc7e30b3000
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:157
     remote address: LID 0000 QPN 0x00bb PSN 0x5db3a7 OUT 0x10 RKey 0x007939 VAddr 0x007f68a13c1000
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:155
    ---------------------------------------------------------------------------------------
     #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
    Conflicting CPU frequency values detected: 999.991000 != 1047.331000. CPU Frequency is not max.
     65536      1000             10584.99            10584.57                  0.169353
    ---------------------------------------------------------------------------------------
    ```

    ```text
    # 在cu05上执行
    $ ib_send_bw

    # 在cu07上执行
    $ ib_send_bw -d mlx5_0 10.0.0.155
    ---------------------------------------------------------------------------------------
                        Send BW Test
     Dual-port       : OFF          Device         : mlx5_0
     Number of qps   : 1            Transport type : IB
     Connection type : RC           Using SRQ      : OFF
     TX depth        : 128
     CQ Moderation   : 100
     Mtu             : 1024[B]
     Link type       : Ethernet
     GID index       : 3
     Max inline data : 0[B]
     rdma_cm QPs     : OFF
     Data ex. method : Ethernet
    ---------------------------------------------------------------------------------------
     local address: LID 0000 QPN 0x00bb PSN 0x7507fa
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:157
     remote address: LID 0000 QPN 0x00bd PSN 0xb1beea
     GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:155
    ---------------------------------------------------------------------------------------
     #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
    Conflicting CPU frequency values detected: 999.996000 != 1031.872000. CPU Frequency is not max.
     65536      1000             11116.32            11115.93                  0.177855
    ---------------------------------------------------------------------------------------
    ```

### 5. 在容器内使用perftest测试

容器内查看设备

```text
$ kubectl exec -it iperf-server -- ibv_devices
device                 node GUID
------              ----------------
mlx5_1              1e8744fffe7ca496
mlx5_65             daa23afffe2452d2
mlx5_37             2a5549fffe26143a
mlx5_75             f6305afffe1b1420
mlx5_47             9edae3fffe18c265
mlx5_19             a66f13fffeb1a016
mlx5_85             6a05a8fffe6f1299
mlx5_57             f6fc11fffe65c6f8
mlx5_101            fec170fffec3484e
mlx5_29             8e8c38fffe7a0590
mlx5_95             4a3b8dfffef3959b
mlx5_3              8e2d1efffef2a3f7
mlx5_67             660e27fffe35c773
mlx5_111            1ac437fffebe9dc2 
......

$ kubectl exec -it iperf-server -- ibv_devinfo -d mlx5_0
hca_id: mlx5_1
        transport:                      InfiniBand (0)
        fw_ver:                         16.23.1020
        node_guid:                      1e87:44ff:fe7c:a496
        sys_image_guid:                 506b:4b03:0028:4df0
        vendor_id:                      0x02c9
        vendor_part_id:                 4120
        hw_ver:                         0x0
        board_id:                       MT_0000000011
        phys_port_cnt:                  1
        Device ports:
                port:   1
                        state:                  PORT_DOWN (1)
                        max_mtu:                4096 (5)
                        active_mtu:             1024 (3)
                        sm_lid:                 0
                        port_lid:               0
                        port_lmc:               0x00
                        link_layer:             Ethernet

$ kubectl exec -it iperf-server -- ibstat mlx5_0
CA 'mlx5_1'
        CA type: MT4120
        Number of ports: 1
        Firmware version: 16.23.1020
        Hardware version: 0
        Node GUID: 0x1e8744fffe7ca496
        System image GUID: 0x506b4b0300284df0
        Port 1:
                State: Down
                Physical state: Disabled
                Rate: 100
                Base lid: 0
                LMC: 0
                SM lid: 0
                Capability mask: 0x04010000
                Port GUID: 0x0000000000000000
                Link layer: Ethernet
```

1. 连通性测试

    ```text
    # 在iperf-server上创建server端
    $  kubectl exec -it iperf-server -- ifconfig eth0
    eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            inet 10.244.3.3  netmask 255.255.255.255  broadcast 0.0.0.0
            ether 0a:f8:22:54:bb:1c  txqueuelen 0  (Ethernet)
            RX packets 7118489  bytes 111002527092 (103.3 GiB)
            RX errors 0  dropped 0  overruns 0  frame 0
            TX packets 2101475  bytes 138788442 (132.3 MiB)
            TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

    $ kubectl exec -it iperf-server -- rdma_server

    # 在iperf-client-1上执行
    $ kubectl exec -it iperf-client-1 -- rdma_client -s 10.244.3.3
    rdma_client: start
    rdma_client: end 0
    ```

2. 性能测试

    ```
    $ kubectl exec -it iperf-server -- ib_atomic_bw -d mlx5_0
    $ kubectl exec -it iperf-client-1 -- ib_atomic_bw -d mlx5_0 10.244.3.3
    ```

 ibping 参数说明
```text
# server 端
-S：以服务器端运行
-C：是CA,来自ibstat的输出
-P：端口号,来自ibstat的输出

 # client 端
-c：发送10000个packet之后停止. 
-f：flood destination 
-C：是CA,来自ibstat的输出 
-P：端口号,来自服务器端运行ibping命令时指定的-P 参数值. 
-L：Base lid,来自服务器端运行ibping命令时指定的端口(-P 参数值)的base lid(参考ibstat)
```

 执行测试

 ```text
# 在一个节点上启动 server
$ ib_send_bw -d mlx5_1 -i 1 -F --report_gbits

 $ ib_send_bw -d mlx4_0 -i 1 -F --report_gbits 12.12.12.1
```

### 参考

#### iperf 相关

https://www.iyunv.com/thread-274855-1-1.html  
https://www.cnblogs.com/yingsong/p/5682080.html  

#### infiniband 相关

https://blog.csdn.net/qq_21125183/article/details/81262483  
https://blog.csdn.net/guohaosun/article/details/82225067?utm_source=blogxgwz0