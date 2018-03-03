# Logistic Regression with different optimizers

## Supported

* pure SGD 
* FTRL
* SVRG
* lr decay as a power of T
* Adagrad lr decay

## Some experimentts

### SVRG + Adagrad
```
train 0.182856555131 {'learning_rate': 24.58060463714603, 'reg': 0.0024110289048637663, 'batch_size': 15.69571664388355, 'num_iters': 7}
valid 0.248475317999 {'learning_rate': 19.548492473424346, 'reg': 0.0018083216621472909, 'batch_size': 79.90458994770898, 'num_iters': 8}
```

### Pure SGD experiment + simple lr decay (~1/\sqrt(T))
```
train 0.19461481173 {'learning_rate': 22.0328756510875, 'reg': 0.00159208361996218, 'batch_size': 40.06412292733098, 'num_iters': 7}
valid 0.250940052922 {'learning_rate': 17.256684748364172, 'reg': 0.0016659947616651735, 'batch_size': 94.11841328244267, 'num_iters': 8}
```

### Pure SGD + Adagrad
```
train 0.199344058438 {'learning_rate': 26.587770109022966, 'reg': 1.4967504367020084e-05, 'batch_size': 24.612144801176285, 'num_iters': 5}
valid 0.24853802224 {'learning_rate': 13.488020538963136, 'reg': 7.516195052601783e-06, 'batch_size': 43.66662938653907, 'num_iters': 6}
```
```
train 0.185811203781 {'learning_rate': 12.650360372465258, 'reg': 4.7497712866780325e-05, 'batch_size': 13.314338297612274, 'num_iters': 7}
valid 0.250754381187 {'learning_rate': 19.12598008841972, 'reg': 3.549997652388787e-05, 'batch_size': 80.8314387270132, 'num_iters': 6}
```

### FTRL + Adagrad
```
train 0.20843418382 {'learning_rate': 3.3469217648992484, 'num_iters': 8, 'reg': 4.6545277948415786e-08, 'batch_size': 15.956279146689095, 'l1': 4.87014500153922e-07}
valid 0.250808444235 {'learning_rate': 3.3469217648992484, 'num_iters': 8, 'reg': 4.6545277948415786e-08, 'batch_size': 15.956279146689095, 'l1': 4.87014500153922e-07}
```


