# 性能测试

## 测试环境

### 硬件

* 主机
  * 配置：  
     cores: 40  
     ram: 192GiB  
     storage: 480GB  
  * 个数：3
* 网络
  * Mellanox RDMA 网络
  * 千兆管理网

### 软件

* 集群管理: maas 2.5
* 系统: ubuntu 16.04
* 内核: xenial (hwe-16.04)
* rdma驱动: MLNX_OFED_LINUX-4.4-2.0.7.0
* kubernetes: 1.11.2
  * cni
    * [multus-cni](https://github.com/intel/multus-cni)
    * [sriov-cni](https://github.com/Mellanox/sriov-cni)
      * ipam: DHCP
    * [k8s-rdma-sriov-dev-plugin](https://github.com/Mellanox/k8s-rdma-sriov-dev-plugin)
    * [macvlan](https://github.com/containernetworking/plugins/tree/master/plugins/main/macvlan)
    * [calico](https://www.projectcalico.org)
  * pv
    * nfs
* 测试工具
  * iperf3
  * perftest

* 说明:
  最初按照mellanox官方文档尝试使用calico作为基础cni, 搭建支持hca的集群。但是始终RDMA总是失败([issue](https://github.com/Mellanox/k8s-rdma-sriov-dev-plugin/issues/18))。遂用macvlan替换calico重新进行测试。

## sriov 容器网络测试

### 镜像准备

因为 `mellanox/centos_7_4_mofed_4_2_1_2_0_0_60` 里只有 `perftest` 没有 `iperf3` 所以需要自己制作镜像

```text
git clone https://github.com/starcloud-ai/mofed_dockerfiles.git
cd mofed_dockerfiles
cp Dockerfile.centos7.2.mofed-4.4 Dockerfile
docker build -t asdfsx/mofed_benchmark .
docker tag asdfsx/mofed_benchmark 172.16.0.200:5000/asdfsx/mofed_benchmark
docker push asdfsx/mofed_benchmark
docker push 172.16.0.200:5000/asdfsx/mofed_benchmark
##########################################################################################
#
# 旧的创建上传方式
# docker build -t mofed_test .
# docker save mofed_test|gzip -c > mofed_test.tar.gz
# scp mofed_test.tar.gz ubuntu@192.168.1.150:/tmp
# ssh ubuntu@192.168.1.150 "docker load < /tmp/mofed_test.tar.gz"
# ssh ubuntu@192.168.1.160 "docker tag mofed_test 192.168.1.150:5000/mofed_test"
# ssh ubuntu@192.168.1.160 "docker push 192.168.1.150:5000/mofed_test"
#
##########################################################################################
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

### 使用 `mofed_benchmark` 创建pod

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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    resources:
      limits:
        rdma/vhca: 1
    stdin: true
    tty: true
```

查看创建的pod

```text
$ kubectl get pod -o wide
NAME             READY     STATUS    RESTARTS   AGE       IP          NODE            NOMINATED NODE
iperf-client-1   1/1       Running   0          18h       10.0.32.4   tender-mammal   <none>
iperf-server     1/1       Running   0          18h       10.0.33.3   mighty-burro    <none>
mofed-test-pod   1/1       Running   0          18h       10.0.31.5   picked-stag     <none>
```

### 使用iperf进行ip网络测试

#### 在sriov网卡上启动iperf server

```text
# 查看网卡
$ kubectl exec -it iperf-server ip a
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.33.3  netmask 255.255.255.0  broadcast 10.0.33.255
        ether ca:fb:bc:77:6e:39  txqueuelen 1000  (Ethernet)
        RX packets 498  bytes 93730 (91.5 KiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 718  bytes 169748 (165.7 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0


# 在sriov网卡上启动iperf server
$ kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.0.33.3 -s
```

#### 选取同一个node上的pod，进行测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.33.3

# 多线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.33.3 -P 4

# 单线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3

# 多线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3 -P 4

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3 -b 100G

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3 -P 4 -b 100G
```

#### 选取不同node上的pod，进行测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.33.3
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  24.7 GBytes  21.2 Gbits/sec  145             sender
[  4]   0.00-10.00  sec  24.7 GBytes  21.2 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.33.3 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  6.18 GBytes  5.31 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  24.7 GBytes  21.2 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  24.7 GBytes  21.2 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.006 ms  0/897 (0%)  
[  4] Sent 897 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.011 ms  0/897 (0%)  
[  4] Sent 897 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.012 ms  0/897 (0%)  
[  6] Sent 897 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.010 ms  0/897 (0%)  
[  8] Sent 897 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.021 ms  0/897 (0%)  
[ 10] Sent 897 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.16 Mbits/sec  0.013 ms  0/3588 (0%)  

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  4.77 GBytes  4.10 Gbits/sec  0.015 ms  1810485/3539660 (51%)  
[  4] Sent 3539660 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.33.3 -P 4 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.62 GBytes  1.39 Gbits/sec  0.016 ms  366275/1199208 (31%)  
[  4] Sent 1199208 datagrams
[  6]   0.00-10.00  sec  1.62 GBytes  1.39 Gbits/sec  0.002 ms  365999/1198655 (31%)  
[  6] Sent 1198655 datagrams
[  8]   0.00-10.00  sec  1.62 GBytes  1.39 Gbits/sec  0.002 ms  365525/1199197 (30%)  
[  8] Sent 1199197 datagrams
[ 10]   0.00-10.00  sec  1.62 GBytes  1.39 Gbits/sec  0.010 ms  365550/1199197 (30%)  
[ 10] Sent 1199197 datagrams
[SUM]   0.00-10.00  sec  6.47 GBytes  5.56 Gbits/sec  0.008 ms  1463349/4796257 (31%)
```

### 使用perftest进行RDMA网络测试

#### RDMA 连通性测试

```text
# 在iperf-server上创建server端
$ kubectl exec -it iperf-server -- rdma_server

# 在iperf-client-1上执行
$ kubectl exec -it iperf-client-1 -- rdma_client -s 10.0.33.3
rdma_client: start
rdma_client: end 0
```

#### 测试之前先选择已经active的网卡

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
hca_id: mlx5_0
        transport:               InfiniBand (0)
        fw_ver:                  16.23.1020
        node_guid:               506b:4b03:0028:4ddc
        sys_image_guid:          506b:4b03:0028:4ddc
        vendor_id:               0x02c9
        vendor_part_id:          4119
        hw_ver:                  0x0
        board_id:                MT_0000000011
        phys_port_cnt:           1
        Device ports:
                port: 1
                      state:              PORT_ACTIVE (4)
                      max_mtu:            4096 (5)
                      active_mtu:         1024 (3)
                      sm_lid:             0
                      port_lid:           0
                      port_lmc:           0x00
                      link_layer:         Ethernet

$ kubectl exec -it iperf-server -- ibstat mlx5_0
CA 'mlx5_0'
        CA type: MT4119
        Number of ports: 1
        Firmware version: 16.23.1020
        Hardware version: 0
        Node GUID: 0x506b4b0300284ddc
        System image GUID: 0x506b4b0300284ddc
        Port 1:
                State: Active
                Physical state: LinkUp
                Rate: 100
                Base lid: 0
                LMC: 0
                SM lid: 0
                Capability mask: 0x04010000
                Port GUID: 0x0000000000000000
                Link layer: Ethernet
```

#### 选取不同node上的pod，进行 RDMA 性能测试

##### ib_read_bw

```text
$ kubectl exec -it iperf-server -- ib_read_bw -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_read_bw -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04ad PSN 0xbc2a9b
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08a3 PSN 0xd7fcff
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.005000 != 1304.752000. CPU Frequency is not max.
 65536      1000             10402.09            10401.68                  0.166427
---------------------------------------------------------------------------------------
```

##### ib_read_lat

```text
$ kubectl exec -it iperf-server -- ib_read_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_read_lat -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b3 PSN 0x9d4c4f
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08a9 PSN 0xccbea9
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.000000 != 1259.399000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 999.988000 != 3299.999000. CPU Frequency is not max.
 2       1000          2.64           5.50         2.69               2.69           0.02                2.75                   5.50
---------------------------------------------------------------------------------------
```

##### ib_write_bw

```text
$ kubectl exec -it iperf-server -- ib_write_bw -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_write_bw -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04af PSN 0x6a56f3
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08a5 PSN 0x88f89d
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.259000 != 2105.420000. CPU Frequency is not max.
 65536      5000             11025.44            11024.71                  0.176395
---------------------------------------------------------------------------------------
```

##### ib_write_lat

```text
$ kubectl exec -it iperf-server -- ib_write_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_write_lat -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b5 PSN 0x5eda
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08ab PSN 0x269d62
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.991000 != 1084.582000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.016000 != 3300.000000. CPU Frequency is not max.
 2       1000          1.54           2.13         1.58               1.58           0.01              1.65                          2.13
---------------------------------------------------------------------------------------
```

##### ib_atomic_bw

```text
$ kubectl exec -it iperf-server -- ib_atomic_bw -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_atomic_bw -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b1 PSN 0xbe1fa7
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08a7 PSN 0x473154
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.007000 != 1278.739000. CPU Frequency is not max.
 8          1000             16.62              16.56                      2.170493
---------------------------------------------------------------------------------------
```

##### ib_atomic_lat

```text
$ kubectl exec -it iperf-server -- ib_atomic_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_atomic_lat -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b7 PSN 0xe63a67
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08ad PSN 0x39caea
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec]
Conflicting CPU frequency values detected: 1000.001000 != 1454.890000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 999.996000 != 3300.000000. CPU Frequency is not max.
 8       1000          2.60           5.01         2.65     	       2.65        	0.03   		2.77    		5.01   
---------------------------------------------------------------------------------------
```

##### ib_send_bw

```text
$ kubectl exec -it iperf-server -- ib_send_bw -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_send_bw -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b9 PSN 0x993dac
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08af PSN 0xece310
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 999.999000 != 1033.893000. CPU Frequency is not max.
 65536      1000             10987.21            10986.50                 0.175784
---------------------------------------------------------------------------------------
```

##### ib_send_lat

```text
$ kubectl exec -it iperf-server -- ib_send_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_send_lat -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04bb PSN 0x7cad5b
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08b1 PSN 0x39b432
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.996000 != 1050.736000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.036000 != 3287.575000. CPU Frequency is not max.
 2       1000          1.61           4.19         1.68                1.70            0.10             2.00                          4.19
---------------------------------------------------------------------------------------
```

## hca 容器网络测试

### 镜像准备

使用上面生成的`mofed_benchmark`镜像

### 使用`mofed_benchmark`创建pod

```text
apiVersion: v1
kind: Pod
metadata:
  name: iperf-server
spec:  # specification of the pod's contents
  containers:
  - name: iperf-server
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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
    image: "172.16.0.200:5000/asdfsx/mofed_benchmark"
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

查看建好的pod

```text
$ kubectl get pod -o wide
NAME             READY     STATUS    RESTARTS   AGE       IP           NODE            NOMINATED NODE
iperf-client-1   1/1       Running   0          26m       10.244.2.3   mighty-burro    <none>
iperf-client-2   1/1       Running   0          26m       10.244.1.4   tender-mammal   <none>
iperf-client-3   1/1       Running   0          26m       10.244.0.6   picked-stag     <none>
iperf-server     1/1       Running   0          26m       10.244.0.5   picked-stag     <none>
mofed-test-pod   1/1       Running   0          45m       10.244.0.4   picked-stag     <none>
```

### 使用iperf进行ip2ib网络测试

#### 启动iperf server

```text
# 查看网卡
$ kubectl exec -it iperf-server ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0@if4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether a2:23:48:b2:79:b0 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.0.32.6/24 scope global eth0
       valid_lft forever preferred_lft forever

# 在sriov网卡上启动iperf server
$ kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.0.32.6 -s
```

#### 选取同一个node上的pod，进行测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.0.32.6
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  53.3 GBytes  45.8 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  53.3 GBytes  45.8 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.0.32.6 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  14.5 GBytes  12.5 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  58.1 GBytes  49.9 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  58.1 GBytes  49.9 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.32.6
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.008 ms  0/897 (0%)  
[  4] Sent 897 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.32.6 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.012 ms  0/897 (0%)  
[  4] Sent 897 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.003 ms  0/897 (0%)  
[  6] Sent 897 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.002 ms  0/897 (0%)  
[  8] Sent 897 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.002 ms  0/897 (0%)  
[ 10] Sent 897 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.16 Mbits/sec  0.005 ms  0/3588 (0%)

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.32.6 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  3.63 GBytes  3.12 Gbits/sec  0.001 ms  9099/2693871 (0.34%)  
[  4] Sent 2693871 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.32.6 -P 4 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.21 GBytes  1.04 Gbits/sec  0.004 ms  1073/897612 (0.12%)  
[  4] Sent 897612 datagrams
[  6]   0.00-10.00  sec  1.21 GBytes  1.04 Gbits/sec  0.001 ms  1073/897612 (0.12%)  
[  6] Sent 897612 datagrams
[  8]   0.00-10.00  sec  1.21 GBytes  1.04 Gbits/sec  0.001 ms  1076/897612 (0.12%)  
[  8] Sent 897612 datagrams
[ 10]   0.00-10.00  sec  1.21 GBytes  1.04 Gbits/sec  0.001 ms  1077/897612 (0.12%)  
[ 10] Sent 897612 datagrams
[SUM]   0.00-10.00  sec  4.84 GBytes  4.16 Gbits/sec  0.002 ms  4299/3590448 (0.12%)  
```

#### 选取不同node上的pod，进行测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.32.6
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  26.0 GBytes  22.3 Gbits/sec   72             sender
[  4]   0.00-10.00  sec  26.0 GBytes  22.3 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.0.32.6 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  6.17 GBytes  5.30 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  24.7 GBytes  21.2 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  24.7 GBytes  21.2 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.32.6
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.009 ms  0/897 (0%)  
[  4] Sent 897 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.32.6 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.013 ms  0/897 (0%)  
[  4] Sent 897 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.015 ms  0/897 (0%)  
[  6] Sent 897 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.015 ms  0/897 (0%)  
[  8] Sent 897 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.013 ms  0/897 (0%)  
[ 10] Sent 897 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.16 Mbits/sec  0.014 ms  0/3588 (0%)

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.32.6 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  4.40 GBytes  3.78 Gbits/sec  0.003 ms  1211922/3259871 (37%)  
[  4] Sent 3259871 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.0.32.6 -P 4 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.15 GBytes   986 Mbits/sec  0.003 ms  122310/851232 (14%)  
[  4] Sent 851232 datagrams
[  6]   0.00-10.00  sec  1.15 GBytes   986 Mbits/sec  0.005 ms  119468/851243 (14%)  
[  6] Sent 851243 datagrams
[  8]   0.00-10.00  sec  1.15 GBytes   986 Mbits/sec  0.003 ms  116082/851226 (14%)  
[  8] Sent 851226 datagrams
[ 10]   0.00-10.00  sec  1.15 GBytes   986 Mbits/sec  0.003 ms  122517/851198 (14%)  
[ 10] Sent 851198 datagrams
[SUM]   0.00-10.00  sec  4.59 GBytes  3.94 Gbits/sec  0.004 ms  480377/3404899 (14%)  
```

### 使用perftest进行RDMA网络测试

#### RDMA 连通性测试

```text
# 在iperf-server上创建server端
$ kubectl exec -it iperf-server -- rdma_server

# 在iperf-client-1上执行
$ kubectl exec -it iperf-client-1 -- rdma_client -s 10.244.0.5
rdma_client: start
rdma_client: end 0
```

#### 测试之前检查RDMA网卡

```text
$ kubectl exec -it iperf-server -- ibv_devices
device               node GUID
------            ----------------
mlx5_0            506b4b0300284df4

......

$ kubectl exec -it iperf-server -- ibv_devinfo -d mlx5_0
hca_id: mlx5_0
        transport:               InfiniBand (0)
        fw_ver:                  16.23.1020
        node_guid:               506b:4b03:0028:4df4
        sys_image_guid:          506b:4b03:0028:4df4
        vendor_id:               0x02c9
        vendor_part_id:          4119
        hw_ver:                  0x0
        board_id:                MT_0000000011
        phys_port_cnt:           1
        Device ports:
                port:	1
                      state:               PORT_ACTIVE (4)
                      max_mtu:             4096 (5)
                      active_mtu:          1024 (3)
                      sm_lid:              0
                      port_lid:            0
                      port_lmc:            0x00
                      link_layer:          Ethernet


$ kubectl exec -it iperf-server -- ibstat mlx5_0
CA 'mlx5_0'
        CA type: MT4119
        Number of ports: 1
        Firmware version: 16.23.1020
        Hardware version: 0
        Node GUID: 0x506b4b0300284df4
        System image GUID: 0x506b4b0300284df4
        Port 1:
              State: Active
              Physical state: LinkUp
              Rate: 100
              Base lid: 0
              LMC: 0
              SM lid: 0
              Capability mask: 0x04010000
              Port GUID: 0x0000000000000000
              Link layer: Ethernet
```

#### 选取同一个node上的pod，进行 RDMA 性能测试

使用HCA，在测试时不需要添加`-zR`参数

##### ib_read_bw

```text
$ kubectl exec -it iperf-server -- ib_read_bw -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_read_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d7 PSN 0x39f9c4 OUT 0x10 RKey 0x006f20 VAddr 0x007f3ce360f000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00d6 PSN 0x972818 OUT 0x10 RKey 0x0039a6 VAddr 0x007fbb12e42000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.013000 != 3085.970000. CPU Frequency is not max.
 65536      1000             8361.75            8361.60            0.133786
---------------------------------------------------------------------------------------
```

##### ib_read_lat

```text
$ kubectl exec -it iperf-server -- ib_read_lat -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_read_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d9 PSN 0xd3de8a OUT 0x10 RKey 0x009442 VAddr 0x007f8a57beb000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00da PSN 0xf7a691 OUT 0x10 RKey 0x009c8b VAddr 0x007fa6ec8ce000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.002000 != 1230.297000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.043000 != 3299.999000. CPU Frequency is not max.
 2       1000          1.41           1.58         1.44                1.44            0.02            1.49                          1.58
---------------------------------------------------------------------------------------
```

##### ib_write_bw

```text
$ kubectl exec -it iperf-server -- ib_write_bw -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_write_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Max inline data : 0[B]
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00dc PSN 0xaf4f66 RKey 0x007221 VAddr 0x007f6a81a7c000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00dd PSN 0x5559f1 RKey 0x0046b1 VAddr 0x007f80acbde000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1004.057000 != 2293.927000. CPU Frequency is not max.
 65536      5000             11750.14            11749.78                  0.187996
---------------------------------------------------------------------------------------
```

##### ib_write_lat

```text
$ kubectl exec -it iperf-server -- ib_write_lat -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_write_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Max inline data : 220[B]
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00df PSN 0xe93629 RKey 0x00ac96 VAddr 0x007f9c82281000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00e0 PSN 0x90e8e3 RKey 0x00c9b4 VAddr 0x007fd09306d000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.997000 != 1025.722000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1001.851000 != 3305.279000. CPU Frequency is not max.
 2       1000          0.76           1.58         0.77                0.77            0.01            0.82                          1.58
---------------------------------------------------------------------------------------
```

##### ib_atomic_bw

```text
$ kubectl exec -it iperf-server -- ib_atomic_bw -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_atomic_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00e3 PSN 0xb9bb78
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00e2 PSN 0x70fdb0
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.001000 != 1040.697000. CPU Frequency is not max.
 8          1000             16.29              16.20               2.123211
---------------------------------------------------------------------------------------
```

##### ib_atomic_lat

```text
$ kubectl exec -it iperf-server -- ib_atomic_lat -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_atomic_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00e5 PSN 0x1f7df5
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00e6 PSN 0x2f4dd0
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.012000 != 1023.381000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.004000 != 3300.000000. CPU Frequency is not max.
 8       1000          1.42           6.29         1.45               1.45           0.02             1.50                        6.29
---------------------------------------------------------------------------------------
```

##### ib_send_bw

```text
$ kubectl exec -it iperf-server -- ib_send_bw -d mlx5_0
$ kubectl exec -it iperf-client-3 -- ib_send_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b9 PSN 0x993dac
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08af PSN 0xece310
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 999.999000 != 1033.893000. CPU Frequency is not max.
 65536      1000             10987.21            10986.50                 0.175784
---------------------------------------------------------------------------------------
```

##### ib_send_lat

```text
$ kubectl exec -it iperf-server -- ib_send_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-3 -- ib_send_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 5
 Max inline data : 236[B]
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00f0 PSN 0xe8654e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:05
 remote address: LID 0000 QPN 0x00f1 PSN 0xcf5ace
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.001000 != 1035.415000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1021.718000 != 998.636000. CPU Frequency is not max.
 2       1000          0.80           1.00         0.86                0.86            0.02            0.91                          1.00
---------------------------------------------------------------------------------------
```

#### 选取不同node上的pod，进行 RDMA 性能测试

##### ib_read_bw

```text
$ kubectl exec -it iperf-server -- ib_read_bw -d mlx5_0
$ kubectl exec -it iperf-client-1 -- ib_read_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF           Device         : mlx5_0
 Number of qps   : 1             Transport type : IB
 Connection type : RC            Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Outstand reads  : 16
 rdma_cm QPs	 : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d9 PSN 0x25a419 OUT 0x10 RKey 0x00a363 VAddr 0x007fb2e944e000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00d5 PSN 0x8f7bc1 OUT 0x10 RKey 0x005ac6 VAddr 0x007f4cb368d000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.005000 != 2294.713000. CPU Frequency is not max.
 65536      1000             10402.10            10401.76                  0.166428
---------------------------------------------------------------------------------------
```

##### ib_write_lat

```text
$ kubectl exec -it iperf-server -- ib_write_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_write_lat -d mlx5_0 10.0.33.3 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00da PSN 0x457738 OUT 0x10 RKey 0x00ab6b VAddr 0x007f56b6263000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00d8 PSN 0xc99349 OUT 0x10 RKey 0x008634 VAddr 0x007fdf146d5000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.004000 != 3037.899000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.002000 != 3299.938000. CPU Frequency is not max.
 2       1000          2.34           7.75         2.38                2.40            0.06              2.71                         7.75
---------------------------------------------------------------------------------------
```

##### ib_write_bw

```text
$ kubectl exec -it iperf-server -- ib_write_bw -d mlx5_0
$ kubectl exec -it iperf-client-1 -- ib_write_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Max inline data : 0[B]
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00db PSN 0x7af55e RKey 0x001a8d VAddr 0x007fd9a8655000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00db PSN 0xe9831e RKey 0x001568 VAddr 0x007ff1684ec000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1001.133000 != 3252.099000. CPU Frequency is not max.
 65536      5000             11026.69            11026.31                  0.176421
---------------------------------------------------------------------------------------
```

##### ib_write_lat

```text
$ kubectl exec -it iperf-server -- ib_write_lat -d mlx5_0
$ kubectl exec -it iperf-client-1 -- ib_write_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Max inline data : 220[B]
 rdma_cm QP      : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00dc PSN 0x8e9419 RKey 0x00b5a9 VAddr 0x007f1e09dc7000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00de PSN 0x92c311 RKey 0x00a894 VAddr 0x007f00a8deb000
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.021000 != 1095.907000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 999.997000 != 2644.217000. CPU Frequency is not max.
 2       1000          1.24           4.63         1.26                1.27            0.10             1.31                         4.63
---------------------------------------------------------------------------------------
```

##### ib_atomic_bw

```text
$ kubectl exec -it iperf-server -- ib_atomic_bw -d mlx5_0
$ kubectl exec -it iperf-client-1 -- ib_atomic_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00dd PSN 0x96044c
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00e1 PSN 0x688d07
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 999.993000 != 1134.962000. CPU Frequency is not max.
 8          1000             16.84              16.13                2.114323
---------------------------------------------------------------------------------------
```

##### ib_atomic_lat

```text
$ kubectl exec -it iperf-server -- ib_atomic_lat -d mlx5_0
$ kubectl exec -it iperf-client-1 -- ib_atomic_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Outstand reads  : 16
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00de PSN 0xccdb77
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00e4 PSN 0x310915
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.013000 != 1137.630000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.080000 != 3313.128000. CPU Frequency is not max.
 8       1000          2.29           2.53         2.33                2.34            0.02              2.40                        2.53
---------------------------------------------------------------------------------------
```

##### ib_send_bw

```text
$ kubectl exec -it iperf-server -- ib_send_bw -d mlx5_0
$ kubectl exec -it iperf-client-1 -- ib_send_bw -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF                Device         : mlx5_0
 Number of qps   : 1                  Transport type : IB
 Connection type : RC                 Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x04b9 PSN 0x993dac
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:04
 remote address: LID 0000 QPN 0x08af PSN 0xece310
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:33:03
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 999.999000 != 1033.893000. CPU Frequency is not max.
 65536      1000             10987.21            10986.50                 0.175784
---------------------------------------------------------------------------------------
```

##### ib_send_lat

```text
$ kubectl exec -it iperf-server -- ib_send_lat -d mlx5_0 -zR
$ kubectl exec -it iperf-client-1 -- ib_send_lat -d mlx5_0 10.0.32.6
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF          Device         : mlx5_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 9
 Max inline data : 236[B]
 rdma_cm QPs     : OFF
 Data ex. method : Ethernet
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00e3 PSN 0xcfb191
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:31:08
 remote address: LID 0000 QPN 0x00ef PSN 0xfae957
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:06
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.001000 != 1158.268000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 999.998000 != 3300.000000. CPU Frequency is not max.
 2       1000          1.29           3.77         1.35                1.35            0.05             1.43                         3.77
---------------------------------------------------------------------------------------
```

### 参考

#### iperf 相关

https://www.iyunv.com/thread-274855-1-1.html  
https://www.cnblogs.com/yingsong/p/5682080.html  

#### infiniband 相关

https://blog.csdn.net/qq_21125183/article/details/81262483  
https://blog.csdn.net/guohaosun/article/details/82225067?utm_source=blogxgwz0