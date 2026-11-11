# UUID performance comparison

Source: `5a8324a47a8410816aa4f12ec712ca7afeac05dc`.

Positive reduction means less time/CPU. Intervals bootstrap the paired process/repeat means
(5,000 resamples, exploratory 95%, no multiple-comparison correction). Inspect all cells
and scheduling overload flags; no saturation throughput or production claim.

| Microbenchmark | 0.6.0 ns | Candidate ns | Reduction % | 95% interval % |
|---|---:|---:|---:|---:|
| v7/candidate/serialize | 359.9 | 162.1 | 54.9 | 53.9, 56.2 |
| parse/candidate-batch | 65.6 | 50.9 | 22.4 | 16.1, 27.6 |
| v7/candidate.native/serialize | 69.5 | 68.4 | 1.6 | -18.2, 3.0 |
| packed/candidate | 130.7 | 115.7 | 11.5 | 8.5, 12.4 |
| format/candidate-UUID | 110.1 | 48.6 | 55.8 | 54.6, 56.5 |
| parse/candidate | 74.0 | 60.0 | 19.0 | 16.4, 22.1 |
| v7/candidate.native/retain | 47.3 | 45.8 | 3.2 | 2.4, 7.7 |
| v4/candidate/serialize | 357.4 | 351.7 | 1.6 | -4.1, 7.1 |
| v4/candidate/direct-string | 63.5 | 62.5 | 1.6 | -1.1, 2.4 |
| v4/candidate/retain | 88.3 | 88.2 | 0.1 | -7.1, 3.4 |
| v7/candidate.native/discard | 41.7 | 41.8 | -0.1 | -2.1, 2.0 |
| v7/candidate/direct-string | 59.1 | 57.7 | 2.3 | 0.9, 3.2 |
| format/candidate-bytes | 28.2 | 28.5 | -1.2 | -3.0, 1.1 |
| packed/candidate-batch | 25.5 | 11.7 | 54.1 | 53.7, 56.3 |
| v4/candidate/format-generated | 202.0 | 144.7 | 28.4 | 27.2, 31.1 |
| v7/candidate/batch | 75.2 | 75.5 | -0.3 | -22.4, 1.6 |
| v4/candidate/discard | 84.7 | 84.7 | 0.0 | -2.0, 1.8 |
| v4/candidate/batch | 75.2 | 76.1 | -1.2 | -4.8, 2.1 |
| v7/candidate/format-generated | 205.2 | 135.9 | 33.8 | 31.2, 34.4 |
| v7/candidate/retain | 86.9 | 87.0 | -0.1 | -2.8, 4.0 |
| v7/candidate/discard | 87.5 | 85.0 | 2.9 | -10.2, 12.6 |

| HTTP scenario | Offered rps | Variant | CPU us/request | p99 ms | Lag p99 ms | Overloaded repeats |
|---|---:|---|---:|---:|---:|---:|
| path | 100 | baseline-default | 489.6 | 5.06 | 1.20 | 0 |
| path | 100 | candidate-explicit | 403.7 | 4.18 | 1.20 | 0 |
| path | 100 | candidate-default | 627.6 | 4.86 | 1.25 | 0 |
| path | 100 | uuid-utils-compat | 444.9 | 4.74 | 1.19 | 0 |
| path | 100 | baseline-explicit | 390.8 | 4.25 | 1.19 | 0 |
| path | 100 | uuid-utils-native | 538.4 | 4.79 | 1.19 | 0 |
| path | 300 | baseline-default | 298.4 | 2.65 | 0.41 | 0 |
| path | 300 | candidate-explicit | 311.3 | 3.72 | 0.53 | 0 |
| path | 300 | candidate-default | 312.1 | 3.59 | 0.50 | 0 |
| path | 300 | uuid-utils-compat | 302.6 | 3.47 | 0.53 | 0 |
| path | 300 | baseline-explicit | 302.9 | 2.76 | 0.45 | 0 |
| path | 300 | uuid-utils-native | 285.0 | 3.13 | 0.47 | 0 |
| body-1 | 100 | baseline-default | 587.2 | 5.05 | 1.20 | 0 |
| body-1 | 100 | candidate-explicit | 650.0 | 5.02 | 1.24 | 0 |
| body-1 | 100 | candidate-default | 650.5 | 4.69 | 1.19 | 0 |
| body-1 | 100 | uuid-utils-compat | 584.9 | 4.93 | 1.20 | 0 |
| body-1 | 100 | baseline-explicit | 687.6 | 4.96 | 1.24 | 0 |
| body-1 | 100 | uuid-utils-native | 598.8 | 4.77 | 1.21 | 0 |
| body-1 | 300 | baseline-default | 319.9 | 2.54 | 0.42 | 0 |
| body-1 | 300 | candidate-explicit | 353.0 | 3.42 | 0.52 | 0 |
| body-1 | 300 | candidate-default | 337.8 | 3.18 | 0.42 | 0 |
| body-1 | 300 | uuid-utils-compat | 332.9 | 3.20 | 0.46 | 0 |
| body-1 | 300 | baseline-explicit | 337.8 | 3.54 | 0.53 | 0 |
| body-1 | 300 | uuid-utils-native | 321.7 | 3.27 | 0.46 | 0 |
| body-1000 | 20 | baseline-default | 1668.2 | 5.95 | 1.35 | 0 |
| body-1000 | 20 | candidate-explicit | 1593.8 | 6.08 | 1.32 | 0 |
| body-1000 | 20 | candidate-default | 1515.3 | 6.07 | 1.30 | 0 |
| body-1000 | 20 | uuid-utils-compat | 1798.6 | 6.49 | 1.34 | 0 |
| body-1000 | 20 | baseline-explicit | 1593.5 | 6.23 | 1.36 | 0 |
| body-1000 | 20 | uuid-utils-native | 1797.2 | 5.95 | 1.28 | 0 |
| body-1000 | 60 | baseline-default | 1075.0 | 5.87 | 1.30 | 0 |
| body-1000 | 60 | candidate-explicit | 1382.1 | 6.19 | 1.32 | 0 |
| body-1000 | 60 | candidate-default | 1047.3 | 5.73 | 1.35 | 0 |
| body-1000 | 60 | uuid-utils-compat | 1355.1 | 6.22 | 1.30 | 0 |
| body-1000 | 60 | baseline-explicit | 1455.2 | 6.12 | 1.34 | 0 |
| body-1000 | 60 | uuid-utils-native | 984.2 | 5.57 | 1.30 | 0 |
| response | 20 | baseline-default | 951.9 | 5.30 | 1.32 | 0 |
| response | 20 | candidate-explicit | 1235.2 | 5.85 | 1.42 | 0 |
| response | 20 | candidate-default | 951.8 | 5.19 | 1.29 | 0 |
| response | 20 | uuid-utils-compat | 1041.8 | 5.38 | 1.32 | 0 |
| response | 20 | baseline-explicit | 1347.4 | 6.37 | 1.33 | 0 |
| response | 20 | uuid-utils-native | 990.2 | 5.50 | 1.31 | 0 |
| response | 60 | baseline-default | 824.0 | 6.31 | 1.31 | 0 |
| response | 60 | candidate-explicit | 890.1 | 5.45 | 1.29 | 0 |
| response | 60 | candidate-default | 627.6 | 5.22 | 1.34 | 0 |
| response | 60 | uuid-utils-compat | 760.4 | 5.37 | 1.37 | 0 |
| response | 60 | baseline-explicit | 968.7 | 5.38 | 1.29 | 0 |
| response | 60 | uuid-utils-native | 749.1 | 4.88 | 1.32 | 0 |
| invalid | 100 | baseline-default | 768.3 | 5.02 | 1.19 | 0 |
| invalid | 100 | candidate-explicit | 762.8 | 5.07 | 1.24 | 0 |
| invalid | 100 | candidate-default | 737.2 | 4.73 | 1.17 | 0 |
| invalid | 100 | uuid-utils-compat | 758.6 | 5.47 | 1.22 | 0 |
| invalid | 100 | baseline-explicit | 762.8 | 4.99 | 1.25 | 0 |
| invalid | 100 | uuid-utils-native | 700.6 | 5.16 | 1.23 | 0 |
| invalid | 300 | baseline-default | 371.9 | 3.96 | 0.64 | 0 |
| invalid | 300 | candidate-explicit | 381.6 | 3.42 | 0.58 | 0 |
| invalid | 300 | candidate-default | 397.7 | 3.34 | 0.48 | 0 |
| invalid | 300 | uuid-utils-compat | 378.4 | 3.39 | 0.48 | 0 |
| invalid | 300 | baseline-explicit | 375.0 | 3.41 | 0.51 | 0 |
| invalid | 300 | uuid-utils-native | 411.3 | 3.85 | 0.54 | 0 |
| generate-v4 | 40 | baseline-default | 965.7 | 5.88 | 1.35 | 0 |
| generate-v4 | 40 | candidate-explicit | 945.0 | 5.66 | 1.32 | 0 |
| generate-v4 | 40 | candidate-default | 934.1 | 5.19 | 1.37 | 0 |
| generate-v4 | 40 | uuid-utils-compat | 921.9 | 5.27 | 1.30 | 0 |
| generate-v4 | 40 | baseline-explicit | 708.0 | 5.49 | 1.32 | 0 |
| generate-v4 | 40 | uuid-utils-native | 790.7 | 5.47 | 1.50 | 0 |
| generate-v4 | 120 | baseline-default | 500.8 | 4.08 | 1.01 | 0 |
| generate-v4 | 120 | candidate-explicit | 444.5 | 4.16 | 1.02 | 0 |
| generate-v4 | 120 | candidate-default | 512.0 | 4.37 | 0.99 | 0 |
| generate-v4 | 120 | uuid-utils-compat | 526.1 | 4.23 | 0.99 | 0 |
| generate-v4 | 120 | baseline-explicit | 494.4 | 4.77 | 1.01 | 0 |
| generate-v4 | 120 | uuid-utils-native | 554.7 | 4.54 | 1.03 | 0 |
| generate-v7 | 40 | baseline-default | 774.4 | 5.53 | 1.50 | 0 |
| generate-v7 | 40 | candidate-explicit | 894.4 | 5.15 | 1.30 | 0 |
| generate-v7 | 40 | candidate-default | 669.7 | 5.29 | 1.29 | 0 |
| generate-v7 | 40 | uuid-utils-compat | 674.5 | 5.55 | 1.30 | 0 |
| generate-v7 | 40 | baseline-explicit | 985.5 | 5.28 | 1.29 | 0 |
| generate-v7 | 40 | uuid-utils-native | 756.8 | 5.41 | 1.32 | 0 |
| generate-v7 | 120 | baseline-default | 498.6 | 4.53 | 0.98 | 0 |
| generate-v7 | 120 | candidate-explicit | 536.0 | 4.30 | 1.00 | 0 |
| generate-v7 | 120 | candidate-default | 523.6 | 4.66 | 1.08 | 0 |
| generate-v7 | 120 | uuid-utils-compat | 508.9 | 4.57 | 1.00 | 0 |
| generate-v7 | 120 | baseline-explicit | 618.1 | 4.57 | 1.05 | 0 |
| generate-v7 | 120 | uuid-utils-native | 471.8 | 4.28 | 1.07 | 0 |
