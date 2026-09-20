# Campaign report

generated 2026-09-20 13:01 UTC

utterance decodes analysed: 440308; cells: 1314


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
| parakeet-ctc/greedy | ami | 200 | 1 | 16.60 | 16.60 | 16.60 | 16.60 | 16.60 | 16.60 |  |  | 0.0 |
| parakeet-ctc/sample | ami | 200 | 32 | 23.01 | 21.84 | 17.10 | 17.27 | 17.33 | 11.53 | 7.52 | 10.75 | 23.6 |
| parakeet-ctc/greedy | common_voice | 147 | 1 | 11.80 | 11.80 | 11.80 | 11.80 | 11.80 | 11.80 |  |  | 0.0 |
| parakeet-ctc/sample | common_voice | 147 | 32 | 13.73 | 12.84 | 11.88 | 11.28 | 11.21 | 8.39 | 6.83 | 8.09 | 9.5 |
| parakeet-ctc/greedy | earnings22 | 200 | 1 | 23.70 | 23.70 | 23.70 | 23.70 | 23.70 | 23.70 |  |  | 0.0 |
| parakeet-ctc/sample | earnings22 | 200 | 32 | 28.73 | 25.36 | 24.41 | 23.61 | 23.64 | 19.84 | 12.63 | 16.10 | 19.4 |
| parakeet-ctc/greedy | fleurs-en | 200 | 1 | 10.09 | 10.09 | 10.09 | 10.09 | 10.09 | 10.09 |  |  | 0.0 |
| parakeet-ctc/sample | fleurs-en | 200 | 32 | 11.73 | 11.02 | 10.30 | 10.02 | 10.02 | 8.11 | 4.39 | 5.73 | 5.9 |
| parakeet-ctc/greedy | ls-dev-other | 200 | 1 | 3.85 | 3.85 | 3.85 | 3.85 | 3.85 | 3.85 |  |  | 0.0 |
| parakeet-ctc/sample | ls-dev-other | 200 | 32 | 5.42 | 4.25 | 4.22 | 3.99 | 3.94 | 2.63 | 1.76 | 2.46 | 4.9 |
| parakeet-ctc/greedy | ls-tc-babble5 | 200 | 1 | 11.66 | 11.66 | 11.66 | 11.66 | 11.66 | 11.66 |  |  | 0.0 |
| parakeet-ctc/sample | ls-tc-babble5 | 200 | 32 | 15.22 | 13.00 | 12.20 | 11.76 | 11.73 | 9.54 | 6.93 | 8.81 | 16.7 |
| parakeet-ctc/greedy | ls-test-clean | 200 | 1 | 1.99 | 1.99 | 1.99 | 1.99 | 1.99 | 1.99 |  |  | 0.0 |
| parakeet-ctc/sample | ls-test-clean | 200 | 32 | 3.20 | 2.58 | 1.89 | 1.86 | 1.86 | 1.09 | 0.72 | 1.01 | 3.3 |
| parakeet-ctc/greedy | ls-test-other | 200 | 1 | 3.50 | 3.50 | 3.50 | 3.50 | 3.50 | 3.50 |  |  | 0.0 |
| parakeet-ctc/sample | ls-test-other | 200 | 32 | 4.79 | 3.98 | 3.56 | 3.53 | 3.56 | 2.04 | 1.60 | 1.96 | 5.0 |
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
| whisper-small/beam | ami | 352 | 8 | 50.39 | 50.52 | 46.79 | 46.73 | 47.36 | 39.62 | 11.17 | 11.92 | 21.6 |
| whisper-small/greedy | ami | 352 | 1 | 19.94 | 19.94 | 19.94 | 19.94 | 19.94 | 19.94 |  |  | 0.0 |
| whisper-small/sample | ami | 352 | 16 | 20.72 | 25.23 | 19.62 | 19.50 | 19.81 | 12.02 | 10.80 | 11.64 | 17.1 |
| whisper-small/beam | common_voice | 147 | 8 | 14.92 | 14.70 | 15.07 | 15.29 | 15.37 | 10.32 | 8.17 | 8.61 | 12.3 |
| whisper-small/greedy | common_voice | 147 | 1 | 16.18 | 16.18 | 16.18 | 16.18 | 16.18 | 16.18 |  |  | 0.0 |
| whisper-small/sample | common_voice | 147 | 16 | 17.45 | 15.00 | 15.81 | 14.77 | 14.92 | 9.43 | 7.57 | 8.83 | 11.8 |
| whisper-small/beam | earnings22 | 200 | 8 | 17.26 | 17.51 | 17.26 | 16.90 | 16.93 | 12.08 | 9.72 | 10.58 | 11.6 |
| whisper-small/greedy | earnings22 | 200 | 1 | 18.49 | 18.49 | 18.49 | 18.49 | 18.49 | 18.49 |  |  | 0.0 |
| whisper-small/sample | earnings22 | 200 | 16 | 23.70 | 17.17 | 21.99 | 21.22 | 21.16 | 11.81 | 8.95 | 10.89 | 15.9 |
| whisper-small/beam | fleurs-en | 200 | 8 | 6.88 | 6.95 | 6.95 | 7.04 | 7.02 | 4.90 | 3.86 | 4.27 | 5.0 |
| whisper-small/greedy | fleurs-en | 200 | 1 | 7.71 | 7.71 | 7.71 | 7.71 | 7.71 | 7.71 |  |  | 0.0 |
| whisper-small/sample | fleurs-en | 200 | 16 | 8.24 | 7.53 | 8.24 | 7.83 | 8.06 | 4.80 | 3.51 | 4.23 | 5.3 |
| whisper-small/beam | ls-dev-other | 400 | 8 | 7.52 | 7.68 | 7.74 | 7.68 | 7.82 | 5.46 | 4.73 | 5.00 | 6.6 |
| whisper-small/greedy | ls-dev-other | 400 | 1 | 8.12 | 8.12 | 8.12 | 8.12 | 8.12 | 8.12 |  |  | 0.0 |
| whisper-small/sample | ls-dev-other | 400 | 16 | 9.44 | 8.40 | 8.00 | 7.68 | 7.76 | 5.06 | 3.99 | 4.84 | 7.0 |
| whisper-small/beam | ls-tc-babble5 | 200 | 8 | 28.17 | 28.84 | 27.60 | 27.60 | 27.58 | 23.83 | 9.33 | 9.77 | 9.7 |
| whisper-small/greedy | ls-tc-babble5 | 200 | 1 | 15.74 | 15.74 | 15.74 | 15.74 | 15.74 | 15.74 |  |  | 0.0 |
| whisper-small/sample | ls-tc-babble5 | 200 | 16 | 16.75 | 18.64 | 15.46 | 15.12 | 15.12 | 9.87 | 7.19 | 9.38 | 16.9 |
| whisper-small/beam | ls-test-clean | 400 | 8 | 3.95 | 4.09 | 4.04 | 4.09 | 4.06 | 2.50 | 2.35 | 2.44 | 4.4 |
| whisper-small/greedy | ls-test-clean | 400 | 1 | 3.96 | 3.96 | 3.96 | 3.96 | 3.96 | 3.96 |  |  | 0.0 |
| whisper-small/sample | ls-test-clean | 400 | 16 | 4.55 | 5.36 | 4.29 | 4.06 | 4.11 | 2.41 | 2.16 | 2.37 | 3.6 |
| whisper-small/beam | ls-test-other | 400 | 8 | 8.18 | 8.26 | 8.21 | 8.24 | 8.24 | 5.73 | 4.80 | 5.27 | 6.7 |
| whisper-small/greedy | ls-test-other | 400 | 1 | 8.82 | 8.82 | 8.82 | 8.82 | 8.82 | 8.82 |  |  | 0.0 |
| whisper-small/sample | ls-test-other | 400 | 16 | 9.71 | 8.88 | 8.65 | 8.52 | 8.77 | 5.31 | 4.01 | 5.04 | 7.4 |
| whisper-turbo/beam | ami | 400 | 8 | 27.95 | 28.00 | 25.28 | 25.90 | 26.46 | 19.23 | 10.33 | 10.90 | 21.2 |
| whisper-turbo/greedy | ami | 400 | 1 | 17.56 | 17.56 | 17.56 | 17.56 | 17.56 | 17.56 |  |  | 0.0 |
| whisper-turbo/sample | ami | 400 | 16 | 18.69 | 17.24 | 17.83 | 17.94 | 17.94 | 11.71 | 10.60 | 11.06 | 12.0 |
| whisper-turbo/beam | common_voice | 147 | 8 | 11.66 | 11.73 | 11.58 | 11.95 | 12.40 | 8.24 | 6.76 | 6.90 | 9.7 |
| whisper-turbo/greedy | common_voice | 147 | 1 | 11.80 | 11.80 | 11.80 | 11.80 | 11.80 | 11.80 |  |  | 0.0 |
| whisper-turbo/sample | common_voice | 147 | 16 | 13.36 | 12.62 | 12.03 | 11.28 | 11.28 | 8.24 | 6.31 | 7.20 | 6.8 |
| whisper-turbo/beam | earnings22 | 307 | 8 | 16.70 | 16.40 | 16.66 | 16.50 | 16.48 | 12.45 | 10.19 | 10.64 | 10.0 |
| whisper-turbo/greedy | earnings22 | 307 | 1 | 16.77 | 16.77 | 16.77 | 16.77 | 16.77 | 16.77 |  |  | 0.0 |
| whisper-turbo/sample | earnings22 | 307 | 16 | 17.44 | 16.46 | 16.72 | 16.50 | 16.52 | 12.78 | 10.50 | 11.12 | 7.1 |
| whisper-turbo/beam | fleurs-en | 200 | 8 | 5.38 | 5.29 | 5.36 | 5.36 | 5.40 | 3.44 | 2.79 | 3.05 | 4.5 |
| whisper-turbo/greedy | fleurs-en | 200 | 1 | 5.50 | 5.50 | 5.50 | 5.50 | 5.50 | 5.50 |  |  | 0.0 |
| whisper-turbo/sample | fleurs-en | 200 | 16 | 5.91 | 5.29 | 5.59 | 5.57 | 5.57 | 3.70 | 3.03 | 3.26 | 3.2 |
| whisper-turbo/beam | ls-dev-other | 400 | 8 | 5.47 | 5.53 | 5.39 | 5.31 | 5.31 | 3.08 | 2.54 | 2.93 | 5.2 |
| whisper-turbo/greedy | ls-dev-other | 400 | 1 | 5.61 | 5.61 | 5.61 | 5.61 | 5.61 | 5.61 |  |  | 0.0 |
| whisper-turbo/sample | ls-dev-other | 400 | 16 | 5.75 | 5.47 | 5.43 | 5.29 | 5.32 | 3.36 | 2.72 | 3.14 | 3.2 |
| whisper-turbo/beam | ls-tc-babble5 | 200 | 8 | 7.68 | 7.55 | 7.44 | 7.31 | 7.39 | 4.81 | 4.19 | 4.50 | 7.2 |
| whisper-turbo/greedy | ls-tc-babble5 | 200 | 1 | 7.62 | 7.62 | 7.62 | 7.62 | 7.62 | 7.62 |  |  | 0.0 |
| whisper-turbo/sample | ls-tc-babble5 | 200 | 16 | 9.25 | 7.44 | 7.57 | 7.44 | 7.39 | 4.88 | 4.11 | 4.57 | 6.9 |
| whisper-turbo/beam | ls-test-clean | 400 | 8 | 3.28 | 3.24 | 3.34 | 3.27 | 3.23 | 1.60 | 1.54 | 1.57 | 4.3 |
| whisper-turbo/greedy | ls-test-clean | 400 | 1 | 3.14 | 3.14 | 3.14 | 3.14 | 3.14 | 3.14 |  |  | 0.0 |
| whisper-turbo/sample | ls-test-clean | 400 | 16 | 3.22 | 3.82 | 3.06 | 3.01 | 3.03 | 1.91 | 1.75 | 1.85 | 2.2 |
| whisper-turbo/beam | ls-test-other | 400 | 8 | 4.90 | 5.10 | 4.96 | 4.97 | 4.98 | 2.59 | 2.18 | 2.39 | 6.3 |
| whisper-turbo/greedy | ls-test-other | 400 | 1 | 5.07 | 5.07 | 5.07 | 5.07 | 5.07 | 5.07 |  |  | 0.0 |
| whisper-turbo/sample | ls-test-other | 400 | 16 | 5.56 | 5.00 | 5.04 | 5.01 | 4.84 | 3.03 | 2.52 | 2.82 | 3.4 |

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
| parakeet-ctc/greedy | ami | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | ami | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | ami | conf | +4.51 | [+3.60, +5.51] | [3.66, 5.38] | 0.0000 | 71/7/122 |
| parakeet-ctc/sample | ami | mbr | -0.22 | [-0.82, +0.40] | [-0.90, 0.35] | 0.4863 | 8/13/179 |
| parakeet-ctc/greedy | common_voice | conf | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/147 |
| parakeet-ctc/greedy | common_voice | mbr | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/147 |
| parakeet-ctc/sample | common_voice | conf | +1.63 | [+0.80, +2.54] | [, ] | 0.0004 | 26/6/115 |
| parakeet-ctc/sample | common_voice | mbr | +0.67 | [+0.08, +1.22] | [, ] | 0.0201 | 12/3/132 |
| parakeet-ctc/greedy | earnings22 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | earnings22 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | earnings22 | conf | +1.72 | [+1.02, +2.45] | [1.19, 2.62] | 0.0000 | 69/26/105 |
| parakeet-ctc/sample | earnings22 | mbr | +0.77 | [+0.28, +1.26] | [0.57, 1.17] | 0.0023 | 34/13/153 |
| parakeet-ctc/greedy | fleurs-en | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | fleurs-en | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | fleurs-en | conf | +0.99 | [+0.59, +1.41] | [0.60, 1.43] | 0.0000 | 39/8/153 |
| parakeet-ctc/sample | fleurs-en | mbr | +0.28 | [+0.05, +0.53] | [0.05, 0.53] | 0.0318 | 14/4/182 |
| parakeet-ctc/greedy | ls-dev-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | ls-dev-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | ls-dev-other | conf | +0.31 | [-0.09, +0.70] | [-0.11, 0.77] | 0.1505 | 21/10/169 |
| parakeet-ctc/sample | ls-dev-other | mbr | +0.28 | [+0.08, +0.50] | [0.09, 0.47] | 0.0124 | 11/2/187 |
| parakeet-ctc/greedy | ls-tc-babble5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | ls-tc-babble5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | ls-tc-babble5 | conf | +1.27 | [+0.80, +1.76] | [0.75, 1.82] | 0.0000 | 49/11/140 |
| parakeet-ctc/sample | ls-tc-babble5 | mbr | +0.47 | [+0.22, +0.73] | [0.23, 0.73] | 0.0011 | 18/3/179 |
| parakeet-ctc/greedy | ls-test-clean | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | ls-test-clean | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | ls-test-clean | conf | +0.72 | [+0.42, +1.02] | [0.42, 1.03] | 0.0000 | 26/3/171 |
| parakeet-ctc/sample | ls-test-clean | mbr | +0.03 | [-0.12, +0.18] | [-0.11, 0.17] | 0.7389 | 3/3/194 |
| parakeet-ctc/greedy | ls-test-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/greedy | ls-test-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| parakeet-ctc/sample | ls-test-other | conf | +0.42 | [+0.03, +0.81] | [-0.05, 0.86] | 0.0250 | 28/13/159 |
| parakeet-ctc/sample | ls-test-other | mbr | +0.00 | [-0.17, +0.19] | [-0.18, 0.17] | 1.0000 | 3/4/193 |
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
| whisper-small/beam | ami | conf | +3.16 | [-0.59, +10.19] | [-0.60, 10.22] | 0.7756 | 48/54/250 |
| whisper-small/beam | ami | mbr | -0.56 | [-1.13, -0.06] | [-0.94, -0.21] | 0.0289 | 24/42/286 |
| whisper-small/greedy | ami | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/352 |
| whisper-small/greedy | ami | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/352 |
| whisper-small/sample | ami | conf | +5.41 | [-0.55, +19.98] | [-0.93, 17.60] | 0.2360 | 45/37/270 |
| whisper-small/sample | ami | mbr | -0.19 | [-0.68, +0.31] | [-0.67, 0.26] | 0.4595 | 21/29/302 |
| whisper-small/beam | common_voice | conf | -0.67 | [-1.81, +0.44] | [, ] | 0.1854 | 15/24/108 |
| whisper-small/beam | common_voice | mbr | -0.30 | [-1.03, +0.45] | [, ] | 0.4328 | 11/15/121 |
| whisper-small/greedy | common_voice | conf | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/147 |
| whisper-small/greedy | common_voice | mbr | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/147 |
| whisper-small/sample | common_voice | conf | +0.07 | [-1.72, +2.15] | [, ] | 0.4939 | 19/24/104 |
| whisper-small/sample | common_voice | mbr | +0.89 | [+0.00, +1.87] | [, ] | 0.0679 | 18/9/120 |
| whisper-small/beam | earnings22 | conf | +0.58 | [-0.31, +1.51] | [0.03, 1.18] | 0.3754 | 39/34/127 |
| whisper-small/beam | earnings22 | mbr | +0.34 | [-0.18, +0.83] | [-0.30, 0.96] | 0.1574 | 27/17/156 |
| whisper-small/greedy | earnings22 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-small/greedy | earnings22 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-small/sample | earnings22 | conf | -3.99 | [-6.89, -1.21] | [-6.81, -1.08] | 0.2492 | 38/42/120 |
| whisper-small/sample | earnings22 | mbr | +0.83 | [+0.29, +1.41] | [0.10, 1.52] | 0.0051 | 40/21/139 |
| whisper-small/beam | fleurs-en | conf | -0.07 | [-0.44, +0.32] | [-0.47, 0.32] | 0.6043 | 17/18/165 |
| whisper-small/beam | fleurs-en | mbr | -0.07 | [-0.34, +0.20] | [-0.33, 0.18] | 0.5566 | 12/11/177 |
| whisper-small/greedy | fleurs-en | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-small/greedy | fleurs-en | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-small/sample | fleurs-en | conf | -0.53 | [-2.23, +0.83] | [-2.07, 0.83] | 0.8897 | 22/24/154 |
| whisper-small/sample | fleurs-en | mbr | +0.18 | [-0.11, +0.48] | [-0.15, 0.49] | 0.1703 | 21/11/168 |
| whisper-small/beam | ls-dev-other | conf | -0.14 | [-0.47, +0.27] | [-0.52, 0.27] | 0.0979 | 25/38/337 |
| whisper-small/beam | ls-dev-other | mbr | -0.08 | [-0.31, +0.13] | [-0.30, 0.13] | 0.4487 | 22/25/353 |
| whisper-small/greedy | ls-dev-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/greedy | ls-dev-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/sample | ls-dev-other | conf | +0.64 | [+0.08, +1.30] | [0.11, 1.21] | 0.0981 | 42/41/317 |
| whisper-small/sample | ls-dev-other | mbr | +0.23 | [+0.03, +0.45] | [-0.03, 0.53] | 0.0348 | 37/22/341 |
| whisper-small/beam | ls-tc-babble5 | conf | +1.27 | [-0.03, +3.21] | [0.10, 3.11] | 0.1408 | 40/27/133 |
| whisper-small/beam | ls-tc-babble5 | mbr | +0.03 | [-0.38, +0.42] | [-0.32, 0.39] | 0.8384 | 22/18/160 |
| whisper-small/greedy | ls-tc-babble5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-small/greedy | ls-tc-babble5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-small/sample | ls-tc-babble5 | conf | +3.52 | [-1.20, +11.61] | [-1.21, 12.02] | 0.3403 | 41/28/131 |
| whisper-small/sample | ls-tc-babble5 | mbr | +0.34 | [-0.21, +0.91] | [-0.36, 0.97] | 0.1949 | 42/26/132 |
| whisper-small/beam | ls-test-clean | conf | +0.02 | [-0.17, +0.24] | [-0.21, 0.27] | 0.9738 | 18/19/363 |
| whisper-small/beam | ls-test-clean | mbr | -0.02 | [-0.19, +0.14] | [-0.20, 0.18] | 0.7580 | 17/18/365 |
| whisper-small/greedy | ls-test-clean | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/greedy | ls-test-clean | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/sample | ls-test-clean | conf | +1.24 | [-0.10, +3.81] | [-0.14, 3.93] | 0.4353 | 24/23/353 |
| whisper-small/sample | ls-test-clean | mbr | +0.17 | [+0.01, +0.36] | [0.02, 0.34] | 0.0513 | 23/13/364 |
| whisper-small/beam | ls-test-other | conf | +0.01 | [-0.34, +0.37] | [-0.34, 0.32] | 0.9552 | 40/43/317 |
| whisper-small/beam | ls-test-other | mbr | -0.03 | [-0.24, +0.19] | [-0.26, 0.21] | 0.8136 | 23/27/350 |
| whisper-small/greedy | ls-test-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/greedy | ls-test-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-small/sample | ls-test-other | conf | +0.11 | [-0.76, +0.91] | [-1.03, 1.04] | 0.2907 | 38/43/319 |
| whisper-small/sample | ls-test-other | mbr | -0.11 | [-0.35, +0.13] | [-0.36, 0.13] | 0.3647 | 23/34/343 |
| whisper-turbo/beam | ami | conf | +1.54 | [-1.77, +7.36] | [-1.44, 6.28] | 0.0124 | 39/77/284 |
| whisper-turbo/beam | ami | mbr | -1.19 | [-1.75, -0.67] | [-1.89, -0.63] | 0.0000 | 19/65/316 |
| whisper-turbo/greedy | ami | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/greedy | ami | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/sample | ami | conf | -0.70 | [-1.55, +0.13] | [-1.39, -0.05] | 0.0876 | 34/45/321 |
| whisper-turbo/sample | ami | mbr | -0.11 | [-0.49, +0.29] | [-0.46, 0.23] | 0.5868 | 22/26/352 |
| whisper-turbo/beam | common_voice | conf | -0.67 | [-1.35, +0.00] | [, ] | 0.0495 | 6/15/126 |
| whisper-turbo/beam | common_voice | mbr | -0.82 | [-1.61, -0.15] | [, ] | 0.0276 | 5/14/128 |
| whisper-turbo/greedy | common_voice | conf | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/147 |
| whisper-turbo/greedy | common_voice | mbr | +0.00 | [+0.00, +0.00] | [, ] | 1.0000 | 0/0/147 |
| whisper-turbo/sample | common_voice | conf | +1.34 | [-1.11, +5.70] | [, ] | 0.2345 | 6/12/129 |
| whisper-turbo/sample | common_voice | mbr | +0.74 | [+0.07, +1.71] | [, ] | 0.0522 | 8/2/137 |
| whisper-turbo/beam | earnings22 | conf | -0.08 | [-0.55, +0.40] | [-0.50, 0.34] | 0.7488 | 32/34/241 |
| whisper-turbo/beam | earnings22 | mbr | +0.18 | [-0.13, +0.49] | [-0.22, 0.40] | 0.2853 | 27/14/266 |
| whisper-turbo/greedy | earnings22 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/307 |
| whisper-turbo/greedy | earnings22 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/307 |
| whisper-turbo/sample | earnings22 | conf | -0.06 | [-0.53, +0.40] | [-0.41, 0.49] | 0.6325 | 33/35/239 |
| whisper-turbo/sample | earnings22 | mbr | +0.21 | [-0.08, +0.47] | [-0.03, 0.49] | 0.1489 | 27/18/262 |
| whisper-turbo/beam | fleurs-en | conf | -0.12 | [-0.39, +0.12] | [-0.37, 0.12] | 0.4497 | 11/14/175 |
| whisper-turbo/beam | fleurs-en | mbr | -0.05 | [-0.29, +0.18] | [-0.30, 0.19] | 0.8165 | 9/8/183 |
| whisper-turbo/greedy | fleurs-en | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/greedy | fleurs-en | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/sample | fleurs-en | conf | -0.28 | [-1.02, +0.24] | [-1.07, 0.24] | 0.9723 | 11/11/178 |
| whisper-turbo/sample | fleurs-en | mbr | +0.02 | [-0.21, +0.26] | [-0.21, 0.24] | 0.8684 | 9/7/184 |
| whisper-turbo/beam | ls-dev-other | conf | +0.22 | [-0.01, +0.48] | [-0.04, 0.48] | 0.0533 | 29/15/356 |
| whisper-turbo/beam | ls-dev-other | mbr | +0.08 | [-0.05, +0.21] | [-0.07, 0.26] | 0.2393 | 14/9/377 |
| whisper-turbo/greedy | ls-dev-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/greedy | ls-dev-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/sample | ls-dev-other | conf | +0.15 | [-0.06, +0.38] | [-0.06, 0.38] | 0.1447 | 26/15/359 |
| whisper-turbo/sample | ls-dev-other | mbr | +0.11 | [-0.04, +0.25] | [0.00, 0.25] | 0.1465 | 16/8/376 |
| whisper-turbo/beam | ls-tc-babble5 | conf | +0.16 | [-0.26, +0.62] | [-0.27, 0.61] | 0.6252 | 18/19/163 |
| whisper-turbo/beam | ls-tc-babble5 | mbr | +0.05 | [-0.25, +0.38] | [-0.23, 0.35] | 0.7232 | 14/14/172 |
| whisper-turbo/greedy | ls-tc-babble5 | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/greedy | ls-tc-babble5 | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/200 |
| whisper-turbo/sample | ls-tc-babble5 | conf | +0.05 | [-0.45, +0.50] | [-0.43, 0.48] | 0.5464 | 22/19/159 |
| whisper-turbo/sample | ls-tc-babble5 | mbr | +0.18 | [-0.11, +0.47] | [-0.05, 0.44] | 0.2997 | 17/11/172 |
| whisper-turbo/beam | ls-test-clean | conf | +0.01 | [-0.20, +0.23] | [-0.20, 0.21] | 0.9957 | 25/24/351 |
| whisper-turbo/beam | ls-test-clean | mbr | +0.11 | [-0.10, +0.32] | [-0.10, 0.34] | 0.3110 | 23/18/359 |
| whisper-turbo/greedy | ls-test-clean | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/greedy | ls-test-clean | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/sample | ls-test-clean | conf | +0.78 | [-0.01, +2.31] | [-0.03, 2.26] | 0.1759 | 19/13/368 |
| whisper-turbo/sample | ls-test-clean | mbr | +0.02 | [-0.12, +0.17] | [-0.10, 0.16] | 0.7232 | 14/14/372 |
| whisper-turbo/beam | ls-test-other | conf | +0.11 | [-0.14, +0.34] | [-0.17, 0.38] | 0.3774 | 34/24/342 |
| whisper-turbo/beam | ls-test-other | mbr | -0.03 | [-0.22, +0.15] | [-0.24, 0.19] | 0.7719 | 16/18/366 |
| whisper-turbo/greedy | ls-test-other | conf | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/greedy | ls-test-other | mbr | +0.00 | [+0.00, +0.00] | [0.00, 0.00] | 1.0000 | 0/0/400 |
| whisper-turbo/sample | ls-test-other | conf | +0.16 | [-0.07, +0.39] | [-0.10, 0.42] | 0.2600 | 28/19/353 |
| whisper-turbo/sample | ls-test-other | mbr | +0.20 | [+0.03, +0.40] | [0.04, 0.36] | 0.0340 | 23/12/365 |

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
| parakeet-ctc | greedy | whisper | cm05 -> rover_cg | 7 | -2.66 | [-3.57, -1.75] | 0.89 | 0 / 7 |
| parakeet-ctc | greedy | whisper | conf -> rover_c | 7 | -2.66 | [-3.57, -1.75] | 0.89 | 0 / 7 |
| parakeet-ctc | greedy | whisper | conf -> rover_cg | 7 | -2.66 | [-3.57, -1.75] | 0.89 | 0 / 7 |
| parakeet-ctc | greedy | whisper | conf -> rover_freq | 7 | -2.66 | [-3.57, -1.75] | 0.89 | 0 / 7 |
| parakeet-ctc | greedy | whisper | first -> rover_cg | 7 | -2.66 | [-3.57, -1.75] | 0.89 | 0 / 7 |
| parakeet-ctc | greedy | whisper | mbr -> rover_cg | 7 | -2.66 | [-3.57, -1.75] | 0.89 | 0 / 7 |
| parakeet-ctc | sample | legacy | cm05 -> rover_cg | 7 | +0.35 | [+0.14, +0.57] | 0.64 | 5 / 0 |
| parakeet-ctc | sample | legacy | conf -> mbr | 7 | +1.17 | [+0.60, +1.74] | 0.89 | 6 / 0 |
| parakeet-ctc | sample | legacy | conf -> rover_c | 7 | +1.49 | [+0.86, +2.12] | 0.91 | 7 / 0 |
| parakeet-ctc | sample | legacy | conf -> rover_cg | 7 | +1.50 | [+0.86, +2.14] | 0.91 | 7 / 0 |
| parakeet-ctc | sample | legacy | conf -> rover_freq | 7 | +1.50 | [+0.85, +2.15] | 0.91 | 7 / 0 |
| parakeet-ctc | sample | legacy | first -> conf | 7 | +1.34 | [+0.68, +1.99] | 0.80 | 5 / 0 |
| parakeet-ctc | sample | legacy | first -> rover_cg | 7 | +2.85 | [+1.85, +3.85] | 0.92 | 7 / 0 |
| parakeet-ctc | sample | legacy | mbr -> rover_cg | 7 | +0.25 | [+0.04, +0.45] | 0.73 | 4 / 0 |
| parakeet-ctc | sample | legacy | rover_freq -> rover_cg | 7 | -0.02 | [-0.10, +0.07] | 0.09 | 0 / 0 |
| parakeet-ctc | sample | whisper | cm05 -> rover_cg | 7 | -2.06 | [-2.90, -1.23] | 0.85 | 0 / 7 |
| parakeet-ctc | sample | whisper | conf -> mbr | 7 | +1.20 | [+0.60, +1.79] | 0.89 | 6 / 0 |
| parakeet-ctc | sample | whisper | conf -> rover_c | 7 | -0.96 | [-1.60, -0.33] | 0.70 | 0 / 3 |
| parakeet-ctc | sample | whisper | conf -> rover_cg | 7 | -0.95 | [-1.62, -0.29] | 0.73 | 0 / 3 |
| parakeet-ctc | sample | whisper | conf -> rover_freq | 7 | -0.95 | [-1.52, -0.37] | 0.62 | 0 / 2 |
| parakeet-ctc | sample | whisper | first -> conf | 7 | +1.36 | [+0.69, +2.03] | 0.80 | 4 / 0 |
| parakeet-ctc | sample | whisper | first -> rover_cg | 7 | +0.41 | [-0.76, +1.58] | 0.88 | 3 / 1 |
| parakeet-ctc | sample | whisper | mbr -> rover_cg | 7 | -2.27 | [-3.28, -1.26] | 0.90 | 0 / 7 |
| parakeet-ctc | sample | whisper | rover_freq -> rover_cg | 7 | +0.00 | [-0.11, +0.11] | 0.30 | 0 / 1 |
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
| whisper-small | beam | legacy | cm05 -> rover_cg | 7 | -0.06 | [-0.25, +0.14] | 0.49 | 0 / 1 |
| whisper-small | beam | legacy | conf -> mbr | 7 | +0.05 | [-0.12, +0.22] | 0.00 | 0 / 0 |
| whisper-small | beam | legacy | conf -> rover_c | 7 | +0.00 | [-0.18, +0.19] | 0.11 | 1 / 0 |
| whisper-small | beam | legacy | conf -> rover_cg | 7 | +0.02 | [-0.14, +0.19] | 0.05 | 0 / 0 |
| whisper-small | beam | legacy | conf -> rover_freq | 7 | +0.07 | [-0.08, +0.22] | 0.00 | 1 / 0 |
| whisper-small | beam | legacy | first -> conf | 7 | -0.12 | [-0.22, -0.02] | 0.00 | 0 / 1 |
| whisper-small | beam | legacy | first -> rover_cg | 7 | -0.04 | [-0.22, +0.13] | 0.18 | 0 / 0 |
| whisper-small | beam | legacy | mbr -> rover_cg | 7 | -0.04 | [-0.15, +0.07] | 0.05 | 0 / 1 |
| whisper-small | beam | legacy | rover_freq -> rover_cg | 7 | -0.06 | [-0.22, +0.10] | 0.46 | 0 / 1 |
| whisper-small | beam | whisper | cm05 -> rover_cg | 7 | -2.65 | [-3.40, -1.89] | 0.79 | 0 / 6 |
| whisper-small | beam | whisper | conf -> mbr | 7 | +0.02 | [-0.15, +0.18] | 0.00 | 0 / 0 |
| whisper-small | beam | whisper | conf -> rover_c | 7 | -2.41 | [-3.06, -1.77] | 0.64 | 0 / 5 |
| whisper-small | beam | whisper | conf -> rover_cg | 7 | -2.42 | [-3.09, -1.76] | 0.66 | 0 / 5 |
| whisper-small | beam | whisper | conf -> rover_freq | 7 | -2.41 | [-3.10, -1.73] | 0.68 | 0 / 5 |
| whisper-small | beam | whisper | first -> conf | 7 | -0.04 | [-0.14, +0.07] | 0.00 | 0 / 0 |
| whisper-small | beam | whisper | first -> rover_cg | 7 | -2.38 | [-2.99, -1.77] | 0.63 | 0 / 5 |
| whisper-small | beam | whisper | mbr -> rover_cg | 7 | -2.58 | [-3.27, -1.90] | 0.76 | 0 / 7 |
| whisper-small | beam | whisper | rover_freq -> rover_cg | 7 | -0.04 | [-0.17, +0.08] | 0.24 | 0 / 1 |
| whisper-small | greedy | whisper | cm05 -> rover_cg | 7 | -3.07 | [-4.15, -1.99] | 0.94 | 0 / 7 |
| whisper-small | greedy | whisper | conf -> rover_c | 7 | -3.07 | [-4.15, -1.99] | 0.94 | 0 / 7 |
| whisper-small | greedy | whisper | conf -> rover_cg | 7 | -3.07 | [-4.15, -1.99] | 0.94 | 0 / 7 |
| whisper-small | greedy | whisper | conf -> rover_freq | 7 | -3.07 | [-4.15, -1.99] | 0.94 | 0 / 7 |
| whisper-small | greedy | whisper | first -> rover_cg | 7 | -3.07 | [-4.15, -1.99] | 0.94 | 0 / 7 |
| whisper-small | greedy | whisper | mbr -> rover_cg | 7 | -3.07 | [-4.15, -1.99] | 0.94 | 0 / 7 |
| whisper-small | sample | legacy | cm05 -> rover_cg | 7 | -0.06 | [-0.19, +0.07] | 0.00 | 0 / 0 |
| whisper-small | sample | legacy | conf -> mbr | 7 | -0.44 | [-1.67, +0.79] | 0.55 | 0 / 1 |
| whisper-small | sample | legacy | conf -> rover_c | 7 | -0.01 | [-1.14, +1.12] | 0.47 | 0 / 1 |
| whisper-small | sample | legacy | conf -> rover_cg | 7 | -0.17 | [-1.27, +0.93] | 0.44 | 0 / 1 |
| whisper-small | sample | legacy | conf -> rover_freq | 7 | -0.27 | [-1.38, +0.84] | 0.50 | 1 / 1 |
| whisper-small | sample | legacy | first -> conf | 7 | +1.32 | [-0.02, +2.67] | 0.67 | 3 / 0 |
| whisper-small | sample | legacy | first -> rover_cg | 7 | +0.99 | [+0.38, +1.61] | 0.55 | 2 / 0 |
| whisper-small | sample | legacy | mbr -> rover_cg | 7 | +0.19 | [-0.03, +0.41] | 0.61 | 2 / 0 |
| whisper-small | sample | legacy | rover_freq -> rover_cg | 7 | -0.01 | [-0.20, +0.17] | 0.55 | 0 / 1 |
| whisper-small | sample | whisper | cm05 -> rover_cg | 7 | -3.30 | [-4.46, -2.13] | 0.92 | 0 / 7 |
| whisper-small | sample | whisper | conf -> mbr | 7 | -0.59 | [-1.87, +0.68] | 0.55 | 0 / 1 |
| whisper-small | sample | whisper | conf -> rover_c | 7 | -2.65 | [-4.29, -1.01] | 0.69 | 0 / 4 |
| whisper-small | sample | whisper | conf -> rover_cg | 7 | -2.82 | [-4.42, -1.21] | 0.67 | 0 / 4 |
| whisper-small | sample | whisper | conf -> rover_freq | 7 | -2.85 | [-4.44, -1.26] | 0.67 | 0 / 4 |
| whisper-small | sample | whisper | first -> conf | 7 | +1.39 | [+0.04, +2.75] | 0.67 | 3 / 0 |
| whisper-small | sample | whisper | first -> rover_cg | 7 | -1.79 | [-2.86, -0.71] | 0.78 | 0 / 4 |
| whisper-small | sample | whisper | mbr -> rover_cg | 7 | -2.71 | [-3.80, -1.63] | 0.92 | 0 / 7 |
| whisper-small | sample | whisper | rover_freq -> rover_cg | 7 | -0.01 | [-0.16, +0.14] | 0.38 | 0 / 1 |
| whisper-turbo | beam | legacy | cm05 -> rover_cg | 7 | -0.16 | [-0.38, +0.06] | 0.74 | 0 / 2 |
| whisper-turbo | beam | legacy | conf -> mbr | 7 | +0.01 | [-0.12, +0.13] | 0.00 | 0 / 0 |
| whisper-turbo | beam | legacy | conf -> rover_c | 7 | +0.01 | [-0.11, +0.13] | 0.00 | 0 / 0 |
| whisper-turbo | beam | legacy | conf -> rover_cg | 7 | -0.01 | [-0.14, +0.12] | 0.05 | 0 / 0 |
| whisper-turbo | beam | legacy | conf -> rover_freq | 7 | -0.03 | [-0.19, +0.13] | 0.33 | 0 / 1 |
| whisper-turbo | beam | legacy | first -> conf | 7 | +0.01 | [-0.12, +0.13] | 0.34 | 0 / 1 |
| whisper-turbo | beam | legacy | first -> rover_cg | 7 | +0.00 | [-0.16, +0.16] | 0.37 | 0 / 1 |
| whisper-turbo | beam | legacy | mbr -> rover_cg | 7 | -0.13 | [-0.37, +0.10] | 0.77 | 0 / 2 |
| whisper-turbo | beam | legacy | rover_freq -> rover_cg | 7 | -0.07 | [-0.28, +0.14] | 0.78 | 1 / 1 |
| whisper-turbo | beam | whisper | cm05 -> rover_cg | 7 | -3.77 | [-5.13, -2.41] | 0.95 | 0 / 7 |
| whisper-turbo | beam | whisper | conf -> mbr | 7 | +0.00 | [-0.24, +0.25] | 0.69 | 1 / 1 |
| whisper-turbo | beam | whisper | conf -> rover_c | 7 | -2.89 | [-3.70, -2.08] | 0.83 | 0 / 7 |
| whisper-turbo | beam | whisper | conf -> rover_cg | 7 | -2.90 | [-3.69, -2.12] | 0.82 | 0 / 7 |
| whisper-turbo | beam | whisper | conf -> rover_freq | 7 | -3.03 | [-3.91, -2.15] | 0.85 | 0 / 7 |
| whisper-turbo | beam | whisper | first -> conf | 7 | +0.01 | [-0.15, +0.18] | 0.64 | 1 / 2 |
| whisper-turbo | beam | whisper | first -> rover_cg | 7 | -2.86 | [-3.61, -2.11] | 0.81 | 0 / 7 |
| whisper-turbo | beam | whisper | mbr -> rover_cg | 7 | -3.70 | [-5.03, -2.37] | 0.95 | 0 / 7 |
| whisper-turbo | beam | whisper | rover_freq -> rover_cg | 7 | +0.03 | [-0.16, +0.21] | 0.75 | 1 / 1 |
| whisper-turbo | greedy | whisper | cm05 -> rover_cg | 7 | -3.40 | [-4.56, -2.24] | 0.94 | 0 / 7 |
| whisper-turbo | greedy | whisper | conf -> rover_c | 7 | -3.40 | [-4.56, -2.24] | 0.94 | 0 / 7 |
| whisper-turbo | greedy | whisper | conf -> rover_cg | 7 | -3.40 | [-4.56, -2.24] | 0.94 | 0 / 7 |
| whisper-turbo | greedy | whisper | conf -> rover_freq | 7 | -3.40 | [-4.56, -2.24] | 0.94 | 0 / 7 |
| whisper-turbo | greedy | whisper | first -> rover_cg | 7 | -3.40 | [-4.56, -2.24] | 0.94 | 0 / 7 |
| whisper-turbo | greedy | whisper | mbr -> rover_cg | 7 | -3.40 | [-4.56, -2.24] | 0.94 | 0 / 7 |
| whisper-turbo | sample | legacy | cm05 -> rover_cg | 7 | +0.03 | [-0.06, +0.11] | 0.00 | 0 / 0 |
| whisper-turbo | sample | legacy | conf -> mbr | 7 | -0.12 | [-0.32, +0.07] | 0.00 | 0 / 0 |
| whisper-turbo | sample | legacy | conf -> rover_c | 7 | -0.05 | [-0.23, +0.13] | 0.00 | 1 / 0 |
| whisper-turbo | sample | legacy | conf -> rover_cg | 7 | +0.03 | [-0.18, +0.24] | 0.11 | 0 / 0 |
| whisper-turbo | sample | legacy | conf -> rover_freq | 7 | -0.13 | [-0.31, +0.06] | 0.00 | 0 / 0 |
| whisper-turbo | sample | legacy | first -> conf | 7 | +0.84 | [+0.38, +1.30] | 0.55 | 5 / 0 |
| whisper-turbo | sample | legacy | first -> rover_cg | 7 | +0.88 | [+0.40, +1.36] | 0.78 | 4 / 0 |
| whisper-turbo | sample | legacy | mbr -> rover_cg | 7 | +0.10 | [+0.00, +0.20] | 0.10 | 2 / 0 |
| whisper-turbo | sample | legacy | rover_freq -> rover_cg | 7 | +0.08 | [-0.08, +0.25] | 0.65 | 1 / 1 |
| whisper-turbo | sample | whisper | cm05 -> rover_cg | 7 | -3.40 | [-4.62, -2.19] | 0.94 | 0 / 7 |
| whisper-turbo | sample | whisper | conf -> mbr | 7 | -0.14 | [-0.34, +0.06] | 0.00 | 0 / 0 |
| whisper-turbo | sample | whisper | conf -> rover_c | 7 | -3.47 | [-5.01, -1.92] | 0.93 | 0 / 5 |
| whisper-turbo | sample | whisper | conf -> rover_cg | 7 | -3.43 | [-4.99, -1.87] | 0.93 | 0 / 6 |
| whisper-turbo | sample | whisper | conf -> rover_freq | 7 | -3.51 | [-4.97, -2.06] | 0.92 | 0 / 6 |
| whisper-turbo | sample | whisper | first -> conf | 7 | +0.85 | [+0.37, +1.34] | 0.62 | 5 / 0 |
| whisper-turbo | sample | whisper | first -> rover_cg | 7 | -2.43 | [-3.53, -1.33] | 0.90 | 0 / 5 |
| whisper-turbo | sample | whisper | mbr -> rover_cg | 7 | -3.22 | [-4.45, -2.00] | 0.94 | 0 / 7 |
| whisper-turbo | sample | whisper | rover_freq -> rover_cg | 7 | +0.09 | [-0.07, +0.24] | 0.66 | 1 / 1 |

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
| drax | ami | Drax standard vs ROVER@T=0.4 | 12.31 | 11.31 | +1.00 | [+0.25, +1.73] |
| drax | common_voice | Drax standard vs ROVER@T=0.4 | 13.26 | 13.49 | -0.22 | [-2.29, +1.28] |
| drax | earnings22 | Drax standard vs ROVER@T=0.4 | 22.08 | 20.91 | +1.17 | [+0.38, +1.96] |
| drax | fleurs-de | Drax standard vs ROVER@T=0.4 | 9.30 | 7.88 | +1.42 | [+0.82, +2.02] |
| drax | fleurs-en | Drax standard vs ROVER@T=0.4 | 10.53 | 10.25 | +0.28 | [-0.21, +0.77] |
| drax | fleurs-es | Drax standard vs ROVER@T=0.4 | 6.49 | 5.95 | +0.54 | [+0.21, +0.90] |
| drax | fleurs-fr | Drax standard vs ROVER@T=0.4 | 12.85 | 11.77 | +1.08 | [+0.51, +1.68] |
| drax | fleurs-it | Drax standard vs ROVER@T=0.4 | 6.68 | 5.64 | +1.04 | [+0.54, +1.54] |
| drax | fleurs-pt | Drax standard vs ROVER@T=0.4 | 13.00 | 11.63 | +1.37 | [+0.77, +2.00] |
| drax | gigaspeech | Drax standard vs ROVER@T=0.4 | 13.86 | 13.09 | +0.77 | [+0.00, +1.56] |
| drax | ls-tc-babble0 | Drax standard vs ROVER@T=0.4 | 40.06 | 40.24 | -0.18 | [-2.36, +1.72] |
| drax | ls-tc-babble10 | Drax standard vs ROVER@T=0.4 | 5.01 | 4.26 | +0.75 | [+0.27, +1.30] |
| drax | ls-tc-babble5 | Drax standard vs ROVER@T=0.4 | 10.49 | 9.49 | +1.01 | [+0.50, +1.52] |
| drax | ls-tc-white5 | Drax standard vs ROVER@T=0.4 | 7.93 | 7.19 | +0.75 | [+0.25, +1.24] |
| drax | ls-test-clean | Drax standard vs ROVER@T=0.4 | 2.79 | 2.53 | +0.26 | [-0.05, +0.56] |
| drax | ls-test-other | Drax standard vs ROVER@T=0.4 | 5.63 | 4.87 | +0.76 | [+0.33, +1.24] |
| drax | slr83 | Drax standard vs ROVER@T=0.4 | 9.25 | 8.42 | +0.83 | [+0.18, +1.48] |
| drax | spgispeech | Drax standard vs ROVER@T=0.4 | 7.79 | 7.50 | +0.29 | [-0.27, +0.82] |
| drax | voxpopuli | Drax standard vs ROVER@T=0.4 | 7.42 | 7.15 | +0.27 | [-0.12, +0.67] |
| drax | ami | Drax standard vs MBR@T=0.4 | 12.31 | 11.14 | +1.17 | [+0.43, +1.91] |
| drax | common_voice | Drax standard vs MBR@T=0.4 | 13.26 | 13.26 | +0.00 | [-2.02, +1.51] |
| drax | earnings22 | Drax standard vs MBR@T=0.4 | 22.08 | 20.85 | +1.23 | [+0.44, +2.06] |
| drax | fleurs-de | Drax standard vs MBR@T=0.4 | 9.30 | 8.07 | +1.23 | [+0.63, +1.83] |
| drax | fleurs-en | Drax standard vs MBR@T=0.4 | 10.53 | 9.98 | +0.55 | [+0.09, +1.04] |
| drax | fleurs-es | Drax standard vs MBR@T=0.4 | 6.49 | 5.99 | +0.50 | [+0.15, +0.88] |
| drax | fleurs-fr | Drax standard vs MBR@T=0.4 | 12.85 | 11.83 | +1.02 | [+0.46, +1.62] |
| drax | fleurs-it | Drax standard vs MBR@T=0.4 | 6.68 | 5.58 | +1.10 | [+0.60, +1.58] |
| drax | fleurs-pt | Drax standard vs MBR@T=0.4 | 13.00 | 11.57 | +1.43 | [+0.83, +2.06] |
| drax | gigaspeech | Drax standard vs MBR@T=0.4 | 13.86 | 12.90 | +0.96 | [+0.25, +1.75] |
| drax | ls-tc-babble0 | Drax standard vs MBR@T=0.4 | 40.06 | 41.30 | -1.24 | [-3.57, +0.84] |
| drax | ls-tc-babble10 | Drax standard vs MBR@T=0.4 | 5.01 | 4.37 | +0.65 | [+0.13, +1.21] |
| drax | ls-tc-babble5 | Drax standard vs MBR@T=0.4 | 10.49 | 9.49 | +1.01 | [+0.47, +1.53] |
| drax | ls-tc-white5 | Drax standard vs MBR@T=0.4 | 7.93 | 7.26 | +0.67 | [+0.18, +1.16] |
| drax | ls-test-clean | Drax standard vs MBR@T=0.4 | 2.79 | 2.61 | +0.18 | [-0.16, +0.51] |
| drax | ls-test-other | Drax standard vs MBR@T=0.4 | 5.63 | 4.82 | +0.81 | [+0.38, +1.30] |
| drax | slr83 | Drax standard vs MBR@T=0.4 | 9.25 | 8.57 | +0.69 | [+0.07, +1.34] |
| drax | spgispeech | Drax standard vs MBR@T=0.4 | 7.79 | 7.24 | +0.56 | [+0.00, +1.09] |
| drax | voxpopuli | Drax standard vs MBR@T=0.4 | 7.42 | 7.07 | +0.35 | [-0.05, +0.73] |
| drax | ami | MBR vs ROVER, both @T=0.4 | 11.14 | 11.31 | -0.17 | [-0.55, +0.18] |
| drax | common_voice | MBR vs ROVER, both @T=0.4 | 13.21 | 13.44 | -0.22 | [-0.56, +0.07] |
| drax | earnings22 | MBR vs ROVER, both @T=0.4 | 20.85 | 20.91 | -0.06 | [-0.46, +0.34] |
| drax | fleurs-de | MBR vs ROVER, both @T=0.4 | 8.07 | 7.88 | +0.19 | [-0.07, +0.47] |
| drax | fleurs-en | MBR vs ROVER, both @T=0.4 | 9.98 | 10.25 | -0.28 | [-0.51, -0.05] |
| drax | fleurs-es | MBR vs ROVER, both @T=0.4 | 5.99 | 5.95 | +0.04 | [-0.12, +0.20] |
| drax | fleurs-fr | MBR vs ROVER, both @T=0.4 | 11.83 | 11.77 | +0.06 | [-0.19, +0.31] |
| drax | fleurs-it | MBR vs ROVER, both @T=0.4 | 5.58 | 5.64 | -0.06 | [-0.26, +0.13] |
| drax | fleurs-pt | MBR vs ROVER, both @T=0.4 | 11.57 | 11.63 | -0.06 | [-0.37, +0.24] |
| drax | gigaspeech | MBR vs ROVER, both @T=0.4 | 12.90 | 13.09 | -0.19 | [-0.50, +0.11] |
| drax | ls-tc-babble0 | MBR vs ROVER, both @T=0.4 | 41.30 | 40.24 | +1.06 | [+0.53, +1.58] |
| drax | ls-tc-babble10 | MBR vs ROVER, both @T=0.4 | 4.37 | 4.26 | +0.10 | [-0.03, +0.25] |
| drax | ls-tc-babble5 | MBR vs ROVER, both @T=0.4 | 9.49 | 9.49 | +0.00 | [-0.25, +0.28] |
| drax | ls-tc-white5 | MBR vs ROVER, both @T=0.4 | 7.26 | 7.19 | +0.08 | [-0.15, +0.30] |
| drax | ls-test-clean | MBR vs ROVER, both @T=0.4 | 2.61 | 2.53 | +0.08 | [-0.08, +0.24] |
| drax | ls-test-other | MBR vs ROVER, both @T=0.4 | 4.82 | 4.87 | -0.06 | [-0.26, +0.16] |
| drax | slr83 | MBR vs ROVER, both @T=0.4 | 8.57 | 8.42 | +0.14 | [-0.19, +0.51] |
| drax | spgispeech | MBR vs ROVER, both @T=0.4 | 7.24 | 7.50 | -0.27 | [-0.50, -0.06] |
| drax | voxpopuli | MBR vs ROVER, both @T=0.4 | 7.07 | 7.15 | -0.08 | [-0.27, +0.13] |
| drax | ami | ROVER@main vs ROVER@T=0.4 | 11.92 | 11.31 | +0.61 | [-0.24, +1.48] |
| drax | common_voice | ROVER@main vs ROVER@T=0.4 | 13.64 | 13.49 | +0.15 | [-2.02, +1.75] |
| drax | earnings22 | ROVER@main vs ROVER@T=0.4 | 24.96 | 20.91 | +4.05 | [+2.02, +6.52] |
| drax | fleurs-de | ROVER@main vs ROVER@T=0.4 | 7.95 | 7.88 | +0.07 | [-0.33, +0.47] |
| drax | fleurs-en | ROVER@main vs ROVER@T=0.4 | 10.21 | 10.25 | -0.05 | [-0.47, +0.38] |
| drax | fleurs-es | ROVER@main vs ROVER@T=0.4 | 6.17 | 5.95 | +0.22 | [-0.04, +0.47] |
| drax | fleurs-fr | ROVER@main vs ROVER@T=0.4 | 11.81 | 11.77 | +0.04 | [-0.39, +0.44] |
| drax | fleurs-it | ROVER@main vs ROVER@T=0.4 | 5.60 | 5.64 | -0.04 | [-0.32, +0.24] |
| drax | fleurs-pt | ROVER@main vs ROVER@T=0.4 | 11.51 | 11.63 | -0.13 | [-0.50, +0.28] |
| drax | gigaspeech | ROVER@main vs ROVER@T=0.4 | 13.09 | 13.09 | +0.00 | [-0.56, +0.58] |
| drax | ls-tc-babble0 | ROVER@main vs ROVER@T=0.4 | 41.04 | 40.24 | +0.80 | [-0.88, +2.44] |
| drax | ls-tc-babble10 | ROVER@main vs ROVER@T=0.4 | 4.45 | 4.26 | +0.18 | [-0.21, +0.57] |
| drax | ls-tc-babble5 | ROVER@main vs ROVER@T=0.4 | 10.31 | 9.49 | +0.83 | [+0.32, +1.36] |
| drax | ls-tc-white5 | ROVER@main vs ROVER@T=0.4 | 7.78 | 7.19 | +0.59 | [+0.23, +0.95] |
| drax | ls-test-clean | ROVER@main vs ROVER@T=0.4 | 2.48 | 2.53 | -0.05 | [-0.31, +0.21] |
| drax | ls-test-other | ROVER@main vs ROVER@T=0.4 | 5.04 | 4.87 | +0.17 | [-0.23, +0.59] |
| drax | slr83 | ROVER@main vs ROVER@T=0.4 | 8.20 | 8.42 | -0.22 | [-0.77, +0.35] |
| drax | spgispeech | ROVER@main vs ROVER@T=0.4 | 7.38 | 7.50 | -0.12 | [-0.48, +0.23] |
| drax | voxpopuli | ROVER@main vs ROVER@T=0.4 | 7.20 | 7.15 | +0.05 | [-0.33, +0.43] |
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
| whisper-small | ami | greedy vs ROVER over samples | 19.94 | 19.81 | +0.13 | [-0.69, +1.03] |
| whisper-small | common_voice | greedy vs ROVER over samples | 16.18 | 14.92 | +1.26 | [-0.14, +2.84] |
| whisper-small | earnings22 | greedy vs ROVER over samples | 18.49 | 21.16 | -2.67 | [-5.41, +0.00] |
| whisper-small | fleurs-en | greedy vs ROVER over samples | 7.71 | 8.06 | -0.35 | [-1.59, +0.47] |
| whisper-small | ls-dev-other | greedy vs ROVER over samples | 8.12 | 7.76 | +0.36 | [+0.07, +0.67] |
| whisper-small | ls-tc-babble5 | greedy vs ROVER over samples | 15.74 | 15.12 | +0.62 | [-1.67, +3.18] |
| whisper-small | ls-test-clean | greedy vs ROVER over samples | 3.96 | 4.11 | -0.15 | [-0.38, +0.07] |
| whisper-small | ls-test-other | greedy vs ROVER over samples | 8.82 | 8.77 | +0.06 | [-0.25, +0.38] |
| whisper-small | ami | greedy vs ROVER over beam n-best | 19.94 | 47.36 | -27.42 | [-48.00, -10.55] |
| whisper-small | common_voice | greedy vs ROVER over beam n-best | 16.18 | 15.37 | +0.82 | [-0.44, +2.05] |
| whisper-small | earnings22 | greedy vs ROVER over beam n-best | 18.49 | 16.93 | +1.56 | [+0.37, +2.99] |
| whisper-small | fleurs-en | greedy vs ROVER over beam n-best | 7.71 | 7.02 | +0.69 | [+0.02, +1.73] |
| whisper-small | ls-dev-other | greedy vs ROVER over beam n-best | 8.12 | 7.82 | +0.30 | [-0.03, +0.65] |
| whisper-small | ls-tc-babble5 | greedy vs ROVER over beam n-best | 15.74 | 27.58 | -11.84 | [-28.05, -0.24] |
| whisper-small | ls-test-clean | greedy vs ROVER over beam n-best | 3.96 | 4.06 | -0.10 | [-0.35, +0.12] |
| whisper-small | ls-test-other | greedy vs ROVER over beam n-best | 8.82 | 8.24 | +0.58 | [-0.04, +1.45] |
| whisper-small | ami | top beam vs ROVER over n-best | 50.39 | 47.36 | +3.04 | [-0.64, +9.94] |
| whisper-small | common_voice | top beam vs ROVER over n-best | 14.92 | 15.37 | -0.45 | [-1.41, +0.47] |
| whisper-small | earnings22 | top beam vs ROVER over n-best | 17.26 | 16.93 | +0.34 | [-0.41, +1.09] |
| whisper-small | fleurs-en | top beam vs ROVER over n-best | 6.88 | 7.02 | -0.14 | [-0.44, +0.16] |
| whisper-small | ls-dev-other | top beam vs ROVER over n-best | 7.52 | 7.82 | -0.30 | [-0.59, -0.01] |
| whisper-small | ls-tc-babble5 | top beam vs ROVER over n-best | 28.17 | 27.58 | +0.59 | [+0.00, +1.24] |
| whisper-small | ls-test-clean | top beam vs ROVER over n-best | 3.95 | 4.06 | -0.11 | [-0.33, +0.11] |
| whisper-small | ls-test-other | top beam vs ROVER over n-best | 8.18 | 8.24 | -0.06 | [-0.34, +0.24] |
| whisper-small | ami | greedy vs MBR over samples | 19.94 | 19.62 | +0.31 | [-0.54, +1.22] |
| whisper-small | common_voice | greedy vs MBR over samples | 16.18 | 15.81 | +0.37 | [-0.58, +1.42] |
| whisper-small | earnings22 | greedy vs MBR over samples | 18.49 | 21.99 | -3.50 | [-6.48, -0.70] |
| whisper-small | fleurs-en | greedy vs MBR over samples | 7.71 | 8.24 | -0.53 | [-1.79, +0.21] |
| whisper-small | ls-dev-other | greedy vs MBR over samples | 8.12 | 8.00 | +0.12 | [-0.17, +0.42] |
| whisper-small | ls-tc-babble5 | greedy vs MBR over samples | 15.74 | 15.46 | +0.28 | [-2.09, +2.75] |
| whisper-small | ls-test-clean | greedy vs MBR over samples | 3.96 | 4.29 | -0.32 | [-0.58, -0.11] |
| whisper-small | ls-test-other | greedy vs MBR over samples | 8.82 | 8.65 | +0.17 | [-0.11, +0.43] |
| whisper-turbo | ami | greedy vs ROVER over samples | 17.56 | 17.94 | -0.38 | [-1.01, +0.22] |
| whisper-turbo | common_voice | greedy vs ROVER over samples | 11.80 | 11.28 | +0.52 | [-0.22, +1.44] |
| whisper-turbo | earnings22 | greedy vs ROVER over samples | 16.77 | 16.52 | +0.25 | [-0.12, +0.62] |
| whisper-turbo | fleurs-en | greedy vs ROVER over samples | 5.50 | 5.57 | -0.07 | [-0.82, +0.46] |
| whisper-turbo | ls-dev-other | greedy vs ROVER over samples | 5.61 | 5.32 | +0.29 | [+0.11, +0.46] |
| whisper-turbo | ls-tc-babble5 | greedy vs ROVER over samples | 7.62 | 7.39 | +0.23 | [-0.18, +0.63] |
| whisper-turbo | ls-test-clean | greedy vs ROVER over samples | 3.14 | 3.03 | +0.11 | [-0.05, +0.28] |
| whisper-turbo | ls-test-other | greedy vs ROVER over samples | 5.07 | 4.84 | +0.23 | [+0.03, +0.45] |
| whisper-turbo | ami | greedy vs ROVER over beam n-best | 17.56 | 26.46 | -8.90 | [-19.25, -0.88] |
| whisper-turbo | common_voice | greedy vs ROVER over beam n-best | 11.80 | 12.40 | -0.59 | [-1.59, +0.31] |
| whisper-turbo | earnings22 | greedy vs ROVER over beam n-best | 16.77 | 16.48 | +0.29 | [-0.12, +0.69] |
| whisper-turbo | fleurs-en | greedy vs ROVER over beam n-best | 5.50 | 5.40 | +0.09 | [-0.20, +0.37] |
| whisper-turbo | ls-dev-other | greedy vs ROVER over beam n-best | 5.61 | 5.31 | +0.30 | [+0.09, +0.51] |
| whisper-turbo | ls-tc-babble5 | greedy vs ROVER over beam n-best | 7.62 | 7.39 | +0.23 | [-0.21, +0.70] |
| whisper-turbo | ls-test-clean | greedy vs ROVER over beam n-best | 3.14 | 3.23 | -0.09 | [-0.29, +0.11] |
| whisper-turbo | ls-test-other | greedy vs ROVER over beam n-best | 5.07 | 4.98 | +0.08 | [-0.13, +0.31] |
| whisper-turbo | ami | top beam vs ROVER over n-best | 27.95 | 26.46 | +1.48 | [-1.74, +7.27] |
| whisper-turbo | common_voice | top beam vs ROVER over n-best | 11.66 | 12.40 | -0.74 | [-1.41, -0.15] |
| whisper-turbo | earnings22 | top beam vs ROVER over n-best | 16.70 | 16.48 | +0.23 | [-0.17, +0.64] |
| whisper-turbo | fleurs-en | top beam vs ROVER over n-best | 5.38 | 5.40 | -0.02 | [-0.28, +0.23] |
| whisper-turbo | ls-dev-other | top beam vs ROVER over n-best | 5.47 | 5.31 | +0.17 | [+0.00, +0.34] |
| whisper-turbo | ls-tc-babble5 | top beam vs ROVER over n-best | 7.68 | 7.39 | +0.28 | [-0.11, +0.72] |
| whisper-turbo | ls-test-clean | top beam vs ROVER over n-best | 3.28 | 3.23 | +0.05 | [-0.18, +0.31] |
| whisper-turbo | ls-test-other | top beam vs ROVER over n-best | 4.90 | 4.98 | -0.08 | [-0.28, +0.10] |
| whisper-turbo | ami | greedy vs MBR over samples | 17.56 | 17.83 | -0.27 | [-0.94, +0.33] |
| whisper-turbo | common_voice | greedy vs MBR over samples | 11.80 | 12.03 | -0.22 | [-0.76, +0.37] |
| whisper-turbo | earnings22 | greedy vs MBR over samples | 16.77 | 16.72 | +0.04 | [-0.32, +0.40] |
| whisper-turbo | fleurs-en | greedy vs MBR over samples | 5.50 | 5.59 | -0.09 | [-0.91, +0.48] |
| whisper-turbo | ls-dev-other | greedy vs MBR over samples | 5.61 | 5.43 | +0.18 | [+0.03, +0.33] |
| whisper-turbo | ls-tc-babble5 | greedy vs MBR over samples | 7.62 | 7.57 | +0.05 | [-0.39, +0.44] |
| whisper-turbo | ls-test-clean | greedy vs MBR over samples | 3.14 | 3.06 | +0.09 | [-0.06, +0.26] |
| whisper-turbo | ls-test-other | greedy vs MBR over samples | 5.07 | 5.04 | +0.03 | [-0.14, +0.21] |
| parakeet-ctc | ami | greedy vs ROVER over sampled CTC paths | 16.60 | 17.33 | -0.72 | [-1.42, -0.06] |
| parakeet-ctc | common_voice | greedy vs ROVER over sampled CTC paths | 11.80 | 11.21 | +0.59 | [+0.07, +1.21] |
| parakeet-ctc | earnings22 | greedy vs ROVER over sampled CTC paths | 23.70 | 23.64 | +0.06 | [-0.51, +0.62] |
| parakeet-ctc | fleurs-en | greedy vs ROVER over sampled CTC paths | 10.09 | 10.02 | +0.07 | [-0.16, +0.31] |
| parakeet-ctc | ls-dev-other | greedy vs ROVER over sampled CTC paths | 3.85 | 3.94 | -0.08 | [-0.36, +0.18] |
| parakeet-ctc | ls-tc-babble5 | greedy vs ROVER over sampled CTC paths | 11.66 | 11.73 | -0.08 | [-0.44, +0.27] |
| parakeet-ctc | ls-test-clean | greedy vs ROVER over sampled CTC paths | 1.99 | 1.86 | +0.13 | [+0.00, +0.29] |
| parakeet-ctc | ls-test-other | greedy vs ROVER over sampled CTC paths | 3.50 | 3.56 | -0.06 | [-0.26, +0.12] |

## Tuned on dev (ls-dev-clean + ls-dev-other), reported on test

- **drax**: alpha=0.7, eps=0.3, gamma=0.5, lambda=3.0 (dev: select 4.35, ROVER 4.07, n=800)
- **whisfusion**: alpha=0.5, eps=0.7, gamma=1.0, lambda=1.5 (dev: select 10.00, ROVER 8.87, n=800)
- **whisper-small**: alpha=0.5, eps=0.7, gamma=1.0, lambda=0.75 (dev: select 7.70, ROVER 7.68, n=400)
- **whisper-turbo**: alpha=0.5, eps=0.7, gamma=1.0, lambda=0.25 (dev: select 5.43, ROVER 5.29, n=400)
- **parakeet-ctc**: alpha=0.5, eps=0.7, gamma=0.5, lambda=0.5 (dev: select 3.91, ROVER 3.94, n=200)

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
| whisper-small | ami | 19.87 | 19.50 | +0.38 | [-0.03, +0.83] |
| whisper-small | common_voice | 40.23 | 40.07 | +0.16 | [-0.57, +0.99] |
| whisper-small | earnings22 | 20.55 | 21.22 | -0.67 | [-2.25, +0.47] |
| whisper-small | fleurs-en | 8.08 | 7.83 | +0.25 | [-0.02, +0.54] |
| whisper-small | ls-tc-babble5 | 14.99 | 15.12 | -0.13 | [-0.76, +0.49] |
| whisper-small | ls-test-clean | 4.11 | 4.06 | +0.05 | [-0.09, +0.19] |
| whisper-small | ls-test-other | 8.61 | 8.52 | +0.08 | [-0.21, +0.36] |
| whisper-turbo | ami | 17.40 | 17.94 | -0.54 | [-1.20, +0.08] |
| whisper-turbo | common_voice | 37.41 | 37.36 | +0.05 | [-0.63, +1.06] |
| whisper-turbo | earnings22 | 16.56 | 16.50 | +0.06 | [-0.23, +0.37] |
| whisper-turbo | fleurs-en | 5.52 | 5.57 | -0.05 | [-0.25, +0.16] |
| whisper-turbo | ls-tc-babble5 | 7.65 | 7.44 | +0.21 | [-0.15, +0.56] |
| whisper-turbo | ls-test-clean | 3.08 | 3.01 | +0.07 | [-0.02, +0.18] |
| whisper-turbo | ls-test-other | 4.90 | 5.01 | -0.11 | [-0.31, +0.08] |
| parakeet-ctc | ami | 18.33 | 17.33 | +1.00 | [+0.35, +1.71] |
| parakeet-ctc | common_voice | 37.73 | 37.25 | +0.48 | [+0.05, +0.91] |
| parakeet-ctc | earnings22 | 24.13 | 23.64 | +0.49 | [-0.06, +1.01] |
| parakeet-ctc | fleurs-en | 10.25 | 10.02 | +0.23 | [+0.02, +0.45] |
| parakeet-ctc | ls-tc-babble5 | 12.38 | 11.73 | +0.65 | [+0.24, +1.05] |
| parakeet-ctc | ls-test-clean | 2.07 | 1.86 | +0.21 | [+0.03, +0.40] |
| parakeet-ctc | ls-test-other | 3.50 | 3.56 | -0.06 | [-0.35, +0.20] |

## Cost

| model | kind | arm | K | T | steps | n | s/utt | encode s | decode s | RTF | ms/candidate | ROVER ms | peak MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drax | kscale | K64 | 64 | 1.30 | 16.0 | 200 | 14.404 | 0.186 | 14.218 | 2.2079 | 222.2 | 2.92 | 5954 |
| drax | lowT | lowT | 16 | 0.40 | 16.0 | 3800 | 3.478 | 0.179 | 3.299 | 0.4184 | 206.2 | 0.68 | 4336 |
| drax | main | main | 16 | 1.30 | 16.0 | 11414 | 3.718 | 0.099 | 3.620 | 0.4684 | 226.2 | 0.74 | 4336 |
| drax | main | ref | 4 | 0.10 | 16.0 | 11414 | 1.050 | 0.099 | 0.951 | 0.1323 | 237.8 | 0.22 | 4336 |
| drax | sweepT | T0.1 | 16 | 0.10 | 16.0 | 200 | 3.791 | 0.029 | 3.762 | 0.5835 | 235.1 | 0.75 | 4336 |
| drax | sweepT | T0.4 | 16 | 0.40 | 16.0 | 200 | 3.776 | 0.029 | 3.747 | 0.5811 | 234.2 | 0.74 | 4336 |
| drax | sweepT | T0.7 | 16 | 0.70 | 16.0 | 200 | 3.775 | 0.029 | 3.746 | 0.5810 | 234.1 | 0.64 | 4336 |
| drax | sweepT | T1 | 16 | 1.00 | 16.0 | 200 | 3.776 | 0.029 | 3.748 | 0.5812 | 234.2 | 0.40 | 4336 |
| drax | sweepT | T1.3 | 16 | 1.30 | 16.0 | 200 | 3.777 | 0.029 | 3.748 | 0.5813 | 234.2 | 0.57 | 4336 |
| drax | sweepT | T1.6 | 16 | 1.60 | 16.0 | 200 | 3.778 | 0.029 | 3.749 | 0.5814 | 234.3 | 0.57 | 4336 |
| drax | sweepT | T2 | 16 | 2.00 | 16.0 | 200 | 3.783 | 0.029 | 3.754 | 0.5822 | 234.6 | 1.01 | 4336 |
| parakeet-ctc | main | greedy | 1 |  | nan | 1600 | 0.181 | 0.180 | 0.001 | 0.0279 | 1.0 | 0.14 | 2167 |
| parakeet-ctc | main | sample | 32 | 1.00 | nan | 1600 | 0.198 | 0.180 | 0.018 | 0.0306 | 0.6 | 1.27 | 2167 |
| whisfusion | ablation | base16 | 16 |  | 4.0 | 200 | 1.146 | 0.015 | 1.131 | 0.1764 | 70.7 | 1.05 | 2454 |
| whisfusion | ablation | fss_T1 | 16 |  | 4.0 | 200 | 1.178 | 0.015 | 1.163 | 0.1813 | 72.7 | 0.93 | 2454 |
| whisfusion | ablation | steps8 | 16 |  | 8.0 | 200 | 2.263 | 0.015 | 2.248 | 0.3483 | 140.5 | 1.03 | 2454 |
| whisfusion | kscale | K64 | 64 |  | 4.0 | 200 | 3.948 | 0.032 | 3.916 | 0.6052 | 61.2 | 2.74 | 7705 |
| whisfusion | main | main | 32 |  | 4.0 | 6400 | 2.367 | 0.038 | 2.329 | 0.3442 | 72.8 | 1.69 | 4205 |
| whisper-small | main | beam | 8 |  | nan | 2352 | 0.542 | 0.006 | 0.536 | 0.0853 | 67.0 | 0.31 | 2744 |
| whisper-small | main | greedy | 1 |  | nan | 2352 | 0.325 | 0.006 | 0.319 | 0.0512 | 319.2 | 0.12 | 2744 |
| whisper-small | main | sample | 16 | 0.60 | nan | 2352 | 0.403 | 0.006 | 0.397 | 0.0635 | 24.8 | 0.54 | 2744 |
| whisper-turbo | main | beam | 8 |  | nan | 2507 | 0.484 | 0.006 | 0.479 | 0.0772 | 59.9 | 0.31 | 3811 |
| whisper-turbo | main | greedy | 1 |  | nan | 2507 | 0.308 | 0.006 | 0.302 | 0.0490 | 302.0 | 0.13 | 3811 |
| whisper-turbo | main | sample | 16 | 0.60 | nan | 2507 | 0.415 | 0.006 | 0.409 | 0.0661 | 25.6 | 0.55 | 3811 |
