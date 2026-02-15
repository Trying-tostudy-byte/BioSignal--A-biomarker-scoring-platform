# BioSignal--A-biomarker-scoring-platform


A quantitative decision-support framework to rank emerging biomarkers across Oncology, Cardiology, Neurology, and Immunology based on clinical and commercial potential.

## Problem

Investors and clinicians lack an integrated, quantitative framework to assess which emerging biomarkers have the highest probability of clinical success and market impact.

## Solution

We built a multi-factor scoring model that integrates:

- Clinical trial activity
- Regulatory progress
- Publication momentum
- Market size
- Competitive density

The output:
- Ranked biomarkers within each therapeutic area
- Cross-area comparison
- Investment heatmap

## Scoring Framework

Each biomarker receives a composite score:

Final Score = 
w1 * Clinical Signal +
w2 * Scientific Momentum +
w3 * Market Opportunity +
w4 * Competitive Landscape

Weights are configurable via `models/scoring_weihts.json`.

## Outputs

- Ranked biomarker list
- Area-level opportunity score
- CSV export for investor decks

## How to Run

1. Clone the repo
2. Install dependencies:

