# Campaign report

generated 2026-09-21 08:55 UTC

utterance decodes analysed: 936395; cells: 2189


## Main arm at the largest K, corpus WER (Whisper normalisation)

| model | set | n | K | first | conf | MBR | ROVER | ROVER-cg | oracle | oracle-comp | control | pairwise % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drax/main | ami | 1000 | 16 | 16.74 | 12.66 | 10.74 | 10.30 | 10.52 | 7.18 | 3.96 | 6.19 | 24.3 |
| drax/ref | ami | 1000 | 4 | 10.60 | 10.32 | 10.14 | 10.20 | 10.43 | 8.20 | 6.54 | 6.76 | 7.1 |
| drax/main | common_voice | 773 | 16 | 21.31 | 15.24 | 13.87 | 13.34 | 13.46 | 9.84 | 7.23 | 9.36 | 22.8 |
| drax/ref | common_voice | 773 | 4 | 13.39 | 12.82 | 12.68 | 12.49 | 12.62 | 10.37 | 9.16 | 9.76 | 7.7 |
| drax/main | earnings22 | 1000 | 16 | 32.96 | 19.64 | 16.66 | 16.06 | 16.15 | 12.88 | 6.92 | 10.35 | 32.2 |
| drax/ref | earnings22 | 1000 | 4 | 14.57 | 13.90 | 13.88 | 14.00 | 14.24 | 11.61 | 9.01 | 9.60 | 9.0 |
| drax/main | fleurs-de | 746 | 16 | 15.00 | 12.06 | 10.81 | 10.17 | 10.15 | 8.31 | 4.28 | 6.52 | 13.9 |
| drax/ref | fleurs-de | 746 | 4 | 11.58 | 10.93 | 10.69 | 10.45 | 10.50 | 9.13 | 5.90 | 6.83 | 6.1 |
| drax/main | fleurs-en | 646 | 16 | 14.16 | 10.70 | 9.46 | 8.93 | 8.95 | 7.47 | 3.64 | 5.85 | 14.1 |
| drax/ref | fleurs-en | 646 | 4 | 9.54 | 9.33 | 8.84 | 8.90 | 8.94 | 7.68 | 4.87 | 5.37 | 4.5 |
| drax/main | fleurs-es | 600 | 16 | 11.45 | 8.97 | 8.21 | 8.05 | 8.07 | 6.60 | 3.16 | 4.63 | 9.6 |
| drax/ref | fleurs-es | 600 | 4 | 8.62 | 8.37 | 8.25 | 8.13 | 8.14 | 7.28 | 4.25 | 4.66 | 3.2 |
| drax/main | fleurs-fr | 542 | 16 | 17.23 | 13.96 | 12.94 | 12.51 | 12.53 | 10.51 | 5.10 | 8.38 | 14.5 |
| drax/ref | fleurs-fr | 542 | 4 | 13.27 | 13.07 | 12.98 | 12.77 | 12.87 | 11.15 | 7.19 | 8.20 | 5.9 |
| drax/main | fleurs-it | 600 | 16 | 12.72 | 9.52 | 8.72 | 8.28 | 8.34 | 6.84 | 3.07 | 4.63 | 11.3 |
| drax/ref | fleurs-it | 600 | 4 | 9.36 | 9.01 | 8.76 | 8.69 | 8.69 | 7.57 | 4.22 | 4.69 | 4.0 |
| drax/main | fleurs-pt | 600 | 16 | 20.90 | 16.51 | 14.88 | 13.87 | 13.88 | 12.42 | 5.30 | 9.47 | 19.2 |
| drax/ref | fleurs-pt | 600 | 4 | 15.36 | 14.92 | 14.49 | 14.20 | 14.28 | 12.76 | 7.26 | 8.66 | 7.7 |
| drax/main | gigaspeech | 1000 | 16 | 18.22 | 13.25 | 12.43 | 11.74 | 11.74 | 9.56 | 6.34 | 8.51 | 19.5 |
| drax/ref | gigaspeech | 1000 | 4 | 12.19 | 12.03 | 11.93 | 11.80 | 11.94 | 10.03 | 8.04 | 8.49 | 6.0 |
| drax/main | ls-dev-clean | 400 | 16 | 5.14 | 3.48 | 2.70 | 2.70 | 2.70 | 1.48 | 1.04 | 1.40 | 7.8 |
| drax/ref | ls-dev-clean | 400 | 4 | 3.09 | 2.86 | 2.82 | 2.74 | 2.74 | 2.17 | 1.96 | 2.02 | 1.6 |
| drax/main | ls-dev-other | 400 | 16 | 9.81 | 6.78 | 6.12 | 5.75 | 5.81 | 4.35 | 2.50 | 4.10 | 12.1 |
| drax/ref | ls-dev-other | 400 | 4 | 5.78 | 5.60 | 5.49 | 5.47 | 5.51 | 4.73 | 3.87 | 4.17 | 2.8 |
| drax/main | ls-tc-babble0 | 600 | 16 | 53.46 | 42.60 | 40.80 | 37.23 | 37.22 | 34.95 | 23.25 | 32.01 | 57.4 |
| drax/ref | ls-tc-babble0 | 600 | 4 | 35.32 | 35.05 | 35.63 | 34.85 | 34.84 | 30.91 | 26.85 | 28.81 | 25.3 |
| drax/main | ls-tc-babble10 | 600 | 16 | 7.74 | 4.98 | 3.95 | 3.85 | 3.88 | 2.64 | 1.79 | 2.55 | 11.1 |
| drax/ref | ls-tc-babble10 | 600 | 4 | 4.34 | 4.14 | 3.95 | 3.87 | 3.97 | 3.24 | 2.80 | 2.96 | 2.6 |
| drax/main | ls-tc-babble15 | 600 | 16 | 5.41 | 3.33 | 2.67 | 2.61 | 2.62 | 1.65 | 1.06 | 1.57 | 8.3 |
| drax/ref | ls-tc-babble15 | 600 | 4 | 2.90 | 2.80 | 2.68 | 2.63 | 2.69 | 2.09 | 1.79 | 1.90 | 1.8 |
| drax/main | ls-tc-babble5 | 600 | 16 | 16.17 | 11.58 | 9.88 | 9.21 | 9.24 | 7.67 | 4.36 | 7.25 | 21.4 |
| drax/ref | ls-tc-babble5 | 600 | 4 | 9.36 | 9.34 | 8.84 | 8.85 | 8.90 | 7.41 | 6.30 | 6.84 | 6.7 |
| drax/main | ls-tc-babbleM5 | 600 | 16 | 105.79 | 98.39 | 92.56 | 90.91 | 90.92 | 85.34 | 77.74 | 79.14 | 93.8 |
| drax/ref | ls-tc-babbleM5 | 600 | 4 | 90.07 | 90.96 | 91.70 | 90.94 | 90.92 | 87.05 | 86.45 | 86.45 | 57.3 |
| drax/main | ls-tc-white0 | 600 | 16 | 25.01 | 19.46 | 17.38 | 15.59 | 15.62 | 14.54 | 8.13 | 13.74 | 31.4 |
| drax/ref | ls-tc-white0 | 600 | 4 | 16.07 | 15.57 | 15.11 | 14.99 | 15.03 | 13.20 | 11.17 | 12.38 | 10.1 |
| drax/main | ls-tc-white10 | 600 | 16 | 7.69 | 4.70 | 3.94 | 3.71 | 3.85 | 2.51 | 1.62 | 2.42 | 11.3 |
| drax/ref | ls-tc-white10 | 600 | 4 | 4.19 | 3.98 | 3.78 | 3.86 | 3.88 | 3.13 | 2.73 | 2.88 | 2.5 |
| drax/main | ls-tc-white5 | 600 | 16 | 11.80 | 8.59 | 7.26 | 6.73 | 6.81 | 5.53 | 3.15 | 5.23 | 16.4 |
| drax/ref | ls-tc-white5 | 600 | 4 | 7.12 | 6.95 | 6.66 | 6.66 | 6.70 | 5.53 | 4.81 | 5.18 | 4.5 |
| drax/main | ls-test-clean | 1000 | 16 | 5.10 | 2.87 | 2.24 | 2.17 | 2.25 | 1.35 | 0.93 | 1.32 | 7.8 |
| drax/ref | ls-test-clean | 1000 | 4 | 2.40 | 2.34 | 2.23 | 2.26 | 2.27 | 1.68 | 1.45 | 1.53 | 1.6 |
| drax/main | ls-test-other | 1000 | 16 | 9.91 | 6.76 | 5.67 | 5.34 | 5.44 | 3.85 | 2.36 | 3.68 | 13.9 |
| drax/ref | ls-test-other | 1000 | 4 | 5.96 | 5.69 | 5.59 | 5.50 | 5.55 | 4.52 | 3.85 | 4.15 | 3.6 |
| drax/main | slr83 | 1000 | 16 | 10.50 | 7.13 | 6.36 | 5.95 | 5.99 | 4.38 | 3.01 | 4.06 | 12.2 |
| drax/ref | slr83 | 1000 | 4 | 6.72 | 6.38 | 6.36 | 6.22 | 6.28 | 5.10 | 4.25 | 4.64 | 3.6 |
| drax/main | spgispeech | 1000 | 16 | 8.73 | 5.51 | 4.47 | 4.33 | 4.42 | 2.95 | 1.47 | 2.56 | 10.9 |
| drax/ref | spgispeech | 1000 | 4 | 4.75 | 4.46 | 4.33 | 4.39 | 4.62 | 3.34 | 2.40 | 2.60 | 2.6 |
| drax/main | voxpopuli | 918 | 16 | 11.83 | 7.79 | 6.94 | 6.97 | 7.06 | 5.45 | 3.39 | 4.77 | 12.5 |
| drax/ref | voxpopuli | 918 | 4 | 7.20 | 7.10 | 7.02 | 7.05 | 7.14 | 6.25 | 4.76 | 4.95 | 2.4 |
| parakeet-ctc/greedy | ami | 600 | 1 | 13.60 | 13.60 | 13.60 | 13.60 | 13.60 | 13.60 |  |  | 0.0 |
| parakeet-ctc/sample | ami | 600 | 32 | 20.11 | 18.41 | 14.11 | 13.86 | 13.97 | 9.05 | 5.88 | 8.04 | 23.8 |
| parakeet-ctc/greedy | common_voice | 468 | 1 | 10.51 | 10.51 | 10.51 | 10.51 | 10.51 | 10.51 |  |  | 0.0 |
| parakeet-ctc/sample | common_voice | 468 | 32 | 12.54 | 11.23 | 10.69 | 10.39 | 10.41 | 7.89 | 6.70 | 7.63 | 9.4 |
| parakeet-ctc/greedy | earnings22 | 600 | 1 | 14.93 | 14.93 | 14.93 | 14.93 | 14.93 | 14.93 |  |  | 0.0 |
| parakeet-ctc/sample | earnings22 | 600 | 32 | 21.20 | 17.46 | 15.47 | 15.00 | 14.98 | 11.67 | 7.59 | 10.20 | 18.5 |
| parakeet-ctc/greedy | fleurs-en | 446 | 1 | 7.67 | 7.67 | 7.67 | 7.67 | 7.67 | 7.67 |  |  | 0.0 |
| parakeet-ctc/sample | fleurs-en | 446 | 32 | 9.31 | 8.61 | 7.77 | 7.55 | 7.57 | 5.71 | 2.54 | 3.58 | 5.6 |
| parakeet-ctc/greedy | ls-dev-other | 600 | 1 | 3.32 | 3.32 | 3.32 | 3.32 | 3.32 | 3.32 |  |  | 0.0 |
| parakeet-ctc/sample | ls-dev-other | 600 | 32 | 4.69 | 3.93 | 3.41 | 3.27 | 3.28 | 2.05 | 1.45 | 1.90 | 4.4 |
| parakeet-ctc/greedy | ls-tc-babble5 | 400 | 1 | 10.75 | 10.75 | 10.75 | 10.75 | 10.75 | 10.75 |  |  | 0.0 |
| parakeet-ctc/sample | ls-tc-babble5 | 400 | 32 | 14.09 | 12.06 | 10.96 | 10.74 | 10.74 | 8.37 | 6.13 | 7.69 | 15.8 |
| parakeet-ctc/greedy | ls-test-clean | 600 | 1 | 1.71 | 1.71 | 1.71 | 1.71 | 1.71 | 1.71 |  |  | 0.0 |
| parakeet-ctc/sample | ls-test-clean | 600 | 32 | 3.15 | 2.43 | 1.75 | 1.64 | 1.65 | 0.94 | 0.56 | 0.87 | 3.4 |
| parakeet-ctc/greedy | ls-test-other | 600 | 1 | 3.67 | 3.67 | 3.67 | 3.67 | 3.67 | 3.67 |  |  | 0.0 |
| parakeet-ctc/sample | ls-test-other | 600 | 32 | 5.24 | 4.26 | 3.56 | 3.52 | 3.49 | 2.10 | 1.58 | 2.02 | 5.2 |
| whisfusion/main | ami | 800 | 32 | 44.38 | 34.82 | 34.55 | 31.96 | 31.93 | 26.64 | 18.44 | 24.98 | 41.7 |
| whisfusion/main | common_voice | 614 | 32 | 41.36 | 32.63 | 31.49 | 29.39 | 29.23 | 24.71 | 17.63 | 22.59 | 34.4 |
| whisfusion/main | earnings22 | 800 | 32 | 43.79 | 34.25 | 31.90 | 29.33 | 29.29 | 26.32 | 13.63 | 23.59 | 40.0 |
| whisfusion/main | fleurs-en | 446 | 32 | 34.09 | 26.71 | 24.39 | 22.24 | 22.23 | 20.73 | 9.69 | 17.98 | 30.9 |
| whisfusion/main | gigaspeech | 800 | 32 | 30.81 | 23.80 | 21.85 | 19.93 | 19.92 | 17.60 | 10.19 | 16.29 | 30.4 |
| whisfusion/main | ls-dev-clean | 400 | 32 | 11.97 | 7.07 | 6.12 | 5.35 | 5.29 | 4.71 | 2.42 | 4.52 | 13.4 |
| whisfusion/main | ls-dev-other | 400 | 32 | 21.52 | 15.07 | 14.09 | 12.56 | 12.59 | 11.03 | 5.86 | 10.43 | 21.8 |
| whisfusion/main | ls-tc-babble0 | 400 | 32 | 76.12 | 68.59 | 65.92 | 58.21 | 58.17 | 59.13 | 37.90 | 47.74 | 62.2 |
| whisfusion/main | ls-tc-babble10 | 400 | 32 | 23.30 | 16.09 | 14.64 | 11.53 | 11.48 | 11.69 | 5.20 | 10.85 | 25.5 |
| whisfusion/main | ls-tc-babble15 | 600 | 32 | 17.17 | 11.09 | 9.42 | 7.54 | 7.48 | 7.48 | 3.25 | 7.01 | 19.4 |
| whisfusion/main | ls-tc-babble5 | 400 | 32 | 39.81 | 31.19 | 29.07 | 24.52 | 24.52 | 25.37 | 13.31 | 23.00 | 39.6 |
| whisfusion/main | ls-tc-babbleM5 | 600 | 32 | 106.10 | 102.65 | 98.18 | 90.86 | 90.85 | 90.03 | 72.86 | 71.95 | 75.4 |
| whisfusion/main | ls-tc-white0 | 600 | 32 | 48.42 | 41.40 | 39.32 | 35.53 | 35.52 | 34.08 | 22.22 | 31.72 | 43.7 |
| whisfusion/main | ls-tc-white10 | 600 | 32 | 20.70 | 14.64 | 13.10 | 11.17 | 11.12 | 10.24 | 5.25 | 9.91 | 22.0 |
| whisfusion/main | ls-tc-white5 | 400 | 32 | 30.29 | 23.57 | 21.92 | 18.80 | 18.81 | 18.55 | 10.40 | 17.45 | 30.3 |
| whisfusion/main | ls-test-clean | 800 | 32 | 12.48 | 7.75 | 6.82 | 5.58 | 5.59 | 4.89 | 2.15 | 4.68 | 14.3 |
| whisfusion/main | ls-test-other | 800 | 32 | 21.72 | 15.37 | 13.63 | 12.36 | 12.33 | 10.86 | 6.21 | 10.49 | 22.0 |
| whisfusion/main | slr83 | 800 | 32 | 28.12 | 20.65 | 18.95 | 17.63 | 17.50 | 14.56 | 8.76 | 13.63 | 28.0 |
| whisfusion/main | spgispeech | 800 | 32 | 25.61 | 18.07 | 15.92 | 13.77 | 13.74 | 13.10 | 5.23 | 12.08 | 27.5 |
| whisfusion/main | voxpopuli | 718 | 32 | 27.26 | 20.26 | 18.99 | 17.27 | 17.24 | 15.64 | 8.92 | 14.33 | 23.8 |
| whisper-small/beam | ami | 752 | 8 | 37.82 | 37.82 | 34.39 | 34.42 | 34.76 | 28.40 | 8.76 | 9.14 | 21.1 |
| whisper-small/greedy | ami | 752 | 1 | 16.26 | 16.26 | 16.26 | 16.26 | 16.26 | 16.26 |  |  | 0.0 |
| whisper-small/sample | ami | 752 | 16 | 18.07 | 20.26 | 16.33 | 16.09 | 16.23 | 9.80 | 8.66 | 9.37 | 16.1 |
| whisper-small/beam | common_voice | 468 | 8 | 18.73 | 18.40 | 18.70 | 18.80 | 18.87 | 14.29 | 8.71 | 9.29 | 11.5 |
| whisper-small/greedy | common_voice | 468 | 1 | 16.83 | 16.83 | 16.83 | 16.83 | 16.83 | 16.83 |  |  | 0.0 |
| whisper-small/sample | common_voice | 468 | 16 | 18.26 | 14.80 | 16.11 | 15.62 | 15.60 | 10.27 | 8.36 | 9.55 | 12.3 |
| whisper-small/beam | earnings22 | 600 | 8 | 12.87 | 12.74 | 12.54 | 12.59 | 12.52 | 8.84 | 5.85 | 6.34 | 9.2 |
| whisper-small/greedy | earnings22 | 600 | 1 | 12.31 | 12.31 | 12.31 | 12.31 | 12.31 | 12.31 |  |  | 0.0 |
| whisper-small/sample | earnings22 | 600 | 16 | 16.18 | 12.77 | 16.84 | 16.20 | 16.24 | 7.56 | 5.64 | 6.64 | 13.2 |
| whisper-small/beam | fleurs-en | 446 | 8 | 7.81 | 7.66 | 8.02 | 8.01 | 7.93 | 5.93 | 3.16 | 3.60 | 4.3 |
| whisper-small/greedy | fleurs-en | 446 | 1 | 8.79 | 8.79 | 8.79 | 8.79 | 8.79 | 8.79 |  |  | 0.0 |
| whisper-small/sample | fleurs-en | 446 | 16 | 9.25 | 8.25 | 8.96 | 8.72 | 8.85 | 5.85 | 2.88 | 3.73 | 4.9 |
| whisper-small/beam | ls-dev-other | 800 | 8 | 6.72 | 6.74 | 6.73 | 6.70 | 6.84 | 4.68 | 3.97 | 4.22 | 6.4 |
| whisper-small/greedy | ls-dev-other | 800 | 1 | 7.16 | 7.16 | 7.16 | 7.16 | 7.16 | 7.16 |  |  | 0.0 |
| whisper-small/sample | ls-dev-other | 800 | 16 | 8.35 | 7.95 | 7.29 | 7.09 | 7.24 | 4.31 | 3.36 | 4.05 | 6.8 |
| whisper-small/beam | ls-tc-babble5 | 400 | 8 | 19.79 | 20.28 | 19.47 | 19.38 | 19.46 | 16.32 | 8.28 | 8.79 | 9.3 |
| whisper-small/greedy | ls-tc-babble5 | 400 | 1 | 13.99 | 13.99 | 13.99 | 13.99 | 13.99 | 13.99 |  |  | 0.0 |
| whisper-small/sample | ls-tc-babble5 | 400 | 16 | 15.71 | 16.12 | 13.53 | 13.27 | 13.33 | 8.95 | 6.35 | 8.46 | 15.1 |
| whisper-small/beam | ls-test-clean | 800 | 8 | 2.95 | 3.06 | 2.99 | 3.03 | 3.03 | 1.77 | 1.56 | 1.65 | 4.0 |
| whisper-small/greedy | ls-test-clean | 800 | 1 | 3.17 | 3.17 | 3.17 | 3.17 | 3.17 | 3.17 |  |  | 0.0 |
| whisper-small/sample | ls-test-clean | 800 | 16 | 3.66 | 4.17 | 3.34 | 3.18 | 3.22 | 1.74 | 1.48 | 1.66 | 3.5 |
| whisper-small/beam | ls-test-other | 800 | 8 | 7.14 | 7.06 | 7.02 | 7.03 | 7.08 | 4.89 | 4.10 | 4.48 | 6.6 |
| whisper-small/greedy | ls-test-other | 800 | 1 | 7.88 | 7.88 | 7.88 | 7.88 | 7.88 | 7.88 |  |  | 0.0 |
| whisper-small/sample | ls-test-other | 800 | 16 | 8.95 | 7.86 | 7.66 | 7.51 | 7.62 | 4.50 | 3.47 | 4.28 | 7.1 |
| whisper-turbo/beam | ami | 800 | 8 | 26.13 | 33.02 | 24.58 | 24.77 | 25.10 | 19.43 | 8.07 | 8.30 | 20.1 |
| whisper-turbo/greedy | ami | 800 | 1 | 14.52 | 14.52 | 14.52 | 14.52 | 14.52 | 14.52 |  |  | 0.0 |
| whisper-turbo/sample | ami | 800 | 16 | 15.50 | 14.62 | 14.63 | 14.36 | 14.40 | 9.15 | 8.17 | 8.52 | 11.8 |
| whisper-turbo/beam | common_voice | 468 | 8 | 18.80 | 18.61 | 18.77 | 19.05 | 19.24 | 14.80 | 6.79 | 6.96 | 9.3 |
| whisper-turbo/greedy | common_voice | 468 | 1 | 11.60 | 11.60 | 11.60 | 11.60 | 11.60 | 11.60 |  |  | 0.0 |
| whisper-turbo/sample | common_voice | 468 | 16 | 12.72 | 11.65 | 11.56 | 11.25 | 11.16 | 7.66 | 6.33 | 6.93 | 7.1 |
| whisper-turbo/beam | earnings22 | 707 | 8 | 10.65 | 10.37 | 10.65 | 10.71 | 10.76 | 7.54 | 5.52 | 5.80 | 8.0 |
| whisper-turbo/greedy | earnings22 | 707 | 1 | 10.82 | 10.82 | 10.82 | 10.82 | 10.82 | 10.82 |  |  | 0.0 |
| whisper-turbo/sample | earnings22 | 707 | 16 | 11.58 | 10.48 | 11.07 | 11.03 | 11.11 | 7.52 | 5.65 | 6.06 | 5.8 |
| whisper-turbo/beam | fleurs-en | 446 | 8 | 6.32 | 6.23 | 6.33 | 6.19 | 6.23 | 4.46 | 2.29 | 2.49 | 3.8 |
| whisper-turbo/greedy | fleurs-en | 446 | 1 | 6.35 | 6.35 | 6.35 | 6.35 | 6.35 | 6.35 |  |  | 0.0 |
| whisper-turbo/sample | fleurs-en | 446 | 16 | 6.76 | 6.29 | 6.47 | 6.39 | 6.36 | 4.41 | 2.20 | 2.58 | 2.8 |
| whisper-turbo/beam | ls-dev-other | 800 | 8 | 3.92 | 4.16 | 3.81 | 3.90 | 3.84 | 2.22 | 1.86 | 2.08 | 4.9 |
| whisper-turbo/greedy | ls-dev-other | 800 | 1 | 3.96 | 3.96 | 3.96 | 3.96 | 3.96 | 3.96 |  |  | 0.0 |
| whisper-turbo/sample | ls-dev-other | 800 | 16 | 4.38 | 4.02 | 3.90 | 3.91 | 3.92 | 2.46 | 2.00 | 2.29 | 2.7 |
| whisper-turbo/beam | ls-tc-babble15 | 200 | 8 | 2.76 | 2.79 | 2.56 | 2.66 | 2.71 | 1.69 | 1.51 | 1.56 | 3.1 |
| whisper-turbo/greedy | ls-tc-babble15 | 200 | 1 | 2.63 | 2.63 | 2.63 | 2.63 | 2.63 | 2.63 |  |  | 0.0 |
| whisper-turbo/sample | ls-tc-babble15 | 200 | 16 | 3.12 | 2.71 | 2.68 | 2.74 | 2.71 | 1.87 | 1.66 | 1.69 | 1.9 |
| whisper-turbo/beam | ls-tc-babble5 | 400 | 8 | 6.32 | 6.25 | 6.12 | 6.22 | 6.25 | 4.10 | 3.60 | 3.84 | 6.7 |
| whisper-turbo/greedy | ls-tc-babble5 | 400 | 1 | 6.64 | 6.64 | 6.64 | 6.64 | 6.64 | 6.64 |  |  | 0.0 |
| whisper-turbo/sample | ls-tc-babble5 | 400 | 16 | 7.44 | 6.23 | 6.40 | 6.30 | 6.32 | 4.15 | 3.37 | 3.84 | 6.0 |
| whisper-turbo/beam | ls-tc-babbleM5 | 200 | 8 | 433.28 | 428.86 | 423.39 | 424.49 | 424.46 | 396.57 | 75.97 | 74.18 | 17.5 |
| whisper-turbo/greedy | ls-tc-babbleM5 | 200 | 1 | 160.58 | 160.58 | 160.58 | 160.58 | 160.58 | 160.58 |  |  | 0.0 |
| whisper-turbo/sample | ls-tc-babbleM5 | 200 | 16 | 106.08 | 197.47 | 89.42 | 87.63 | 87.60 | 77.91 | 69.76 | 72.03 | 71.8 |
| whisper-turbo/beam | ls-tc-white0 | 200 | 8 | 11.27 | 11.73 | 11.32 | 11.35 | 11.43 | 8.77 | 7.57 | 8.05 | 8.4 |
| whisper-turbo/greedy | ls-tc-white0 | 200 | 1 | 12.19 | 12.19 | 12.19 | 12.19 | 12.19 | 12.19 |  |  | 0.0 |
| whisper-turbo/sample | ls-tc-white0 | 200 | 16 | 13.34 | 12.12 | 12.60 | 12.22 | 12.30 | 8.21 | 6.39 | 7.95 | 10.0 |
| whisper-turbo/beam | ls-tc-white10 | 200 | 8 | 3.60 | 3.78 | 3.40 | 3.53 | 3.55 | 2.07 | 1.87 | 1.99 | 3.9 |
| whisper-turbo/greedy | ls-tc-white10 | 200 | 1 | 3.45 | 3.45 | 3.45 | 3.45 | 3.45 | 3.45 |  |  | 0.0 |
| whisper-turbo/sample | ls-tc-white10 | 200 | 16 | 3.86 | 5.01 | 3.48 | 3.48 | 3.50 | 2.22 | 1.89 | 2.10 | 2.4 |
| whisper-turbo/beam | ls-test-clean | 800 | 8 | 1.91 | 1.97 | 1.88 | 1.93 | 1.97 | 1.02 | 0.92 | 0.94 | 3.7 |
| whisper-turbo/greedy | ls-test-clean | 800 | 1 | 1.98 | 1.98 | 1.98 | 1.98 | 1.98 | 1.98 |  |  | 0.0 |
| whisper-turbo/sample | ls-test-clean | 800 | 16 | 2.21 | 2.25 | 1.94 | 1.92 | 1.93 | 1.15 | 0.97 | 1.06 | 1.8 |
| whisper-turbo/beam | ls-test-other | 800 | 8 | 3.89 | 4.02 | 3.94 | 3.90 | 3.85 | 2.14 | 1.75 | 1.93 | 5.6 |
| whisper-turbo/greedy | ls-test-other | 800 | 1 | 3.93 | 3.93 | 3.93 | 3.93 | 3.93 | 3.93 |  |  | 0.0 |
| whisper-turbo/sample | ls-test-other | 800 | 16 | 4.38 | 3.86 | 3.92 | 3.89 | 3.82 | 2.38 | 1.93 | 2.21 | 3.1 |

## ROVER-cg against the best selection, paired bootstrap (main arm, largest K)

| model | set | vs | delta | 95% CI | cluster CI | Wilcoxon p | better/worse/tied |
|---|---|---|---|---|---|---|---|
| drax/main | ami | conf | +2.13 | [+1.57, +2.66] | [1.21, 2.91] | 0.0000 | 223/78/699 |
| drax/main | ami | mbr | +0.21 | [-0.07, +0.51] | [-0.09, 0.51] | 0.1865 | 72/61/867 |
| drax/ref | ami | conf | -0.11 | [-0.41, +0.20] | [-0.44, 0.26] | 0.5019 | 62/70/868 |
| drax/ref | ami | mbr | -0.29 | [-0.54, -0.03] | [-0.51, -0.02] | 0.0265 | 42/67/891 |
| drax/main | common_voice | conf | +1.78 | [+1.23, +2.37] | [, ] | 0.0000 | 154/72/547 |
| drax/main | common_voice | mbr | +0.40 | [+0.06, +0.76] | [, ] | 0.0236 | 65/47/661 |
| drax/ref | common_voice | conf | +0.20 | [-0.21, +0.60] | [, ] | 0.2953 | 50/45/678 |
| drax/ref | common_voice | mbr | +0.06 | [-0.21, +0.33] | [, ] | 0.7195 | 38/31/704 |
| drax/main | earnings22 | conf | +3.48 | [+2.35, +4.75] | [2.70, 4.16] | 0.0000 | 332/162/506 |
| drax/main | earnings22 | mbr | +0.50 | [+0.22, +0.77] | [0.25, 0.72] | 0.0000 | 194/122/684 |
| drax/ref | earnings22 | conf | -0.34 | [-0.65, -0.05] | [-0.73, -0.12] | 0.1075 | 140/160/700 |
| drax/ref | earnings22 | mbr | -0.36 | [-0.56, -0.17] | [-0.63, -0.21] | 0.0005 | 84/141/775 |
| drax/main | fleurs-de | conf | +1.91 | [+1.56, +2.26] | [1.55, 2.28] | 0.0000 | 244/64/438 |
| drax/main | fleurs-de | mbr | +0.66 | [+0.47, +0.85] | [0.47, 0.87] | 0.0000 | 117/36/593 |
| drax/ref | fleurs-de | conf | +0.43 | [+0.20, +0.66] | [0.20, 0.68] | 0.0005 | 127/77/542 |
| drax/ref | fleurs-de | mbr | +0.19 | [+0.04, +0.36] | [0.03, 0.36] | 0.0312 | 73/52/621 |
| drax/main | fleurs-en | conf | +1.75 | [+1.40, +2.13] | [1.35, 2.16] | 0.0000 | 196/47/403 |
| drax/main | fleurs-en | mbr | +0.51 | [+0.30, +0.73] | [0.28, 0.77] | 0.0000 | 87/38/521 |
| drax/ref | fleurs-en | conf | +0.39 | [+0.15, +0.66] | [0.15, 0.66] | 0.0024 | 89/67/490 |
| drax/ref | fleurs-en | mbr | -0.10 | [-0.27, +0.08] | [-0.26, 0.06] | 0.3008 | 45/60/541 |
| drax/main | fleurs-es | conf | +0.89 | [+0.63, +1.16] | [0.65, 1.15] | 0.0000 | 143/54/403 |
| drax/main | fleurs-es | mbr | +0.13 | [+0.01, +0.26] | [0.01, 0.26] | 0.0387 | 48/31/521 |
| drax/ref | fleurs-es | conf | +0.23 | [+0.08, +0.39] | [0.06, 0.41] | 0.0034 | 71/44/485 |
| drax/ref | fleurs-es | mbr | +0.11 | [-0.01, +0.24] | [-0.01, 0.25] | 0.0655 | 42/30/528 |
| drax/main | fleurs-fr | conf | +1.43 | [+1.09, +1.80] | [1.07, 1.79] | 0.0000 | 185/72/285 |
| drax/main | fleurs-fr | mbr | +0.41 | [+0.22, +0.61] | [0.23, 0.60] | 0.0000 | 86/41/415 |
| drax/ref | fleurs-fr | conf | +0.20 | [-0.08, +0.47] | [-0.09, 0.50] | 0.2575 | 89/81/372 |
| drax/ref | fleurs-fr | mbr | +0.11 | [-0.06, +0.30] | [-0.07, 0.29] | 0.1811 | 60/45/437 |
| drax/main | fleurs-it | conf | +1.18 | [+0.91, +1.45] | [0.90, 1.45] | 0.0000 | 153/38/409 |
| drax/main | fleurs-it | mbr | +0.38 | [+0.22, +0.54] | [0.22, 0.54] | 0.0000 | 74/31/495 |
| drax/ref | fleurs-it | conf | +0.32 | [+0.10, +0.54] | [0.10, 0.54] | 0.0033 | 87/56/457 |
| drax/ref | fleurs-it | mbr | +0.07 | [-0.08, +0.23] | [-0.10, 0.23] | 0.3443 | 48/45/507 |
| drax/main | fleurs-pt | conf | +2.63 | [+2.22, +3.06] | [2.24, 3.03] | 0.0000 | 257/56/287 |
| drax/main | fleurs-pt | mbr | +1.00 | [+0.76, +1.23] | [0.75, 1.26] | 0.0000 | 144/41/415 |
| drax/ref | fleurs-pt | conf | +0.64 | [+0.37, +0.90] | [0.36, 0.90] | 0.0000 | 133/68/399 |
| drax/ref | fleurs-pt | mbr | +0.21 | [+0.00, +0.41] | [0.01, 0.42] | 0.0525 | 92/68/440 |
| drax/main | gigaspeech | conf | +1.52 | [+1.06, +2.05] | [1.03, 2.08] | 0.0000 | 273/87/640 |
| drax/main | gigaspeech | mbr | +0.70 | [+0.51, +0.91] | [0.46, 0.92] | 0.0000 | 155/54/791 |
| drax/ref | gigaspeech | conf | +0.09 | [-0.17, +0.34] | [-0.21, 0.36] | 0.2461 | 133/114/753 |
| drax/ref | gigaspeech | mbr | -0.01 | [-0.18, +0.16] | [-0.19, 0.16] | 0.9698 | 85/91/824 |
| drax/main | ls-dev-clean | conf | +0.78 | [+0.27, +1.45] | [0.32, 1.37] | 0.0012 | 50/24/326 |
| drax/main | ls-dev-clean | mbr | +0.00 | [-0.13, +0.14] | [-0.11, 0.12] | 1.0000 | 11/11/378 |
| drax/ref | ls-dev-clean | conf | +0.12 | [-0.06, +0.30] | [-0.07, 0.30] | 0.2042 | 21/13/366 |
| drax/ref | ls-dev-clean | mbr | +0.08 | [-0.07, +0.22] | [-0.06, 0.21] | 0.2899 | 14/9/377 |
| drax/main | ls-dev-other | conf | +0.97 | [+0.16, +1.61] | [0.14, 1.73] | 0.0000 | 75/20/305 |
| drax/main | ls-dev-other | mbr | +0.31 | [+0.08, +0.54] | [0.03, 0.61] | 0.0089 | 32/16/352 |
| drax/ref | ls-dev-other | conf | +0.10 | [-0.15, +0.36] | [-0.18, 0.35] | 0.4603 | 29/23/348 |
| drax/ref | ls-dev-other | mbr | -0.01 | [-0.21, +0.18] | [-0.21, 0.17] | 0.8880 | 18/19/363 |
| drax/main | ls-tc-babble0 | conf | +5.37 | [+4.37, +6.36] | [4.07, 6.56] | 0.0000 | 324/80/196 |
| drax/main | ls-tc-babble0 | mbr | +3.58 | [+3.08, +4.08] | [3.13, 3.99] | 0.0000 | 270/54/276 |
| drax/ref | ls-tc-babble0 | conf | +0.21 | [-0.41, +0.83] | [-0.37, 0.75] | 0.0090 | 169/120/311 |
| drax/ref | ls-tc-babble0 | mbr | +0.78 | [+0.46, +1.10] | [0.46, 1.11] | 0.0000 | 140/83/377 |
| drax/main | ls-tc-babble10 | conf | +1.11 | [+0.81, +1.40] | [0.79, 1.42] | 0.0000 | 117/37/446 |
| drax/main | ls-tc-babble10 | mbr | +0.07 | [-0.08, +0.24] | [-0.07, 0.23] | 0.3988 | 35/29/536 |
| drax/ref | ls-tc-babble10 | conf | +0.17 | [-0.01, +0.35] | [-0.01, 0.34] | 0.0814 | 39/30/531 |
| drax/ref | ls-tc-babble10 | mbr | -0.02 | [-0.15, +0.12] | [-0.13, 0.11] | 0.8096 | 27/29/544 |
| drax/main | ls-tc-babble15 | conf | +0.71 | [+0.46, +0.96] | [0.43, 1.00] | 0.0000 | 90/28/482 |
| drax/main | ls-tc-babble15 | mbr | +0.05 | [-0.08, +0.18] | [-0.09, 0.17] | 0.4459 | 26/21/553 |
| drax/ref | ls-tc-babble15 | conf | +0.11 | [-0.05, +0.28] | [-0.05, 0.27] | 0.2300 | 35/30/535 |
| drax/ref | ls-tc-babble15 | mbr | -0.01 | [-0.13, +0.11] | [-0.10, 0.09] | 0.9307 | 17/21/562 |
| drax/main | ls-tc-babble5 | conf | +2.35 | [+1.88, +2.79] | [1.83, 2.90] | 0.0000 | 201/58/341 |
| drax/main | ls-tc-babble5 | mbr | +0.65 | [+0.38, +0.92] | [0.35, 0.96] | 0.0000 | 103/54/443 |
| drax/ref | ls-tc-babble5 | conf | +0.43 | [+0.17, +0.70] | [0.20, 0.68] | 0.0018 | 90/55/455 |
| drax/ref | ls-tc-babble5 | mbr | -0.07 | [-0.24, +0.11] | [-0.26, 0.11] | 0.5161 | 40/50/510 |
| drax/main | ls-tc-babbleM5 | conf | +7.46 | [+5.80, +9.23] | [5.67, 9.41] | 0.0000 | 232/99/269 |
| drax/main | ls-tc-babbleM5 | mbr | +1.64 | [+1.30, +1.97] | [1.22, 2.11] | 0.0000 | 204/60/336 |
| drax/ref | ls-tc-babbleM5 | conf | +0.04 | [-0.39, +0.44] | [-0.35, 0.42] | 0.0895 | 105/60/435 |
| drax/ref | ls-tc-babbleM5 | mbr | +0.78 | [+0.58, +0.98] | [0.54, 1.02] | 0.0000 | 97/17/486 |
| drax/main | ls-tc-white0 | conf | +3.84 | [+3.27, +4.44] | [3.17, 4.52] | 0.0000 | 269/70/261 |
| drax/main | ls-tc-white0 | mbr | +1.76 | [+1.40, +2.15] | [1.33, 2.21] | 0.0000 | 166/47/387 |
| drax/ref | ls-tc-white0 | conf | +0.54 | [+0.25, +0.83] | [0.23, 0.88] | 0.0007 | 110/70/420 |
| drax/ref | ls-tc-white0 | mbr | +0.08 | [-0.14, +0.31] | [-0.12, 0.30] | 0.5230 | 58/59/483 |
| drax/main | ls-tc-white10 | conf | +0.85 | [+0.57, +1.13] | [0.56, 1.16] | 0.0000 | 116/40/444 |
| drax/main | ls-tc-white10 | mbr | +0.08 | [-0.07, +0.24] | [-0.07, 0.23] | 0.2660 | 37/28/535 |
| drax/ref | ls-tc-white10 | conf | +0.10 | [-0.07, +0.27] | [-0.05, 0.26] | 0.2266 | 39/33/528 |
| drax/ref | ls-tc-white10 | mbr | -0.10 | [-0.23, +0.02] | [-0.22, 0.02] | 0.1125 | 15/26/559 |
| drax/main | ls-tc-white5 | conf | +1.78 | [+1.42, +2.16] | [1.30, 2.28] | 0.0000 | 172/43/385 |
| drax/main | ls-tc-white5 | mbr | +0.45 | [+0.24, +0.67] | [0.19, 0.71] | 0.0001 | 70/37/493 |
| drax/ref | ls-tc-white5 | conf | +0.25 | [+0.03, +0.46] | [0.04, 0.42] | 0.0356 | 68/44/488 |
| drax/ref | ls-tc-white5 | mbr | -0.03 | [-0.20, +0.13] | [-0.19, 0.12] | 0.6912 | 35/39/526 |
| drax/main | ls-test-clean | conf | +0.62 | [+0.42, +0.81] | [0.43, 0.82] | 0.0000 | 133/47/820 |
| drax/main | ls-test-clean | mbr | -0.01 | [-0.11, +0.08] | [-0.10, 0.08] | 0.8411 | 35/37/928 |
| drax/ref | ls-test-clean | conf | +0.08 | [-0.05, +0.19] | [-0.05, 0.20] | 0.2104 | 48/38/914 |
| drax/ref | ls-test-clean | mbr | -0.04 | [-0.14, +0.07] | [-0.14, 0.07] | 0.4468 | 28/36/936 |
| drax/main | ls-test-other | conf | +1.32 | [+1.01, +1.61] | [0.94, 1.72] | 0.0000 | 201/66/733 |
| drax/main | ls-test-other | mbr | +0.23 | [+0.08, +0.38] | [0.08, 0.40] | 0.0026 | 76/49/875 |
| drax/ref | ls-test-other | conf | +0.14 | [-0.03, +0.32] | [-0.02, 0.31] | 0.1321 | 76/63/861 |
| drax/ref | ls-test-other | mbr | +0.05 | [-0.07, +0.16] | [-0.07, 0.16] | 0.4404 | 47/43/910 |
| drax/main | slr83 | conf | +1.14 | [+0.83, +1.47] | [0.82, 1.48] | 0.0000 | 158/60/782 |
| drax/main | slr83 | mbr | +0.37 | [+0.19, +0.57] | [0.13, 0.65] | 0.0002 | 75/44/881 |
| drax/ref | slr83 | conf | +0.10 | [-0.10, +0.30] | [-0.07, 0.26] | 0.2931 | 66/58/876 |
| drax/ref | slr83 | mbr | +0.08 | [-0.07, +0.23] | [-0.10, 0.25] | 0.3228 | 45/39/916 |
| drax/main | spgispeech | conf | +1.09 | [+0.85, +1.32] | [0.86, 1.32] | 0.0000 | 263/101/636 |
| drax/main | spgispeech | mbr | +0.06 | [-0.07, +0.19] | [-0.07, 0.19] | 0.5045 | 81/79/840 |
| drax/ref | spgispeech | conf | -0.16 | [-0.34, +0.01] | [-0.36, 0.02] | 0.0692 | 102/139/759 |
| drax/ref | spgispeech | mbr | -0.29 | [-0.41, -0.18] | [-0.41, -0.18] | 0.0000 | 55/125/820 |
| drax/main | voxpopuli | conf | +0.73 | [+0.46, +1.00] | [0.46, 1.03] | 0.0000 | 155/80/683 |
| drax/main | voxpopuli | mbr | -0.12 | [-0.24, -0.01] | [-0.24, -0.01] | 0.0392 | 34/54/830 |
| drax/ref | voxpopuli | conf | -0.04 | [-0.18, +0.10] | [-0.20, 0.10] | 0.6333 | 54/62/802 |
| drax/ref | voxpopuli | mbr | -0.12 | [-0.24, +0.01] | [-0.26, 0.02] | 0.0610 | 37/54/827 |
| parakeet-ctc/greedy | ami | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/greedy | ami | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/sample | ami | conf | +4.44 | [+3.73, +5.15] | [3.85, 4.97] | 0.0000 | 203/39/358 |
| parakeet-ctc/sample | ami | mbr | +0.14 | [-0.21, +0.49] | [-0.17, 0.43] | 0.3995 | 38/35/527 |
| parakeet-ctc/greedy | common_voice | conf | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/468 |
| parakeet-ctc/greedy | common_voice | mbr | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/468 |
| parakeet-ctc/sample | common_voice | conf | +0.82 | [+0.40, +1.24] | [, ] | 0.0002 | 55/23/390 |
| parakeet-ctc/sample | common_voice | mbr | +0.28 | [+0.02, +0.54] | [, ] | 0.0339 | 20/9/439 |
| parakeet-ctc/greedy | earnings22 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/greedy | earnings22 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/sample | earnings22 | conf | +2.48 | [+2.01, +2.94] | [1.81, 3.03] | 0.0000 | 230/73/297 |
| parakeet-ctc/sample | earnings22 | mbr | +0.50 | [+0.25, +0.76] | [0.12, 0.85] | 0.0001 | 78/41/481 |
| parakeet-ctc/greedy | fleurs-en | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/446 |
| parakeet-ctc/greedy | fleurs-en | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/446 |
| parakeet-ctc/sample | fleurs-en | conf | +1.05 | [+0.78, +1.34] | [0.73, 1.34] | 0.0000 | 95/20/331 |
| parakeet-ctc/sample | fleurs-en | mbr | +0.20 | [+0.06, +0.35] | [0.05, 0.36] | 0.0073 | 30/14/402 |
| parakeet-ctc/greedy | ls-dev-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/greedy | ls-dev-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/sample | ls-dev-other | conf | +0.64 | [+0.40, +0.91] | [0.32, 0.99] | 0.0000 | 79/23/498 |
| parakeet-ctc/sample | ls-dev-other | mbr | +0.13 | [+0.04, +0.23] | [0.03, 0.24] | 0.0106 | 20/7/573 |
| parakeet-ctc/greedy | ls-tc-babble5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| parakeet-ctc/greedy | ls-tc-babble5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| parakeet-ctc/sample | ls-tc-babble5 | conf | +1.32 | [+0.97, +1.71] | [0.96, 1.72] | 0.0000 | 103/25/272 |
| parakeet-ctc/sample | ls-tc-babble5 | mbr | +0.22 | [-0.01, +0.45] | [-0.03, 0.46] | 0.0678 | 38/23/339 |
| parakeet-ctc/greedy | ls-test-clean | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/greedy | ls-test-clean | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/sample | ls-test-clean | conf | +0.78 | [+0.56, +1.01] | [0.52, 1.04] | 0.0000 | 84/17/499 |
| parakeet-ctc/sample | ls-test-clean | mbr | +0.10 | [-0.01, +0.21] | [-0.02, 0.23] | 0.0788 | 19/11/570 |
| parakeet-ctc/greedy | ls-test-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/greedy | ls-test-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| parakeet-ctc/sample | ls-test-other | conf | +0.77 | [+0.56, +0.99] | [0.55, 1.01] | 0.0000 | 90/22/488 |
| parakeet-ctc/sample | ls-test-other | mbr | +0.07 | [-0.03, +0.18] | [-0.02, 0.17] | 0.1573 | 18/11/571 |
| whisfusion/main | ami | conf | +2.88 | [+2.15, +3.61] | [2.17, 3.51] | 0.0000 | 240/100/460 |
| whisfusion/main | ami | mbr | +2.62 | [+2.16, +3.07] | [2.18, 3.04] | 0.0000 | 185/31/584 |
| whisfusion/main | common_voice | conf | +3.40 | [+2.58, +4.24] | [, ] | 0.0000 | 181/72/361 |
| whisfusion/main | common_voice | mbr | +2.26 | [+1.77, +2.78] | [, ] | 0.0000 | 122/24/468 |
| whisfusion/main | earnings22 | conf | +4.96 | [+4.34, +5.59] | [4.04, 5.71] | 0.0000 | 399/108/293 |
| whisfusion/main | earnings22 | mbr | +2.62 | [+2.27, +2.96] | [2.31, 2.86] | 0.0000 | 301/63/436 |
| whisfusion/main | fleurs-en | conf | +4.48 | [+3.91, +5.08] | [3.85, 5.15] | 0.0000 | 245/41/160 |
| whisfusion/main | fleurs-en | mbr | +2.16 | [+1.79, +2.58] | [1.77, 2.59] | 0.0000 | 165/28/253 |
| whisfusion/main | gigaspeech | conf | +3.87 | [+3.38, +4.35] | [3.30, 4.44] | 0.0000 | 358/99/343 |
| whisfusion/main | gigaspeech | mbr | +1.93 | [+1.62, +2.24] | [1.53, 2.33] | 0.0000 | 243/57/500 |
| whisfusion/main | ls-dev-clean | conf | +1.78 | [+1.35, +2.24] | [1.21, 2.33] | 0.0000 | 106/27/267 |
| whisfusion/main | ls-dev-clean | mbr | +0.83 | [+0.57, +1.12] | [0.50, 1.16] | 0.0000 | 62/14/324 |
| whisfusion/main | ls-dev-other | conf | +2.49 | [+1.90, +3.13] | [1.82, 3.18] | 0.0000 | 130/48/222 |
| whisfusion/main | ls-dev-other | mbr | +1.50 | [+1.08, +1.95] | [0.99, 2.11] | 0.0000 | 88/22/290 |
| whisfusion/main | ls-tc-babble0 | conf | +10.42 | [+9.26, +11.63] | [9.11, 11.87] | 0.0000 | 266/39/95 |
| whisfusion/main | ls-tc-babble0 | mbr | +7.75 | [+6.91, +8.62] | [6.78, 8.69] | 0.0000 | 243/13/144 |
| whisfusion/main | ls-tc-babble10 | conf | +4.61 | [+3.92, +5.32] | [3.83, 5.39] | 0.0000 | 176/28/196 |
| whisfusion/main | ls-tc-babble10 | mbr | +3.17 | [+2.69, +3.70] | [2.58, 3.76] | 0.0000 | 144/11/245 |
| whisfusion/main | ls-tc-babble15 | conf | +3.61 | [+3.07, +4.14] | [3.00, 4.21] | 0.0000 | 227/42/331 |
| whisfusion/main | ls-tc-babble15 | mbr | +1.94 | [+1.59, +2.28] | [1.53, 2.33] | 0.0000 | 155/21/424 |
| whisfusion/main | ls-tc-babble5 | conf | +6.66 | [+5.85, +7.49] | [5.64, 7.72] | 0.0000 | 226/39/135 |
| whisfusion/main | ls-tc-babble5 | mbr | +4.54 | [+3.94, +5.12] | [3.87, 5.22] | 0.0000 | 179/24/197 |
| whisfusion/main | ls-tc-babbleM5 | conf | +11.81 | [+9.92, +14.11] | [9.48, 14.39] | 0.0000 | 361/54/185 |
| whisfusion/main | ls-tc-babbleM5 | mbr | +7.33 | [+6.19, +8.63] | [5.94, 8.95] | 0.0000 | 299/42/259 |
| whisfusion/main | ls-tc-white0 | conf | +5.88 | [+5.26, +6.53] | [5.16, 6.56] | 0.0000 | 317/62/221 |
| whisfusion/main | ls-tc-white0 | mbr | +3.80 | [+3.33, +4.29] | [3.27, 4.32] | 0.0000 | 252/48/300 |
| whisfusion/main | ls-tc-white10 | conf | +3.53 | [+3.00, +4.05] | [2.91, 4.08] | 0.0000 | 234/52/314 |
| whisfusion/main | ls-tc-white10 | mbr | +1.99 | [+1.64, +2.32] | [1.56, 2.43] | 0.0000 | 152/18/430 |
| whisfusion/main | ls-tc-white5 | conf | +4.77 | [+4.08, +5.44] | [3.97, 5.58] | 0.0000 | 199/25/176 |
| whisfusion/main | ls-tc-white5 | mbr | +3.12 | [+2.61, +3.65] | [2.59, 3.65] | 0.0000 | 144/15/241 |
| whisfusion/main | ls-test-clean | conf | +2.16 | [+1.79, +2.54] | [1.71, 2.63] | 0.0000 | 224/62/514 |
| whisfusion/main | ls-test-clean | mbr | +1.23 | [+0.98, +1.49] | [0.99, 1.50] | 0.0000 | 145/25/630 |
| whisfusion/main | ls-test-other | conf | +3.04 | [+2.61, +3.44] | [2.60, 3.51] | 0.0000 | 273/67/460 |
| whisfusion/main | ls-test-other | mbr | +1.30 | [+1.05, +1.55] | [1.03, 1.61] | 0.0000 | 174/42/584 |
| whisfusion/main | slr83 | conf | +3.15 | [+2.65, +3.70] | [2.58, 3.70] | 0.0000 | 283/75/442 |
| whisfusion/main | slr83 | mbr | +1.45 | [+1.17, +1.73] | [1.04, 1.81] | 0.0000 | 166/34/600 |
| whisfusion/main | spgispeech | conf | +4.33 | [+3.95, +4.72] | [3.94, 4.74] | 0.0000 | 478/69/253 |
| whisfusion/main | spgispeech | mbr | +2.18 | [+1.92, +2.43] | [1.91, 2.44] | 0.0000 | 324/43/433 |
| whisfusion/main | voxpopuli | conf | +3.02 | [+2.56, +3.50] | [2.55, 3.50] | 0.0000 | 281/76/361 |
| whisfusion/main | voxpopuli | mbr | +1.76 | [+1.46, +2.07] | [1.45, 2.07] | 0.0000 | 197/35/486 |
| whisper-small/beam | ami | conf | +3.07 | [+0.03, +7.78] | [-0.06, 7.97] | 0.2569 | 120/104/528 |
| whisper-small/beam | ami | mbr | -0.37 | [-0.71, -0.04] | [-0.73, -0.02] | 0.0391 | 52/72/628 |
| whisper-small/greedy | ami | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/752 |
| whisper-small/greedy | ami | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/752 |
| whisper-small/sample | ami | conf | +4.03 | [+0.14, +10.15] | [0.06, 9.64] | 0.0483 | 112/78/562 |
| whisper-small/sample | ami | mbr | +0.10 | [-0.21, +0.42] | [-0.24, 0.48] | 0.5197 | 51/46/655 |
| whisper-small/beam | common_voice | conf | -0.47 | [-1.07, +0.14] | [, ] | 0.1287 | 41/57/370 |
| whisper-small/beam | common_voice | mbr | -0.16 | [-0.50, +0.16] | [, ] | 0.3538 | 25/32/411 |
| whisper-small/greedy | common_voice | conf | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/468 |
| whisper-small/greedy | common_voice | mbr | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/468 |
| whisper-small/sample | common_voice | conf | -0.79 | [-1.60, +0.07] | [, ] | 0.0186 | 40/62/366 |
| whisper-small/sample | common_voice | mbr | +0.51 | [+0.05, +0.93] | [, ] | 0.0181 | 46/26/396 |
| whisper-small/beam | earnings22 | conf | +0.22 | [-0.26, +0.71] | [-0.08, 0.68] | 0.9732 | 89/96/415 |
| whisper-small/beam | earnings22 | mbr | +0.02 | [-0.21, +0.23] | [-0.18, 0.12] | 0.9197 | 56/57/487 |
| whisper-small/greedy | earnings22 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| whisper-small/greedy | earnings22 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/600 |
| whisper-small/sample | earnings22 | conf | -3.47 | [-6.53, +0.74] | [-5.54, -1.03] | 0.0000 | 74/126/400 |
| whisper-small/sample | earnings22 | mbr | +0.60 | [+0.33, +0.91] | [0.26, 0.88] | 0.0001 | 84/44/472 |
| whisper-small/beam | fleurs-en | conf | -0.27 | [-0.50, -0.05] | [-0.51, -0.04] | 0.0176 | 26/46/374 |
| whisper-small/beam | fleurs-en | mbr | +0.09 | [-0.08, +0.28] | [-0.10, 0.30] | 0.2786 | 28/20/398 |
| whisper-small/greedy | fleurs-en | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/446 |
| whisper-small/greedy | fleurs-en | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/446 |
| whisper-small/sample | fleurs-en | conf | -0.60 | [-1.41, +0.13] | [-1.70, 0.27] | 0.1715 | 43/55/348 |
| whisper-small/sample | fleurs-en | mbr | +0.11 | [-0.08, +0.31] | [-0.07, 0.30] | 0.2636 | 35/30/381 |
| whisper-small/beam | ls-dev-other | conf | -0.10 | [-0.34, +0.17] | [-0.37, 0.19] | 0.0594 | 51/84/665 |
| whisper-small/beam | ls-dev-other | mbr | -0.10 | [-0.25, +0.05] | [-0.28, 0.06] | 0.1445 | 41/56/703 |
| whisper-small/greedy | ls-dev-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-small/greedy | ls-dev-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-small/sample | ls-dev-other | conf | +0.71 | [-0.38, +2.24] | [-0.36, 2.31] | 0.5210 | 66/97/637 |
| whisper-small/sample | ls-dev-other | mbr | +0.06 | [-0.10, +0.21] | [-0.14, 0.27] | 0.5230 | 53/45/702 |
| whisper-small/beam | ls-tc-babble5 | conf | +0.82 | [+0.08, +1.81] | [0.09, 1.84] | 0.1139 | 70/55/275 |
| whisper-small/beam | ls-tc-babble5 | mbr | +0.01 | [-0.24, +0.28] | [-0.23, 0.24] | 0.8593 | 37/35/328 |
| whisper-small/greedy | ls-tc-babble5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/greedy | ls-tc-babble5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/sample | ls-tc-babble5 | conf | +2.79 | [-0.45, +7.75] | [-0.55, 7.97] | 0.4906 | 75/68/257 |
| whisper-small/sample | ls-tc-babble5 | mbr | +0.20 | [-0.14, +0.55] | [-0.27, 0.70] | 0.1129 | 67/45/288 |
| whisper-small/beam | ls-test-clean | conf | +0.02 | [-0.12, +0.18] | [-0.16, 0.25] | 0.9016 | 31/34/735 |
| whisper-small/beam | ls-test-clean | mbr | -0.04 | [-0.16, +0.06] | [-0.15, 0.06] | 0.4622 | 28/34/738 |
| whisper-small/greedy | ls-test-clean | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-small/greedy | ls-test-clean | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-small/sample | ls-test-clean | conf | +0.94 | [+0.07, +2.40] | [0.04, 2.40] | 0.3396 | 48/45/707 |
| whisper-small/sample | ls-test-clean | mbr | +0.12 | [-0.01, +0.24] | [-0.01, 0.26] | 0.0594 | 42/28/730 |
| whisper-small/beam | ls-test-other | conf | -0.02 | [-0.29, +0.23] | [-0.29, 0.26] | 0.8286 | 73/85/642 |
| whisper-small/beam | ls-test-other | mbr | -0.06 | [-0.21, +0.09] | [-0.18, 0.08] | 0.4667 | 39/47/714 |
| whisper-small/greedy | ls-test-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-small/greedy | ls-test-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-small/sample | ls-test-other | conf | +0.24 | [-0.33, +0.80] | [-0.41, 0.79] | 0.3190 | 98/93/609 |
| whisper-small/sample | ls-test-other | mbr | +0.04 | [-0.12, +0.19] | [-0.11, 0.18] | 0.5321 | 54/48/698 |
| whisper-turbo/beam | ami | conf | +7.92 | [+1.81, +15.98] | [1.84, 16.83] | 0.3919 | 109/116/575 |
| whisper-turbo/beam | ami | mbr | -0.51 | [-0.82, -0.20] | [-0.89, -0.20] | 0.0008 | 45/84/671 |
| whisper-turbo/greedy | ami | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/greedy | ami | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/sample | ami | conf | +0.21 | [-0.36, +0.80] | [-0.27, 0.73] | 0.4505 | 83/74/643 |
| whisper-turbo/sample | ami | mbr | +0.22 | [-0.07, +0.52] | [-0.03, 0.49] | 0.1423 | 56/38/706 |
| whisper-turbo/beam | common_voice | conf | -0.63 | [-1.12, -0.18] | [, ] | 0.0091 | 20/38/410 |
| whisper-turbo/beam | common_voice | mbr | -0.47 | [-0.81, -0.14] | [, ] | 0.0063 | 13/29/426 |
| whisper-turbo/greedy | common_voice | conf | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/468 |
| whisper-turbo/greedy | common_voice | mbr | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/468 |
| whisper-turbo/sample | common_voice | conf | +0.49 | [-0.62, +1.96] | [, ] | 0.7655 | 29/28/411 |
| whisper-turbo/sample | common_voice | mbr | +0.40 | [+0.02, +0.81] | [, ] | 0.0501 | 25/15/428 |
| whisper-turbo/beam | earnings22 | conf | -0.39 | [-0.68, -0.10] | [-0.77, -0.04] | 0.0050 | 58/93/556 |
| whisper-turbo/beam | earnings22 | mbr | -0.10 | [-0.27, +0.05] | [-0.19, 0.00] | 0.2247 | 33/45/629 |
| whisper-turbo/greedy | earnings22 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/707 |
| whisper-turbo/greedy | earnings22 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/707 |
| whisper-turbo/sample | earnings22 | conf | -0.63 | [-1.19, -0.15] | [-1.32, 0.04] | 0.0179 | 58/83/566 |
| whisper-turbo/sample | earnings22 | mbr | -0.03 | [-0.19, +0.13] | [-0.11, 0.03] | 0.6764 | 36/43/628 |
| whisper-turbo/beam | fleurs-en | conf | +0.00 | [-0.19, +0.20] | [-0.20, 0.20] | 0.9821 | 27/28/391 |
| whisper-turbo/beam | fleurs-en | mbr | +0.10 | [-0.06, +0.28] | [-0.05, 0.28] | 0.2515 | 23/16/407 |
| whisper-turbo/greedy | fleurs-en | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/446 |
| whisper-turbo/greedy | fleurs-en | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/446 |
| whisper-turbo/sample | fleurs-en | conf | -0.07 | [-0.46, +0.21] | [-0.46, 0.22] | 0.5991 | 23/19/404 |
| whisper-turbo/sample | fleurs-en | mbr | +0.11 | [-0.04, +0.27] | [-0.04, 0.28] | 0.1563 | 24/16/406 |
| whisper-turbo/beam | ls-dev-other | conf | +0.32 | [+0.15, +0.50] | [0.14, 0.50] | 0.0004 | 66/33/701 |
| whisper-turbo/beam | ls-dev-other | mbr | -0.03 | [-0.15, +0.08] | [-0.12, 0.06] | 0.5382 | 24/29/747 |
| whisper-turbo/greedy | ls-dev-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/greedy | ls-dev-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/sample | ls-dev-other | conf | +0.10 | [-0.03, +0.26] | [-0.08, 0.30] | 0.2583 | 43/30/727 |
| whisper-turbo/sample | ls-dev-other | mbr | -0.01 | [-0.11, +0.08] | [-0.11, 0.09] | 0.7679 | 21/21/758 |
| whisper-turbo/beam | ls-tc-babble15 | conf | +0.08 | [-0.12, +0.28] | [-0.08, 0.24] | 0.4386 | 7/5/188 |
| whisper-turbo/beam | ls-tc-babble15 | mbr | -0.15 | [-0.31, +0.00] | [-0.32, 0.00] | 0.0578 | 1/6/193 |
| whisper-turbo/greedy | ls-tc-babble15 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/greedy | ls-tc-babble15 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/sample | ls-tc-babble15 | conf | +0.00 | [-0.18, +0.19] | [-0.13, 0.15] | 1.0000 | 5/6/189 |
| whisper-turbo/sample | ls-tc-babble15 | mbr | -0.03 | [-0.14, +0.08] | [-0.14, 0.08] | 0.6547 | 2/3/195 |
| whisper-turbo/beam | ls-tc-babble5 | conf | +0.00 | [-0.27, +0.30] | [-0.30, 0.31] | 0.7513 | 32/37/331 |
| whisper-turbo/beam | ls-tc-babble5 | mbr | -0.13 | [-0.31, +0.07] | [-0.35, 0.08] | 0.1346 | 17/27/356 |
| whisper-turbo/greedy | ls-tc-babble5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/greedy | ls-tc-babble5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/sample | ls-tc-babble5 | conf | -0.09 | [-0.39, +0.19] | [-0.39, 0.19] | 0.7681 | 37/34/329 |
| whisper-turbo/sample | ls-tc-babble5 | mbr | +0.08 | [-0.12, +0.27] | [-0.11, 0.27] | 0.5134 | 28/22/350 |
| whisper-turbo/beam | ls-tc-babbleM5 | conf | +4.40 | [+0.36, +8.24] | [0.56, 8.24] | 0.0000 | 82/34/84 |
| whisper-turbo/beam | ls-tc-babbleM5 | mbr | -1.07 | [-2.22, -0.16] | [-2.04, -0.14] | 0.1060 | 27/43/130 |
| whisper-turbo/greedy | ls-tc-babbleM5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/greedy | ls-tc-babbleM5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/sample | ls-tc-babbleM5 | conf | +109.87 | [+77.56, +145.86] | [72.67, 149.17] | 0.0000 | 121/25/54 |
| whisper-turbo/sample | ls-tc-babbleM5 | mbr | +1.81 | [+1.09, +2.54] | [1.30, 2.35] | 0.0000 | 64/16/120 |
| whisper-turbo/beam | ls-tc-white0 | conf | +0.31 | [-0.10, +0.77] | [-0.10, 0.73] | 0.2128 | 27/18/155 |
| whisper-turbo/beam | ls-tc-white0 | mbr | -0.10 | [-0.38, +0.19] | [-0.33, 0.12] | 0.4795 | 12/17/171 |
| whisper-turbo/greedy | ls-tc-white0 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/greedy | ls-tc-white0 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/sample | ls-tc-white0 | conf | -0.18 | [-1.20, +0.63] | [-1.22, 0.60] | 0.5929 | 32/28/140 |
| whisper-turbo/sample | ls-tc-white0 | mbr | +0.31 | [-0.08, +0.70] | [-0.05, 0.63] | 0.1151 | 25/17/158 |
| whisper-turbo/beam | ls-tc-white10 | conf | +0.23 | [+0.03, +0.46] | [0.03, 0.45] | 0.0293 | 9/2/189 |
| whisper-turbo/beam | ls-tc-white10 | mbr | -0.15 | [-0.39, +0.07] | [-0.41, 0.05] | 0.1927 | 3/8/189 |
| whisper-turbo/greedy | ls-tc-white10 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/greedy | ls-tc-white10 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/sample | ls-tc-white10 | conf | +1.51 | [-0.02, +4.48] | [-0.03, 4.56] | 0.1535 | 8/4/188 |
| whisper-turbo/sample | ls-tc-white10 | mbr | -0.03 | [-0.14, +0.08] | [-0.15, 0.09] | 0.6547 | 2/3/195 |
| whisper-turbo/beam | ls-test-clean | conf | +0.00 | [-0.11, +0.11] | [-0.13, 0.13] | 0.9859 | 32/34/734 |
| whisper-turbo/beam | ls-test-clean | mbr | -0.10 | [-0.21, +0.00] | [-0.19, 0.00] | 0.0606 | 16/30/754 |
| whisper-turbo/greedy | ls-test-clean | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/greedy | ls-test-clean | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/sample | ls-test-clean | conf | +0.32 | [-0.08, +1.04] | [-0.09, 1.04] | 0.9310 | 23/24/753 |
| whisper-turbo/sample | ls-test-clean | mbr | +0.01 | [-0.05, +0.08] | [-0.05, 0.07] | 0.7150 | 14/13/773 |
| whisper-turbo/beam | ls-test-other | conf | +0.17 | [-0.03, +0.35] | [-0.01, 0.34] | 0.0130 | 63/37/700 |
| whisper-turbo/beam | ls-test-other | mbr | +0.09 | [-0.03, +0.22] | [-0.04, 0.22] | 0.1281 | 33/24/743 |
| whisper-turbo/greedy | ls-test-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/greedy | ls-test-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/800 |
| whisper-turbo/sample | ls-test-other | conf | +0.04 | [-0.13, +0.22] | [-0.13, 0.22] | 0.7667 | 42/38/720 |
| whisper-turbo/sample | ls-test-other | mbr | +0.11 | [+0.00, +0.21] | [0.01, 0.19] | 0.0502 | 28/16/756 |

## Pooled over test sets (random effects)

| model | arm | norm | a -> b | sets | pooled delta | 95% CI | I2 | sets sig + / - |
|---|---|---|---|---|---|---|---|---|
| drax | main | legacy | conf -> mbr | 23 | +1.21 | [+1.01, +1.41] | 0.87 | 23 / 0 |
| drax | main | legacy | conf -> rover_cg | 23 | +1.87 | [+1.53, +2.21] | 0.95 | 23 / 0 |
| drax | main | legacy | first -> conf | 23 | +4.19 | [+3.68, +4.71] | 0.94 | 23 / 0 |
| drax | main | legacy | first -> rover_cg | 23 | +6.32 | [+5.51, +7.13] | 0.98 | 23 / 0 |
| drax | main | legacy | mbr -> rover_cg | 23 | +0.60 | [+0.40, +0.80] | 0.96 | 15 / 0 |
| drax | main | whisper | cm05 -> rover_cg | 23 | +0.75 | [+0.56, +0.93] | 0.93 | 20 / 0 |
| drax | main | whisper | conf -> mbr | 23 | +1.19 | [+1.01, +1.36] | 0.84 | 23 / 0 |
| drax | main | whisper | conf -> rover_c | 23 | +1.86 | [+1.55, +2.17] | 0.94 | 23 / 0 |
| drax | main | whisper | conf -> rover_cg | 23 | +1.81 | [+1.50, +2.12] | 0.95 | 23 / 0 |
| drax | main | whisper | conf -> rover_freq | 23 | +2.03 | [+1.68, +2.39] | 0.96 | 23 / 0 |
| drax | main | whisper | first -> conf | 23 | +4.18 | [+3.66, +4.70] | 0.94 | 23 / 0 |
| drax | main | whisper | first -> rover_cg | 23 | +6.25 | [+5.46, +7.04] | 0.98 | 23 / 0 |
| drax | main | whisper | mbr -> rover_cg | 23 | +0.55 | [+0.37, +0.73] | 0.96 | 16 / 1 |
| drax | main | whisper | rover_freq -> rover_cg | 23 | -0.19 | [-0.28, -0.11] | 0.88 | 0 / 9 |
| drax | ref | legacy | conf -> mbr | 23 | +0.16 | [+0.09, +0.24] | 0.54 | 7 / 1 |
| drax | ref | legacy | conf -> rover_cg | 23 | +0.20 | [+0.12, +0.28] | 0.64 | 9 / 0 |
| drax | ref | legacy | first -> conf | 23 | +0.25 | [+0.16, +0.34] | 0.61 | 10 / 1 |
| drax | ref | legacy | first -> rover_cg | 23 | +0.46 | [+0.33, +0.59] | 0.85 | 18 / 1 |
| drax | ref | legacy | mbr -> rover_cg | 23 | +0.07 | [-0.02, +0.17] | 0.87 | 4 / 1 |
| drax | ref | whisper | cm05 -> rover_cg | 23 | +0.01 | [-0.06, +0.09] | 0.82 | 3 / 4 |
| drax | ref | whisper | conf -> mbr | 23 | +0.16 | [+0.09, +0.23] | 0.54 | 9 / 1 |
| drax | ref | whisper | conf -> rover_c | 23 | +0.24 | [+0.17, +0.31] | 0.61 | 12 / 0 |
| drax | ref | whisper | conf -> rover_cg | 23 | +0.17 | [+0.09, +0.25] | 0.70 | 8 / 1 |
| drax | ref | whisper | conf -> rover_freq | 23 | +0.25 | [+0.18, +0.31] | 0.48 | 12 / 0 |
| drax | ref | whisper | first -> conf | 23 | +0.24 | [+0.16, +0.32] | 0.54 | 10 / 1 |
| drax | ref | whisper | first -> rover_cg | 23 | +0.42 | [+0.29, +0.54] | 0.84 | 16 / 1 |
| drax | ref | whisper | mbr -> rover_cg | 23 | +0.04 | [-0.05, +0.12] | 0.85 | 3 / 3 |
| drax | ref | whisper | rover_freq -> rover_cg | 23 | -0.09 | [-0.13, -0.05] | 0.59 | 0 / 7 |
| parakeet-ctc | sample | legacy | conf -> mbr | 7 | +1.24 | [+0.74, +1.75] | 0.95 | 7 / 0 |
| parakeet-ctc | sample | legacy | conf -> rover_cg | 7 | +1.48 | [+0.93, +2.02] | 0.95 | 7 / 0 |
| parakeet-ctc | sample | legacy | first -> conf | 7 | +1.49 | [+0.81, +2.17] | 0.93 | 7 / 0 |
| parakeet-ctc | sample | legacy | first -> rover_cg | 7 | +3.01 | [+1.95, +4.06] | 0.97 | 7 / 0 |
| parakeet-ctc | sample | legacy | mbr -> rover_cg | 7 | +0.21 | [+0.06, +0.37] | 0.79 | 4 / 0 |
| parakeet-ctc | sample | whisper | cm05 -> rover_cg | 7 | +0.33 | [+0.16, +0.50] | 0.76 | 5 / 0 |
| parakeet-ctc | sample | whisper | conf -> mbr | 7 | +1.38 | [+0.84, +1.93] | 0.96 | 7 / 0 |
| parakeet-ctc | sample | whisper | conf -> rover_c | 7 | +1.61 | [+1.01, +2.22] | 0.96 | 7 / 0 |
| parakeet-ctc | sample | whisper | conf -> rover_cg | 7 | +1.60 | [+1.01, +2.18] | 0.96 | 7 / 0 |
| parakeet-ctc | sample | whisper | conf -> rover_freq | 7 | +1.66 | [+1.03, +2.29] | 0.96 | 7 / 0 |
| parakeet-ctc | sample | whisper | first -> conf | 7 | +1.56 | [+0.90, +2.22] | 0.93 | 7 / 0 |
| parakeet-ctc | sample | whisper | first -> rover_cg | 7 | +3.23 | [+2.07, +4.38] | 0.98 | 7 / 0 |
| parakeet-ctc | sample | whisper | mbr -> rover_cg | 7 | +0.18 | [+0.09, +0.28] | 0.49 | 3 / 0 |
| parakeet-ctc | sample | whisper | rover_freq -> rover_cg | 7 | -0.01 | [-0.06, +0.04] | 0.00 | 0 / 0 |
| whisfusion | main | legacy | conf -> mbr | 18 | +1.72 | [+1.48, +1.96] | 0.76 | 18 / 0 |
| whisfusion | main | legacy | conf -> rover_cg | 18 | +4.71 | [+4.05, +5.36] | 0.96 | 18 / 0 |
| whisfusion | main | legacy | first -> conf | 18 | +7.02 | [+6.44, +7.60] | 0.88 | 18 / 0 |
| whisfusion | main | legacy | first -> rover_cg | 18 | +11.82 | [+10.75, +12.90] | 0.97 | 18 / 0 |
| whisfusion | main | legacy | mbr -> rover_cg | 18 | +2.92 | [+2.45, +3.40] | 0.96 | 18 / 0 |
| whisfusion | main | whisper | cm05 -> rover_cg | 18 | +3.12 | [+2.57, +3.67] | 0.96 | 18 / 0 |
| whisfusion | main | whisper | conf -> mbr | 18 | +1.74 | [+1.48, +2.00] | 0.79 | 17 / 0 |
| whisfusion | main | whisper | conf -> rover_c | 18 | +4.59 | [+3.92, +5.26] | 0.96 | 18 / 0 |
| whisfusion | main | whisper | conf -> rover_cg | 18 | +4.62 | [+3.96, +5.29] | 0.96 | 18 / 0 |
| whisfusion | main | whisper | conf -> rover_freq | 18 | +3.93 | [+3.36, +4.51] | 0.94 | 18 / 0 |
| whisfusion | main | whisper | first -> conf | 18 | +7.14 | [+6.51, +7.77] | 0.90 | 18 / 0 |
| whisfusion | main | whisper | first -> rover_cg | 18 | +11.86 | [+10.76, +12.96] | 0.97 | 18 / 0 |
| whisfusion | main | whisper | mbr -> rover_cg | 18 | +2.84 | [+2.36, +3.32] | 0.97 | 18 / 0 |
| whisfusion | main | whisper | rover_freq -> rover_cg | 18 | +0.56 | [+0.40, +0.72] | 0.90 | 15 / 0 |
| whisper-small | beam | legacy | conf -> mbr | 7 | +0.06 | [-0.09, +0.22] | 0.24 | 2 / 0 |
| whisper-small | beam | legacy | conf -> rover_cg | 7 | +0.06 | [-0.14, +0.27] | 0.57 | 2 / 0 |
| whisper-small | beam | legacy | first -> conf | 7 | -0.03 | [-0.15, +0.10] | 0.31 | 0 / 1 |
| whisper-small | beam | legacy | first -> rover_cg | 7 | +0.06 | [-0.10, +0.22] | 0.51 | 1 / 0 |
| whisper-small | beam | legacy | mbr -> rover_cg | 7 | -0.05 | [-0.16, +0.07] | 0.53 | 0 / 1 |
| whisper-small | beam | whisper | cm05 -> rover_cg | 7 | -0.11 | [-0.21, -0.01] | 0.35 | 0 / 1 |
| whisper-small | beam | whisper | conf -> mbr | 7 | -0.00 | [-0.26, +0.25] | 0.67 | 2 / 1 |
| whisper-small | beam | whisper | conf -> rover_c | 7 | -0.03 | [-0.27, +0.21] | 0.68 | 2 / 1 |
| whisper-small | beam | whisper | conf -> rover_cg | 7 | -0.03 | [-0.24, +0.18] | 0.56 | 2 / 1 |
| whisper-small | beam | whisper | conf -> rover_freq | 7 | -0.02 | [-0.28, +0.24] | 0.72 | 2 / 1 |
| whisper-small | beam | whisper | first -> conf | 7 | +0.04 | [-0.09, +0.18] | 0.40 | 0 / 0 |
| whisper-small | beam | whisper | first -> rover_cg | 7 | +0.02 | [-0.13, +0.17] | 0.44 | 1 / 0 |
| whisper-small | beam | whisper | mbr -> rover_cg | 7 | -0.04 | [-0.11, +0.04] | 0.11 | 0 / 1 |
| whisper-small | beam | whisper | rover_freq -> rover_cg | 7 | -0.03 | [-0.11, +0.06] | 0.38 | 0 / 0 |
| whisper-small | sample | legacy | conf -> mbr | 7 | -0.32 | [-1.25, +0.60] | 0.72 | 0 / 2 |
| whisper-small | sample | legacy | conf -> rover_cg | 7 | -0.06 | [-0.77, +0.65] | 0.54 | 1 / 0 |
| whisper-small | sample | legacy | first -> conf | 7 | +1.23 | [+0.17, +2.29] | 0.78 | 4 / 0 |
| whisper-small | sample | legacy | first -> rover_cg | 7 | +1.22 | [+0.59, +1.85] | 0.85 | 5 / 0 |
| whisper-small | sample | legacy | mbr -> rover_cg | 7 | +0.25 | [+0.06, +0.43] | 0.74 | 2 / 0 |
| whisper-small | sample | whisper | cm05 -> rover_cg | 7 | -0.28 | [-0.53, -0.03] | 0.69 | 0 / 2 |
| whisper-small | sample | whisper | conf -> mbr | 7 | -0.25 | [-1.17, +0.66] | 0.71 | 0 / 1 |
| whisper-small | sample | whisper | conf -> rover_c | 7 | -0.00 | [-0.80, +0.80] | 0.64 | 2 / 0 |
| whisper-small | sample | whisper | conf -> rover_cg | 7 | -0.07 | [-0.85, +0.71] | 0.62 | 2 / 0 |
| whisper-small | sample | whisper | conf -> rover_freq | 7 | -0.13 | [-1.00, +0.73] | 0.69 | 2 / 1 |
| whisper-small | sample | whisper | first -> conf | 7 | +1.22 | [+0.12, +2.31] | 0.78 | 3 / 0 |
| whisper-small | sample | whisper | first -> rover_cg | 7 | +1.28 | [+0.62, +1.95] | 0.87 | 5 / 0 |
| whisper-small | sample | whisper | mbr -> rover_cg | 7 | +0.19 | [+0.06, +0.33] | 0.59 | 2 / 0 |
| whisper-small | sample | whisper | rover_freq -> rover_cg | 7 | +0.02 | [-0.07, +0.11] | 0.34 | 0 / 1 |
| whisper-turbo | beam | legacy | conf -> mbr | 11 | +0.03 | [-0.11, +0.17] | 0.52 | 2 / 0 |
| whisper-turbo | beam | legacy | conf -> rover_cg | 11 | +0.00 | [-0.14, +0.14] | 0.54 | 2 / 1 |
| whisper-turbo | beam | legacy | first -> conf | 11 | +0.00 | [-0.11, +0.12] | 0.56 | 1 / 2 |
| whisper-turbo | beam | legacy | first -> rover_cg | 11 | +0.00 | [-0.13, +0.14] | 0.64 | 1 / 0 |
| whisper-turbo | beam | legacy | mbr -> rover_cg | 11 | -0.11 | [-0.23, +0.02] | 0.73 | 0 / 3 |
| whisper-turbo | beam | whisper | cm05 -> rover_cg | 11 | -0.13 | [-0.25, -0.01] | 0.73 | 0 / 4 |
| whisper-turbo | beam | whisper | conf -> mbr | 11 | +0.09 | [-0.06, +0.24] | 0.68 | 4 / 1 |
| whisper-turbo | beam | whisper | conf -> rover_c | 11 | +0.05 | [-0.08, +0.18] | 0.65 | 3 / 2 |
| whisper-turbo | beam | whisper | conf -> rover_cg | 11 | +0.01 | [-0.14, +0.16] | 0.69 | 3 / 2 |
| whisper-turbo | beam | whisper | conf -> rover_freq | 11 | +0.02 | [-0.14, +0.17] | 0.73 | 3 / 1 |
| whisper-turbo | beam | whisper | first -> conf | 11 | -0.01 | [-0.13, +0.11] | 0.67 | 2 / 2 |
| whisper-turbo | beam | whisper | first -> rover_cg | 11 | +0.01 | [-0.12, +0.13] | 0.68 | 1 / 0 |
| whisper-turbo | beam | whisper | mbr -> rover_cg | 11 | -0.12 | [-0.23, -0.02] | 0.67 | 0 / 3 |
| whisper-turbo | beam | whisper | rover_freq -> rover_cg | 11 | -0.03 | [-0.10, +0.05] | 0.55 | 0 / 2 |
| whisper-turbo | sample | legacy | conf -> mbr | 11 | -0.05 | [-0.38, +0.27] | 0.78 | 2 / 0 |
| whisper-turbo | sample | legacy | conf -> rover_cg | 11 | +0.02 | [-0.28, +0.32] | 0.78 | 2 / 0 |
| whisper-turbo | sample | legacy | first -> conf | 11 | +0.68 | [+0.27, +1.09] | 0.81 | 6 / 1 |
| whisper-turbo | sample | legacy | first -> rover_cg | 11 | +0.73 | [+0.44, +1.02] | 0.74 | 9 / 0 |
| whisper-turbo | sample | legacy | mbr -> rover_cg | 11 | +0.10 | [-0.01, +0.20] | 0.71 | 2 / 0 |
| whisper-turbo | sample | whisper | cm05 -> rover_cg | 11 | -0.03 | [-0.09, +0.04] | 0.30 | 1 / 1 |
| whisper-turbo | sample | whisper | conf -> mbr | 11 | -0.08 | [-0.41, +0.24] | 0.80 | 1 / 1 |
| whisper-turbo | sample | whisper | conf -> rover_c | 11 | +0.00 | [-0.30, +0.30] | 0.80 | 1 / 1 |
| whisper-turbo | sample | whisper | conf -> rover_cg | 11 | +0.00 | [-0.31, +0.31] | 0.81 | 1 / 1 |
| whisper-turbo | sample | whisper | conf -> rover_freq | 11 | -0.05 | [-0.37, +0.27] | 0.80 | 1 / 1 |
| whisper-turbo | sample | whisper | first -> conf | 11 | +0.68 | [+0.31, +1.06] | 0.81 | 7 / 1 |
| whisper-turbo | sample | whisper | first -> rover_cg | 11 | +0.65 | [+0.40, +0.90] | 0.74 | 8 / 0 |
| whisper-turbo | sample | whisper | mbr -> rover_cg | 11 | +0.09 | [+0.00, +0.18] | 0.72 | 2 / 0 |
| whisper-turbo | sample | whisper | rover_freq -> rover_cg | 11 | +0.04 | [-0.00, +0.07] | 0.00 | 0 / 0 |

## Against each model's standard decoding

| model | set | comparison | WER a | WER b | delta | 95% CI |
|---|---|---|---|---|---|---|
| drax | ami | Drax standard (T=0.1, 1 sample) vs ROVER@main | 10.60 | 10.52 | +0.08 | [-0.35, +0.50] |
| drax | common_voice | Drax standard (T=0.1, 1 sample) vs ROVER@main | 13.39 | 13.46 | -0.07 | [-0.67, +0.58] |
| drax | earnings22 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 14.57 | 16.15 | -1.59 | [-2.55, -0.73] |
| drax | fleurs-de | Drax standard (T=0.1, 1 sample) vs ROVER@main | 11.58 | 10.15 | +1.43 | [+1.13, +1.75] |
| drax | fleurs-en | Drax standard (T=0.1, 1 sample) vs ROVER@main | 9.54 | 8.95 | +0.59 | [+0.28, +0.90] |
| drax | fleurs-es | Drax standard (T=0.1, 1 sample) vs ROVER@main | 8.62 | 8.07 | +0.55 | [+0.33, +0.78] |
| drax | fleurs-fr | Drax standard (T=0.1, 1 sample) vs ROVER@main | 13.27 | 12.53 | +0.73 | [+0.42, +1.04] |
| drax | fleurs-it | Drax standard (T=0.1, 1 sample) vs ROVER@main | 9.36 | 8.34 | +1.02 | [+0.74, +1.28] |
| drax | fleurs-pt | Drax standard (T=0.1, 1 sample) vs ROVER@main | 15.36 | 13.88 | +1.48 | [+1.13, +1.81] |
| drax | gigaspeech | Drax standard (T=0.1, 1 sample) vs ROVER@main | 12.19 | 11.74 | +0.45 | [+0.04, +0.85] |
| drax | ls-dev-clean | Drax standard (T=0.1, 1 sample) vs ROVER@main | 3.09 | 2.70 | +0.40 | [+0.08, +0.78] |
| drax | ls-dev-other | Drax standard (T=0.1, 1 sample) vs ROVER@main | 5.78 | 5.81 | -0.03 | [-0.98, +0.59] |
| drax | ls-tc-babble0 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 35.32 | 37.22 | -1.91 | [-2.83, -1.04] |
| drax | ls-tc-babble10 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 4.34 | 3.88 | +0.47 | [+0.21, +0.73] |
| drax | ls-tc-babble15 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 2.90 | 2.62 | +0.28 | [+0.08, +0.49] |
| drax | ls-tc-babble5 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 9.36 | 9.24 | +0.12 | [-0.28, +0.50] |
| drax | ls-tc-babbleM5 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 90.07 | 90.92 | -0.86 | [-1.50, -0.23] |
| drax | ls-tc-white0 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 16.07 | 15.62 | +0.46 | [+0.02, +0.91] |
| drax | ls-tc-white10 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 4.19 | 3.85 | +0.33 | [+0.09, +0.58] |
| drax | ls-tc-white5 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 7.12 | 6.81 | +0.32 | [+0.02, +0.60] |
| drax | ls-test-clean | Drax standard (T=0.1, 1 sample) vs ROVER@main | 2.40 | 2.25 | +0.15 | [+0.00, +0.28] |
| drax | ls-test-other | Drax standard (T=0.1, 1 sample) vs ROVER@main | 5.96 | 5.44 | +0.52 | [+0.29, +0.76] |
| drax | slr83 | Drax standard (T=0.1, 1 sample) vs ROVER@main | 6.72 | 5.99 | +0.73 | [+0.43, +1.04] |
| drax | spgispeech | Drax standard (T=0.1, 1 sample) vs ROVER@main | 4.75 | 4.42 | +0.33 | [+0.12, +0.56] |
| drax | voxpopuli | Drax standard (T=0.1, 1 sample) vs ROVER@main | 7.20 | 7.06 | +0.15 | [-0.06, +0.35] |
| drax | ami | Drax standard vs confidence pick@main | 10.60 | 12.66 | -2.06 | [-2.67, -1.45] |
| drax | common_voice | Drax standard vs confidence pick@main | 13.39 | 15.24 | -1.85 | [-2.62, -1.10] |
| drax | earnings22 | Drax standard vs confidence pick@main | 14.57 | 19.64 | -5.07 | [-6.83, -3.43] |
| drax | fleurs-de | Drax standard vs confidence pick@main | 11.58 | 12.06 | -0.48 | [-0.89, -0.07] |
| drax | fleurs-en | Drax standard vs confidence pick@main | 9.54 | 10.70 | -1.16 | [-1.59, -0.74] |
| drax | fleurs-es | Drax standard vs confidence pick@main | 8.62 | 8.97 | -0.34 | [-0.63, -0.06] |
| drax | fleurs-fr | Drax standard vs confidence pick@main | 13.27 | 13.96 | -0.69 | [-1.08, -0.29] |
| drax | fleurs-it | Drax standard vs confidence pick@main | 9.36 | 9.52 | -0.16 | [-0.49, +0.17] |
| drax | fleurs-pt | Drax standard vs confidence pick@main | 15.36 | 16.51 | -1.15 | [-1.60, -0.70] |
| drax | gigaspeech | Drax standard vs confidence pick@main | 12.19 | 13.25 | -1.07 | [-1.56, -0.60] |
| drax | ls-dev-clean | Drax standard vs confidence pick@main | 3.09 | 3.48 | -0.38 | [-1.02, +0.08] |
| drax | ls-dev-other | Drax standard vs confidence pick@main | 5.78 | 6.78 | -1.00 | [-1.54, -0.50] |
| drax | ls-tc-babble0 | Drax standard vs confidence pick@main | 35.32 | 42.60 | -7.28 | [-8.46, -6.19] |
| drax | ls-tc-babble10 | Drax standard vs confidence pick@main | 4.34 | 4.98 | -0.64 | [-0.98, -0.30] |
| drax | ls-tc-babble15 | Drax standard vs confidence pick@main | 2.90 | 3.33 | -0.42 | [-0.71, -0.15] |
| drax | ls-tc-babble5 | Drax standard vs confidence pick@main | 9.36 | 11.58 | -2.22 | [-2.75, -1.71] |
| drax | ls-tc-babbleM5 | Drax standard vs confidence pick@main | 90.07 | 98.39 | -8.32 | [-10.17, -6.55] |
| drax | ls-tc-white0 | Drax standard vs confidence pick@main | 16.07 | 19.46 | -3.39 | [-4.03, -2.75] |
| drax | ls-tc-white10 | Drax standard vs confidence pick@main | 4.19 | 4.70 | -0.52 | [-0.81, -0.21] |
| drax | ls-tc-white5 | Drax standard vs confidence pick@main | 7.12 | 8.59 | -1.46 | [-1.88, -1.06] |
| drax | ls-test-clean | Drax standard vs confidence pick@main | 2.40 | 2.87 | -0.47 | [-0.68, -0.26] |
| drax | ls-test-other | Drax standard vs confidence pick@main | 5.96 | 6.76 | -0.80 | [-1.11, -0.48] |
| drax | slr83 | Drax standard vs confidence pick@main | 6.72 | 7.13 | -0.40 | [-0.79, -0.03] |
| drax | spgispeech | Drax standard vs confidence pick@main | 4.75 | 5.51 | -0.76 | [-1.05, -0.48] |
| drax | voxpopuli | Drax standard vs confidence pick@main | 7.20 | 7.79 | -0.58 | [-0.88, -0.30] |
| drax | ami | Drax standard vs MBR pick@main | 10.60 | 10.74 | -0.14 | [-0.60, +0.29] |
| drax | common_voice | Drax standard vs MBR pick@main | 13.39 | 13.87 | -0.47 | [-1.11, +0.23] |
| drax | earnings22 | Drax standard vs MBR pick@main | 14.57 | 16.66 | -2.09 | [-3.02, -1.25] |
| drax | fleurs-de | Drax standard vs MBR pick@main | 11.58 | 10.81 | +0.76 | [+0.46, +1.09] |
| drax | fleurs-en | Drax standard vs MBR pick@main | 9.54 | 9.46 | +0.08 | [-0.27, +0.42] |
| drax | fleurs-es | Drax standard vs MBR pick@main | 8.62 | 8.21 | +0.42 | [+0.20, +0.64] |
| drax | fleurs-fr | Drax standard vs MBR pick@main | 13.27 | 12.94 | +0.32 | [-0.01, +0.67] |
| drax | fleurs-it | Drax standard vs MBR pick@main | 9.36 | 8.72 | +0.63 | [+0.36, +0.91] |
| drax | fleurs-pt | Drax standard vs MBR pick@main | 15.36 | 14.88 | +0.48 | [+0.13, +0.85] |
| drax | gigaspeech | Drax standard vs MBR pick@main | 12.19 | 12.43 | -0.25 | [-0.74, +0.17] |
| drax | ls-dev-clean | Drax standard vs MBR pick@main | 3.09 | 2.70 | +0.40 | [+0.07, +0.79] |
| drax | ls-dev-other | Drax standard vs MBR pick@main | 5.78 | 6.12 | -0.34 | [-1.35, +0.29] |
| drax | ls-tc-babble0 | Drax standard vs MBR pick@main | 35.32 | 40.80 | -5.48 | [-6.52, -4.45] |
| drax | ls-tc-babble10 | Drax standard vs MBR pick@main | 4.34 | 3.95 | +0.39 | [+0.13, +0.65] |
| drax | ls-tc-babble15 | Drax standard vs MBR pick@main | 2.90 | 2.67 | +0.23 | [+0.03, +0.43] |
| drax | ls-tc-babble5 | Drax standard vs MBR pick@main | 9.36 | 9.88 | -0.52 | [-1.01, -0.07] |
| drax | ls-tc-babbleM5 | Drax standard vs MBR pick@main | 90.07 | 92.56 | -2.50 | [-3.13, -1.88] |
| drax | ls-tc-white0 | Drax standard vs MBR pick@main | 16.07 | 17.38 | -1.31 | [-1.84, -0.80] |
| drax | ls-tc-white10 | Drax standard vs MBR pick@main | 4.19 | 3.94 | +0.25 | [-0.01, +0.51] |
| drax | ls-tc-white5 | Drax standard vs MBR pick@main | 7.12 | 7.26 | -0.13 | [-0.47, +0.20] |
| drax | ls-test-clean | Drax standard vs MBR pick@main | 2.40 | 2.24 | +0.16 | [+0.03, +0.30] |
| drax | ls-test-other | Drax standard vs MBR pick@main | 5.96 | 5.67 | +0.30 | [+0.07, +0.54] |
| drax | slr83 | Drax standard vs MBR pick@main | 6.72 | 6.36 | +0.36 | [+0.05, +0.65] |
| drax | spgispeech | Drax standard vs MBR pick@main | 4.75 | 4.47 | +0.27 | [+0.06, +0.52] |
| drax | voxpopuli | Drax standard vs MBR pick@main | 7.20 | 6.94 | +0.27 | [+0.07, +0.46] |
| drax | ami | ROVER@T=0.1 vs ROVER@main | 10.43 | 10.52 | -0.10 | [-0.49, +0.27] |
| drax | common_voice | ROVER@T=0.1 vs ROVER@main | 12.62 | 13.46 | -0.85 | [-1.43, -0.26] |
| drax | earnings22 | ROVER@T=0.1 vs ROVER@main | 14.24 | 16.15 | -1.91 | [-2.82, -1.06] |
| drax | fleurs-de | ROVER@T=0.1 vs ROVER@main | 10.50 | 10.15 | +0.35 | [+0.09, +0.60] |
| drax | fleurs-en | ROVER@T=0.1 vs ROVER@main | 8.94 | 8.95 | -0.01 | [-0.26, +0.23] |
| drax | fleurs-es | ROVER@T=0.1 vs ROVER@main | 8.14 | 8.07 | +0.07 | [-0.11, +0.26] |
| drax | fleurs-fr | ROVER@T=0.1 vs ROVER@main | 12.87 | 12.53 | +0.34 | [+0.06, +0.61] |
| drax | fleurs-it | ROVER@T=0.1 vs ROVER@main | 8.69 | 8.34 | +0.35 | [+0.15, +0.54] |
| drax | fleurs-pt | ROVER@T=0.1 vs ROVER@main | 14.28 | 13.88 | +0.40 | [+0.11, +0.70] |
| drax | gigaspeech | ROVER@T=0.1 vs ROVER@main | 11.94 | 11.74 | +0.20 | [-0.17, +0.57] |
| drax | ls-dev-clean | ROVER@T=0.1 vs ROVER@main | 2.74 | 2.70 | +0.04 | [-0.25, +0.40] |
| drax | ls-dev-other | ROVER@T=0.1 vs ROVER@main | 5.51 | 5.81 | -0.30 | [-1.24, +0.30] |
| drax | ls-tc-babble0 | ROVER@T=0.1 vs ROVER@main | 34.84 | 37.22 | -2.38 | [-3.21, -1.55] |
| drax | ls-tc-babble10 | ROVER@T=0.1 vs ROVER@main | 3.97 | 3.88 | +0.09 | [-0.11, +0.28] |
| drax | ls-tc-babble15 | ROVER@T=0.1 vs ROVER@main | 2.69 | 2.62 | +0.07 | [-0.10, +0.24] |
| drax | ls-tc-babble5 | ROVER@T=0.1 vs ROVER@main | 8.90 | 9.24 | -0.33 | [-0.66, -0.01] |
| drax | ls-tc-babbleM5 | ROVER@T=0.1 vs ROVER@main | 90.92 | 90.92 | +0.00 | [-0.64, +0.63] |
| drax | ls-tc-white0 | ROVER@T=0.1 vs ROVER@main | 15.03 | 15.62 | -0.59 | [-1.03, -0.17] |
| drax | ls-tc-white10 | ROVER@T=0.1 vs ROVER@main | 3.88 | 3.85 | +0.02 | [-0.16, +0.22] |
| drax | ls-tc-white5 | ROVER@T=0.1 vs ROVER@main | 6.70 | 6.81 | -0.11 | [-0.35, +0.13] |
| drax | ls-test-clean | ROVER@T=0.1 vs ROVER@main | 2.27 | 2.25 | +0.02 | [-0.10, +0.15] |
| drax | ls-test-other | ROVER@T=0.1 vs ROVER@main | 5.55 | 5.44 | +0.11 | [-0.08, +0.31] |
| drax | slr83 | ROVER@T=0.1 vs ROVER@main | 6.28 | 5.99 | +0.29 | [+0.06, +0.54] |
| drax | spgispeech | ROVER@T=0.1 vs ROVER@main | 4.62 | 4.42 | +0.21 | [+0.02, +0.40] |
| drax | voxpopuli | ROVER@T=0.1 vs ROVER@main | 7.14 | 7.06 | +0.08 | [-0.09, +0.24] |
| drax | ami | Drax standard vs ROVER@T=0.4 | 10.73 | 9.78 | +0.96 | [+0.41, +1.48] |
| drax | common_voice | Drax standard vs ROVER@T=0.4 | 13.05 | 13.42 | -0.36 | [-2.38, +1.18] |
| drax | earnings22 | Drax standard vs ROVER@T=0.4 | 14.00 | 13.18 | +0.81 | [+0.23, +1.39] |
| drax | fleurs-de | Drax standard vs ROVER@T=0.4 | 12.08 | 10.30 | +1.78 | [+1.18, +2.40] |
| drax | fleurs-en | Drax standard vs ROVER@T=0.4 | 9.61 | 9.26 | +0.35 | [-0.10, +0.81] |
| drax | fleurs-es | Drax standard vs ROVER@T=0.4 | 8.20 | 7.65 | +0.55 | [+0.24, +0.91] |
| drax | fleurs-fr | Drax standard vs ROVER@T=0.4 | 13.79 | 12.87 | +0.92 | [+0.42, +1.47] |
| drax | fleurs-it | Drax standard vs ROVER@T=0.4 | 9.40 | 8.33 | +1.08 | [+0.56, +1.60] |
| drax | fleurs-pt | Drax standard vs ROVER@T=0.4 | 15.54 | 13.93 | +1.61 | [+1.06, +2.17] |
| drax | gigaspeech | Drax standard vs ROVER@T=0.4 | 11.73 | 11.04 | +0.68 | [+0.26, +1.13] |
| drax | ls-tc-babble0 | Drax standard vs ROVER@T=0.4 | 39.75 | 39.80 | -0.05 | [-2.20, +1.84] |
| drax | ls-tc-babble10 | Drax standard vs ROVER@T=0.4 | 4.93 | 4.12 | +0.82 | [+0.35, +1.35] |
| drax | ls-tc-babble15 | Drax standard vs ROVER@T=0.4 | 3.35 | 3.02 | +0.33 | [-0.03, +0.72] |
| drax | ls-tc-babble5 | Drax standard vs ROVER@T=0.4 | 10.51 | 9.41 | +1.10 | [+0.58, +1.61] |
| drax | ls-tc-babbleM5 | Drax standard vs ROVER@T=0.4 | 92.51 | 93.40 | -0.89 | [-2.28, +0.28] |
| drax | ls-tc-white0 | Drax standard vs ROVER@T=0.4 | 17.77 | 15.72 | +2.04 | [+1.34, +2.78] |
| drax | ls-tc-white10 | Drax standard vs ROVER@T=0.4 | 4.86 | 4.55 | +0.31 | [-0.15, +0.75] |
| drax | ls-tc-white5 | Drax standard vs ROVER@T=0.4 | 7.98 | 7.26 | +0.72 | [+0.21, +1.20] |
| drax | ls-test-clean | Drax standard vs ROVER@T=0.4 | 2.38 | 2.15 | +0.23 | [+0.04, +0.42] |
| drax | ls-test-other | Drax standard vs ROVER@T=0.4 | 5.74 | 4.95 | +0.79 | [+0.50, +1.13] |
| drax | slr83 | Drax standard vs ROVER@T=0.4 | 7.37 | 6.33 | +1.04 | [+0.47, +1.67] |
| drax | spgispeech | Drax standard vs ROVER@T=0.4 | 4.52 | 4.00 | +0.53 | [+0.21, +0.84] |
| drax | voxpopuli | Drax standard vs ROVER@T=0.4 | 7.40 | 7.23 | +0.17 | [-0.11, +0.45] |
| drax | ami | Drax standard vs MBR@T=0.4 | 10.73 | 9.83 | +0.90 | [+0.39, +1.44] |
| drax | common_voice | Drax standard vs MBR@T=0.4 | 13.05 | 13.13 | -0.07 | [-2.11, +1.47] |
| drax | earnings22 | Drax standard vs MBR@T=0.4 | 14.00 | 13.00 | +0.99 | [+0.38, +1.59] |
| drax | fleurs-de | Drax standard vs MBR@T=0.4 | 12.08 | 10.47 | +1.61 | [+1.04, +2.22] |
| drax | fleurs-en | Drax standard vs MBR@T=0.4 | 9.61 | 8.98 | +0.63 | [+0.17, +1.12] |
| drax | fleurs-es | Drax standard vs MBR@T=0.4 | 8.20 | 7.74 | +0.47 | [+0.14, +0.83] |
| drax | fleurs-fr | Drax standard vs MBR@T=0.4 | 13.79 | 12.93 | +0.86 | [+0.31, +1.42] |
| drax | fleurs-it | Drax standard vs MBR@T=0.4 | 9.40 | 8.26 | +1.14 | [+0.64, +1.64] |
| drax | fleurs-pt | Drax standard vs MBR@T=0.4 | 15.54 | 13.82 | +1.72 | [+1.14, +2.31] |
| drax | gigaspeech | Drax standard vs MBR@T=0.4 | 11.73 | 11.06 | +0.67 | [+0.23, +1.11] |
| drax | ls-tc-babble0 | Drax standard vs MBR@T=0.4 | 39.75 | 40.90 | -1.15 | [-3.50, +0.90] |
| drax | ls-tc-babble10 | Drax standard vs MBR@T=0.4 | 4.93 | 4.24 | +0.69 | [+0.20, +1.23] |
| drax | ls-tc-babble15 | Drax standard vs MBR@T=0.4 | 3.35 | 3.09 | +0.26 | [-0.18, +0.68] |
| drax | ls-tc-babble5 | Drax standard vs MBR@T=0.4 | 10.51 | 9.38 | +1.12 | [+0.60, +1.65] |
| drax | ls-tc-babbleM5 | Drax standard vs MBR@T=0.4 | 92.51 | 94.50 | -1.99 | [-3.58, -0.70] |
| drax | ls-tc-white0 | Drax standard vs MBR@T=0.4 | 17.77 | 15.85 | +1.92 | [+1.30, +2.57] |
| drax | ls-tc-white10 | Drax standard vs MBR@T=0.4 | 4.86 | 4.55 | +0.31 | [-0.14, +0.74] |
| drax | ls-tc-white5 | Drax standard vs MBR@T=0.4 | 7.98 | 7.31 | +0.66 | [+0.16, +1.14] |
| drax | ls-test-clean | Drax standard vs MBR@T=0.4 | 2.38 | 2.18 | +0.20 | [+0.01, +0.41] |
| drax | ls-test-other | Drax standard vs MBR@T=0.4 | 5.74 | 4.94 | +0.80 | [+0.49, +1.15] |
| drax | slr83 | Drax standard vs MBR@T=0.4 | 7.37 | 6.44 | +0.93 | [+0.38, +1.53] |
| drax | spgispeech | Drax standard vs MBR@T=0.4 | 4.52 | 3.86 | +0.66 | [+0.33, +0.98] |
| drax | voxpopuli | Drax standard vs MBR@T=0.4 | 7.40 | 7.08 | +0.32 | [+0.05, +0.60] |
| drax | ami | MBR vs ROVER, both @T=0.4 | 9.83 | 9.78 | +0.06 | [-0.22, +0.32] |
| drax | common_voice | MBR vs ROVER, both @T=0.4 | 13.08 | 13.37 | -0.29 | [-0.65, +0.00] |
| drax | earnings22 | MBR vs ROVER, both @T=0.4 | 13.00 | 13.18 | -0.18 | [-0.46, +0.10] |
| drax | fleurs-de | MBR vs ROVER, both @T=0.4 | 10.47 | 10.30 | +0.17 | [-0.07, +0.42] |
| drax | fleurs-en | MBR vs ROVER, both @T=0.4 | 8.98 | 9.26 | -0.28 | [-0.57, -0.02] |
| drax | fleurs-es | MBR vs ROVER, both @T=0.4 | 7.74 | 7.65 | +0.08 | [-0.10, +0.26] |
| drax | fleurs-fr | MBR vs ROVER, both @T=0.4 | 12.93 | 12.87 | +0.06 | [-0.19, +0.30] |
| drax | fleurs-it | MBR vs ROVER, both @T=0.4 | 8.26 | 8.33 | -0.06 | [-0.28, +0.15] |
| drax | fleurs-pt | MBR vs ROVER, both @T=0.4 | 13.82 | 13.93 | -0.11 | [-0.40, +0.20] |
| drax | gigaspeech | MBR vs ROVER, both @T=0.4 | 11.06 | 11.04 | +0.01 | [-0.17, +0.20] |
| drax | ls-tc-babble0 | MBR vs ROVER, both @T=0.4 | 40.90 | 39.80 | +1.10 | [+0.59, +1.57] |
| drax | ls-tc-babble10 | MBR vs ROVER, both @T=0.4 | 4.24 | 4.12 | +0.13 | [+0.00, +0.26] |
| drax | ls-tc-babble15 | MBR vs ROVER, both @T=0.4 | 3.09 | 3.02 | +0.08 | [-0.10, +0.25] |
| drax | ls-tc-babble5 | MBR vs ROVER, both @T=0.4 | 9.38 | 9.41 | -0.03 | [-0.34, +0.32] |
| drax | ls-tc-babbleM5 | MBR vs ROVER, both @T=0.4 | 94.50 | 93.40 | +1.10 | [+0.77, +1.44] |
| drax | ls-tc-white0 | MBR vs ROVER, both @T=0.4 | 15.85 | 15.72 | +0.13 | [-0.19, +0.45] |
| drax | ls-tc-white10 | MBR vs ROVER, both @T=0.4 | 4.55 | 4.55 | +0.00 | [-0.17, +0.18] |
| drax | ls-tc-white5 | MBR vs ROVER, both @T=0.4 | 7.31 | 7.26 | +0.05 | [-0.14, +0.24] |
| drax | ls-test-clean | MBR vs ROVER, both @T=0.4 | 2.18 | 2.15 | +0.03 | [-0.05, +0.10] |
| drax | ls-test-other | MBR vs ROVER, both @T=0.4 | 4.94 | 4.95 | -0.01 | [-0.15, +0.12] |
| drax | slr83 | MBR vs ROVER, both @T=0.4 | 6.44 | 6.33 | +0.11 | [-0.18, +0.43] |
| drax | spgispeech | MBR vs ROVER, both @T=0.4 | 3.86 | 4.00 | -0.13 | [-0.30, +0.03] |
| drax | voxpopuli | MBR vs ROVER, both @T=0.4 | 7.08 | 7.23 | -0.15 | [-0.28, -0.03] |
| drax | ami | ROVER@main vs ROVER@T=0.4 | 10.65 | 9.78 | +0.87 | [+0.33, +1.43] |
| drax | common_voice | ROVER@main vs ROVER@T=0.4 | 13.56 | 13.42 | +0.15 | [-1.91, +1.70] |
| drax | earnings22 | ROVER@main vs ROVER@T=0.4 | 16.03 | 13.18 | +2.85 | [+1.65, +4.26] |
| drax | fleurs-de | ROVER@main vs ROVER@T=0.4 | 10.33 | 10.30 | +0.02 | [-0.36, +0.42] |
| drax | fleurs-en | ROVER@main vs ROVER@T=0.4 | 9.45 | 9.26 | +0.19 | [-0.23, +0.63] |
| drax | fleurs-es | ROVER@main vs ROVER@T=0.4 | 7.90 | 7.65 | +0.24 | [+0.00, +0.48] |
| drax | fleurs-fr | ROVER@main vs ROVER@T=0.4 | 12.93 | 12.87 | +0.06 | [-0.36, +0.45] |
| drax | fleurs-it | ROVER@main vs ROVER@T=0.4 | 8.37 | 8.33 | +0.04 | [-0.29, +0.36] |
| drax | fleurs-pt | ROVER@main vs ROVER@T=0.4 | 13.87 | 13.93 | -0.06 | [-0.42, +0.32] |
| drax | gigaspeech | ROVER@main vs ROVER@T=0.4 | 11.19 | 11.04 | +0.14 | [-0.23, +0.54] |
| drax | ls-tc-babble0 | ROVER@main vs ROVER@T=0.4 | 41.23 | 39.80 | +1.43 | [-0.12, +2.95] |
| drax | ls-tc-babble10 | ROVER@main vs ROVER@T=0.4 | 4.27 | 4.12 | +0.15 | [-0.20, +0.53] |
| drax | ls-tc-babble15 | ROVER@main vs ROVER@T=0.4 | 3.02 | 3.02 | +0.00 | [-0.29, +0.30] |
| drax | ls-tc-babble5 | ROVER@main vs ROVER@T=0.4 | 10.22 | 9.41 | +0.82 | [+0.33, +1.33] |
| drax | ls-tc-babbleM5 | ROVER@main vs ROVER@T=0.4 | 93.63 | 93.40 | +0.23 | [-1.00, +1.35] |
| drax | ls-tc-white0 | ROVER@main vs ROVER@T=0.4 | 16.97 | 15.72 | +1.25 | [+0.52, +2.03] |
| drax | ls-tc-white10 | ROVER@main vs ROVER@T=0.4 | 4.52 | 4.55 | -0.03 | [-0.36, +0.33] |
| drax | ls-tc-white5 | ROVER@main vs ROVER@T=0.4 | 7.80 | 7.26 | +0.54 | [+0.16, +0.92] |
| drax | ls-test-clean | ROVER@main vs ROVER@T=0.4 | 2.19 | 2.15 | +0.04 | [-0.15, +0.24] |
| drax | ls-test-other | ROVER@main vs ROVER@T=0.4 | 5.09 | 4.95 | +0.14 | [-0.13, +0.42] |
| drax | slr83 | ROVER@main vs ROVER@T=0.4 | 6.22 | 6.33 | -0.11 | [-0.63, +0.39] |
| drax | spgispeech | ROVER@main vs ROVER@T=0.4 | 4.08 | 4.00 | +0.08 | [-0.20, +0.36] |
| drax | voxpopuli | ROVER@main vs ROVER@T=0.4 | 7.29 | 7.23 | +0.06 | [-0.21, +0.32] |
| whisfusion | ami | Whisfusion upstream (K=15 confidence) vs ROVER@main | 35.61 | 31.93 | +3.67 | [+2.92, +4.45] |
| whisfusion | common_voice | Whisfusion upstream (K=15 confidence) vs ROVER@main | 33.80 | 29.23 | +4.58 | [+3.65, +5.49] |
| whisfusion | earnings22 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 35.18 | 29.29 | +5.89 | [+5.28, +6.49] |
| whisfusion | fleurs-en | Whisfusion upstream (K=15 confidence) vs ROVER@main | 27.20 | 22.23 | +4.97 | [+4.38, +5.58] |
| whisfusion | gigaspeech | Whisfusion upstream (K=15 confidence) vs ROVER@main | 24.22 | 19.92 | +4.30 | [+3.77, +4.81] |
| whisfusion | ls-dev-clean | Whisfusion upstream (K=15 confidence) vs ROVER@main | 7.35 | 5.29 | +2.05 | [+1.59, +2.55] |
| whisfusion | ls-dev-other | Whisfusion upstream (K=15 confidence) vs ROVER@main | 15.89 | 12.59 | +3.31 | [+2.68, +3.94] |
| whisfusion | ls-tc-babble0 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 69.13 | 58.17 | +10.96 | [+9.90, +12.10] |
| whisfusion | ls-tc-babble10 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 16.81 | 11.48 | +5.33 | [+4.56, +6.09] |
| whisfusion | ls-tc-babble15 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 11.41 | 7.48 | +3.93 | [+3.42, +4.41] |
| whisfusion | ls-tc-babble5 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 32.76 | 24.52 | +8.24 | [+7.32, +9.16] |
| whisfusion | ls-tc-babbleM5 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 101.90 | 90.85 | +11.05 | [+9.56, +12.70] |
| whisfusion | ls-tc-white0 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 42.40 | 35.52 | +6.88 | [+6.18, +7.57] |
| whisfusion | ls-tc-white10 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 14.81 | 11.12 | +3.69 | [+3.14, +4.24] |
| whisfusion | ls-tc-white5 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 24.65 | 18.81 | +5.84 | [+5.06, +6.60] |
| whisfusion | ls-test-clean | Whisfusion upstream (K=15 confidence) vs ROVER@main | 8.08 | 5.59 | +2.49 | [+2.11, +2.89] |
| whisfusion | ls-test-other | Whisfusion upstream (K=15 confidence) vs ROVER@main | 15.94 | 12.33 | +3.61 | [+3.18, +4.05] |
| whisfusion | slr83 | Whisfusion upstream (K=15 confidence) vs ROVER@main | 21.28 | 17.50 | +3.79 | [+3.26, +4.32] |
| whisfusion | spgispeech | Whisfusion upstream (K=15 confidence) vs ROVER@main | 19.20 | 13.74 | +5.46 | [+5.05, +5.88] |
| whisfusion | voxpopuli | Whisfusion upstream (K=15 confidence) vs ROVER@main | 21.06 | 17.24 | +3.82 | [+3.34, +4.31] |
| whisfusion | ami | Whisfusion upstream vs ROVER at the same K=15 | 35.61 | 32.49 | +3.12 | [+2.35, +3.90] |
| whisfusion | common_voice | Whisfusion upstream vs ROVER at the same K=15 | 33.80 | 29.84 | +3.96 | [+3.10, +4.83] |
| whisfusion | earnings22 | Whisfusion upstream vs ROVER at the same K=15 | 35.18 | 30.12 | +5.06 | [+4.45, +5.66] |
| whisfusion | fleurs-en | Whisfusion upstream vs ROVER at the same K=15 | 27.20 | 22.79 | +4.41 | [+3.80, +5.03] |
| whisfusion | gigaspeech | Whisfusion upstream vs ROVER at the same K=15 | 24.22 | 20.32 | +3.91 | [+3.39, +4.43] |
| whisfusion | ls-dev-clean | Whisfusion upstream vs ROVER at the same K=15 | 7.35 | 5.52 | +1.83 | [+1.37, +2.32] |
| whisfusion | ls-dev-other | Whisfusion upstream vs ROVER at the same K=15 | 15.89 | 12.75 | +3.14 | [+2.54, +3.79] |
| whisfusion | ls-tc-babble0 | Whisfusion upstream vs ROVER at the same K=15 | 69.13 | 58.53 | +10.60 | [+9.51, +11.68] |
| whisfusion | ls-tc-babble10 | Whisfusion upstream vs ROVER at the same K=15 | 16.81 | 11.90 | +4.91 | [+4.19, +5.66] |
| whisfusion | ls-tc-babble15 | Whisfusion upstream vs ROVER at the same K=15 | 11.41 | 7.85 | +3.55 | [+3.06, +4.03] |
| whisfusion | ls-tc-babble5 | Whisfusion upstream vs ROVER at the same K=15 | 32.76 | 25.55 | +7.22 | [+6.35, +8.14] |
| whisfusion | ls-tc-babbleM5 | Whisfusion upstream vs ROVER at the same K=15 | 101.90 | 91.28 | +10.62 | [+9.18, +12.20] |
| whisfusion | ls-tc-white0 | Whisfusion upstream vs ROVER at the same K=15 | 42.40 | 35.96 | +6.44 | [+5.79, +7.08] |
| whisfusion | ls-tc-white10 | Whisfusion upstream vs ROVER at the same K=15 | 14.81 | 11.42 | +3.39 | [+2.85, +3.89] |
| whisfusion | ls-tc-white5 | Whisfusion upstream vs ROVER at the same K=15 | 24.65 | 19.41 | +5.23 | [+4.47, +6.02] |
| whisfusion | ls-test-clean | Whisfusion upstream vs ROVER at the same K=15 | 8.08 | 5.70 | +2.37 | [+1.98, +2.78] |
| whisfusion | ls-test-other | Whisfusion upstream vs ROVER at the same K=15 | 15.94 | 12.48 | +3.46 | [+3.04, +3.87] |
| whisfusion | slr83 | Whisfusion upstream vs ROVER at the same K=15 | 21.28 | 17.93 | +3.35 | [+2.84, +3.91] |
| whisfusion | spgispeech | Whisfusion upstream vs ROVER at the same K=15 | 19.20 | 14.18 | +5.01 | [+4.62, +5.42] |
| whisfusion | voxpopuli | Whisfusion upstream vs ROVER at the same K=15 | 21.06 | 17.76 | +3.30 | [+2.83, +3.79] |
| whisper-small | ami | greedy vs ROVER over samples | 16.26 | 16.23 | +0.03 | [-0.58, +0.61] |
| whisper-small | common_voice | greedy vs ROVER over samples | 16.83 | 15.60 | +1.24 | [+0.55, +1.93] |
| whisper-small | earnings22 | greedy vs ROVER over samples | 12.31 | 16.24 | -3.93 | [-5.84, -2.29] |
| whisper-small | fleurs-en | greedy vs ROVER over samples | 8.79 | 8.85 | -0.06 | [-0.56, +0.32] |
| whisper-small | ls-dev-other | greedy vs ROVER over samples | 7.16 | 7.24 | -0.08 | [-0.55, +0.29] |
| whisper-small | ls-tc-babble5 | greedy vs ROVER over samples | 13.99 | 13.33 | +0.67 | [-0.42, +1.96] |
| whisper-small | ls-test-clean | greedy vs ROVER over samples | 3.17 | 3.22 | -0.05 | [-0.23, +0.13] |
| whisper-small | ls-test-other | greedy vs ROVER over samples | 7.88 | 7.62 | +0.26 | [+0.01, +0.49] |
| whisper-small | ami | greedy vs ROVER over beam n-best | 16.26 | 34.76 | -18.50 | [-30.09, -8.98] |
| whisper-small | common_voice | greedy vs ROVER over beam n-best | 16.83 | 18.87 | -2.03 | [-9.65, +2.02] |
| whisper-small | earnings22 | greedy vs ROVER over beam n-best | 12.31 | 12.52 | -0.21 | [-3.56, +1.83] |
| whisper-small | fleurs-en | greedy vs ROVER over beam n-best | 8.79 | 7.93 | +0.85 | [+0.33, +1.50] |
| whisper-small | ls-dev-other | greedy vs ROVER over beam n-best | 7.16 | 6.84 | +0.33 | [+0.03, +0.64] |
| whisper-small | ls-tc-babble5 | greedy vs ROVER over beam n-best | 13.99 | 19.46 | -5.47 | [-13.60, +0.74] |
| whisper-small | ls-test-clean | greedy vs ROVER over beam n-best | 3.17 | 3.03 | +0.14 | [+0.00, +0.28] |
| whisper-small | ls-test-other | greedy vs ROVER over beam n-best | 7.88 | 7.08 | +0.81 | [+0.35, +1.34] |
| whisper-small | ami | top beam vs ROVER over n-best | 37.82 | 34.76 | +3.07 | [+0.03, +7.63] |
| whisper-small | common_voice | top beam vs ROVER over n-best | 18.73 | 18.87 | -0.14 | [-0.63, +0.34] |
| whisper-small | earnings22 | top beam vs ROVER over n-best | 12.87 | 12.52 | +0.35 | [-0.06, +0.78] |
| whisper-small | fleurs-en | top beam vs ROVER over n-best | 7.81 | 7.93 | -0.12 | [-0.32, +0.07] |
| whisper-small | ls-dev-other | top beam vs ROVER over n-best | 6.72 | 6.84 | -0.11 | [-0.32, +0.12] |
| whisper-small | ls-tc-babble5 | top beam vs ROVER over n-best | 19.79 | 19.46 | +0.33 | [-0.05, +0.77] |
| whisper-small | ls-test-clean | top beam vs ROVER over n-best | 2.95 | 3.03 | -0.08 | [-0.21, +0.05] |
| whisper-small | ls-test-other | top beam vs ROVER over n-best | 7.14 | 7.08 | +0.06 | [-0.15, +0.28] |
| whisper-small | ami | greedy vs MBR over samples | 16.26 | 16.33 | -0.07 | [-0.71, +0.54] |
| whisper-small | common_voice | greedy vs MBR over samples | 16.83 | 16.11 | +0.72 | [+0.00, +1.41] |
| whisper-small | earnings22 | greedy vs MBR over samples | 12.31 | 16.84 | -4.53 | [-6.62, -2.78] |
| whisper-small | fleurs-en | greedy vs MBR over samples | 8.79 | 8.96 | -0.17 | [-0.72, +0.22] |
| whisper-small | ls-dev-other | greedy vs MBR over samples | 7.16 | 7.29 | -0.13 | [-0.64, +0.24] |
| whisper-small | ls-tc-babble5 | greedy vs MBR over samples | 13.99 | 13.53 | +0.46 | [-0.67, +1.75] |
| whisper-small | ls-test-clean | greedy vs MBR over samples | 3.17 | 3.34 | -0.17 | [-0.36, +0.01] |
| whisper-small | ls-test-other | greedy vs MBR over samples | 7.88 | 7.66 | +0.22 | [-0.02, +0.45] |
| whisper-turbo | ami | greedy vs ROVER over samples | 14.52 | 14.40 | +0.12 | [-0.32, +0.56] |
| whisper-turbo | common_voice | greedy vs ROVER over samples | 11.60 | 11.16 | +0.44 | [-0.23, +1.14] |
| whisper-turbo | earnings22 | greedy vs ROVER over samples | 10.82 | 11.11 | -0.29 | [-0.80, +0.13] |
| whisper-turbo | fleurs-en | greedy vs ROVER over samples | 6.35 | 6.36 | -0.01 | [-0.40, +0.27] |
| whisper-turbo | ls-dev-other | greedy vs ROVER over samples | 3.96 | 3.92 | +0.04 | [-0.07, +0.15] |
| whisper-turbo | ls-tc-babble15 | greedy vs ROVER over samples | 2.63 | 2.71 | -0.08 | [-0.19, +0.03] |
| whisper-turbo | ls-tc-babble5 | greedy vs ROVER over samples | 6.64 | 6.32 | +0.32 | [+0.04, +0.61] |
| whisper-turbo | ls-tc-babbleM5 | greedy vs ROVER over samples | 160.58 | 87.60 | +72.98 | [+44.62, +103.44] |
| whisper-turbo | ls-tc-white0 | greedy vs ROVER over samples | 12.19 | 12.30 | -0.10 | [-1.12, +0.74] |
| whisper-turbo | ls-tc-white10 | greedy vs ROVER over samples | 3.45 | 3.50 | -0.05 | [-0.23, +0.15] |
| whisper-turbo | ls-test-clean | greedy vs ROVER over samples | 1.98 | 1.93 | +0.05 | [-0.04, +0.14] |
| whisper-turbo | ls-test-other | greedy vs ROVER over samples | 3.93 | 3.82 | +0.11 | [-0.02, +0.25] |
| whisper-turbo | ami | greedy vs ROVER over beam n-best | 14.52 | 25.10 | -10.58 | [-18.90, -3.92] |
| whisper-turbo | common_voice | greedy vs ROVER over beam n-best | 11.60 | 19.24 | -7.63 | [-18.61, -0.26] |
| whisper-turbo | earnings22 | greedy vs ROVER over beam n-best | 10.82 | 10.76 | +0.06 | [-0.21, +0.32] |
| whisper-turbo | fleurs-en | greedy vs ROVER over beam n-best | 6.35 | 6.23 | +0.12 | [-0.07, +0.33] |
| whisper-turbo | ls-dev-other | greedy vs ROVER over beam n-best | 3.96 | 3.84 | +0.12 | [-0.01, +0.25] |
| whisper-turbo | ls-tc-babble15 | greedy vs ROVER over beam n-best | 2.63 | 2.71 | -0.08 | [-0.26, +0.08] |
| whisper-turbo | ls-tc-babble5 | greedy vs ROVER over beam n-best | 6.64 | 6.25 | +0.40 | [+0.14, +0.67] |
| whisper-turbo | ls-tc-babbleM5 | greedy vs ROVER over beam n-best | 160.58 | 424.46 | -263.88 | [-319.22, -212.00] |
| whisper-turbo | ls-tc-white0 | greedy vs ROVER over beam n-best | 12.19 | 11.43 | +0.77 | [+0.22, +1.35] |
| whisper-turbo | ls-tc-white10 | greedy vs ROVER over beam n-best | 3.45 | 3.55 | -0.10 | [-0.33, +0.11] |
| whisper-turbo | ls-test-clean | greedy vs ROVER over beam n-best | 1.98 | 1.97 | +0.01 | [-0.11, +0.14] |
| whisper-turbo | ls-test-other | greedy vs ROVER over beam n-best | 3.93 | 3.85 | +0.08 | [-0.11, +0.25] |
| whisper-turbo | ami | top beam vs ROVER over n-best | 26.13 | 25.10 | +1.03 | [-0.66, +3.94] |
| whisper-turbo | common_voice | top beam vs ROVER over n-best | 18.80 | 19.24 | -0.44 | [-0.99, +0.14] |
| whisper-turbo | earnings22 | top beam vs ROVER over n-best | 10.65 | 10.76 | -0.10 | [-0.37, +0.14] |
| whisper-turbo | fleurs-en | top beam vs ROVER over n-best | 6.32 | 6.23 | +0.09 | [-0.07, +0.27] |
| whisper-turbo | ls-dev-other | top beam vs ROVER over n-best | 3.92 | 3.84 | +0.08 | [-0.04, +0.21] |
| whisper-turbo | ls-tc-babble15 | top beam vs ROVER over n-best | 2.76 | 2.71 | +0.05 | [-0.09, +0.22] |
| whisper-turbo | ls-tc-babble5 | top beam vs ROVER over n-best | 6.32 | 6.25 | +0.08 | [-0.18, +0.34] |
| whisper-turbo | ls-tc-babbleM5 | top beam vs ROVER over n-best | 433.28 | 424.46 | +8.82 | [+5.31, +12.32] |
| whisper-turbo | ls-tc-white0 | top beam vs ROVER over n-best | 11.27 | 11.43 | -0.15 | [-0.55, +0.23] |
| whisper-turbo | ls-tc-white10 | top beam vs ROVER over n-best | 3.60 | 3.55 | +0.05 | [-0.16, +0.28] |
| whisper-turbo | ls-test-clean | top beam vs ROVER over n-best | 1.91 | 1.97 | -0.06 | [-0.17, +0.05] |
| whisper-turbo | ls-test-other | top beam vs ROVER over n-best | 3.89 | 3.85 | +0.04 | [-0.08, +0.17] |
| whisper-turbo | ami | greedy vs MBR over samples | 14.52 | 14.63 | -0.11 | [-0.56, +0.33] |
| whisper-turbo | common_voice | greedy vs MBR over samples | 11.60 | 11.56 | +0.05 | [-0.71, +0.75] |
| whisper-turbo | earnings22 | greedy vs MBR over samples | 10.82 | 11.07 | -0.26 | [-0.80, +0.19] |
| whisper-turbo | fleurs-en | greedy vs MBR over samples | 6.35 | 6.47 | -0.12 | [-0.52, +0.15] |
| whisper-turbo | ls-dev-other | greedy vs MBR over samples | 3.96 | 3.90 | +0.06 | [-0.05, +0.17] |
| whisper-turbo | ls-tc-babble15 | greedy vs MBR over samples | 2.63 | 2.68 | -0.05 | [-0.21, +0.11] |
| whisper-turbo | ls-tc-babble5 | greedy vs MBR over samples | 6.64 | 6.40 | +0.24 | [-0.04, +0.51] |
| whisper-turbo | ls-tc-babbleM5 | greedy vs MBR over samples | 160.58 | 89.42 | +71.17 | [+43.45, +101.28] |
| whisper-turbo | ls-tc-white0 | greedy vs MBR over samples | 12.19 | 12.60 | -0.41 | [-1.55, +0.44] |
| whisper-turbo | ls-tc-white10 | greedy vs MBR over samples | 3.45 | 3.48 | -0.03 | [-0.15, +0.10] |
| whisper-turbo | ls-test-clean | greedy vs MBR over samples | 1.98 | 1.94 | +0.04 | [-0.03, +0.11] |
| whisper-turbo | ls-test-other | greedy vs MBR over samples | 3.93 | 3.92 | +0.01 | [-0.12, +0.14] |
| parakeet-ctc | ami | greedy vs ROVER over sampled CTC paths | 13.60 | 13.97 | -0.37 | [-0.85, +0.09] |
| parakeet-ctc | common_voice | greedy vs ROVER over sampled CTC paths | 10.51 | 10.41 | +0.09 | [-0.21, +0.43] |
| parakeet-ctc | earnings22 | greedy vs ROVER over sampled CTC paths | 14.93 | 14.98 | -0.05 | [-0.34, +0.24] |
| parakeet-ctc | fleurs-en | greedy vs ROVER over sampled CTC paths | 7.67 | 7.57 | +0.10 | [-0.08, +0.28] |
| parakeet-ctc | ls-dev-other | greedy vs ROVER over sampled CTC paths | 3.32 | 3.28 | +0.04 | [-0.08, +0.16] |
| parakeet-ctc | ls-tc-babble5 | greedy vs ROVER over sampled CTC paths | 10.75 | 10.74 | +0.01 | [-0.23, +0.25] |
| parakeet-ctc | ls-test-clean | greedy vs ROVER over sampled CTC paths | 1.71 | 1.65 | +0.07 | [-0.01, +0.16] |
| parakeet-ctc | ls-test-other | greedy vs ROVER over sampled CTC paths | 3.67 | 3.49 | +0.19 | [+0.06, +0.32] |

## Tuned on dev (ls-dev-clean + ls-dev-other), reported on test

- **drax**: alpha=1.0, eps=0.5, gamma=1.0, lambda=3.0 (dev: select 4.28, ROVER 4.16, n=800)
- **whisfusion**: alpha=0.5, eps=0.7, gamma=0.5, lambda=3.0 (dev: select 9.89, ROVER 8.87, n=800)
- **whisper-small**: alpha=0.5, eps=0.7, gamma=1.0, lambda=0.25 (dev: select 6.92, ROVER 7.09, n=800)
- **whisper-turbo**: alpha=0.7, eps=0.7, gamma=1.0, lambda=1.0 (dev: select 3.88, ROVER 3.88, n=800)
- **parakeet-ctc**: alpha=0.5, eps=0.7, gamma=1.0, lambda=0.5 (dev: select 3.38, ROVER 3.27, n=600)

| model | set | tuned select | tuned ROVER | delta | 95% CI |
|---|---|---|---|---|---|
| drax | ami | 10.54 | 10.01 | +0.53 | [+0.24, +0.82] |
| drax | common_voice | 36.63 | 36.21 | +0.43 | [+0.17, +0.69] |
| drax | earnings22 | 16.68 | 15.65 | +1.03 | [+0.76, +1.33] |
| drax | fleurs-de | 10.75 | 10.16 | +0.59 | [+0.40, +0.78] |
| drax | fleurs-en | 9.45 | 8.79 | +0.65 | [+0.43, +0.88] |
| drax | fleurs-es | 8.23 | 8.01 | +0.22 | [+0.07, +0.38] |
| drax | fleurs-fr | 12.97 | 12.45 | +0.51 | [+0.29, +0.74] |
| drax | fleurs-it | 8.69 | 8.41 | +0.28 | [+0.15, +0.41] |
| drax | fleurs-pt | 14.96 | 13.79 | +1.17 | [+0.91, +1.44] |
| drax | gigaspeech | 12.21 | 11.78 | +0.43 | [+0.18, +0.67] |
| drax | ls-tc-babble0 | 40.60 | 35.77 | +4.83 | [+4.29, +5.40] |
| drax | ls-tc-babble10 | 4.05 | 3.82 | +0.23 | [+0.09, +0.37] |
| drax | ls-tc-babble15 | 2.70 | 2.59 | +0.11 | [-0.01, +0.23] |
| drax | ls-tc-babble5 | 10.02 | 8.96 | +1.06 | [+0.75, +1.37] |
| drax | ls-tc-babbleM5 | 92.36 | 89.42 | +2.95 | [+2.50, +3.39] |
| drax | ls-tc-white0 | 17.22 | 15.20 | +2.02 | [+1.65, +2.40] |
| drax | ls-tc-white10 | 3.94 | 3.80 | +0.13 | [+0.01, +0.28] |
| drax | ls-tc-white5 | 7.21 | 6.68 | +0.52 | [+0.31, +0.73] |
| drax | ls-test-clean | 2.26 | 2.16 | +0.10 | [+0.03, +0.17] |
| drax | ls-test-other | 5.59 | 5.33 | +0.26 | [+0.13, +0.40] |
| drax | slr83 | 6.33 | 6.08 | +0.24 | [+0.07, +0.41] |
| drax | spgispeech | 4.52 | 4.34 | +0.18 | [+0.08, +0.28] |
| drax | voxpopuli | 6.94 | 6.91 | +0.03 | [-0.06, +0.12] |
| whisfusion | ami | 34.17 | 31.93 | +2.24 | [+1.74, +2.74] |
| whisfusion | common_voice | 50.43 | 48.46 | +1.97 | [+1.51, +2.40] |
| whisfusion | earnings22 | 31.83 | 29.29 | +2.54 | [+2.18, +2.91] |
| whisfusion | fleurs-en | 24.22 | 22.23 | +1.99 | [+1.59, +2.42] |
| whisfusion | gigaspeech | 21.90 | 19.92 | +1.98 | [+1.64, +2.31] |
| whisfusion | ls-tc-babble0 | 65.35 | 58.17 | +7.18 | [+6.31, +8.10] |
| whisfusion | ls-tc-babble10 | 14.52 | 11.48 | +3.04 | [+2.54, +3.56] |
| whisfusion | ls-tc-babble15 | 9.37 | 7.48 | +1.89 | [+1.53, +2.22] |
| whisfusion | ls-tc-babble5 | 29.03 | 24.52 | +4.51 | [+3.88, +5.11] |
| whisfusion | ls-tc-babbleM5 | 98.32 | 90.85 | +7.47 | [+6.35, +8.79] |
| whisfusion | ls-tc-white0 | 39.14 | 35.52 | +3.62 | [+3.07, +4.13] |
| whisfusion | ls-tc-white10 | 13.00 | 11.12 | +1.89 | [+1.53, +2.25] |
| whisfusion | ls-tc-white5 | 21.74 | 18.81 | +2.93 | [+2.39, +3.48] |
| whisfusion | ls-test-clean | 6.76 | 5.59 | +1.17 | [+0.92, +1.44] |
| whisfusion | ls-test-other | 13.57 | 12.33 | +1.24 | [+0.99, +1.49] |
| whisfusion | slr83 | 18.82 | 17.50 | +1.32 | [+1.03, +1.59] |
| whisfusion | spgispeech | 15.97 | 13.74 | +2.23 | [+1.96, +2.50] |
| whisfusion | voxpopuli | 18.82 | 17.24 | +1.58 | [+1.28, +1.89] |
| whisper-small | ami | 15.94 | 16.09 | -0.14 | [-0.65, +0.34] |
| whisper-small | common_voice | 36.58 | 37.18 | -0.60 | [-1.10, -0.12] |
| whisper-small | earnings22 | 13.19 | 16.20 | -3.00 | [-4.49, -1.75] |
| whisper-small | fleurs-en | 8.42 | 8.72 | -0.29 | [-0.85, +0.10] |
| whisper-small | ls-tc-babble5 | 12.76 | 13.27 | -0.51 | [-1.38, +0.20] |
| whisper-small | ls-test-clean | 3.27 | 3.18 | +0.09 | [-0.09, +0.34] |
| whisper-small | ls-test-other | 7.41 | 7.51 | -0.11 | [-0.53, +0.23] |
| whisper-turbo | ami | 14.26 | 14.35 | -0.09 | [-0.34, +0.15] |
| whisper-turbo | common_voice | 33.79 | 33.88 | -0.09 | [-0.55, +0.33] |
| whisper-turbo | earnings22 | 10.70 | 11.01 | -0.32 | [-0.71, -0.04] |
| whisper-turbo | fleurs-en | 6.36 | 6.41 | -0.05 | [-0.17, +0.06] |
| whisper-turbo | ls-tc-babble15 | 2.61 | 2.74 | -0.13 | [-0.28, -0.02] |
| whisper-turbo | ls-tc-babble5 | 6.39 | 6.34 | +0.05 | [-0.09, +0.19] |
| whisper-turbo | ls-tc-babbleM5 | 90.75 | 87.37 | +3.37 | [+1.65, +5.55] |
| whisper-turbo | ls-tc-white0 | 12.07 | 12.19 | -0.13 | [-0.69, +0.33] |
| whisper-turbo | ls-tc-white10 | 3.48 | 3.50 | -0.03 | [-0.11, +0.05] |
| whisper-turbo | ls-test-clean | 1.90 | 1.91 | -0.01 | [-0.05, +0.04] |
| whisper-turbo | ls-test-other | 3.87 | 3.88 | -0.01 | [-0.08, +0.06] |
| parakeet-ctc | ami | 14.97 | 13.86 | +1.10 | [+0.64, +1.55] |
| parakeet-ctc | common_voice | 33.25 | 33.16 | +0.09 | [-0.11, +0.30] |
| parakeet-ctc | earnings22 | 15.67 | 15.00 | +0.67 | [+0.33, +1.01] |
| parakeet-ctc | fleurs-en | 7.79 | 7.55 | +0.24 | [+0.06, +0.43] |
| parakeet-ctc | ls-tc-babble5 | 11.26 | 10.74 | +0.52 | [+0.24, +0.84] |
| parakeet-ctc | ls-test-clean | 1.82 | 1.64 | +0.18 | [+0.06, +0.31] |
| parakeet-ctc | ls-test-other | 3.61 | 3.52 | +0.09 | [-0.04, +0.23] |

## Cost

| model | kind | arm | K | T | steps | n | s/utt | encode s | decode s | RTF | ms/candidate | ROVER ms | peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drax | kscale | K64 | 64 | 1.30 | 16.0 | 200 | 14.404 | 0.186 | 14.218 | 2.2079 | 222.2 | 5.70 | 5954 |
| drax | lowT | lowT | 16 | 0.40 | 16.0 | 5868 | 3.449 | 0.178 | 3.271 | 0.4473 | 204.5 | 0.53 | 4336 |
| drax | main | main | 16 | 1.30 | 16.0 | 18252 | 3.589 | 0.095 | 3.494 | 0.4616 | 218.4 | 0.73 | 4336 |
| drax | main | ref | 4 | 0.10 | 16.0 | 18252 | 1.026 | 0.095 | 0.931 | 0.1319 | 232.6 | 0.46 | 4336 |
| drax | sweepT | T0.1 | 16 | 0.10 | 16.0 | 300 | 2.536 | 0.028 | 2.508 | 0.4702 | 156.8 | 0.57 | 4336 |
| drax | sweepT | T0.4 | 16 | 0.40 | 16.0 | 800 | 3.504 | 0.034 | 3.471 | 0.6039 | 216.9 | 0.47 | 4336 |
| drax | sweepT | T0.7 | 16 | 0.70 | 16.0 | 800 | 3.496 | 0.034 | 3.463 | 0.6024 | 216.4 | 0.93 | 4336 |
| drax | sweepT | T1 | 16 | 1.00 | 16.0 | 800 | 3.497 | 0.034 | 3.463 | 0.6025 | 216.4 | 1.18 | 4336 |
| drax | sweepT | T1.3 | 16 | 1.30 | 16.0 | 800 | 3.497 | 0.034 | 3.463 | 0.6026 | 216.5 | 1.51 | 4336 |
| drax | sweepT | T1.6 | 16 | 1.60 | 16.0 | 800 | 3.498 | 0.034 | 3.465 | 0.6028 | 216.5 | 1.83 | 4336 |
| drax | sweepT | T2 | 16 | 2.00 | 16.0 | 300 | 2.531 | 0.028 | 2.503 | 0.4691 | 156.4 | 3.14 | 4336 |
| parakeet-ctc | main | greedy | 1 |  | nan | 4446 | 0.125 | 0.124 | 0.001 | 0.0195 | 0.9 | 0.08 | 2167 |
| parakeet-ctc | main | sample | 32 | 1.00 | nan | 4446 | 0.141 | 0.124 | 0.017 | 0.0221 | 0.5 | 2.37 | 2167 |
| parakeet-ctc | sweepT | T0.5 | 32 | 0.50 | nan | 600 | 0.144 | 0.129 | 0.015 | 0.0258 | 0.5 | 0.93 | 2166 |
| parakeet-ctc | sweepT | T1 | 32 | 1.00 | nan | 600 | 0.144 | 0.129 | 0.015 | 0.0259 | 0.5 | 3.03 | 2166 |
| parakeet-ctc | sweepT | T1.5 | 32 | 1.50 | nan | 600 | 0.145 | 0.129 | 0.016 | 0.0261 | 0.5 | 4.33 | 2166 |
| parakeet-ctc | sweepT | T2 | 32 | 2.00 | nan | 600 | 0.149 | 0.129 | 0.020 | 0.0268 | 0.6 | 6.69 | 2166 |
| parakeet-ctc | sweepT | greedy | 1 |  | nan | 600 | 0.130 | 0.129 | 0.001 | 0.0234 | 1.0 | 0.07 | 2166 |
| whisfusion | ablation | base16 | 16 |  | 4.0 | 200 | 1.146 | 0.015 | 1.131 | 0.1764 | 70.7 | 0.94 | 2454 |
| whisfusion | ablation | fss_T1 | 16 |  | 4.0 | 200 | 1.178 | 0.015 | 1.163 | 0.1813 | 72.7 | 2.20 | 2454 |
| whisfusion | ablation | steps8 | 16 |  | 8.0 | 200 | 2.263 | 0.015 | 2.248 | 0.3483 | 140.5 | 2.04 | 2454 |
| whisfusion | kscale | K64 | 64 |  | 4.0 | 200 | 3.948 | 0.032 | 3.916 | 0.6052 | 61.2 | 7.42 | 7705 |
| whisfusion | main | main | 32 |  | 4.0 | 12364 | 2.229 | 0.037 | 2.191 | 0.3264 | 68.5 | 3.12 | 4205 |
| whisfusion | sweepT | fss0 | 32 |  | 4.0 | 600 | 2.016 | 0.010 | 2.007 | 0.3619 | 62.7 | 1.40 | 4205 |
| whisfusion | sweepT | fssT0.5 | 32 |  | 4.0 | 600 | 2.071 | 0.010 | 2.061 | 0.3717 | 64.4 | 3.65 | 4205 |
| whisfusion | sweepT | fssT1 | 32 |  | 4.0 | 600 | 2.071 | 0.010 | 2.061 | 0.3717 | 64.4 | 4.45 | 4205 |
| whisfusion | sweepT | fssT1.5 | 32 |  | 4.0 | 600 | 2.071 | 0.010 | 2.062 | 0.3718 | 64.4 | 4.44 | 4205 |
| whisper-small | main | beam | 8 |  | nan | 5198 | 0.531 | 0.006 | 0.525 | 0.0836 | 65.6 | 0.21 | 2744 |
| whisper-small | main | greedy | 1 |  | nan | 5198 | 0.323 | 0.006 | 0.317 | 0.0508 | 316.8 | 0.08 | 2744 |
| whisper-small | main | sample | 16 | 0.60 | nan | 5198 | 0.401 | 0.006 | 0.395 | 0.0631 | 24.7 | 1.27 | 2744 |
| whisper-turbo | main | beam | 8 |  | nan | 6153 | 0.505 | 0.006 | 0.499 | 0.0787 | 62.4 | 0.32 | 3811 |
| whisper-turbo | main | greedy | 1 |  | nan | 6153 | 0.304 | 0.006 | 0.298 | 0.0474 | 298.1 | 0.08 | 3811 |
| whisper-turbo | main | sample | 16 | 0.60 | nan | 6153 | 0.407 | 0.006 | 0.401 | 0.0634 | 25.1 | 1.33 | 3811 |
| whisper-turbo | sweepT | T0.3 | 16 | 0.30 | nan | 600 | 0.358 | 0.004 | 0.355 | 0.0643 | 22.2 | 0.35 | 3811 |
| whisper-turbo | sweepT | T0.6 | 16 | 0.60 | nan | 600 | 0.364 | 0.004 | 0.360 | 0.0653 | 22.5 | 0.87 | 3811 |
| whisper-turbo | sweepT | T0.9 | 16 | 0.90 | nan | 600 | 0.377 | 0.004 | 0.374 | 0.0677 | 23.4 | 1.28 | 3811 |
| whisper-turbo | sweepT | T1.2 | 16 | 1.20 | nan | 600 | 0.860 | 0.004 | 0.856 | 0.1544 | 53.5 | 1.97 | 3811 |
| whisper-turbo | sweepT | greedy | 1 |  | nan | 600 | 0.278 | 0.004 | 0.275 | 0.0500 | 274.7 | 0.08 | 3811 |
