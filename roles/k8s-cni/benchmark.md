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
    * [calico](https://www.projectcalico.org)
  * pv
    * nfs
* 测试工具
  * iperf3
  * perftest

## sriov 容器网络测试

### 镜像准备

因为`mellanox/centos_7_4_mofed_4_2_1_2_0_0_60`里只有`perftest` 没有`iperf3`所以需要自己制作镜像

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

### 使用`mofed_benchmark`创建pod

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

#### 选取不同node上的pod，进行 RDMA 性能测试

测试之前先选择已经active的网卡

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
2: tunl0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN group default qlen 1000
    link/ipip 0.0.0.0 brd 0.0.0.0
4: eth0@if329: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether ce:1e:59:f0:fb:16 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.244.0.5/32 scope global eth0
       valid_lft forever preferred_lft forever

# 在sriov网卡上启动iperf server
$ kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.244.0.5 -s
```

#### 选取同一个node上的pod，进行测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.244.0.5
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  42.5 GBytes  36.5 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  42.5 GBytes  36.5 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.244.0.5 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  11.1 GBytes  9.57 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  44.5 GBytes  38.3 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  44.5 GBytes  38.3 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.0.5
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.005 ms  0/897 (0%)  
[  4] Sent 897 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.0.5 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.004 ms  0/897 (0%)  
[  4] Sent 897 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.002 ms  0/897 (0%)  
[  6] Sent 897 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.001 ms  0/897 (0%)  
[  8] Sent 897 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.001 ms  0/897 (0%)  
[ 10] Sent 897 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.16 Mbits/sec  0.002 ms  0/3588 (0%)

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.0.5 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.96 GBytes  1.68 Gbits/sec  0.002 ms  888/1450751 (0.061%)  
[  4] Sent 1450751 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.244.0.5 -P 4 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec   703 MBytes   590 Mbits/sec  0.004 ms  0/509295 (0%)  
[  4] Sent 509295 datagrams
[  6]   0.00-10.00  sec   703 MBytes   590 Mbits/sec  0.004 ms  0/509295 (0%)  
[  6] Sent 509295 datagrams
[  8]   0.00-10.00  sec   703 MBytes   590 Mbits/sec  0.002 ms  0/509295 (0%)  
[  8] Sent 509295 datagrams
[ 10]   0.00-10.00  sec   703 MBytes   590 Mbits/sec  0.004 ms  0/509295 (0%)  
[ 10] Sent 509295 datagrams
[SUM]   0.00-10.00  sec  2.75 GBytes  2.36 Gbits/sec  0.003 ms  0/2037180 (0%)
```

#### 选取不同node上的pod，进行测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.244.0.5
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  12.0 GBytes  10.3 Gbits/sec  975             sender
[  4]   0.00-10.00  sec  12.0 GBytes  10.3 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -c 10.244.0.5 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  3.35 GBytes  2.88 Gbits/sec  435             sender
[  4]   0.00-10.00  sec  3.35 GBytes  2.88 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  3.46 GBytes  2.97 Gbits/sec  629             sender
[  6]   0.00-10.00  sec  3.46 GBytes  2.97 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  3.33 GBytes  2.86 Gbits/sec  508             sender
[  8]   0.00-10.00  sec  3.33 GBytes  2.86 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  3.40 GBytes  2.92 Gbits/sec  539             sender
[ 10]   0.00-10.00  sec  3.40 GBytes  2.92 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec  2111             sender
[SUM]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.0.5
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.016 ms  0/935 (0%)  
[  4] Sent 935 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.0.5 -P 4
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.093 ms  0/935 (0%)  
[  4] Sent 935 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.095 ms  0/935 (0%)  
[  6] Sent 935 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.100 ms  0/935 (0%)  
[  8] Sent 935 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.098 ms  0/935 (0%)  
[ 10] Sent 935 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.15 Mbits/sec  0.096 ms  0/3740 (0%)

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.0.5 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.84 GBytes  1.58 Gbits/sec  0.005 ms  569816/1420298 (40%)  
[  4] Sent 1420298 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-1 -- /usr/bin/iperf3 -u -c 10.244.0.5 -P 4 -b 100G
......
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec   517 MBytes   434 Mbits/sec  0.027 ms  259/390784 (0.066%)  
[  4] Sent 390784 datagrams
[  6]   0.00-10.00  sec   517 MBytes   434 Mbits/sec  0.028 ms  260/390783 (0.067%)  
[  6] Sent 390783 datagrams
[  8]   0.00-10.00  sec   517 MBytes   434 Mbits/sec  0.028 ms  260/390783 (0.067%)  
[  8] Sent 390783 datagrams
[ 10]   0.00-10.00  sec   517 MBytes   434 Mbits/sec  0.028 ms  260/390783 (0.067%)  
[ 10] Sent 390783 datagrams
[SUM]   0.00-10.00  sec  2.02 GBytes  1.74 Gbits/sec  0.028 ms  1039/1563133 (0.066%)
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

#### 选取同一个node上的pod，进行 RDMA 性能测试

#### 选取不同node上的pod，进行 RDMA 性能测试


1. 选取跨主机的client pod执行测试

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

2. 选取同主机的client pod执行测试

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