# UUID performance comparison

Source: `5a8324a47a8410816aa4f12ec712ca7afeac05dc`.

Positive reduction means less time/CPU. Intervals bootstrap the paired process/repeat means
(5,000 resamples, exploratory 95%, no multiple-comparison correction). Inspect all cells
and scheduling overload flags; no saturation throughput or production claim.

| Microbenchmark | 0.6.0 ns | Candidate ns | Reduction % | 95% interval % |
|---|---:|---:|---:|---:|
| v7/candidate/serialize | 714.5 | 309.7 | 56.6 | 54.9, 57.1 |
| parse/candidate-batch | 125.5 | 111.0 | 11.6 | 8.9, 14.5 |
| v7/candidate.native/serialize | 129.6 | 130.7 | -0.9 | -3.7, 4.2 |
| packed/candidate | 225.8 | 206.2 | 8.7 | 4.1, 10.9 |
| format/candidate-UUID | 182.2 | 81.1 | 55.5 | 54.4, 57.5 |
| parse/candidate | 138.4 | 128.0 | 7.5 | 4.2, 10.2 |
| v7/candidate.native/retain | 82.3 | 82.1 | 0.2 | -2.5, 3.6 |
| v4/candidate/serialize | 675.2 | 671.8 | 0.5 | -7.5, 2.1 |
| v4/candidate/direct-string | 97.6 | 98.7 | -1.2 | -3.0, 0.8 |
| v4/candidate/retain | 160.3 | 159.1 | 0.8 | -0.6, 5.1 |
| v7/candidate.native/discard | 77.0 | 77.0 | 0.0 | -2.1, 5.3 |
| v7/candidate/direct-string | 103.2 | 104.9 | -1.6 | -3.9, -0.1 |
| format/candidate-bytes | 51.1 | 51.7 | -1.3 | -5.2, 7.2 |
| packed/candidate-batch | 39.0 | 18.3 | 53.2 | 52.7, 53.2 |
| v4/candidate/format-generated | 369.4 | 244.2 | 33.9 | 33.6, 35.0 |
| v7/candidate/batch | 151.0 | 152.7 | -1.1 | -3.3, 3.8 |
| v4/candidate/discard | 160.4 | 156.0 | 2.8 | -5.2, 2.8 |
| v4/candidate/batch | 136.8 | 137.4 | -0.4 | -1.6, 4.7 |
| v7/candidate/format-generated | 405.5 | 253.9 | 37.4 | 34.4, 40.5 |
| v7/candidate/retain | 178.2 | 176.6 | 0.9 | -3.5, 4.5 |
| v7/candidate/discard | 167.6 | 176.7 | -5.5 | -7.0, 0.2 |

| HTTP scenario | Offered rps | Variant | CPU us/request | p99 ms | Lag p99 ms | Overloaded repeats |
|---|---:|---|---:|---:|---:|---:|
| path | 100 | baseline-default | 439.9 | 43.99 | 1.88 | 0 |
| path | 100 | candidate-explicit | 420.4 | 43.96 | 2.07 | 0 |
| path | 100 | candidate-default | 450.1 | 44.02 | 2.04 | 0 |
| path | 100 | uuid-utils-compat | 444.4 | 44.25 | 2.10 | 0 |
| path | 100 | baseline-explicit | 446.7 | 44.07 | 2.09 | 0 |
| path | 100 | uuid-utils-native | 491.7 | 43.76 | 2.10 | 0 |
| path | 300 | baseline-default | 340.4 | 43.81 | 1.08 | 0 |
| path | 300 | candidate-explicit | 291.0 | 43.87 | 1.09 | 0 |
| path | 300 | candidate-default | 329.4 | 43.77 | 1.07 | 0 |
| path | 300 | uuid-utils-compat | 288.9 | 43.77 | 1.07 | 0 |
| path | 300 | baseline-explicit | 314.3 | 43.72 | 1.04 | 0 |
| path | 300 | uuid-utils-native | 334.0 | 43.89 | 1.09 | 0 |
| body-1 | 100 | baseline-default | 517.0 | 43.95 | 2.06 | 0 |
| body-1 | 100 | candidate-explicit | 493.7 | 43.75 | 1.94 | 0 |
| body-1 | 100 | candidate-default | 474.4 | 43.66 | 2.02 | 0 |
| body-1 | 100 | uuid-utils-compat | 458.8 | 43.80 | 2.08 | 0 |
| body-1 | 100 | baseline-explicit | 455.2 | 43.50 | 2.09 | 0 |
| body-1 | 100 | uuid-utils-native | 568.1 | 44.05 | 2.10 | 0 |
| body-1 | 300 | baseline-default | 347.1 | 43.93 | 1.09 | 0 |
| body-1 | 300 | candidate-explicit | 356.4 | 43.86 | 1.06 | 0 |
| body-1 | 300 | candidate-default | 364.2 | 43.85 | 1.08 | 0 |
| body-1 | 300 | uuid-utils-compat | 351.0 | 43.75 | 1.07 | 0 |
| body-1 | 300 | baseline-explicit | 361.7 | 43.70 | 1.08 | 0 |
| body-1 | 300 | uuid-utils-native | 350.4 | 43.85 | 1.05 | 0 |
| body-1000 | 20 | baseline-default | 1103.7 | 43.96 | 0.50 | 0 |
| body-1000 | 20 | candidate-explicit | 1185.3 | 43.27 | 0.49 | 0 |
| body-1000 | 20 | candidate-default | 1194.9 | 44.04 | 0.47 | 0 |
| body-1000 | 20 | uuid-utils-compat | 1122.2 | 44.03 | 0.51 | 0 |
| body-1000 | 20 | baseline-explicit | 1391.1 | 44.18 | 0.55 | 0 |
| body-1000 | 20 | uuid-utils-native | 1218.3 | 44.16 | 0.56 | 0 |
| body-1000 | 60 | baseline-default | 931.5 | 43.91 | 1.10 | 0 |
| body-1000 | 60 | candidate-explicit | 899.7 | 43.90 | 2.01 | 0 |
| body-1000 | 60 | candidate-default | 990.5 | 43.96 | 1.14 | 0 |
| body-1000 | 60 | uuid-utils-compat | 923.3 | 43.89 | 1.15 | 0 |
| body-1000 | 60 | baseline-explicit | 1085.6 | 44.41 | 1.14 | 0 |
| body-1000 | 60 | uuid-utils-native | 1094.8 | 44.00 | 1.17 | 0 |
| response | 20 | baseline-default | 787.9 | 43.11 | 1.14 | 0 |
| response | 20 | candidate-explicit | 822.0 | 43.03 | 0.51 | 0 |
| response | 20 | candidate-default | 707.8 | 43.05 | 0.42 | 0 |
| response | 20 | uuid-utils-compat | 648.3 | 43.76 | 1.13 | 0 |
| response | 20 | baseline-explicit | 884.0 | 43.83 | 0.55 | 0 |
| response | 20 | uuid-utils-native | 796.6 | 43.04 | 0.48 | 0 |
| response | 60 | baseline-default | 549.7 | 43.86 | 2.03 | 0 |
| response | 60 | candidate-explicit | 687.2 | 43.88 | 2.04 | 0 |
| response | 60 | candidate-default | 605.6 | 43.80 | 2.02 | 0 |
| response | 60 | uuid-utils-compat | 553.4 | 43.85 | 2.10 | 0 |
| response | 60 | baseline-explicit | 637.5 | 43.88 | 2.06 | 0 |
| response | 60 | uuid-utils-native | 646.8 | 43.82 | 1.20 | 0 |
| invalid | 100 | baseline-default | 530.5 | 43.87 | 2.01 | 0 |
| invalid | 100 | candidate-explicit | 593.6 | 44.04 | 2.09 | 0 |
| invalid | 100 | candidate-default | 533.6 | 43.70 | 2.08 | 0 |
| invalid | 100 | uuid-utils-compat | 522.6 | 43.86 | 1.96 | 0 |
| invalid | 100 | baseline-explicit | 564.1 | 43.88 | 2.08 | 0 |
| invalid | 100 | uuid-utils-native | 593.2 | 43.79 | 1.98 | 0 |
| invalid | 300 | baseline-default | 416.6 | 43.84 | 1.07 | 0 |
| invalid | 300 | candidate-explicit | 413.5 | 43.73 | 1.07 | 0 |
| invalid | 300 | candidate-default | 400.2 | 43.81 | 1.04 | 0 |
| invalid | 300 | uuid-utils-compat | 407.8 | 43.91 | 1.04 | 0 |
| invalid | 300 | baseline-explicit | 440.5 | 43.91 | 1.07 | 0 |
| invalid | 300 | uuid-utils-native | 420.5 | 43.86 | 1.05 | 0 |
| generate-v4 | 40 | baseline-default | 562.2 | 43.87 | 2.07 | 0 |
| generate-v4 | 40 | candidate-explicit | 642.9 | 43.91 | 2.02 | 0 |
| generate-v4 | 40 | candidate-default | 535.7 | 43.87 | 2.13 | 0 |
| generate-v4 | 40 | uuid-utils-compat | 664.4 | 43.91 | 2.10 | 0 |
| generate-v4 | 40 | baseline-explicit | 620.7 | 43.78 | 1.19 | 0 |
| generate-v4 | 40 | uuid-utils-native | 659.6 | 43.91 | 2.09 | 0 |
| generate-v4 | 120 | baseline-default | 427.7 | 43.66 | 1.25 | 0 |
| generate-v4 | 120 | candidate-explicit | 419.5 | 43.58 | 1.40 | 0 |
| generate-v4 | 120 | candidate-default | 447.4 | 43.52 | 1.14 | 0 |
| generate-v4 | 120 | uuid-utils-compat | 441.6 | 43.55 | 1.38 | 0 |
| generate-v4 | 120 | baseline-explicit | 476.3 | 44.04 | 1.31 | 0 |
| generate-v4 | 120 | uuid-utils-native | 465.8 | 44.18 | 1.52 | 0 |
| generate-v7 | 40 | baseline-default | 594.6 | 43.85 | 1.20 | 0 |
| generate-v7 | 40 | candidate-explicit | 605.4 | 43.87 | 2.13 | 0 |
| generate-v7 | 40 | candidate-default | 550.8 | 43.89 | 2.14 | 0 |
| generate-v7 | 40 | uuid-utils-compat | 606.4 | 43.80 | 2.01 | 0 |
| generate-v7 | 40 | baseline-explicit | 571.7 | 43.88 | 2.07 | 0 |
| generate-v7 | 40 | uuid-utils-native | 578.3 | 43.87 | 2.06 | 0 |
| generate-v7 | 120 | baseline-default | 438.1 | 43.70 | 1.24 | 0 |
| generate-v7 | 120 | candidate-explicit | 423.2 | 43.76 | 1.24 | 0 |
| generate-v7 | 120 | candidate-default | 416.7 | 43.67 | 1.26 | 0 |
| generate-v7 | 120 | uuid-utils-compat | 446.8 | 43.86 | 1.26 | 0 |
| generate-v7 | 120 | baseline-explicit | 427.9 | 43.64 | 1.24 | 0 |
| generate-v7 | 120 | uuid-utils-native | 482.2 | 43.88 | 1.43 | 0 |
