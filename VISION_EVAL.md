# Vision model evaluation

Model: CLIP ViT-B-32 (laion2b_s34b_b79k), 462 reviewer-graded icons.

| vision weight | tune: primary | tune: either | test: primary | test: either |
|---|---|---|---|---|
| 0.0 | 73.9% | 83.8% | 78.1% | 86.8% |
| 0.25 | 74.4% | 82.1% | 79.8% | 87.7% |
| 0.5 | 76.5% | 82.9% | 78.1% | 87.7% |
| 0.75 **chosen** | 77.4% | 83.3% | 78.5% | 87.7% |
| 1.0 | 76.5% | 83.3% | 77.6% | 88.2% |
| 1.5 | 76.9% | 82.9% | 76.8% | 87.3% |
| 2.0 | 76.5% | 81.6% | 76.3% | 86.4% |
| 3.0 | 66.7% | 80.3% | 70.6% | 83.8% |

Weight 0.75 set by hand (config.json vision_weight_locked): test accuracy 78.1% → 78.5% (primary), 86.8% → 87.7% (either).
