# UUID performance comparison

Source: `5a8324a47a8410816aa4f12ec712ca7afeac05dc`.

Positive reduction means less time/CPU. Intervals bootstrap the paired process/repeat means
(5,000 resamples, exploratory 95%, no multiple-comparison correction). Inspect all cells
and scheduling overload flags; no saturation throughput or production claim.

| Microbenchmark | 0.6.0 ns | Candidate ns | Reduction % | 95% interval % |
|---|---:|---:|---:|---:|
| parse/candidate-batch | 155.9 | 113.6 | 27.2 | 25.4, 27.8 |
| v7/candidate/serialize | 1029.3 | 349.5 | 66.0 | 63.2, 66.2 |
| packed/candidate | 285.0 | 229.2 | 19.6 | 19.4, 20.4 |
| v7/candidate/format-generated | 443.0 | 267.4 | 39.6 | 38.8, 39.9 |
| format/candidate-UUID | 216.3 | 81.0 | 62.6 | 62.1, 63.2 |
| v7/candidate.native/serialize | 128.4 | 130.1 | -1.3 | -1.5, 0.9 |
| parse/candidate | 169.8 | 132.7 | 21.9 | 19.8, 22.8 |
| v7/candidate/direct-string | 108.2 | 112.6 | -4.1 | -6.3, -3.6 |
| v7/candidate.native/discard | 81.8 | 82.8 | -1.2 | -1.4, -0.8 |
| v4/candidate/serialize | 1011.8 | 1008.4 | 0.3 | -0.2, 2.7 |
| v4/candidate/direct-string | 95.8 | 96.7 | -1.0 | -1.4, -0.5 |
| v4/candidate/retain | 173.9 | 174.9 | -0.6 | -1.4, 0.0 |
| v7/candidate.native/retain | 91.1 | 93.6 | -2.7 | -3.4, -0.3 |
| format/candidate-bytes | 47.4 | 48.5 | -2.3 | -5.1, -1.2 |
| packed/candidate-batch | 52.1 | 21.3 | 59.1 | 58.8, 59.6 |
| v4/candidate/format-generated | 408.0 | 249.7 | 38.8 | 36.5, 39.9 |
| v4/candidate/discard | 163.0 | 165.1 | -1.3 | -1.9, 1.4 |
| v4/candidate/batch | 149.9 | 149.8 | 0.0 | -0.8, 1.3 |
| v7/candidate/batch | 163.9 | 166.3 | -1.5 | -3.2, -0.7 |
| v7/candidate/retain | 189.4 | 194.8 | -2.8 | -7.0, -1.7 |
| v7/candidate/discard | 178.5 | 183.5 | -2.8 | -3.4, -1.9 |

| HTTP scenario | Offered rps | Variant | CPU us/request | p99 ms | Lag p99 ms | Overloaded repeats |
|---|---:|---|---:|---:|---:|---:|
| path | 100 | baseline-default | 509.5 | 44.08 | 2.21 | 0 |
| path | 100 | candidate-explicit | 481.4 | 43.99 | 2.08 | 0 |
| path | 100 | candidate-default | 426.3 | 43.98 | 1.74 | 0 |
| path | 100 | uuid-utils-compat | 519.5 | 43.97 | 1.97 | 0 |
| path | 100 | baseline-explicit | 576.1 | 44.45 | 2.11 | 0 |
| path | 100 | uuid-utils-native | 507.4 | 44.36 | 2.00 | 0 |
| path | 300 | baseline-default | 371.6 | 44.00 | 1.11 | 0 |
| path | 300 | candidate-explicit | 394.6 | 44.07 | 1.11 | 0 |
| path | 300 | candidate-default | 384.2 | 43.92 | 1.12 | 0 |
| path | 300 | uuid-utils-compat | 362.2 | 44.03 | 1.12 | 0 |
| path | 300 | baseline-explicit | 354.7 | 44.31 | 1.14 | 0 |
| path | 300 | uuid-utils-native | 363.9 | 44.03 | 1.13 | 0 |
| body-1 | 100 | baseline-default | 475.9 | 44.15 | 2.08 | 0 |
| body-1 | 100 | candidate-explicit | 645.2 | 44.40 | 1.81 | 0 |
| body-1 | 100 | candidate-default | 603.9 | 44.62 | 1.78 | 0 |
| body-1 | 100 | uuid-utils-compat | 608.0 | 43.81 | 2.13 | 0 |
| body-1 | 100 | baseline-explicit | 550.6 | 44.53 | 2.12 | 0 |
| body-1 | 100 | uuid-utils-native | 512.4 | 44.54 | 1.81 | 0 |
| body-1 | 300 | baseline-default | 410.5 | 44.25 | 1.11 | 0 |
| body-1 | 300 | candidate-explicit | 451.5 | 44.00 | 1.12 | 0 |
| body-1 | 300 | candidate-default | 397.0 | 44.08 | 1.12 | 0 |
| body-1 | 300 | uuid-utils-compat | 477.9 | 45.21 | 1.30 | 0 |
| body-1 | 300 | baseline-explicit | 477.8 | 44.35 | 1.12 | 0 |
| body-1 | 300 | uuid-utils-native | 418.4 | 44.18 | 1.09 | 0 |
| body-1000 | 20 | baseline-default | 1517.0 | 44.75 | 1.17 | 0 |
| body-1000 | 20 | candidate-explicit | 2145.5 | 57.11 | 1.16 | 0 |
| body-1000 | 20 | candidate-default | 1491.3 | 45.44 | 1.15 | 0 |
| body-1000 | 20 | uuid-utils-compat | 1455.6 | 44.58 | 1.04 | 0 |
| body-1000 | 20 | baseline-explicit | 1794.6 | 44.82 | 1.12 | 0 |
| body-1000 | 20 | uuid-utils-native | 1444.4 | 44.80 | 0.95 | 0 |
| body-1000 | 60 | baseline-default | 1279.3 | 44.95 | 1.20 | 0 |
| body-1000 | 60 | candidate-explicit | 1330.2 | 44.81 | 1.85 | 0 |
| body-1000 | 60 | candidate-default | 1329.3 | 45.24 | 1.34 | 0 |
| body-1000 | 60 | uuid-utils-compat | 1227.6 | 44.81 | 1.17 | 0 |
| body-1000 | 60 | baseline-explicit | 1442.5 | 44.98 | 1.32 | 0 |
| body-1000 | 60 | uuid-utils-native | 1299.0 | 44.76 | 1.32 | 0 |
| response | 20 | baseline-default | 910.1 | 44.05 | 1.05 | 0 |
| response | 20 | candidate-explicit | 948.7 | 43.96 | 1.06 | 0 |
| response | 20 | candidate-default | 880.1 | 43.99 | 1.18 | 0 |
| response | 20 | uuid-utils-compat | 913.4 | 43.25 | 0.64 | 0 |
| response | 20 | baseline-explicit | 1073.2 | 44.04 | 0.81 | 0 |
| response | 20 | uuid-utils-native | 873.9 | 44.01 | 0.59 | 0 |
| response | 60 | baseline-default | 638.5 | 43.93 | 1.18 | 0 |
| response | 60 | candidate-explicit | 818.0 | 43.93 | 1.16 | 0 |
| response | 60 | candidate-default | 789.0 | 43.83 | 1.16 | 0 |
| response | 60 | uuid-utils-compat | 745.5 | 43.81 | 1.21 | 0 |
| response | 60 | baseline-explicit | 801.2 | 43.86 | 1.20 | 0 |
| response | 60 | uuid-utils-native | 678.0 | 43.90 | 1.19 | 0 |
| invalid | 100 | baseline-default | 564.7 | 44.61 | 2.31 | 0 |
| invalid | 100 | candidate-explicit | 716.6 | 44.54 | 2.14 | 0 |
| invalid | 100 | candidate-default | 708.5 | 45.17 | 2.14 | 0 |
| invalid | 100 | uuid-utils-compat | 708.4 | 44.68 | 2.04 | 0 |
| invalid | 100 | baseline-explicit | 633.7 | 44.67 | 1.91 | 0 |
| invalid | 100 | uuid-utils-native | 671.6 | 44.14 | 2.27 | 0 |
| invalid | 300 | baseline-default | 526.9 | 44.06 | 1.11 | 0 |
| invalid | 300 | candidate-explicit | 559.8 | 44.17 | 1.12 | 0 |
| invalid | 300 | candidate-default | 501.5 | 44.12 | 1.12 | 0 |
| invalid | 300 | uuid-utils-compat | 530.5 | 44.24 | 1.10 | 0 |
| invalid | 300 | baseline-explicit | 539.8 | 44.30 | 1.11 | 0 |
| invalid | 300 | uuid-utils-native | 556.8 | 46.13 | 1.11 | 0 |
| generate-v4 | 40 | baseline-default | 647.0 | 43.96 | 1.22 | 0 |
| generate-v4 | 40 | candidate-explicit | 737.1 | 43.93 | 1.23 | 0 |
| generate-v4 | 40 | candidate-default | 764.7 | 43.81 | 1.21 | 0 |
| generate-v4 | 40 | uuid-utils-compat | 833.2 | 43.84 | 1.15 | 0 |
| generate-v4 | 40 | baseline-explicit | 793.0 | 43.84 | 1.20 | 0 |
| generate-v4 | 40 | uuid-utils-native | 779.6 | 43.90 | 1.20 | 0 |
| generate-v4 | 120 | baseline-default | 481.0 | 44.11 | 1.65 | 0 |
| generate-v4 | 120 | candidate-explicit | 519.0 | 44.73 | 1.54 | 0 |
| generate-v4 | 120 | candidate-default | 546.8 | 43.97 | 1.54 | 0 |
| generate-v4 | 120 | uuid-utils-compat | 577.9 | 44.45 | 1.58 | 0 |
| generate-v4 | 120 | baseline-explicit | 457.0 | 44.52 | 1.79 | 0 |
| generate-v4 | 120 | uuid-utils-native | 404.6 | 44.68 | 1.76 | 0 |
| generate-v7 | 40 | baseline-default | 657.5 | 43.92 | 1.17 | 0 |
| generate-v7 | 40 | candidate-explicit | 765.5 | 43.89 | 1.18 | 0 |
| generate-v7 | 40 | candidate-default | 821.8 | 43.91 | 1.13 | 0 |
| generate-v7 | 40 | uuid-utils-compat | 840.5 | 43.85 | 1.18 | 0 |
| generate-v7 | 40 | baseline-explicit | 749.0 | 43.95 | 1.22 | 0 |
| generate-v7 | 40 | uuid-utils-native | 718.6 | 43.86 | 1.22 | 0 |
| generate-v7 | 120 | baseline-default | 517.1 | 44.68 | 1.70 | 0 |
| generate-v7 | 120 | candidate-explicit | 528.3 | 44.72 | 1.79 | 0 |
| generate-v7 | 120 | candidate-default | 449.3 | 44.50 | 1.54 | 0 |
| generate-v7 | 120 | uuid-utils-compat | 585.4 | 44.47 | 1.52 | 0 |
| generate-v7 | 120 | baseline-explicit | 448.0 | 44.20 | 1.67 | 0 |
| generate-v7 | 120 | uuid-utils-native | 414.3 | 44.48 | 1.71 | 0 |
