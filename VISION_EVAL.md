# Vision model evaluation

Model: CLIP ViT-B-32 (laion2b_s34b_b79k), 462 reviewer-graded icons.

| vision weight | tune: primary | tune: either | test: primary | test: either |
|---|---|---|---|---|
| 0.0 | 78.2% | 88.0% | 82.9% | 91.7% |
| 0.25 | 78.6% | 86.3% | 84.2% | 92.1% |
| 0.5 | 80.8% | 87.2% | 82.5% | 92.1% |
| 0.75 **chosen** | 81.6% | 87.6% | 82.9% | 92.1% |
| 1.0 | 80.8% | 87.6% | 82.0% | 92.5% |
| 1.5 | 81.2% | 87.2% | 81.1% | 91.7% |
| 2.0 | 80.8% | 85.9% | 81.1% | 90.8% |
| 3.0 | 70.9% | 84.6% | 75.4% | 88.2% |

Weight 0.75 set by hand (config.json vision_weight_locked): test accuracy 82.9% → 82.9% (primary), 91.7% → 92.1% (either).
