Async Server based on asyncore/asynchat (with epoll patch).


Load testing results:
ab -n 50000 -c 100 -r http://localhost:8080/

1) One worker
This is ApacheBench, Version 2.3 <$Revision: 1528965 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)


Server Software:        Blashyrkh
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        127 bytes

Concurrency Level:      100
Time taken for tests:   14.088 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      12700000 bytes
HTML transferred:       6350000 bytes
Requests per second:    3549.16 [#/sec] (mean)
Time per request:       28.176 [ms] (mean)
Time per request:       0.282 [ms] (mean, across all concurrent requests)
Transfer rate:          880.36 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       2
Processing:     1   28   2.6     27      37
Waiting:        1   28   2.6     27      37
Total:          2   28   2.6     27      37

Percentage of the requests served within a certain time (ms)
  50%     27
  66%     28
  75%     28
  80%     28
  90%     30
  95%     36
  98%     36
  99%     36
 100%     37 (longest request)


2) 4 workers
./httpd.py -r ./http-test-suite/ -p 8080 -w 4
This is ApacheBench, Version 2.3 <$Revision: 1528965 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)


Server Software:        Blashyrkh
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        127 bytes

Concurrency Level:      100
Time taken for tests:   7.575 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      12700000 bytes
HTML transferred:       6350000 bytes
Requests per second:    6600.53 [#/sec] (mean)
Time per request:       15.150 [ms] (mean)
Time per request:       0.152 [ms] (mean, across all concurrent requests)
Transfer rate:          1637.24 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.2      0       4
Processing:     0   15  24.4      1      76
Waiting:        0   15  24.4      1      76
Total:          0   15  24.4      1      76

Percentage of the requests served within a certain time (ms)
  50%      1
  66%      2
  75%     42
  80%     53
  90%     58
  95%     61
  98%     64
  99%     66
 100%     76 (longest request)


