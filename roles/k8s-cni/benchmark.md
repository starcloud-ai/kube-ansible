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



## 裸机测试

### 软件准备

* perftest 

  `mofed`自带的测试工具

* iperf3

  > apt-get install -y iperf3

### 使用iperf进行ip网络测试

#### 在mellanox网卡上启动iperf server

```text
# 查看网卡
root@cpu1:~# ip a
......
4: enp175s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq switchid 506b4b284df4 state UP group default qlen 1000
    link/ether 50:6b:4b:28:4d:f4 brd ff:ff:ff:ff:ff:ff
    inet 10.0.32.34/24 brd 10.0.32.255 scope global enp175s0
       valid_lft forever preferred_lft forever
    inet6 fe80::526b:4bff:fe28:4df4/64 scope link 
       valid_lft forever preferred_lft forever

# 在sriov网卡上启动iperf server
root@cpu1:~# /usr/bin/iperf3 --bind 10.0.32.34 -s
```

#### 同一个节点上进行测试

```text
# 单线程测试tcp
root@cpu1:~# /usr/bin/iperf3 -c 10.0.32.34
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  47.7 GBytes  40.9 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  47.7 GBytes  40.9 Gbits/sec                  receiver

# 多线程测试tcp
root@cpu1:~# /usr/bin/iperf3 -c 10.0.32.34 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  13.5 GBytes  11.6 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  53.9 GBytes  46.3 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  53.9 GBytes  46.3 Gbits/sec                  receiver

# 单线程测试udp
root@cpu1:~# /usr/bin/iperf3 -u -c 10.0.32.34
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.013 ms  0/159 (0%)  
[  4] Sent 159 datagrams

# 多线程测试udp
root@cpu1:~# /usr/bin/iperf3 -u -c 10.0.32.34 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.009 ms  0/159 (0%)  
[  4] Sent 159 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.004 ms  0/159 (0%)  
[  6] Sent 159 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.003 ms  0/159 (0%)  
[  8] Sent 159 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.003 ms  0/159 (0%)  
[ 10] Sent 159 datagrams
[SUM]   0.00-10.00  sec  4.97 MBytes  4.17 Mbits/sec  0.005 ms  0/636 (0%) 

# 单线程测试udp，增加带宽参数
root@cpu1:~# /usr/bin/iperf3 -u -c 10.0.32.34 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  13.0 GBytes  11.2 Gbits/sec  0.002 ms  2368/1705114 (0.14%)  
[  4] Sent 1705114 datagrams

# 多线程测试udp，增加带宽参数
root@cpu1:~# /usr/bin/iperf3 -u -c 10.0.32.34 -P 4 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  4.09 GBytes  3.51 Gbits/sec  0.000 ms  142/536293 (0.026%)  
[  4] Sent 536293 datagrams
[  6]   0.00-10.00  sec  4.09 GBytes  3.51 Gbits/sec  0.000 ms  143/536293 (0.027%)  
[  6] Sent 536293 datagrams
[  8]   0.00-10.00  sec  4.09 GBytes  3.51 Gbits/sec  0.001 ms  144/536293 (0.027%)  
[  8] Sent 536293 datagrams
[ 10]   0.00-10.00  sec  4.09 GBytes  3.51 Gbits/sec  0.001 ms  143/536293 (0.027%)  
[ 10] Sent 536293 datagrams
[SUM]   0.00-10.00  sec  16.4 GBytes  14.1 Gbits/sec  0.001 ms  572/2145172 (0.027%)
```

#### 不同节点上进行测试

```text
# 单线程测试tcp
root@cpu3:~# /usr/bin/iperf3 -c 10.0.32.34
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  25.2 GBytes  21.7 Gbits/sec  2048             sender
[  4]   0.00-10.00  sec  25.2 GBytes  21.7 Gbits/sec                  receiver

# 多线程测试tcp
root@cpu3:~# /usr/bin/iperf3 -c 10.0.32.34 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  5.91 GBytes  5.07 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  5.90 GBytes  5.07 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  5.90 GBytes  5.07 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  5.90 GBytes  5.07 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  5.90 GBytes  5.07 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  5.90 GBytes  5.07 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  5.90 GBytes  5.06 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  5.89 GBytes  5.06 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  23.6 GBytes  20.3 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  23.6 GBytes  20.3 Gbits/sec                  receiver

# 单线程测试udp
root@cpu3:~# /usr/bin/iperf3 -u -c 10.0.32.34
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.019 ms  0/159 (0%)  
[  4] Sent 159 datagrams

# 多线程测试udp
root@cpu3:~# /usr/bin/iperf3 -u -c 10.0.32.34 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.038 ms  0/159 (0%)  
[  4] Sent 159 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.038 ms  0/159 (0%)  
[  6] Sent 159 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.048 ms  0/159 (0%)  
[  8] Sent 159 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.058 ms  0/159 (0%)  
[ 10] Sent 159 datagrams
[SUM]   0.00-10.00  sec  4.97 MBytes  4.17 Mbits/sec  0.046 ms  0/636 (0%)  

# 单线程测试udp，增加带宽参数
root@cpu3:~# /usr/bin/iperf3 -u -c 10.0.32.34 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  8.04 GBytes  6.91 Gbits/sec  0.011 ms  18502/1053733 (1.8%)  
[  4] Sent 1053733 datagrams

# 多线程测试udp，增加带宽参数
root@cpu3:~# /usr/bin/iperf3 -u -c 10.0.32.34 -P 4 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  2.22 GBytes  1.90 Gbits/sec  0.016 ms  187/290428 (0.064%)  
[  4] Sent 290428 datagrams
[  6]   0.00-10.00  sec  2.22 GBytes  1.90 Gbits/sec  0.017 ms  188/290428 (0.065%)  
[  6] Sent 290428 datagrams
[  8]   0.00-10.00  sec  2.22 GBytes  1.90 Gbits/sec  0.017 ms  187/290417 (0.064%)  
[  8] Sent 290417 datagrams
[ 10]   0.00-10.00  sec  2.22 GBytes  1.90 Gbits/sec  0.016 ms  191/290428 (0.066%)  
[ 10] Sent 290428 datagrams
[SUM]   0.00-10.00  sec  8.86 GBytes  7.61 Gbits/sec  0.016 ms  753/1161701 (0.065%)  

```

#### 整理结果

| 测试名称 | Transfer | Bandwidth | Retr | Jitter | Lost/Total Datagrams |
| ---- | -------- | -------- | --------- | ---- | ------ | ------ |
| TCP同节点单线程 | 47.7 GBytes | 40.9 Gbits/sec | 0 |        ||
| TCP不同节点单线程 | 25.2 GBytes | 21.7 Gbits/sec | 2048 |        ||
| TCP同节点4线程  | 53.9 GBytes | 46.3 Gbits/sec | 0 |        ||
| TCP不同节点4线程  | 23.6 GBytes | 20.3 Gbits/sec | 0 |        ||
| UDP同节点单线程  | 1.24 MBytes | 1.04 Mbits/sec |      | 0.013 ms |0/159 (0%)|
| UDP不同节点单线程  | 1.24 MBytes | 1.04 Mbits/sec |      | 0.019 ms |0/159 (0%)|
| UDP同节点4线程  | 4.97 MBytes | 4.17 Mbits/sec |      | 0.005 ms |0/636 (0%)|
| UDP不同节点4线程  | 4.97 MBytes | 4.17 Mbits/sec |      | 0.046 ms |0/636 (0%)|
| UDP同节点单线程100G带宽  | 13.0 GBytes | 11.2 Gbits/sec |      | 0.002 ms |2368/1705114 (0.14%)|
| UDP不同节点单线程100G带宽  | 8.04 GBytes | 6.91 Gbits/sec |      | 0.011 ms |18502/1053733 (1.8%)|
| UDP同节点4线程100G带宽  | 16.4 GBytes | 14.1 Gbits/sec |      | 0.001 ms |572/2145172 (0.027%)|
| UDP不同节点4线程100G带宽  | 8.86 GBytes | 7.61 Gbits/sec |      | 0.016 ms |753/1161701 (0.065%)|

### 使用perftest进行ib网路测试

#### 在同一个节点，进行IB网络测试

##### 测试结果

###### ib_read_bw

```text
root@cpu1:~# ib_read_bw -d mlx5_0 -zR
root@cpu1:~# ib_read_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00df PSN 0x8c1a24
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00e0 PSN 0x213d4d
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.001000 != 3002.923000. CPU Frequency is not max.
 65536      1000             8354.37            8354.22		   0.133667
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_read_bw -d mlx5_0 -zR -D 300
root@gpu1:~# ib_read_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0123 PSN 0xd9cb0e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x0124 PSN 0xba4f3e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2037.063000 != 1030.142000. CPU Frequency is not max.
 65536      20506500         0.00               8543.45		   0.136695
---------------------------------------------------------------------------------------
```



###### ib_read_lat

```text
root@cpu1:~# ib_read_lat -d mlx5_0 -zR
root@cpu1:~# ib_read_lat -d mlx5_0 10.0.32.34
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00e3 PSN 0xbc9c8d
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00e4 PSN 0xe82c13
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.001000 != 3073.683000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2260.502000 != 1000.007000. CPU Frequency is not max.
 2       1000          1.44           2.93         1.48     	       1.49        	0.02   		1.56    		2.93   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_read_lat -d mlx5_0 -zR -D 300
root@gpu1:~# ib_read_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0127 PSN 0xb4b85e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x0128 PSN 0x12598e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 917.203000 != 2153.728000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 898.215000 != 800.056000. CPU Frequency is not max.
 2             62078352            2.42           413812.77
---------------------------------------------------------------------------------------
```

###### ib_write_bw

```text
root@cpu1:~# ib_write_bw -d mlx5_0 -zR
root@cpu1:~# ib_write_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00e7 PSN 0x8e81e8
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00e8 PSN 0xd5f5c0
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.061000 != 3300.001000. CPU Frequency is not max.
 65536      5000             11660.36            11660.12		   0.186562
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_write_bw -d mlx5_0 -zR -D 300
root@gpu1:~# ib_write_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x012b PSN 0x35762
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x012c PSN 0xa24f5f
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 864.338000 != 2702.240000. CPU Frequency is not max.
 65536      24777100         0.00               10322.23		   0.165156
---------------------------------------------------------------------------------------
```



###### ib_write_lat

```text
root@cpu1:~# ib_write_lat -d mlx5_0 -zR
root@cpu1:~# ib_write_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00eb PSN 0x5d9378
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00ec PSN 0x6674dd
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1023.201000 != 1000.854000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 999.999000 != 1021.153000. CPU Frequency is not max.
 2       1000          0.76           0.95         0.78     	       0.78        	0.01   		0.83    		0.95   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_write_lat -d mlx5_0 -zR -D 300
root@gpu1:~# ib_write_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00f9 PSN 0x41f896
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x00fa PSN 0xfa8036
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 902.996000 != 866.521000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1055.916000 != 1106.156000. CPU Frequency is not max.
 2             58732912            1.28           391518.70
---------------------------------------------------------------------------------------
```

> ib_write_lat 如果客户端加了-D参数，服务端也必须加-D参数。否则，服务端会很快退出，然后客户端也会跟着结束。

###### ib_atomic_bw

```text
root@cpu1:~# ib_atomic_bw -d mlx5_0 -zR
root@cpu1:~# ib_atomic_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00ef PSN 0xb6df89
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00f0 PSN 0x3a7abc
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1195.116000 != 999.993000. CPU Frequency is not max.
 8          1000             16.29              16.25  		   2.129385
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_atomic_bw -d mlx5_0 -zR -D 300
root@gpu1:~# ib_atomic_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x012f PSN 0xfed1bb
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x0130 PSN 0xffd228
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1037.714000 != 921.511000. CPU Frequency is not max.
 8          210853400        0.00               10.72  		   1.405510
---------------------------------------------------------------------------------------
```

###### ib_atomic_lat

```text
root@cpu1:~# ib_atomic_lat -d mlx5_0 -zR
root@cpu1:~# ib_atomic_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00f3 PSN 0xea1696
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00f4 PSN 0xebef2f
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.999000 != 3053.673000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2600.091000 != 1000.021000. CPU Frequency is not max.
 8       1000          1.44           3.92         1.46     	       1.46        	0.02   		1.52    		3.92   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_atomic_lat -d mlx5_0 -zR -D 300
root@gpu1:~# ib_atomic_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0134 PSN 0xbd7ab6
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x0135 PSN 0x1a2a8f
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 936.962000 != 1685.107000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 899.979000 != 989.906000. CPU Frequency is not max.
 8             69732891            2.15           464864.75
---------------------------------------------------------------------------------------
```



###### ib_send_bw

```text
root@cpu1:~# ib_send_bw -d mlx5_0 -zR
root@cpu1:~# ib_send_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00f7 PSN 0x656a40
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00f8 PSN 0xb01839
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 999.999000 != 2836.723000. CPU Frequency is not max.
 65536      1000             11593.84            11593.58		   0.185497
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_send_bw -d mlx5_0 -zR -D 300
root@gpu1:~# ib_send_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x010f PSN 0xa5954b
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x0110 PSN 0xb0859
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 817.886000 != 799.922000. CPU Frequency is not max.
 65536      24738300         0.00               10306.79		   0.164909
---------------------------------------------------------------------------------------
```

> 当客户端有-D参数时，服务器端需要增加-D参数

###### ib_send_lat

```text
root@cpu1:~# ib_send_lat -d mlx5_0 -zR
root@cpu1:~# ib_send_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00fb PSN 0x671723
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
 remote address: LID 0000 QPN 0x00fc PSN 0x671fae
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.999000 != 1025.401000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 999.998000 != 1028.091000. CPU Frequency is not max.
 2       1000          0.82           1.01         0.88     	       0.88        	0.02   		0.94    		1.01   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_send_lat -d mlx5_0 -zR -D 300
root@gpu1:~# ib_send_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0107 PSN 0xed0f77
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
 remote address: LID 0000 QPN 0x0108 PSN 0xdbebb6
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 1032.071000 != 1131.428000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1855.620000 != 899.288000. CPU Frequency is not max.
 2             55356678            1.35           369020.18
---------------------------------------------------------------------------------------
```

> 当客户端有-D参数时，服务器端需要增加-D参数

##### 整理结果

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 1000        | 8354.37         | 8354.22            | 0.133667      |
| ib_write_bw  | 65536  | 5000        | 11660.36        | 11660.12           | 0.186562      |
| ib_atomic_bw | 8      | 1000        | 16.29           | 16.25              | 2.129385      |
| ib_send_bw   | 65536  | 1000        | 11593.84        | 11593.58           | 0.185497      |

|               | #bytes | #iterations | t_min[usec] | t_max[usec] | t_typical[usec] | t_avg[usec] | t_stdev[usec] | 99% percentile[usec] | 99.9% percentile[usec] |
| ------------- | ------ | ----------- | ----------- | ----------- | --------------- | ----------- | ------------- | -------------------- | ---------------------- |
| ib_read_lat   | 2      | 1000        | 1.44        | 2.93        | 1.48            | 1.49        | 0.02          | 1.56                 | 2.93                   |
| ib_write_lat  | 2      | 1000        | 0.76        | 0.95        | 0.78            | 0.78        | 0.01          | 0.83                 | 0.95                   |
| ib_atomic_lat | 8      | 1000        | 1.44        | 3.92        | 1.46            | 1.46        | 0.02          | 1.52                 | 3.92                   |
| ib_send_lat   | 2      | 1000        | 0.82        | 1.01        | 0.88            | 0.88        | 0.02          | 0.94                 | 1.01                   |

增加`-D 300`参数以后，重新测试

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 20506500    | 0.00            | 8543.45            | 0.136695      |
| ib_write_bw  | 65536  | 24777100    | 0.00            | 10322.23           | 0.165156      |
| ib_atomic_bw | 8      | 210853400   | 0.00            | 10.72              | 1.405510      |
| ib_send_bw   | 65536  | 24738300    | 0.00            | 10306.79           | 0.164909      |


|               | #bytes | #iterations | t_avg[usec] | tps average |
| ------------- | ------ | ----------- | ----------- | ----------- |
| ib_read_lat   | 2      | 62078352    | 2.42        | 413812.77   |
| ib_write_lat  | 2      | 58732912    | 1.28        | 391518.70   |
| ib_atomic_lat | 8      | 69732891    | 2.15        | 464864.75   |
| ib_send_lat   | 2      | 55356678    | 1.35        | 369020.18   |

#### 在不同节点，进行IB网络测试

##### 测试结果

###### ib_read_bw

```text
root@cpu1:~# ib_read_bw -d mlx5_0 -zR
root@cpu3:~# ib_read_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d1 PSN 0x3f8228
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x00fe PSN 0xeb8e18
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1001.724000 != 2468.931000. CPU Frequency is not max.
 65536      1000             10182.70            24.95  		   0.000399
---------------------------------------------------------------------------------------
```

```text
root@cpu1:~# ib_read_bw -d mlx5_0 -zR -D 300
root@gpu2:~# ib_read_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d8 PSN 0xdaecd3
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x013b PSN 0xf8255d
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 800.224000 != 881.536000. CPU Frequency is not max.
 65536      23147000         0.00               9641.89		   0.154270
---------------------------------------------------------------------------------------
```



###### ib_read_lat

```text
root@cpu1:~# ib_read_lat -d mlx5_0 -zR
root@cpu3:~# ib_read_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d3 PSN 0xdebec1
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x0100 PSN 0xc66982
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.999000 != 2902.402000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.001000 != 3088.637000. CPU Frequency is not max.
 2       1000          2.36           5.23         2.40     	       2.41        	0.03   		2.53    		5.23   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_read_lat -d mlx5_0 -zR -D 300
root@gpu2:~# ib_read_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00da PSN 0xceb44d
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x013d PSN 0x6fd204
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 800.033000 != 846.381000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 800.059000 != 880.590000. CPU Frequency is not max.
 2             46543043            3.22           310266.84
---------------------------------------------------------------------------------------
```



###### ib_write_bw

```text
root@cpu1:~# ib_write_bw -d mlx5_0 -zR
root@cpu3:~# ib_write_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d5 PSN 0x8fda20
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x0102 PSN 0x91c3a3
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.148000 != 2469.764000. CPU Frequency is not max.
 65536      5000             11023.87            11023.48		   0.176376
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_write_bw -d mlx5_0 -zR -D 300
root@gpu2:~# ib_write_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00dc PSN 0x2b192
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x0140 PSN 0xee6a60
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2263.919000 != 800.202000. CPU Frequency is not max.
 65536      24558600         0.00               10231.95		   0.163711
---------------------------------------------------------------------------------------
```



###### ib_write_lat

```text
root@cpu1:~# ib_write_lat -d mlx5_0 -zR
root@cpu3:~# ib_write_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d7 PSN 0x3eb300
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x0104 PSN 0xd33261
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.991000 != 2990.938000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.032000 != 3288.195000. CPU Frequency is not max.
 2       1000          1.24           3.11         1.26     	       1.26        	0.02   		1.29    		3.11   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_write_lat -d mlx5_0 -zR -D 300
root@gpu2:~# ib_write_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00ce PSN 0xc841f4
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x00f6 PSN 0xb596a2
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 1729.519000 != 800.121000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 813.112000 != 955.648000. CPU Frequency is not max.
 2             45001924            1.67           300009.90
---------------------------------------------------------------------------------------

```

> ib_write_lat 如果客户端加了-D参数，服务端也必须加-D参数。否则，服务端会很快退出，然后客户端也会跟着结束。

###### ib_atomic_bw

```text
root@cpu1:~# ib_atomic_bw -d mlx5_0 -zR
root@cpu3:~# ib_atomic_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d9 PSN 0x87a054
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x0106 PSN 0x2f60b4
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.005000 != 2812.017000. CPU Frequency is not max.
 8          1000             16.59              16.53  		   2.166391
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_atomic_bw -d mlx5_0 -zR -D 300
root@gpu2:~# ib_atomic_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00de PSN 0x3890ce
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x0142 PSN 0xbbda5c
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2317.936000 != 800.137000. CPU Frequency is not max.
 8          211557600        0.00               10.76  		   1.410197
---------------------------------------------------------------------------------------
```



###### ib_atomic_lat

```text
root@cpu1:~# ib_atomic_lat -d mlx5_0 -zR
root@cpu3:~# ib_atomic_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00db PSN 0x748be2
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x0108 PSN 0x1dfbb6
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1000.007000 != 2955.999000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.005000 != 3236.512000. CPU Frequency is not max.
 8       1000          2.28           4.93         2.32     	       2.32        	0.02   		2.40    		4.93   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_atomic_lat -d mlx5_0 -zR -D 300
root@gpu2:~# ib_atomic_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00e0 PSN 0x3afbea
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x0144 PSN 0x63f59
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 800.096000 != 826.626000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1629.088000 != 800.042000. CPU Frequency is not max.
 8             50379762            2.98           335853.20
---------------------------------------------------------------------------------------
```



###### ib_send_bw

```text
root@cpu1:~# ib_send_bw -d mlx5_0 -zR
root@cpu3:~# ib_send_bw -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00dd PSN 0xd0c16c
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x010a PSN 0xf20dff
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 1000.040000 != 2862.691000. CPU Frequency is not max.
 65536      1000             10988.09            10987.52		   0.175800
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_send_bw -d mlx5_0 -zR -D 300
root@gpu2:~# ib_send_bw -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d4 PSN 0x85b276
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x010c PSN 0xf824d4
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 802.604000 != 879.872000. CPU Frequency is not max.
 65536      24530500         0.00               10220.23		   0.163524
---------------------------------------------------------------------------------------

```

> 当客户端有-D参数时，服务器端需要增加-D参数

###### ib_send_lat

```text
root@cpu1:~# ib_send_lat -d mlx5_0 -zR
root@cpu3:~# ib_send_lat -d mlx5_0 10.0.32.34 -zR
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00df PSN 0xc6bd6e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:34:02
 remote address: LID 0000 QPN 0x010c PSN 0x8c5534
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:32:34
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 999.999000 != 2803.887000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1000.004000 != 3077.021000. CPU Frequency is not max.
 2       1000          1.29           4.08         1.34     	       1.34        	0.02   		1.39    		4.08   
---------------------------------------------------------------------------------------
```

```text
root@gpu1:~# ib_send_lat -d mlx5_0 -zR -D 300
root@gpu2:~# ib_send_lat -d mlx5_0 10.0.13.2 -zR -D 300
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x00d2 PSN 0xf1b259
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:02
 remote address: LID 0000 QPN 0x010a PSN 0xdf78c5
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:02
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 2087.104000 != 800.133000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2051.661000 != 804.187000. CPU Frequency is not max.
 2             42056694            1.78           280352.18
---------------------------------------------------------------------------------------
```

> 当客户端有-D参数时，服务器端需要增加-D参数

##### 整理结果

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 1000        | 10182.70        | 24.95              | 0.000399      |
| ib_write_bw  | 65536  | 5000        | 11023.87        | 11023.48           | 0.176376      |
| ib_atomic_bw | 8      | 1000        | 16.59           | 16.53              | 2.166391      |
| ib_send_bw   | 65536  | 1000        | 10988.09        | 10987.52           | 0.175800      |

|               | #bytes | #iterations | t_min[usec] | t_max[usec] | t_typical[usec] | t_avg[usec] | t_stdev[usec] | 99% percentile[usec] | 99.9% percentile[usec] |
| ------------- | ------ | ----------- | ----------- | ----------- | --------------- | ----------- | ------------- | -------------------- | ---------------------- |
| ib_read_lat   | 2      | 1000        | 2.36        | 5.23        | 2.40            | 2.41        | 0.03          | 2.53                 | 5.23                   |
| ib_write_lat  | 2      | 1000        | 1.24        | 3.11        | 1.26            | 1.26        | 0.02          | 1.29                 | 3.11                   |
| ib_atomic_lat | 8      | 1000        | 2.28        | 4.93        | 2.32            | 2.32        | 0.02          | 2.40                 | 4.93                   |
| ib_send_lat   | 2      | 1000        | 1.29        | 4.08        | 1.34            | 1.34        | 0.02          | 1.39                 | 4.08                   |

增加`-D 300`参数以后，重新测试

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 23147000    | 0.00            | 9641.89            | 0.154270      |
| ib_write_bw  | 65536  | 24558600    | 0.00            | 10231.95           | 0.163711      |
| ib_atomic_bw | 8      | 211557600   | 0.00            | 10.76              | 1.410197      |
| ib_send_bw   | 65536  | 24530500    | 0.00            | 10220.23           | 0.163524      |

|               | #bytes | #iterations | t_avg[usec] | tps average |
| ------------- | ------ | ----------- | ----------- | ----------- |
| ib_read_lat   | 2      | 46543043    | 3.22        | 310266.84   |
| ib_write_lat  | 2      | 45001924    | 1.67        | 300009.90   |
| ib_atomic_lat | 8      | 50379762    | 2.98        | 335853.20   |
| ib_send_lat   | 2      | 42056694    | 1.78        | 280352.18   |

## Sriov 容器网络测试

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

### 使用 `mofed_benchmark` 创建测试用pod

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
    image: "172.16.0.3:5000/asdfsx/mofed_benchmark:centos7.5"
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    resources:
      limits:
        rdma/vhca: 1
    stdin: true
    tty: true
    securityContext:
      capabilities:
        add: ["SYS_RESOURCE"]
  tolerations:
  - effect: NoSchedule
    key: nvidia.com/gpu
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
    image: "172.16.0.3:5000/asdfsx/mofed_benchmark:centos7.5"
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    resources:
      limits:
        rdma/vhca: 1
    stdin: true
    tty: true
    securityContext:
      capabilities:
        add: ["SYS_RESOURCE"]
  tolerations:
  - effect: NoSchedule
    key: nvidia.com/gpu
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
    image: "172.16.0.3:5000/asdfsx/mofed_benchmark:centos7.5"
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    resources:
      limits:
        rdma/vhca: 1
    stdin: true
    tty: true
    securityContext:
      capabilities:
        add: ["SYS_RESOURCE"]
  tolerations:
  - effect: NoSchedule
    key: nvidia.com/gpu
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
    image: "172.16.0.3:5000/asdfsx/mofed_benchmark:centos7.5"
    command: ["/bin/bash", "-c", "sleep 2000000000000"]
    resources:
      limits:
        rdma/vhca: 1
    stdin: true
    tty: true
    securityContext:
      capabilities:
        add: ["SYS_RESOURCE"]
  tolerations:
  - effect: NoSchedule
    key: nvidia.com/gpu
```

查看创建的pod

```text
$ kubectl get pod -o wide
NAME             READY     STATUS    RESTARTS   AGE       IP           NODE      NOMINATED NODE
iperf-client-1   1/1       Running   0          22m       10.244.0.6   cpu1      <none>
iperf-client-2   1/1       Running   0          22m       10.244.0.8   cpu1      <none>
iperf-client-3   1/1       Running   0          22m       10.244.0.7   cpu1      <none>
iperf-server     1/1       Running   0          22m       10.244.0.5   cpu1      <none>
```

### 使用iperf进行ip网络测试

#### 在sriov网卡上启动iperf server

```text
# 查看网卡
$ kubectl exec -it iperf-server ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
3: eth0@if112: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default 
    link/ether 0a:58:0a:f4:01:03 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.244.1.3/24 scope global eth0
       valid_lft forever preferred_lft forever
94: net1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 92:62:be:be:70:95 brd ff:ff:ff:ff:ff:ff
    inet 10.0.34.3/24 brd 10.0.34.255 scope global net1
       valid_lft forever preferred_lft forever

# 在sriov网卡上启动iperf server
$ kubectl exec -it iperf-server -- /usr/bin/iperf3 --bind 10.0.34.3 -s
```

#### 选取同一个node上的pod，进行ip网络测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-2 -- /usr/bin/iperf3 -c 10.0.34.3
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  18.5 GBytes  15.9 Gbits/sec  3535             sender
[  4]   0.00-10.00  sec  18.5 GBytes  15.9 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-2 -- /usr/bin/iperf3 -c 10.0.34.3 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  7.14 GBytes  6.13 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  7.13 GBytes  6.13 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  7.12 GBytes  6.12 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  7.11 GBytes  6.11 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  7.13 GBytes  6.12 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  7.12 GBytes  6.12 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  7.12 GBytes  6.12 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  7.11 GBytes  6.11 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  28.5 GBytes  24.5 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  28.5 GBytes  24.5 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-2 -- /usr/bin/iperf3 -u -c 10.0.34.3
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.013 ms  0/897 (0%)  
[  4] Sent 897 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-2 -- /usr/bin/iperf3 -u -c 10.0.34.3 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.013 ms  0/897 (0%)  
[  4] Sent 897 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.014 ms  0/897 (0%)  
[  6] Sent 897 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.012 ms  0/897 (0%)  
[  8] Sent 897 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.017 ms  0/897 (0%)  
[ 10] Sent 897 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.16 Mbits/sec  0.014 ms  0/3588 (0%)  

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-2 -- /usr/bin/iperf3 -u -c 10.0.34.3 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  4.60 GBytes  3.95 Gbits/sec  0.001 ms  1864056/3412029 (55%)  
[  4] Sent 3412029 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-2 -- /usr/bin/iperf3 -u -c 10.0.34.3 -P 4 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.59 GBytes  1.37 Gbits/sec  0.009 ms  322919/1181411 (27%)  
[  4] Sent 1181411 datagrams
[  6]   0.00-10.00  sec  1.59 GBytes  1.37 Gbits/sec  0.008 ms  323049/1181410 (27%)  
[  6] Sent 1181410 datagrams
[  8]   0.00-10.00  sec  1.59 GBytes  1.37 Gbits/sec  0.007 ms  320616/1181407 (27%)  
[  8] Sent 1181407 datagrams
[ 10]   0.00-10.00  sec  1.59 GBytes  1.37 Gbits/sec  0.006 ms  307320/1181441 (26%)  
[ 10] Sent 1181441 datagrams
[SUM]   0.00-10.00  sec  6.37 GBytes  5.47 Gbits/sec  0.008 ms  1273904/4725669 (27%)  
```

#### 选取不同node上的pod，进行ip网络测试

```text
# 单线程测试tcp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.0.34.3
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  23.2 GBytes  20.0 Gbits/sec  825             sender
[  4]   0.00-10.00  sec  23.2 GBytes  20.0 Gbits/sec                  receiver

# 多线程测试tcp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -c 10.0.34.3 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Retr
[  4]   0.00-10.00  sec  7.70 GBytes  6.61 Gbits/sec    0             sender
[  4]   0.00-10.00  sec  7.69 GBytes  6.61 Gbits/sec                  receiver
[  6]   0.00-10.00  sec  7.70 GBytes  6.61 Gbits/sec    0             sender
[  6]   0.00-10.00  sec  7.69 GBytes  6.61 Gbits/sec                  receiver
[  8]   0.00-10.00  sec  7.70 GBytes  6.61 Gbits/sec    0             sender
[  8]   0.00-10.00  sec  7.69 GBytes  6.61 Gbits/sec                  receiver
[ 10]   0.00-10.00  sec  7.69 GBytes  6.61 Gbits/sec    0             sender
[ 10]   0.00-10.00  sec  7.69 GBytes  6.60 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  30.8 GBytes  26.4 Gbits/sec    0             sender
[SUM]   0.00-10.00  sec  30.8 GBytes  26.4 Gbits/sec                  receiver

# 单线程测试udp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.34.3
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.006 ms  0/897 (0%)  
[  4] Sent 897 datagrams

# 多线程测试udp
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.34.3 -P 4
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.007 ms  0/897 (0%)  
[  4] Sent 897 datagrams
[  6]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.006 ms  0/897 (0%)  
[  6] Sent 897 datagrams
[  8]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.008 ms  0/897 (0%)  
[  8] Sent 897 datagrams
[ 10]   0.00-10.00  sec  1.24 MBytes  1.04 Mbits/sec  0.007 ms  0/897 (0%)  
[ 10] Sent 897 datagrams
[SUM]   0.00-10.00  sec  4.95 MBytes  4.16 Mbits/sec  0.007 ms  0/3588 (0%)   

# 单线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.34.3 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  5.38 GBytes  4.62 Gbits/sec  0.003 ms  1146797/3988591 (29%)  
[  4] Sent 3988591 datagrams

# 多线程测试udp，增加带宽参数
$ kubectl exec -it iperf-client-3 -- /usr/bin/iperf3 -u -c 10.0.34.3 -P 4 -b 100G
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bandwidth       Jitter    Lost/Total Datagrams
[  4]   0.00-10.00  sec  1.42 GBytes  1.22 Gbits/sec  0.002 ms  167751/1052153 (16%)  
[  4] Sent 1052153 datagrams
[  6]   0.00-10.00  sec  1.42 GBytes  1.22 Gbits/sec  0.002 ms  178060/1052124 (17%)  
[  6] Sent 1052124 datagrams
[  8]   0.00-10.00  sec  1.42 GBytes  1.22 Gbits/sec  0.002 ms  167951/1052153 (16%)  
[  8] Sent 1052153 datagrams
[ 10]   0.00-10.00  sec  1.42 GBytes  1.22 Gbits/sec  0.008 ms  168101/1052153 (16%)  
[ 10] Sent 1052153 datagrams
[SUM]   0.00-10.00  sec  5.68 GBytes  4.88 Gbits/sec  0.004 ms  681863/4208583 (16%) 
```

#### 整理结果

| 测试名称                     | Transfer    | Bandwidth      | Retr | Jitter   | Lost/Total Datagrams  |
| ---------------------------- | ----------- | -------------- | ---- | -------- | --------------------- |
| TCP同节点pod单线程           | 18.5 GBytes | 15.9 Gbits/sec | 3535 |          |                       |
| TCP不同节点pod单线程         | 23.2 GBytes | 20.0 Gbits/sec | 825  |          |                       |
| TCP同节点pod4线程            | 28.5 GBytes | 24.5 Gbits/sec | 0    |          |                       |
| TCP不同节点pod4线程          | 30.8 GBytes | 26.4 Gbits/sec | 0    |          |                       |
| UDP同节点pod单线程           | 1.24 MBytes | 1.04 Mbits/sec |      | 0.013 ms | 0/897(0%)             |
| UDP不同节点pod单线程         | 1.24 MBytes | 1.04 Mbits/sec |      | 0.006 ms | 0/897 (0%)            |
| UDP同节点pod4线程            | 4.95 MBytes | 4.16 Mbits/sec |      | 0.014 ms | 0/3588 (0%)           |
| UDP不同节点pod4线程          | 4.95 MBytes | 4.16 Mbits/sec |      | 0.007 ms | 0/3588 (0%)           |
| UDP同节点pod单线程100G带宽   | 4.60 GBytes | 3.95 Gbits/sec |      | 0.001 ms | 1864056/3412029 (55%) |
| UDP不同节点pod单线程100G带宽 | 5.38 GBytes | 4.62 Gbits/sec |      | 0.003 ms | 1146797/3988591 (29%) |
| UDP同节点pod4线程100G带宽    | 6.37 GBytes | 5.47 Gbits/sec |      | 0.008 ms | 1273904/4725669 (27%) |
| UDP不同节点pod4线程100G带宽  | 5.68 GBytes | 4.88 Gbits/sec |      | 0.004 ms | 681863/4208583 (16%)  |

### 使用perftest进行ib网络测试

#### RDMA 连通性测试

```text
# 查看iperf-server的ip地址
$ kubectl exec -it iperf-server -- ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
3: eth0@if121: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default 
    link/ether 0a:58:0a:f4:00:30 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.244.0.48/24 scope global eth0
       valid_lft forever preferred_lft forever
57: net1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether f2:db:76:88:fe:d9 brd ff:ff:ff:ff:ff:ff
    inet 10.0.13.6/24 brd 10.0.13.255 scope global net1
       valid_lft forever preferred_lft forever

# 在iperf-server上创建server端
$ kubectl exec -it iperf-server -- rdma_server

# 在iperf-client-1上执行
$ kubectl exec -it iperf-client-1 -- rdma_client -s 10.0.13.6
rdma_client: start
rdma_client: end 0
```

#### 测试之前先选择已经active的网卡

```text
$ kubectl exec -it iperf-server -- ibv_devices
device          	   node GUID
------          	----------------
mlx5_18         	de5eaefffea1e7ee
mlx5_6          	52fec4fffed527ef
mlx5_28         	723ce5fffe41e757
mlx5_8          	1e47bbfffebd4d6c
mlx5_11         	aa4d6cfffeb867e9
mlx5_21         	329e24fffe99788b
mlx5_31         	de28e7fffef318e2
mlx5_13         	cefb5bfffe91fa1a
mlx5_1          	9262befffebe7095
mlx5_23         	429a70fffe6d3801
mlx5_15         	0e4a3afffe2e8154
mlx5_3          	c23ce4fffe058709
mlx5_25         	4afde7fffee09b7f
mlx5_17         	06dd39fffe6dfc06
mlx5_5          	ce737ffffe7d7a14
......

$ kubectl exec -it iperf-server -- ibv_devinfo -d mlx5_18
hca_id:	mlx5_0
        transport:          InfiniBand (0)
        fw_ver:             16.23.1020
        node_guid:          506b:4b03:0028:4dec
        sys_image_guid:     506b:4b03:0028:4dec
        vendor_id:          0x02c9
        vendor_part_id:     4119
        hw_ver:             0x0
        board_id:           MT_0000000011
        phys_port_cnt:      1
        Device ports:
                port:   1
                        state:          PORT_ACTIVE (4)
                        max_mtu:        4096 (5)
                        active_mtu:     1024 (3)
                        sm_lid:         0
                        port_lid:       0
                        port_lmc:       0x00
                        link_layer:     Ethernet

$ kubectl exec -it iperf-server -- ibstat mlx5_0
CA 'mlx5_0'
        CA type: MT4119
        Number of ports: 1
        Firmware version: 16.23.1020
        Hardware version: 0
        Node GUID: 0x506b4b0300284dec
        System image GUID: 0x506b4b0300284dec
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

#### 测试方法

1. 进入pod

   ```text
   $ kubectl exec -it iperf-server -- /bin/bash
   $ kubectl exec -it iperf-client-2 -- /bin/bash
   ```

2. 修改容器内的ulimit

   ```text
   # 在iperf-server中
   [root@iperf-server tmp]# ulimit -l unlimited
   
   # 在iperf-client-2中
   [root@iperf-client-2 tmp]# ulimit -l unlimited
   ```

   > 注意，如果不执行ulimit命令，会报错`Couldn't allocate MR`。应该是容器默认的内存太小，无法创建IB客户端

3. 执行测试

####选取同一个node上的pod，进行 ib 网络测试 

##### 测试结果

###### ib_read_bw

```text
[root@iperf-server tmp]# ib_read_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_read_bw -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0aae PSN 0x1b51dc
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04a9 PSN 0x9110c8
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2101.482000 != 848.828000. CPU Frequency is not max.
 65536      1000             8809.91            8646.57		   0.138345
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_read_bw -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_read_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02a1 PSN 0x6bf62e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0ca2 PSN 0xb3188e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 801.956000 != 1472.899000. CPU Frequency is not max.
 65536      20503100         0.00               8542.27		   0.136676
---------------------------------------------------------------------------------------
```



###### ib_read_lat

```text
[root@iperf-server tmp]# ib_read_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_read_lat -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab0 PSN 0x857801
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04ab PSN 0xee41e7
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1176.065000 != 1008.476000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1060.100000 != 958.747000. CPU Frequency is not max.
 2       1000          3.33           7.74         3.40     	       3.42        	0.08   		3.73    		7.74   
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_read_lat -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_read_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02a3 PSN 0x944d3e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0ca7 PSN 0x26812e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 819.058000 != 868.717000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 800.281000 != 2880.180000. CPU Frequency is not max.
 2             47819004            3.14           318773.56
---------------------------------------------------------------------------------------
```



###### ib_write_bw

```text
[root@iperf-server tmp]# ib_write_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_write_bw -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab2 PSN 0xc09739
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04ad PSN 0x7ba3ca
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 981.234000 != 897.838000. CPU Frequency is not max.
 65536      5000             10228.95            10228.64		   0.163658
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_write_bw -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_write_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02a5 PSN 0xc55089
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0cab PSN 0xc74e44
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2800.947000 != 800.863000. CPU Frequency is not max.
 65536      24252600         0.00               10104.07		   0.161665
---------------------------------------------------------------------------------------
```



###### ib_write_lat

```text
[root@iperf-server tmp]# ib_write_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_write_lat -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab4 PSN 0x2419
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04af PSN 0xa509fe
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1103.368000 != 941.582000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 833.333000 != 2702.517000. CPU Frequency is not max.
 2       1000          1.81           3.90         1.85     	       1.85        	0.02   		1.94    		3.90   
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_write_lat -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_write_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02a7 PSN 0x6b4ffa
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0cb5 PSN 0x861cd6
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 817.911000 != 2529.545000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2352.465000 != 1887.515000. CPU Frequency is not max.
 2             39634703            1.89           264054.03
---------------------------------------------------------------------------------------
```



###### ib_atomic_bw

```tezt
[root@iperf-server tmp]# ib_atomic_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_atomic_bw -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab6 PSN 0xc2fd1e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04b1 PSN 0xe4a863
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 936.912000 != 983.528000. CPU Frequency is not max.
 8          1000             10.23              10.22  		   1.339122
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_atomic_bw -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_atomic_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02a9 PSN 0xd95fe4
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0cb9 PSN 0xeed4df
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2560.433000 != 799.678000. CPU Frequency is not max.
 8          209883500        0.00               10.67  		   1.398963
---------------------------------------------------------------------------------------
```



###### ib_atomic_lat

```text
[root@iperf-server tmp]# ib_atomic_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_atomic_lat -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab8 PSN 0x4f76c9
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04b3 PSN 0xc71b67
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 925.103000 != 1046.531000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 924.943000 != 952.562000. CPU Frequency is not max.
 8       1000          2.81           7.39         2.86     	       2.87        	0.03   		2.98    		7.39   
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_atomic_lat -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_atomic_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02ab PSN 0x128b2
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0cbd PSN 0x81a14e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 829.997000 != 800.062000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2597.427000 != 1081.824000. CPU Frequency is not max.
 8             52451594            2.86           349666.51
---------------------------------------------------------------------------------------
```



###### ib_send_bw

```text
[root@iperf-server tmp]# ib_send_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_send_bw -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0aba PSN 0x80923
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04b5 PSN 0x1f90d4
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 918.161000 != 846.210000. CPU Frequency is not max.
 65536      1000             10936.79            10936.75		   0.174988
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_send_bw -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_send_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02ad PSN 0x21ffc9
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0d81 PSN 0x60d339
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 837.254000 != 894.035000. CPU Frequency is not max.
 65536      23212900         0.00               9671.29		   0.154741
---------------------------------------------------------------------------------------
```



###### ib_send_lat

```text
[root@iperf-server tmp]# ib_send_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_send_lat -d mlx5_0 10.0.13.4 -zR
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0abc PSN 0xdca6e2
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:34
 remote address: LID 0000 QPN 0x04b7 PSN 0xe478fa
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:13:04
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 1136.065000 != 826.000000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 921.147000 != 826.262000. CPU Frequency is not max.
 2       1000          1.87           4.31         1.92     	       1.93        	0.04   		2.07    		4.31   
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_send_lat -d mlx5_0 -zR -D 300
[root@iperf-client-2 tmp]# ib_send_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x02af PSN 0xb8c7c6
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:36
 remote address: LID 0000 QPN 0x0d85 PSN 0x4d7bfe
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 835.643000 != 2204.104000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 800.020000 != 2033.016000. CPU Frequency is not max.
 2             35945839            2.09           239632.64
---------------------------------------------------------------------------------------
```



##### 整理结果

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 1000        | 8809.91         | 8646.57            | 0.138345      |
| ib_write_bw  | 65536  | 5000        | 10228.95        | 10228.64           | 0.163658      |
| ib_atomic_bw | 8      | 1000        | 10.23           | 10.22              | 1.339122      |
| ib_send_bw   | 65536  | 1000        | 10936.79        | 10936.75           | 0.174988      |

|               | #bytes | #iterations | t_min[usec] | t_max[usec] | t_typical[usec] | t_avg[usec] | t_stdev[usec] | 99% percentile[usec] | 99.9% percentile[usec] |
| ------------- | ------ | ----------- | ----------- | ----------- | --------------- | ----------- | ------------- | -------------------- | ---------------------- |
| ib_read_lat   | 2      | 1000        | 3.33        | 7.74        | 3.40            | 3.42        | 0.08          | 3.73                 | 7.74                   |
| ib_write_lat  | 2      | 1000        | 1.81        | 3.90        | 1.85            | 1.85        | 0.02          | 1.94                 | 3.90                   |
| ib_atomic_lat | 8      | 1000        | 2.81        | 7.39        | 2.86            | 2.87        | 0.03          | 2.98                 | 7.39                   |
| ib_send_lat   | 2      | 1000        | 1.87        | 4.31        | 1.92            | 1.93        | 0.04          | 2.07                 | 4.31                   |

增加`-D 300`参数以后，重新测试

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 20503100    | 0.00            | 8542.27            | 0.136676      |
| ib_write_bw  | 65536  | 24252600    | 0.00            | 10104.07           | 0.161665      |
| ib_atomic_bw | 8      | 209883500   | 0.00            | 10.67              | 1.398963      |
| ib_send_bw   | 65536  | 23212900    | 0.00            | 9671.29            | 0.154741      |

|               | #bytes | #iterations | t_avg[usec] | tps average |
| ------------- | ------ | ----------- | ----------- | ----------- |
| ib_read_lat   | 2      | 47819004    | 3.14        | 318773.56   |
| ib_write_lat  | 2      | 39634703    | 1.89        | 264054.03   |
| ib_atomic_lat | 8      | 52451594    | 2.86        | 349666.51   |
| ib_send_lat   | 2      | 35945839    | 2.09        | 239632.64   |

#### 选取不同node上的pod，进行 ib 网络测试

##### 测试结果

###### ib_read_bw

```text
[root@iperf-server tmp]# ib_read_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_read_bw -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ca3 PSN 0x92ab5
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04a1 PSN 0x5d0d10
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 800.557000 != 920.583000. CPU Frequency is not max.
 65536      1000             10396.69            10381.74		   0.166108
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_read_bw -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_read_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0aa2 PSN 0x8a5bc6
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0ca5 PSN 0xe05101
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 831.523000 != 800.054000. CPU Frequency is not max.
 65536      12996000         0.00               5414.28		   0.086628
---------------------------------------------------------------------------------------
```



###### ib_read_lat

```text
[root@iperf-server tmp]# ib_read_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_read_lat -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ca5 PSN 0x42e033
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04a3 PSN 0xc3bda9
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 800.319000 != 974.705000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 800.012000 != 918.786000. CPU Frequency is not max.
 2       1000          4.23           15.28        4.31     	       4.37        	0.58   		4.64    		15.28  
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_read_lat -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_read_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Read Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0aa4 PSN 0xe8034a
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0ca9 PSN 0x2f4d0a
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 1067.411000 != 885.943000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2366.047000 != 800.176000. CPU Frequency is not max.
 2             39230260            3.82           261521.01
---------------------------------------------------------------------------------------
```



###### ib_write_bw

```text
[root@iperf-server tmp]# ib_write_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_write_bw -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ca7 PSN 0xb873de
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04a5 PSN 0x319dca
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 800.673000 != 816.849000. CPU Frequency is not max.
 65536      5000             10367.47            10344.93		   0.165519
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_write_bw -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_write_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0aad PSN 0xce9800
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0cb3 PSN 0x784d50
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2146.169000 != 799.770000. CPU Frequency is not max.
 65536      24701400         0.00               10290.36		   0.164646
---------------------------------------------------------------------------------------
```



###### ib_write_lat

```text
[root@iperf-server tmp]# ib_write_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_write_lat -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ca9 PSN 0xd31d65
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04a7 PSN 0x5f125e
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 809.967000 != 870.275000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 800.013000 != 888.407000. CPU Frequency is not max.
 2       1000          2.78           9.08         2.81     	       2.83        	0.13   		2.99    		9.08   
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_write_lat -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_write_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    RDMA_Write Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 220[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0aaf PSN 0x159913
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0cb7 PSN 0xfa0e1c
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 834.463000 != 800.181000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 799.827000 != 921.444000. CPU Frequency is not max.
 2             32598482            2.30           217316.73
---------------------------------------------------------------------------------------
```



###### ib_atomic_bw

```text
[root@iperf-server tmp]# ib_atomic_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_atomic_bw -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0cab PSN 0x91b362
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04a9 PSN 0x8c6808
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 800.036000 != 841.891000. CPU Frequency is not max.
 8          1000             10.29              10.27  		   1.345677
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_atomic_bw -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_atomic_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab1 PSN 0x122770
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0cbb PSN 0x5f44f0
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 2358.117000 != 800.124000. CPU Frequency is not max.
 8          211566900        0.00               10.76  		   1.410300
---------------------------------------------------------------------------------------
```



###### ib_atomic_lat

```text
[root@iperf-server tmp]# ib_atomic_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_atomic_lat -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0cad PSN 0x39cbd1
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04ab PSN 0xc9734b
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 800.590000 != 853.354000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 800.068000 != 880.815000. CPU Frequency is not max.
 8       1000          4.07           15.64        4.14     	       4.18        	0.51   		4.43    		15.64  
---------------------------------------------------------------------------------------

```

```text
[root@iperf-server tmp]# ib_atomic_lat -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_atomic_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Atomic FETCH_AND_ADD Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Outstand reads  : 16
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab3 PSN 0x806cd3
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0cbf PSN 0x39a779
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 800.041000 != 860.108000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2007.275000 != 1007.828000. CPU Frequency is not max.
 8             40078627            3.74           267167.46
---------------------------------------------------------------------------------------
```



###### ib_send_bw

```text
[root@iperf-server tmp]# ib_send_bw -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_send_bw -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0caf PSN 0xf236e8
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04ad PSN 0xf236e8
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
Conflicting CPU frequency values detected: 801.300000 != 822.055000. CPU Frequency is not max.
 65536      1000             10345.08            10326.48		   0.165224
---------------------------------------------------------------------------------------
```

```text
[root@iperf-server tmp]# ib_send_bw -d mlx5_0 -zR -D 300
[root@iperf-client-3 tmp]# ib_send_bw -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 128
 CQ Moderation   : 100
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 0[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab5 PSN 0x468f4
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0d83 PSN 0x5d9a5d
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[MB/sec]    BW average[MB/sec]   MsgRate[Mpps]
操作Conflicting CPU frequency values detected: 2372.210000 != 799.748000. CPU Frequency is not max.
 65536      24622100         0.00               10257.24		   0.164116
---------------------------------------------------------------------------------------
```



###### ib_send_lat

```text
[root@iperf-server tmp]# ib_send_lat -d mlx5_0 -zR
[root@iperf-client-2 tmp]# ib_send_lat -d mlx5_0 10.0.17.28 -zR
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0cb1 PSN 0xc434fe
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:35
 remote address: LID 0000 QPN 0x04af PSN 0xc434fe
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:28
---------------------------------------------------------------------------------------
 #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] 
Conflicting CPU frequency values detected: 800.158000 != 826.897000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 1003.548000 != 1914.037000. CPU Frequency is not max.
 2       1000          2.50           17.59        2.63     	       2.68        	0.39   		2.96    		17.59  
---------------------------------------------------------------------------------------
```

```text
[root@iperf-client-3 tmp]# ib_send_lat -d mlx5_0 10.0.17.66 -zR -D 300
---------------------------------------------------------------------------------------
                    Send Latency Test
 Dual-port       : OFF		Device         : mlx5_0
 Number of qps   : 1		Transport type : IB
 Connection type : RC		Using SRQ      : OFF
 TX depth        : 1
 Mtu             : 1024[B]
 Link type       : Ethernet
 GID index       : 3
 Max inline data : 236[B]
 rdma_cm QPs	 : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x0ab7 PSN 0x4b3f06
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:15:65
 remote address: LID 0000 QPN 0x0d87 PSN 0x819a97
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:17:66
---------------------------------------------------------------------------------------
 #bytes        #iterations       t_avg[usec]    tps average
Conflicting CPU frequency values detected: 814.318000 != 871.977000. CPU Frequency is not max.
Conflicting CPU frequency values detected: 2560.997000 != 800.299000. CPU Frequency is not max.
 2             29176347            2.57           194503.83
---------------------------------------------------------------------------------------
```



##### 整理结果

|  | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| -- | -- | -- | -- | -- | -- |
|ib_read_bw | 65536 | 1000 | 10396.69 | 10381.74 | 0.166108 |
|ib_write_bw | 65536 | 5000 | 10367.47 | 10344.93 | 0.165519 |
|ib_atomic_bw | 8 | 1000 | 10.29 | 10.27 | 1.345677 |
|ib_send_bw | 65536 | 1000 | 10345.08 | 10326.48 | 0.165224 |

|  | #bytes | #iterations | t_min[usec] | t_max[usec] | t_typical[usec] | t_avg[usec] | t_stdev[usec] | 99% percentile[usec] | 99.9% percentile[usec] |
| -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
|ib_read_lat | 2 | 1000 | 4.23 | 15.28 | 4.31 | 4.37 | 0.58 | 4.64 | 15.28 |
|ib_write_lat | 2 | 1000 | 1.81 | 3.90 | 1.85 | 1.85 | 0.02 | 1.94 | 3.90 |
|ib_atomic_lat | 8 | 1000 | 4.07 | 15.64 | 4.14 | 4.18 | 0.51 | 4.43 | 15.64 |
|ib_send_lat | 2      | 1000 | 2.50 | 17.59 | 2.63 | 2.68 | 0.39 | 2.96 | 17.59 |

增加`-D 300`参数以后，重新测试

|              | #bytes | #iterations | BW peak[MB/sec] | BW average[MB/sec] | MsgRate[Mpps] |
| ------------ | ------ | ----------- | --------------- | ------------------ | ------------- |
| ib_read_bw   | 65536  | 12996000 | 0.00        | 5414.28     | 0.086628 |
| ib_write_bw  | 65536  | 24701400 | 0.00            | 10290.36   | 0.164646 |
| ib_atomic_bw | 8      | 211566900 | 0.00            | 10.76         | 1.410300 |
| ib_send_bw   | 65536  | 24622100 | 0.00            | 10257.24    | 0.164116 |

|               | #bytes | #iterations | t_avg[usec] | tps average |
| ------------- | ------ | ----------- | ----------- | ----------- |
| ib_read_lat   | 2      | 39230260 | 3.82    | 261521.01 |
| ib_write_lat  | 2      | 32598482 | 2.30    | 217316.73 |
| ib_atomic_lat | 8      | 40078627 | 3.74    | 267167.46 |
| ib_send_lat   | 2      | 29176347 | 2.57    | 194503.83 |

#### 

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
