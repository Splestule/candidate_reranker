# Campaign report

generated 2026-09-20 09:08 UTC

utterance decodes analysed: 282379; cells: 665


## Main arm at the largest K, corpus WER (legacy normalisation)

| model | set | n | K | first | conf | MBR | ROVER | ROVER-cg | oracle | oracle-comp | control | pairwise % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drax/main | ami | 600 | 16 | 17.83 | 14.11 | 11.40 | 11.07 | 11.10 | 7.86 | 4.04 | 6.60 | 26.8 |
| drax/ref | ami | 600 | 4 | 11.48 | 11.22 | 10.99 | 11.10 | 11.23 | 9.16 | 7.32 | 7.69 | 8.6 |
| drax/main | common_voice | 455 | 16 | 20.94 | 14.89 | 13.36 | 13.04 | 13.09 | 9.81 | 7.46 | 9.24 | 21.5 |
| drax/ref | common_voice | 455 | 4 | 13.53 | 12.81 | 12.47 | 12.42 | 12.64 | 10.78 | 9.42 | 9.84 | 7.0 |
| drax/main | earnings22 | 600 | 16 | 37.74 | 25.28 | 23.21 | 22.59 | 22.74 | 18.27 | 9.90 | 14.27 | 32.9 |
| drax/ref | earnings22 | 600 | 4 | 20.97 | 20.40 | 20.49 | 20.44 | 20.70 | 17.69 | 12.82 | 13.58 | 9.5 |
| drax/main | fleurs-de | 546 | 16 | 12.61 | 9.74 | 8.45 | 7.95 | 7.94 | 6.18 | 4.24 | 5.97 | 13.6 |
| drax/ref | fleurs-de | 546 | 4 | 9.24 | 8.70 | 8.53 | 8.41 | 8.43 | 7.00 | 6.01 | 6.63 | 5.8 |
| drax/main | fleurs-en | 600 | 16 | 14.43 | 11.36 | 10.16 | 9.61 | 9.64 | 7.94 | 4.84 | 7.17 | 14.6 |
| drax/ref | fleurs-en | 600 | 4 | 9.95 | 9.98 | 9.59 | 9.49 | 9.55 | 8.15 | 6.26 | 6.79 | 4.8 |
| drax/main | fleurs-es | 400 | 16 | 9.52 | 6.92 | 6.16 | 6.01 | 6.00 | 4.69 | 3.08 | 4.22 | 9.1 |
| drax/ref | fleurs-es | 400 | 4 | 6.69 | 6.46 | 6.25 | 6.08 | 6.09 | 5.36 | 4.14 | 4.47 | 3.0 |
| drax/main | fleurs-fr | 468 | 16 | 16.11 | 12.72 | 11.76 | 11.11 | 11.17 | 9.16 | 5.56 | 8.62 | 15.8 |
| drax/ref | fleurs-fr | 468 | 4 | 11.94 | 11.56 | 11.60 | 11.32 | 11.38 | 9.66 | 7.78 | 8.62 | 6.5 |
| drax/main | fleurs-it | 400 | 16 | 10.48 | 7.09 | 6.36 | 5.83 | 5.87 | 4.61 | 2.95 | 4.30 | 11.7 |
| drax/ref | fleurs-it | 400 | 4 | 6.96 | 6.63 | 6.41 | 6.29 | 6.33 | 5.11 | 4.14 | 4.51 | 4.0 |
| drax/main | fleurs-pt | 400 | 16 | 19.34 | 14.75 | 13.20 | 12.10 | 12.07 | 10.75 | 5.21 | 9.38 | 19.2 |
| drax/ref | fleurs-pt | 400 | 4 | 13.68 | 13.12 | 12.72 | 12.53 | 12.57 | 10.98 | 7.08 | 8.61 | 8.1 |
| drax/main | gigaspeech | 600 | 16 | 20.39 | 15.52 | 14.45 | 13.92 | 13.91 | 11.25 | 7.34 | 10.14 | 20.9 |
| drax/ref | gigaspeech | 600 | 4 | 14.50 | 14.37 | 13.96 | 13.96 | 14.11 | 12.10 | 9.78 | 10.31 | 6.7 |
| drax/main | ls-dev-clean | 400 | 16 | 5.32 | 3.20 | 2.82 | 2.79 | 2.78 | 1.63 | 1.11 | 1.52 | 7.9 |
| drax/ref | ls-dev-clean | 400 | 4 | 3.11 | 2.90 | 2.78 | 2.66 | 2.66 | 2.18 | 1.98 | 2.04 | 1.7 |
| drax/main | ls-dev-other | 400 | 16 | 9.99 | 6.76 | 5.79 | 5.42 | 5.47 | 4.42 | 2.50 | 4.17 | 12.5 |
| drax/ref | ls-dev-other | 400 | 4 | 5.83 | 5.68 | 5.60 | 5.60 | 5.61 | 4.75 | 3.97 | 4.26 | 2.8 |
| drax/main | ls-tc-babble0 | 600 | 16 | 53.80 | 42.81 | 41.13 | 36.86 | 36.86 | 35.07 | 23.38 | 32.34 | 57.9 |
| drax/ref | ls-tc-babble0 | 600 | 4 | 35.54 | 35.36 | 35.89 | 34.94 | 34.95 | 31.05 | 27.04 | 29.00 | 25.7 |
| drax/main | ls-tc-babble10 | 600 | 16 | 8.12 | 5.30 | 4.14 | 4.07 | 4.11 | 2.74 | 1.81 | 2.67 | 11.6 |
| drax/ref | ls-tc-babble10 | 600 | 4 | 4.54 | 4.35 | 4.13 | 4.08 | 4.18 | 3.39 | 2.99 | 3.18 | 2.7 |
| drax/main | ls-tc-babble5 | 600 | 16 | 16.52 | 11.90 | 10.12 | 9.41 | 9.42 | 7.76 | 4.35 | 7.40 | 21.9 |
| drax/ref | ls-tc-babble5 | 600 | 4 | 9.53 | 9.46 | 8.98 | 8.93 | 8.95 | 7.58 | 6.47 | 7.06 | 6.8 |
| drax/main | ls-tc-white5 | 600 | 16 | 11.91 | 8.77 | 7.41 | 6.95 | 7.02 | 5.62 | 3.25 | 5.38 | 16.9 |
| drax/ref | ls-tc-white5 | 600 | 4 | 7.26 | 7.04 | 6.83 | 6.78 | 6.77 | 5.68 | 4.96 | 5.39 | 4.6 |
| drax/main | ls-test-clean | 600 | 16 | 5.24 | 2.81 | 2.38 | 2.30 | 2.41 | 1.38 | 0.94 | 1.33 | 7.8 |
| drax/ref | ls-test-clean | 600 | 4 | 2.57 | 2.44 | 2.39 | 2.38 | 2.35 | 1.77 | 1.58 | 1.65 | 1.5 |
| drax/main | ls-test-other | 600 | 16 | 10.26 | 7.15 | 5.95 | 5.64 | 5.73 | 4.03 | 2.47 | 3.90 | 14.1 |
| drax/ref | ls-test-other | 600 | 4 | 6.36 | 6.07 | 5.90 | 5.76 | 5.82 | 4.88 | 4.25 | 4.55 | 3.5 |
| drax/main | slr83 | 600 | 16 | 11.09 | 7.65 | 7.00 | 6.72 | 6.83 | 4.87 | 3.56 | 4.50 | 12.0 |
| drax/ref | slr83 | 600 | 4 | 7.59 | 7.19 | 7.22 | 7.04 | 7.05 | 5.88 | 4.85 | 5.25 | 3.9 |
| drax/main | spgispeech | 600 | 16 | 11.58 | 8.39 | 7.56 | 7.51 | 7.56 | 5.25 | 2.53 | 4.21 | 11.6 |
| drax/ref | spgispeech | 600 | 4 | 7.58 | 7.56 | 7.11 | 7.41 | 7.67 | 6.03 | 3.84 | 4.14 | 3.0 |
| drax/main | voxpopuli | 600 | 16 | 12.34 | 8.55 | 7.67 | 7.57 | 7.65 | 5.87 | 3.58 | 5.07 | 13.4 |
| drax/ref | voxpopuli | 600 | 4 | 7.75 | 7.66 | 7.60 | 7.59 | 7.70 | 6.80 | 5.22 | 5.40 | 2.6 |
| whisfusion/main | ami | 400 | 32 | 46.21 | 36.63 | 35.37 | 33.29 | 33.26 | 28.32 | 21.18 | 27.16 | 41.4 |
| whisfusion/main | common_voice | 296 | 32 | 42.13 | 32.62 | 31.32 | 29.18 | 28.95 | 24.29 | 16.62 | 22.27 | 33.7 |
| whisfusion/main | earnings22 | 400 | 32 | 48.05 | 39.28 | 37.25 | 34.45 | 34.40 | 31.66 | 18.27 | 28.03 | 40.0 |
| whisfusion/main | fleurs-en | 400 | 32 | 34.56 | 27.96 | 25.69 | 23.47 | 23.47 | 21.96 | 11.45 | 19.37 | 30.5 |
| whisfusion/main | gigaspeech | 400 | 32 | 32.08 | 24.93 | 23.68 | 21.48 | 21.48 | 19.27 | 11.54 | 18.03 | 30.9 |
| whisfusion/main | ls-dev-clean | 400 | 32 | 11.95 | 7.07 | 6.14 | 5.31 | 5.32 | 4.70 | 2.42 | 4.54 | 13.4 |
| whisfusion/main | ls-dev-other | 400 | 32 | 21.59 | 15.31 | 14.34 | 12.59 | 12.63 | 11.25 | 5.94 | 10.64 | 22.0 |
| whisfusion/main | ls-tc-babble0 | 400 | 32 | 76.62 | 68.81 | 66.27 | 58.31 | 58.28 | 59.35 | 38.08 | 48.09 | 62.3 |
| whisfusion/main | ls-tc-babble10 | 400 | 32 | 23.23 | 15.94 | 14.44 | 11.47 | 11.40 | 11.67 | 5.32 | 10.91 | 25.5 |
| whisfusion/main | ls-tc-babble5 | 400 | 32 | 39.83 | 31.42 | 29.14 | 24.43 | 24.41 | 25.48 | 13.50 | 23.11 | 39.7 |
| whisfusion/main | ls-tc-white5 | 400 | 32 | 30.35 | 23.69 | 21.97 | 18.94 | 18.96 | 18.58 | 10.50 | 17.51 | 30.5 |
| whisfusion/main | ls-test-clean | 400 | 32 | 12.46 | 7.59 | 6.91 | 5.55 | 5.51 | 4.93 | 2.00 | 4.67 | 14.6 |
| whisfusion/main | ls-test-other | 400 | 32 | 21.31 | 15.39 | 13.47 | 11.98 | 11.92 | 10.92 | 6.13 | 10.51 | 22.2 |
| whisfusion/main | slr83 | 400 | 32 | 27.85 | 19.92 | 18.66 | 17.10 | 17.05 | 14.48 | 8.59 | 13.35 | 27.1 |
| whisfusion/main | spgispeech | 400 | 32 | 27.06 | 19.33 | 17.20 | 14.91 | 14.88 | 14.35 | 6.14 | 13.28 | 27.6 |
| whisfusion/main | voxpopuli | 400 | 32 | 28.50 | 21.11 | 20.11 | 18.11 | 18.05 | 16.62 | 9.50 | 15.40 | 24.1 |

## ROVER-cg against the best selection, paired bootstrap (main arm, largest K)

| model | set | vs | delta | 95% CI | cluster CI | Wilcoxon p | better/worse/tied |
|---|---|---|---|---|---|---|---|
| drax/main | ami | conf | +3.00 | [+2.31, +3.66] | [1.80, 4.12] | 0.0000 | 154/40/406 |
| drax/main | ami | mbr | +0.30 | [-0.08, +0.66] | [-0.18, 0.77] | 0.1181 | 41/32/527 |
| drax/ref | ami | conf | -0.02 | [-0.37, +0.33] | [-0.35, 0.32] | 0.9821 | 37/34/529 |
| drax/ref | ami | mbr | -0.24 | [-0.53, +0.06] | [-0.51, -0.02] | 0.1009 | 23/34/543 |
| drax/main | common_voice | conf | +1.81 | [+1.17, +2.46] | [, ] | 0.0000 | 84/31/340 |
| drax/main | common_voice | mbr | +0.27 | [-0.15, +0.68] | [, ] | 0.1898 | 30/24/401 |
| drax/ref | common_voice | conf | +0.17 | [-0.29, +0.64] | [, ] | 0.4636 | 25/23/407 |
| drax/ref | common_voice | mbr | -0.17 | [-0.52, +0.18] | [, ] | 0.3204 | 17/20/418 |
| drax/main | earnings22 | conf | +2.54 | [+1.30, +3.98] | [1.90, 3.31] | 0.0000 | 196/121/283 |
| drax/main | earnings22 | mbr | +0.47 | [+0.11, +0.83] | [0.24, 0.84] | 0.0155 | 129/92/379 |
| drax/ref | earnings22 | conf | -0.30 | [-0.70, +0.09] | [-0.53, -0.01] | 0.2503 | 91/105/404 |
| drax/ref | earnings22 | mbr | -0.21 | [-0.51, +0.08] | [-0.37, -0.09] | 0.1692 | 66/87/447 |
| drax/main | fleurs-de | conf | +1.80 | [+1.39, +2.22] | [1.39, 2.23] | 0.0000 | 172/57/317 |
| drax/main | fleurs-de | mbr | +0.51 | [+0.27, +0.76] | [0.27, 0.77] | 0.0000 | 77/38/431 |
| drax/ref | fleurs-de | conf | +0.27 | [+0.01, +0.55] | [-0.01, 0.55] | 0.0650 | 79/58/409 |
| drax/ref | fleurs-de | mbr | +0.11 | [-0.10, +0.29] | [-0.09, 0.29] | 0.3322 | 42/34/470 |
| drax/main | fleurs-en | conf | +1.72 | [+1.32, +2.14] | [1.30, 2.21] | 0.0000 | 185/56/359 |
| drax/main | fleurs-en | mbr | +0.52 | [+0.26, +0.78] | [0.23, 0.84] | 0.0001 | 83/46/471 |
| drax/ref | fleurs-en | conf | +0.42 | [+0.18, +0.68] | [0.18, 0.69] | 0.0014 | 88/59/453 |
| drax/ref | fleurs-en | mbr | +0.04 | [-0.11, +0.20] | [-0.11, 0.19] | 0.6328 | 49/48/503 |
| drax/main | fleurs-es | conf | +0.93 | [+0.65, +1.23] | [0.63, 1.21] | 0.0000 | 100/33/267 |
| drax/main | fleurs-es | mbr | +0.17 | [+0.04, +0.31] | [0.03, 0.31] | 0.0215 | 30/16/354 |
| drax/ref | fleurs-es | conf | +0.36 | [+0.17, +0.56] | [0.16, 0.55] | 0.0003 | 57/25/318 |
| drax/ref | fleurs-es | mbr | +0.16 | [+0.01, +0.31] | [-0.01, 0.31] | 0.0374 | 30/18/352 |
| drax/main | fleurs-fr | conf | +1.55 | [+1.16, +1.95] | [1.17, 1.99] | 0.0000 | 166/69/233 |
| drax/main | fleurs-fr | mbr | +0.60 | [+0.34, +0.86] | [0.34, 0.86] | 0.0000 | 95/50/323 |
| drax/ref | fleurs-fr | conf | +0.17 | [-0.15, +0.49] | [-0.15, 0.50] | 0.3859 | 75/77/316 |
| drax/ref | fleurs-fr | mbr | +0.22 | [+0.00, +0.42] | [0.01, 0.43] | 0.0336 | 55/39/374 |
| drax/main | fleurs-it | conf | +1.22 | [+0.89, +1.55] | [0.88, 1.57] | 0.0000 | 108/26/266 |
| drax/main | fleurs-it | mbr | +0.48 | [+0.27, +0.72] | [0.27, 0.70] | 0.0000 | 55/19/326 |
| drax/ref | fleurs-it | conf | +0.30 | [+0.02, +0.59] | [0.02, 0.62] | 0.0278 | 55/40/305 |
| drax/ref | fleurs-it | mbr | +0.08 | [-0.11, +0.29] | [-0.12, 0.29] | 0.3649 | 32/30/338 |
| drax/main | fleurs-pt | conf | +2.68 | [+2.21, +3.16] | [2.20, 3.16] | 0.0000 | 173/35/192 |
| drax/main | fleurs-pt | mbr | +1.14 | [+0.83, +1.43] | [0.83, 1.45] | 0.0000 | 102/22/276 |
| drax/ref | fleurs-pt | conf | +0.55 | [+0.21, +0.88] | [0.22, 0.90] | 0.0007 | 92/52/256 |
| drax/ref | fleurs-pt | mbr | +0.16 | [-0.12, +0.43] | [-0.11, 0.44] | 0.2717 | 60/47/293 |
| drax/main | gigaspeech | conf | +1.61 | [+1.16, +2.04] | [1.13, 2.07] | 0.0000 | 167/68/365 |
| drax/main | gigaspeech | mbr | +0.54 | [+0.27, +0.81] | [0.31, 0.77] | 0.0001 | 89/44/467 |
| drax/ref | gigaspeech | conf | +0.27 | [-0.07, +0.60] | [-0.12, 0.63] | 0.0571 | 85/64/451 |
| drax/ref | gigaspeech | mbr | -0.14 | [-0.36, +0.06] | [-0.37, 0.09] | 0.1767 | 49/66/485 |
| drax/main | ls-dev-clean | conf | +0.42 | [+0.16, +0.72] | [0.13, 0.71] | 0.0030 | 46/25/329 |
| drax/main | ls-dev-clean | mbr | +0.04 | [-0.10, +0.18] | [-0.08, 0.17] | 0.5799 | 13/10/377 |
| drax/ref | ls-dev-clean | conf | +0.24 | [+0.05, +0.43] | [0.07, 0.41] | 0.0117 | 25/12/363 |
| drax/ref | ls-dev-clean | mbr | +0.12 | [-0.01, +0.25] | [0.01, 0.24] | 0.0719 | 15/7/378 |
| drax/main | ls-dev-other | conf | +1.28 | [+0.86, +1.77] | [0.77, 1.94] | 0.0000 | 74/20/306 |
| drax/main | ls-dev-other | mbr | +0.32 | [+0.06, +0.59] | [-0.01, 0.69] | 0.0229 | 32/18/350 |
| drax/ref | ls-dev-other | conf | +0.07 | [-0.20, +0.34] | [-0.26, 0.35] | 0.4293 | 30/22/348 |
| drax/ref | ls-dev-other | mbr | -0.01 | [-0.21, +0.19] | [-0.23, 0.19] | 0.9057 | 18/20/362 |
| drax/main | ls-tc-babble0 | conf | +5.96 | [+4.96, +6.97] | [4.59, 7.15] | 0.0000 | 343/77/180 |
| drax/main | ls-tc-babble0 | mbr | +4.27 | [+3.75, +4.80] | [3.62, 4.92] | 0.0000 | 278/49/273 |
| drax/ref | ls-tc-babble0 | conf | +0.41 | [-0.24, +1.04] | [-0.20, 0.98] | 0.0028 | 170/112/318 |
| drax/ref | ls-tc-babble0 | mbr | +0.94 | [+0.61, +1.29] | [0.57, 1.30] | 0.0000 | 147/83/370 |
| drax/main | ls-tc-babble10 | conf | +1.19 | [+0.85, +1.52] | [0.84, 1.57] | 0.0000 | 122/38/440 |
| drax/main | ls-tc-babble10 | mbr | +0.03 | [-0.13, +0.18] | [-0.13, 0.20] | 0.8177 | 34/33/533 |
| drax/ref | ls-tc-babble10 | conf | +0.18 | [-0.01, +0.37] | [-0.03, 0.39] | 0.0845 | 43/30/527 |
| drax/ref | ls-tc-babble10 | mbr | -0.05 | [-0.18, +0.09] | [-0.17, 0.08] | 0.4656 | 27/32/541 |
| drax/main | ls-tc-babble5 | conf | +2.48 | [+2.01, +2.93] | [1.95, 3.03] | 0.0000 | 206/62/332 |
| drax/main | ls-tc-babble5 | mbr | +0.70 | [+0.41, +0.97] | [0.39, 1.01] | 0.0000 | 111/56/433 |
| drax/ref | ls-tc-babble5 | conf | +0.50 | [+0.25, +0.75] | [0.30, 0.72] | 0.0001 | 96/52/452 |
| drax/ref | ls-tc-babble5 | mbr | +0.03 | [-0.13, +0.19] | [-0.14, 0.17] | 0.7508 | 43/45/512 |
| drax/main | ls-tc-white5 | conf | +1.75 | [+1.38, +2.14] | [1.26, 2.24] | 0.0000 | 165/46/389 |
| drax/main | ls-tc-white5 | mbr | +0.39 | [+0.18, +0.59] | [0.13, 0.64] | 0.0002 | 67/35/498 |
| drax/ref | ls-tc-white5 | conf | +0.27 | [+0.05, +0.49] | [0.08, 0.44] | 0.0137 | 64/39/497 |
| drax/ref | ls-tc-white5 | mbr | +0.06 | [-0.12, +0.22] | [-0.07, 0.19] | 0.4921 | 41/35/524 |
| drax/main | ls-test-clean | conf | +0.40 | [+0.17, +0.65] | [0.15, 0.65] | 0.0011 | 75/39/486 |
| drax/main | ls-test-clean | mbr | -0.03 | [-0.16, +0.10] | [-0.17, 0.12] | 0.6899 | 25/25/550 |
| drax/ref | ls-test-clean | conf | +0.09 | [-0.05, +0.24] | [-0.05, 0.25] | 0.2550 | 24/18/558 |
| drax/ref | ls-test-clean | mbr | +0.04 | [-0.07, +0.16] | [-0.07, 0.17] | 0.5271 | 17/15/568 |
| drax/main | ls-test-other | conf | +1.42 | [+1.05, +1.78] | [0.97, 1.86] | 0.0000 | 136/48/416 |
| drax/main | ls-test-other | mbr | +0.22 | [+0.03, +0.41] | [0.03, 0.41] | 0.0325 | 54/38/508 |
| drax/ref | ls-test-other | conf | +0.24 | [+0.01, +0.46] | [0.05, 0.43] | 0.0449 | 49/33/518 |
| drax/ref | ls-test-other | mbr | +0.08 | [-0.07, +0.23] | [-0.07, 0.22] | 0.2980 | 27/21/552 |
| drax/main | slr83 | conf | +0.82 | [+0.47, +1.18] | [0.50, 1.14] | 0.0000 | 89/45/466 |
| drax/main | slr83 | mbr | +0.17 | [-0.06, +0.40] | [-0.05, 0.40] | 0.1714 | 42/33/525 |
| drax/ref | slr83 | conf | +0.15 | [-0.15, +0.44] | [-0.14, 0.40] | 0.3198 | 46/42/512 |
| drax/ref | slr83 | mbr | +0.17 | [-0.04, +0.38] | [-0.03, 0.38] | 0.1042 | 34/24/542 |
| drax/main | spgispeech | conf | +0.83 | [+0.51, +1.15] | [0.51, 1.15] | 0.0000 | 152/84/364 |
| drax/main | spgispeech | mbr | +0.00 | [-0.20, +0.19] | [-0.18, 0.19] | 0.8331 | 54/61/485 |
| drax/ref | spgispeech | conf | -0.11 | [-0.30, +0.10] | [-0.31, 0.10] | 0.1496 | 63/86/451 |
| drax/ref | spgispeech | mbr | -0.56 | [-0.72, -0.40] | [-0.72, -0.41] | 0.0000 | 24/95/481 |
| drax/main | voxpopuli | conf | +0.90 | [+0.54, +1.26] | [0.53, 1.35] | 0.0000 | 107/53/440 |
| drax/main | voxpopuli | mbr | +0.02 | [-0.16, +0.19] | [-0.15, 0.18] | 0.9067 | 36/36/528 |
| drax/ref | voxpopuli | conf | -0.04 | [-0.23, +0.15] | [-0.22, 0.14] | 0.6960 | 36/41/523 |
| drax/ref | voxpopuli | mbr | -0.10 | [-0.26, +0.05] | [-0.26, 0.05] | 0.2065 | 27/39/534 |
| whisfusion/main | ami | conf | +3.37 | [+2.38, +4.41] | [2.57, 4.08] | 0.0000 | 121/41/238 |
| whisfusion/main | ami | mbr | +2.10 | [+1.55, +2.71] | [1.59, 2.60] | 0.0000 | 81/16/303 |
| whisfusion/main | common_voice | conf | +3.67 | [+2.56, +4.86] | [, ] | 0.0000 | 94/30/172 |
| whisfusion/main | common_voice | mbr | +2.37 | [+1.68, +3.11] | [, ] | 0.0000 | 65/13/218 |
| whisfusion/main | earnings22 | conf | +4.88 | [+4.06, +5.70] | [3.60, 5.92] | 0.0000 | 192/51/157 |
| whisfusion/main | earnings22 | mbr | +2.85 | [+2.32, +3.39] | [2.28, 3.30] | 0.0000 | 156/31/213 |
| whisfusion/main | fleurs-en | conf | +4.49 | [+3.92, +5.08] | [3.87, 5.12] | 0.0000 | 226/32/142 |
| whisfusion/main | fleurs-en | mbr | +2.21 | [+1.82, +2.60] | [1.81, 2.63] | 0.0000 | 155/26/219 |
| whisfusion/main | gigaspeech | conf | +3.45 | [+2.73, +4.15] | [2.67, 4.22] | 0.0000 | 165/55/180 |
| whisfusion/main | gigaspeech | mbr | +2.20 | [+1.70, +2.69] | [1.72, 2.70] | 0.0000 | 127/33/240 |
| whisfusion/main | ls-dev-clean | conf | +1.75 | [+1.35, +2.21] | [1.25, 2.24] | 0.0000 | 104/26/270 |
| whisfusion/main | ls-dev-clean | mbr | +0.82 | [+0.55, +1.11] | [0.50, 1.12] | 0.0000 | 63/15/322 |
| whisfusion/main | ls-dev-other | conf | +2.68 | [+2.06, +3.35] | [2.01, 3.34] | 0.0000 | 138/48/214 |
| whisfusion/main | ls-dev-other | mbr | +1.71 | [+1.28, +2.16] | [1.11, 2.41] | 0.0000 | 96/20/284 |
| whisfusion/main | ls-tc-babble0 | conf | +10.53 | [+9.38, +11.74] | [9.25, 11.86] | 0.0000 | 264/40/96 |
| whisfusion/main | ls-tc-babble0 | mbr | +7.99 | [+7.13, +8.88] | [7.07, 8.92] | 0.0000 | 250/16/134 |
| whisfusion/main | ls-tc-babble10 | conf | +4.55 | [+3.89, +5.26] | [3.76, 5.34] | 0.0000 | 178/28/194 |
| whisfusion/main | ls-tc-babble10 | mbr | +3.04 | [+2.56, +3.57] | [2.48, 3.61] | 0.0000 | 144/12/244 |
| whisfusion/main | ls-tc-babble5 | conf | +7.01 | [+6.16, +7.85] | [5.87, 8.12] | 0.0000 | 231/34/135 |
| whisfusion/main | ls-tc-babble5 | mbr | +4.73 | [+4.08, +5.36] | [3.95, 5.49] | 0.0000 | 183/23/194 |
| whisfusion/main | ls-tc-white5 | conf | +4.72 | [+4.03, +5.41] | [3.94, 5.51] | 0.0000 | 199/29/172 |
| whisfusion/main | ls-tc-white5 | mbr | +3.01 | [+2.49, +3.54] | [2.49, 3.52] | 0.0000 | 141/18/241 |
| whisfusion/main | ls-test-clean | conf | +2.09 | [+1.58, +2.63] | [1.54, 2.64] | 0.0000 | 106/25/269 |
| whisfusion/main | ls-test-clean | mbr | +1.40 | [+1.02, +1.82] | [1.01, 1.81] | 0.0000 | 76/13/311 |
| whisfusion/main | ls-test-other | conf | +3.47 | [+2.91, +4.01] | [2.94, 4.11] | 0.0000 | 152/25/223 |
| whisfusion/main | ls-test-other | mbr | +1.54 | [+1.18, +1.92] | [1.16, 1.98] | 0.0000 | 97/15/288 |
| whisfusion/main | slr83 | conf | +2.87 | [+2.26, +3.55] | [2.20, 3.60] | 0.0000 | 137/32/231 |
| whisfusion/main | slr83 | mbr | +1.61 | [+1.25, +2.01] | [1.23, 1.99] | 0.0000 | 88/13/299 |
| whisfusion/main | spgispeech | conf | +4.45 | [+3.89, +5.01] | [3.91, 4.97] | 0.0000 | 232/39/129 |
| whisfusion/main | spgispeech | mbr | +2.32 | [+1.96, +2.69] | [1.96, 2.68] | 0.0000 | 164/20/216 |
| whisfusion/main | voxpopuli | conf | +3.05 | [+2.47, +3.67] | [2.46, 3.64] | 0.0000 | 160/40/200 |
| whisfusion/main | voxpopuli | mbr | +2.05 | [+1.65, +2.50] | [1.65, 2.48] | 0.0000 | 118/20/262 |

## Pooled over test sets (random effects)

| model | arm | norm | a -> b | sets | pooled delta | 95% CI | I2 | sets sig + / - |
|---|---|---|---|---|---|---|---|---|
| drax | main | legacy | cm05 -> rover_cg | 19 | +0.71 | [+0.49, +0.93] | 0.92 | 16 / 0 |
| drax | main | legacy | conf -> mbr | 19 | +1.17 | [+0.96, +1.38] | 0.82 | 19 / 0 |
| drax | main | legacy | conf -> rover_c | 19 | +1.77 | [+1.42, +2.11] | 0.93 | 19 / 0 |
| drax | main | legacy | conf -> rover_cg | 19 | +1.73 | [+1.37, +2.08] | 0.93 | 19 / 0 |
| drax | main | legacy | conf -> rover_freq | 19 | +1.86 | [+1.48, +2.25] | 0.94 | 19 / 0 |
| drax | main | legacy | first -> conf | 19 | +4.07 | [+3.53, +4.62] | 0.92 | 19 / 0 |
| drax | main | legacy | first -> rover_cg | 19 | +6.00 | [+5.17, +6.82] | 0.96 | 19 / 0 |
| drax | main | legacy | mbr -> rover_cg | 19 | +0.52 | [+0.30, +0.74] | 0.95 | 12 / 0 |
| drax | main | legacy | rover_freq -> rover_cg | 19 | -0.12 | [-0.19, -0.04] | 0.71 | 0 / 6 |
| drax | main | whisper | cm05 -> rover_cg | 19 | -1.91 | [-2.83, -0.98] | 0.99 | 4 / 14 |
| drax | main | whisper | conf -> mbr | 19 | +0.98 | [+0.80, +1.16] | 0.73 | 18 / 0 |
| drax | main | whisper | conf -> rover_c | 19 | -0.97 | [-1.95, +0.00] | 0.98 | 5 / 9 |
| drax | main | whisper | conf -> rover_cg | 19 | -1.02 | [-2.00, -0.03] | 0.98 | 5 / 9 |
| drax | main | whisper | conf -> rover_freq | 19 | -0.93 | [-1.93, +0.06] | 0.98 | 5 / 9 |
| drax | main | whisper | first -> conf | 19 | +4.09 | [+3.54, +4.64] | 0.92 | 19 / 0 |
| drax | main | whisper | first -> rover_cg | 19 | +3.32 | [+2.04, +4.60] | 0.98 | 15 / 1 |
| drax | main | whisper | mbr -> rover_cg | 19 | -2.07 | [-2.92, -1.22] | 0.99 | 3 / 15 |
| drax | main | whisper | rover_freq -> rover_cg | 19 | -0.06 | [-0.13, +0.01] | 0.65 | 0 / 3 |
| drax | ref | legacy | cm05 -> rover_cg | 19 | +0.02 | [-0.07, +0.12] | 0.80 | 5 / 1 |
| drax | ref | legacy | conf -> mbr | 19 | +0.20 | [+0.12, +0.28] | 0.40 | 7 / 0 |
| drax | ref | legacy | conf -> rover_c | 19 | +0.27 | [+0.19, +0.34] | 0.43 | 10 / 0 |
| drax | ref | legacy | conf -> rover_cg | 19 | +0.20 | [+0.11, +0.29] | 0.58 | 8 / 0 |
| drax | ref | legacy | conf -> rover_freq | 19 | +0.26 | [+0.20, +0.33] | 0.26 | 8 / 0 |
| drax | ref | legacy | first -> conf | 19 | +0.22 | [+0.14, +0.30] | 0.26 | 7 / 0 |
| drax | ref | legacy | first -> rover_cg | 19 | +0.46 | [+0.33, +0.59] | 0.76 | 14 / 0 |
| drax | ref | legacy | mbr -> rover_cg | 19 | +0.02 | [-0.08, +0.12] | 0.82 | 2 / 1 |
| drax | ref | legacy | rover_freq -> rover_cg | 19 | -0.07 | [-0.11, -0.02] | 0.53 | 0 / 4 |
| drax | ref | whisper | cm05 -> rover_cg | 19 | -2.73 | [-3.56, -1.90] | 0.99 | 0 / 16 |
| drax | ref | whisper | conf -> mbr | 19 | +0.13 | [+0.07, +0.19] | 0.11 | 3 / 0 |
| drax | ref | whisper | conf -> rover_c | 19 | -2.53 | [-3.37, -1.68] | 0.99 | 1 / 16 |
| drax | ref | whisper | conf -> rover_cg | 19 | -2.59 | [-3.45, -1.74] | 0.99 | 1 / 16 |
| drax | ref | whisper | conf -> rover_freq | 19 | -2.54 | [-3.39, -1.69] | 0.99 | 1 / 16 |
| drax | ref | whisper | first -> conf | 19 | +0.22 | [+0.15, +0.28] | 0.06 | 5 / 0 |
| drax | ref | whisper | first -> rover_cg | 19 | -2.31 | [-3.20, -1.43] | 0.99 | 3 / 15 |
| drax | ref | whisper | mbr -> rover_cg | 19 | -2.69 | [-3.51, -1.87] | 0.99 | 0 / 15 |
| drax | ref | whisper | rover_freq -> rover_cg | 19 | -0.04 | [-0.08, +0.00] | 0.46 | 0 / 4 |
| whisfusion | main | legacy | cm05 -> rover_cg | 14 | +3.02 | [+2.35, +3.68] | 0.95 | 14 / 0 |
| whisfusion | main | legacy | conf -> mbr | 14 | +1.63 | [+1.32, +1.95] | 0.74 | 14 / 0 |
| whisfusion | main | legacy | conf -> rover_c | 14 | +4.38 | [+3.55, +5.22] | 0.95 | 14 / 0 |
| whisfusion | main | legacy | conf -> rover_cg | 14 | +4.43 | [+3.60, +5.26] | 0.95 | 14 / 0 |
| whisfusion | main | legacy | conf -> rover_freq | 14 | +3.70 | [+2.98, +4.43] | 0.93 | 14 / 0 |
| whisfusion | main | legacy | first -> conf | 14 | +7.44 | [+6.76, +8.13] | 0.82 | 14 / 0 |
| whisfusion | main | legacy | first -> rover_cg | 14 | +11.98 | [+10.63, +13.33] | 0.95 | 14 / 0 |
| whisfusion | main | legacy | mbr -> rover_cg | 14 | +2.77 | [+2.17, +3.37] | 0.96 | 14 / 0 |
| whisfusion | main | legacy | rover_freq -> rover_cg | 14 | +0.64 | [+0.47, +0.81] | 0.80 | 13 / 0 |
| whisfusion | main | whisper | cm05 -> rover_cg | 14 | +1.40 | [+0.37, +2.43] | 0.96 | 9 / 2 |
| whisfusion | main | whisper | conf -> mbr | 14 | +1.52 | [+1.18, +1.85] | 0.75 | 12 / 0 |
| whisfusion | main | whisper | conf -> rover_c | 14 | +2.72 | [+1.54, +3.89] | 0.96 | 10 / 1 |
| whisfusion | main | whisper | conf -> rover_cg | 14 | +2.77 | [+1.60, +3.93] | 0.96 | 11 / 1 |
| whisfusion | main | whisper | conf -> rover_freq | 14 | +2.02 | [+0.96, +3.08] | 0.95 | 10 / 1 |
| whisfusion | main | whisper | first -> conf | 14 | +7.64 | [+6.87, +8.41] | 0.86 | 14 / 0 |
| whisfusion | main | whisper | first -> rover_cg | 14 | +10.48 | [+8.89, +12.07] | 0.96 | 14 / 0 |
| whisfusion | main | whisper | mbr -> rover_cg | 14 | +1.24 | [+0.26, +2.23] | 0.97 | 8 / 2 |
| whisfusion | main | whisper | rover_freq -> rover_cg | 14 | +0.67 | [+0.49, +0.85] | 0.83 | 13 / 0 |

## Against each model's standard decoding

| model | set | comparison | WER a | WER b | delta | 95% CI |
|---|---|---|---|---|---|---|
| drax | ami | Drax standard (T=0.1, 1 sample) vs ROVER@main | 11.48 | 11.10 | +0.37 | [-0.17, +0.89] |
| drax | common_voice | Drax standard (T=0.1, 1 sample) vs ROVER@main | 13.53 | 13.09 | +0.45 | [-0.18, +1.11] |
| drax | earnings22 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 20.97 | 22.74 | -1.77 | [-2.77, -0.85] |
| drax | fleurs-de | Drax standard (T=0.1, 1 sample) vs ROVER@main | 9.24 | 7.94 | +1.31 | [+0.98, +1.65] |
| drax | fleurs-en | Drax standard (T=0.1, 1 sample) vs ROVER@main | 9.95 | 9.64 | +0.32 | [-0.01, +0.63] |
| drax | fleurs-es | Drax standard (T=0.1, 1 sample) vs ROVER@main | 6.69 | 6.00 | +0.69 | [+0.43, +0.97] |
| drax | fleurs-fr | Drax standard (T=0.1, 1 sample) vs ROVER@main | 11.94 | 11.17 | +0.77 | [+0.41, +1.15] |
| drax | fleurs-it | Drax standard (T=0.1, 1 sample) vs ROVER@main | 6.96 | 5.87 | +1.08 | [+0.75, +1.43] |
| drax | fleurs-pt | Drax standard (T=0.1, 1 sample) vs ROVER@main | 13.68 | 12.07 | +1.62 | [+1.18, +2.05] |
| drax | gigaspeech | Drax standard (T=0.1, 1 sample) vs ROVER@main | 14.50 | 13.91 | +0.59 | [+0.19, +1.01] |
| drax | ls-dev-clean | Drax standard (T=0.1, 1 sample) vs ROVER@main | 3.11 | 2.78 | +0.33 | [+0.06, +0.59] |
| drax | ls-dev-other | Drax standard (T=0.1, 1 sample) vs ROVER@main | 5.83 | 5.47 | +0.36 | [-0.01, +0.75] |
| drax | ls-tc-babble0 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 35.54 | 36.86 | -1.32 | [-2.26, -0.41] |
| drax | ls-tc-babble10 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 4.54 | 4.11 | +0.43 | [+0.15, +0.71] |
| drax | ls-tc-babble5 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 9.53 | 9.42 | +0.11 | [-0.28, +0.48] |
| drax | ls-tc-white5 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 7.26 | 7.02 | +0.23 | [-0.08, +0.53] |
| drax | ls-test-clean | Drax standard (T=0.1, 1 sample) vs ROVER@main | 2.57 | 2.41 | +0.16 | [-0.03, +0.35] |
| drax | ls-test-other | Drax standard (T=0.1, 1 sample) vs ROVER@main | 6.36 | 5.73 | +0.63 | [+0.35, +0.92] |
| drax | slr83 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 7.59 | 6.83 | +0.76 | [+0.38, +1.14] |
| drax | spgispeech | Drax standard (T=0.1, 1 sample) vs ROVER@main | 7.58 | 7.56 | +0.01 | [-0.27, +0.30] |
| drax | voxpopuli | Drax standard (T=0.1, 1 sample) vs ROVER@main | 7.75 | 7.65 | +0.09 | [-0.18, +0.35] |
| drax | ami | Drax standard vs confidence pick@main | 11.48 | 14.11 | -2.63 | [-3.39, -1.91] |
| drax | common_voice | Drax standard vs confidence pick@main | 13.53 | 14.89 | -1.36 | [-2.21, -0.53] |
| drax | earnings22 | Drax standard vs confidence pick@main | 20.97 | 25.28 | -4.32 | [-6.16, -2.77] |
| drax | fleurs-de | Drax standard vs confidence pick@main | 9.24 | 9.74 | -0.49 | [-0.96, -0.02] |
| drax | fleurs-en | Drax standard vs confidence pick@main | 9.95 | 11.36 | -1.41 | [-1.86, -0.96] |
| drax | fleurs-es | Drax standard vs confidence pick@main | 6.69 | 6.92 | -0.23 | [-0.56, +0.08] |
| drax | fleurs-fr | Drax standard vs confidence pick@main | 11.94 | 12.72 | -0.79 | [-1.26, -0.32] |
| drax | fleurs-it | Drax standard vs confidence pick@main | 6.96 | 7.09 | -0.14 | [-0.56, +0.29] |
| drax | fleurs-pt | Drax standard vs confidence pick@main | 13.68 | 14.75 | -1.06 | [-1.58, -0.52] |
| drax | gigaspeech | Drax standard vs confidence pick@main | 14.50 | 15.52 | -1.02 | [-1.55, -0.45] |
| drax | ls-dev-clean | Drax standard vs confidence pick@main | 3.11 | 3.20 | -0.09 | [-0.40, +0.19] |
| drax | ls-dev-other | Drax standard vs confidence pick@main | 5.83 | 6.76 | -0.93 | [-1.49, -0.40] |
| drax | ls-tc-babble0 | Drax standard vs confidence pick@main | 35.54 | 42.81 | -7.27 | [-8.44, -6.21] |
| drax | ls-tc-babble10 | Drax standard vs confidence pick@main | 4.54 | 5.30 | -0.76 | [-1.13, -0.39] |
| drax | ls-tc-babble5 | Drax standard vs confidence pick@main | 9.53 | 11.90 | -2.37 | [-2.93, -1.82] |
| drax | ls-tc-white5 | Drax standard vs confidence pick@main | 7.26 | 8.77 | -1.51 | [-1.94, -1.10] |
| drax | ls-test-clean | Drax standard vs confidence pick@main | 2.57 | 2.81 | -0.24 | [-0.50, -0.01] |
| drax | ls-test-other | Drax standard vs confidence pick@main | 6.36 | 7.15 | -0.79 | [-1.13, -0.44] |
| drax | slr83 | Drax standard vs confidence pick@main | 7.59 | 7.65 | -0.06 | [-0.54, +0.41] |
| drax | spgispeech | Drax standard vs confidence pick@main | 7.58 | 8.39 | -0.81 | [-1.17, -0.44] |
| drax | voxpopuli | Drax standard vs confidence pick@main | 7.75 | 8.55 | -0.81 | [-1.20, -0.46] |
| drax | ami | Drax standard vs MBR pick@main | 11.48 | 11.40 | +0.07 | [-0.46, +0.62] |
| drax | common_voice | Drax standard vs MBR pick@main | 13.53 | 13.36 | +0.17 | [-0.49, +0.83] |
| drax | earnings22 | Drax standard vs MBR pick@main | 20.97 | 23.21 | -2.24 | [-3.24, -1.26] |
| drax | fleurs-de | Drax standard vs MBR pick@main | 9.24 | 8.45 | +0.80 | [+0.45, +1.16] |
| drax | fleurs-en | Drax standard vs MBR pick@main | 9.95 | 10.16 | -0.20 | [-0.57, +0.16] |
| drax | fleurs-es | Drax standard vs MBR pick@main | 6.69 | 6.16 | +0.53 | [+0.29, +0.78] |
| drax | fleurs-fr | Drax standard vs MBR pick@main | 11.94 | 11.76 | +0.17 | [-0.20, +0.55] |
| drax | fleurs-it | Drax standard vs MBR pick@main | 6.96 | 6.36 | +0.60 | [+0.26, +0.94] |
| drax | fleurs-pt | Drax standard vs MBR pick@main | 13.68 | 13.20 | +0.48 | [-0.02, +0.96] |
| drax | gigaspeech | Drax standard vs MBR pick@main | 14.50 | 14.45 | +0.05 | [-0.38, +0.50] |
| drax | ls-dev-clean | Drax standard vs MBR pick@main | 3.11 | 2.82 | +0.29 | [+0.03, +0.55] |
| drax | ls-dev-other | Drax standard vs MBR pick@main | 5.83 | 5.79 | +0.04 | [-0.35, +0.43] |
| drax | ls-tc-babble0 | Drax standard vs MBR pick@main | 35.54 | 41.13 | -5.59 | [-6.64, -4.54] |
| drax | ls-tc-babble10 | Drax standard vs MBR pick@main | 4.54 | 4.14 | +0.40 | [+0.14, +0.67] |
| drax | ls-tc-babble5 | Drax standard vs MBR pick@main | 9.53 | 10.12 | -0.59 | [-1.06, -0.15] |
| drax | ls-tc-white5 | Drax standard vs MBR pick@main | 7.26 | 7.41 | -0.15 | [-0.48, +0.18] |
| drax | ls-test-clean | Drax standard vs MBR pick@main | 2.57 | 2.38 | +0.18 | [+0.01, +0.37] |
| drax | ls-test-other | Drax standard vs MBR pick@main | 6.36 | 5.95 | +0.41 | [+0.12, +0.71] |
| drax | slr83 | Drax standard vs MBR pick@main | 7.59 | 7.00 | +0.59 | [+0.19, +0.96] |
| drax | spgispeech | Drax standard vs MBR pick@main | 7.58 | 7.56 | +0.01 | [-0.29, +0.32] |
| drax | voxpopuli | Drax standard vs MBR pick@main | 7.75 | 7.67 | +0.07 | [-0.18, +0.32] |
| drax | ami | ROVER@T=0.1 vs ROVER@main | 11.23 | 11.10 | +0.13 | [-0.35, +0.60] |
| drax | common_voice | ROVER@T=0.1 vs ROVER@main | 12.64 | 13.09 | -0.45 | [-1.01, +0.12] |
| drax | earnings22 | ROVER@T=0.1 vs ROVER@main | 20.70 | 22.74 | -2.04 | [-3.09, -1.12] |
| drax | fleurs-de | ROVER@T=0.1 vs ROVER@main | 8.43 | 7.94 | +0.49 | [+0.21, +0.76] |
| drax | fleurs-en | ROVER@T=0.1 vs ROVER@main | 9.55 | 9.64 | -0.08 | [-0.36, +0.18] |
| drax | fleurs-es | ROVER@T=0.1 vs ROVER@main | 6.09 | 6.00 | +0.10 | [-0.12, +0.32] |
| drax | fleurs-fr | ROVER@T=0.1 vs ROVER@main | 11.38 | 11.17 | +0.22 | [-0.07, +0.50] |
| drax | fleurs-it | ROVER@T=0.1 vs ROVER@main | 6.33 | 5.87 | +0.45 | [+0.21, +0.71] |
| drax | fleurs-pt | ROVER@T=0.1 vs ROVER@main | 12.57 | 12.07 | +0.50 | [+0.12, +0.87] |
| drax | gigaspeech | ROVER@T=0.1 vs ROVER@main | 14.11 | 13.91 | +0.19 | [-0.19, +0.57] |
| drax | ls-dev-clean | ROVER@T=0.1 vs ROVER@main | 2.66 | 2.78 | -0.12 | [-0.34, +0.09] |
| drax | ls-dev-other | ROVER@T=0.1 vs ROVER@main | 5.61 | 5.47 | +0.14 | [-0.21, +0.47] |
| drax | ls-tc-babble0 | ROVER@T=0.1 vs ROVER@main | 34.95 | 36.86 | -1.90 | [-2.75, -1.08] |
| drax | ls-tc-babble10 | ROVER@T=0.1 vs ROVER@main | 4.18 | 4.11 | +0.07 | [-0.14, +0.28] |
| drax | ls-tc-babble5 | ROVER@T=0.1 vs ROVER@main | 8.95 | 9.42 | -0.47 | [-0.79, -0.16] |
| drax | ls-tc-white5 | ROVER@T=0.1 vs ROVER@main | 6.77 | 7.02 | -0.25 | [-0.53, +0.01] |
| drax | ls-test-clean | ROVER@T=0.1 vs ROVER@main | 2.35 | 2.41 | -0.06 | [-0.24, +0.11] |
| drax | ls-test-other | ROVER@T=0.1 vs ROVER@main | 5.82 | 5.73 | +0.09 | [-0.13, +0.33] |
| drax | slr83 | ROVER@T=0.1 vs ROVER@main | 7.05 | 6.83 | +0.22 | [-0.07, +0.49] |
| drax | spgispeech | ROVER@T=0.1 vs ROVER@main | 7.67 | 7.56 | +0.11 | [-0.11, +0.34] |
| drax | voxpopuli | ROVER@T=0.1 vs ROVER@main | 7.70 | 7.65 | +0.05 | [-0.17, +0.26] |
| whisfusion | ami | Whisfusion upstream (K=15 confidence) vs ROVER@main | 37.50 | 33.26 | +4.24 | [+3.17, +5.39] |
| whisfusion | common_voice | Whisfusion upstream (K=15 confidence) vs ROVER@main | 33.19 | 28.95 | +4.24 | [+3.06, +5.42] |
| whisfusion | earnings22 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 40.11 | 34.40 | +5.71 | [+4.89, +6.55] |
| whisfusion | fleurs-en | Whisfusion upstream (K=15 confidence) vs ROVER@main | 28.27 | 23.47 | +4.80 | [+4.25, +5.36] |
| whisfusion | gigaspeech | Whisfusion upstream (K=15 confidence) vs ROVER@main | 25.93 | 21.48 | +4.45 | [+3.72, +5.14] |
| whisfusion | ls-dev-clean | Whisfusion upstream (K=15 confidence) vs ROVER@main | 7.30 | 5.32 | +1.98 | [+1.53, +2.47] |
| whisfusion | ls-dev-other | Whisfusion upstream (K=15 confidence) vs ROVER@main | 16.15 | 12.63 | +3.52 | [+2.86, +4.18] |
| whisfusion | ls-tc-babble0 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 69.39 | 58.28 | +11.11 | [+10.01, +12.23] |
| whisfusion | ls-tc-babble10 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 16.70 | 11.40 | +5.31 | [+4.58, +6.01] |
| whisfusion | ls-tc-babble5 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 32.82 | 24.41 | +8.41 | [+7.49, +9.35] |
| whisfusion | ls-tc-white5 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 24.75 | 18.96 | +5.79 | [+5.02, +6.57] |
| whisfusion | ls-test-clean | Whisfusion upstream (K=15 confidence) vs ROVER@main | 7.75 | 5.51 | +2.25 | [+1.72, +2.79] |
| whisfusion | ls-test-other | Whisfusion upstream (K=15 confidence) vs ROVER@main | 15.87 | 11.92 | +3.95 | [+3.34, +4.55] |
| whisfusion | slr83 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 20.69 | 17.05 | +3.64 | [+2.95, +4.34] |
| whisfusion | spgispeech | Whisfusion upstream (K=15 confidence) vs ROVER@main | 20.46 | 14.88 | +5.58 | [+5.00, +6.16] |
| whisfusion | voxpopuli | Whisfusion upstream (K=15 confidence) vs ROVER@main | 21.82 | 18.05 | +3.76 | [+3.14, +4.40] |
| whisfusion | ami | Whisfusion upstream vs ROVER at the same K=15 | 37.50 | 33.53 | +3.97 | [+2.88, +5.07] |
| whisfusion | common_voice | Whisfusion upstream vs ROVER at the same K=15 | 33.19 | 29.49 | +3.71 | [+2.58, +4.94] |
| whisfusion | earnings22 | Whisfusion upstream vs ROVER at the same K=15 | 40.11 | 35.07 | +5.03 | [+4.21, +5.93] |
| whisfusion | fleurs-en | Whisfusion upstream vs ROVER at the same K=15 | 28.27 | 23.80 | +4.47 | [+3.85, +5.12] |
| whisfusion | gigaspeech | Whisfusion upstream vs ROVER at the same K=15 | 25.93 | 21.54 | +4.38 | [+3.69, +5.07] |
| whisfusion | ls-dev-clean | Whisfusion upstream vs ROVER at the same K=15 | 7.30 | 5.48 | +1.83 | [+1.39, +2.30] |
| whisfusion | ls-dev-other | Whisfusion upstream vs ROVER at the same K=15 | 16.15 | 12.89 | +3.26 | [+2.64, +3.92] |
| whisfusion | ls-tc-babble0 | Whisfusion upstream vs ROVER at the same K=15 | 69.39 | 58.66 | +10.74 | [+9.62, +11.84] |
| whisfusion | ls-tc-babble10 | Whisfusion upstream vs ROVER at the same K=15 | 16.70 | 11.69 | +5.01 | [+4.31, +5.74] |
| whisfusion | ls-tc-babble5 | Whisfusion upstream vs ROVER at the same K=15 | 32.82 | 25.38 | +7.44 | [+6.54, +8.35] |
| whisfusion | ls-tc-white5 | Whisfusion upstream vs ROVER at the same K=15 | 24.75 | 19.41 | +5.34 | [+4.55, +6.17] |
| whisfusion | ls-test-clean | Whisfusion upstream vs ROVER at the same K=15 | 7.75 | 5.55 | +2.20 | [+1.66, +2.77] |
| whisfusion | ls-test-other | Whisfusion upstream vs ROVER at the same K=15 | 15.87 | 12.19 | +3.68 | [+3.08, +4.26] |
| whisfusion | slr83 | Whisfusion upstream vs ROVER at the same K=15 | 20.69 | 17.49 | +3.20 | [+2.54, +3.87] |
| whisfusion | spgispeech | Whisfusion upstream vs ROVER at the same K=15 | 20.46 | 15.17 | +5.29 | [+4.71, +5.83] |
| whisfusion | voxpopuli | Whisfusion upstream vs ROVER at the same K=15 | 21.82 | 18.63 | +3.19 | [+2.59, +3.83] |

## Tuned on dev (ls-dev-clean + ls-dev-other), reported on test

- **drax**: alpha=0.7, eps=0.3, gamma=0.5, lambda=3.0 (dev: select 4.35, ROVER 4.07, n=800)
- **whisfusion**: alpha=0.5, eps=0.7, gamma=1.0, lambda=1.5 (dev: select 10.00, ROVER 8.87, n=800)

| model | set | tuned select | tuned ROVER | delta | 95% CI |
|---|---|---|---|---|---|
| drax | ami | 11.36 | 11.03 | +0.33 | [-0.06, +0.73] |
| drax | common_voice | 37.48 | 37.13 | +0.34 | [+0.00, +0.71] |
| drax | earnings22 | 23.12 | 22.69 | +0.43 | [-0.02, +0.86] |
| drax | fleurs-de | 8.42 | 7.95 | +0.47 | [+0.24, +0.69] |
| drax | fleurs-en | 10.19 | 9.51 | +0.67 | [+0.42, +0.92] |
| drax | fleurs-es | 6.17 | 5.97 | +0.20 | [+0.05, +0.36] |
| drax | fleurs-fr | 11.74 | 11.09 | +0.65 | [+0.39, +0.91] |
| drax | fleurs-it | 6.37 | 5.94 | +0.43 | [+0.22, +0.67] |
| drax | fleurs-pt | 13.27 | 12.01 | +1.26 | [+0.95, +1.57] |
| drax | gigaspeech | 14.38 | 13.75 | +0.63 | [+0.36, +0.90] |
| drax | ls-tc-babble0 | 40.75 | 36.62 | +4.13 | [+3.58, +4.69] |
| drax | ls-tc-babble10 | 4.25 | 4.09 | +0.17 | [+0.01, +0.32] |
| drax | ls-tc-babble5 | 10.24 | 9.24 | +1.00 | [+0.67, +1.33] |
| drax | ls-tc-white5 | 7.43 | 6.97 | +0.46 | [+0.21, +0.71] |
| drax | ls-test-clean | 2.38 | 2.32 | +0.07 | [-0.08, +0.21] |
| drax | ls-test-other | 5.98 | 5.71 | +0.27 | [+0.07, +0.49] |
| drax | slr83 | 6.99 | 6.69 | +0.30 | [+0.08, +0.52] |
| drax | spgispeech | 7.55 | 7.55 | +0.00 | [-0.18, +0.18] |
| drax | voxpopuli | 7.72 | 7.64 | +0.07 | [-0.10, +0.25] |
| whisfusion | ami | 35.39 | 33.29 | +2.10 | [+1.46, +2.78] |
| whisfusion | common_voice | 52.21 | 50.53 | +1.67 | [+1.04, +2.30] |
| whisfusion | earnings22 | 37.37 | 34.45 | +2.92 | [+2.29, +3.54] |
| whisfusion | fleurs-en | 25.64 | 23.47 | +2.17 | [+1.76, +2.58] |
| whisfusion | gigaspeech | 23.70 | 21.48 | +2.22 | [+1.76, +2.70] |
| whisfusion | ls-tc-babble0 | 65.94 | 58.31 | +7.63 | [+6.69, +8.59] |
| whisfusion | ls-tc-babble10 | 14.54 | 11.47 | +3.07 | [+2.53, +3.64] |
| whisfusion | ls-tc-babble5 | 29.25 | 24.43 | +4.82 | [+4.17, +5.42] |
| whisfusion | ls-tc-white5 | 21.86 | 18.94 | +2.92 | [+2.36, +3.48] |
| whisfusion | ls-test-clean | 6.71 | 5.55 | +1.16 | [+0.76, +1.58] |
| whisfusion | ls-test-other | 13.61 | 11.98 | +1.63 | [+1.24, +2.00] |
| whisfusion | slr83 | 18.71 | 17.10 | +1.61 | [+1.25, +2.00] |
| whisfusion | spgispeech | 17.28 | 14.91 | +2.37 | [+2.00, +2.74] |
| whisfusion | voxpopuli | 19.79 | 18.11 | +1.68 | [+1.30, +2.11] |

## Cost

| model | kind | arm | K | T | steps | n | s/utt | encode s | decode s | RTF | ms/candidate | ROVER ms | peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drax | kscale | K64 | 64 | 1.30 | 16 | 200 | 14.404 | 0.186 | 14.218 | 2.2079 | 222.2 | 2.92 | 5954 |
| drax | main | main | 16 | 1.30 | 16 | 11414 | 3.718 | 0.099 | 3.620 | 0.4684 | 226.2 | 0.74 | 4336 |
| drax | main | ref | 4 | 0.10 | 16 | 11414 | 1.050 | 0.099 | 0.951 | 0.1323 | 237.8 | 0.22 | 4336 |
| drax | sweepT | T0.1 | 16 | 0.10 | 16 | 200 | 3.791 | 0.029 | 3.762 | 0.5835 | 235.1 | 0.75 | 4336 |
| drax | sweepT | T0.4 | 16 | 0.40 | 16 | 200 | 3.776 | 0.029 | 3.747 | 0.5811 | 234.2 | 0.74 | 4336 |
| drax | sweepT | T0.7 | 16 | 0.70 | 16 | 200 | 3.775 | 0.029 | 3.746 | 0.5810 | 234.1 | 0.64 | 4336 |
| drax | sweepT | T1 | 16 | 1.00 | 16 | 200 | 3.776 | 0.029 | 3.748 | 0.5812 | 234.2 | 0.40 | 4336 |
| drax | sweepT | T1.3 | 16 | 1.30 | 16 | 200 | 3.777 | 0.029 | 3.748 | 0.5813 | 234.2 | 0.57 | 4336 |
| drax | sweepT | T1.6 | 16 | 1.60 | 16 | 200 | 3.778 | 0.029 | 3.749 | 0.5814 | 234.3 | 0.57 | 4336 |
| drax | sweepT | T2 | 16 | 2.00 | 16 | 200 | 3.783 | 0.029 | 3.754 | 0.5822 | 234.6 | 1.01 | 4336 |
| whisfusion | ablation | base16 | 16 |  | 4 | 200 | 1.146 | 0.015 | 1.131 | 0.1764 | 70.7 | 1.05 | 2454 |
| whisfusion | ablation | fss_T1 | 16 |  | 4 | 200 | 1.178 | 0.015 | 1.163 | 0.1813 | 72.7 | 0.93 | 2454 |
| whisfusion | ablation | steps8 | 16 |  | 8 | 200 | 2.263 | 0.015 | 2.248 | 0.3483 | 140.5 | 1.03 | 2454 |
| whisfusion | main | main | 32 |  | 4 | 6400 | 2.367 | 0.038 | 2.329 | 0.3442 | 72.8 | 1.69 | 4205 |
