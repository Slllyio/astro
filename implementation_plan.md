# Medini Engine: Round 7 Deep Research & Implementation Plan

## Goal Description
Following the massive methodological exploration in Round 6, the objective of Round 7 is to **maximize the scientific rigor, predictive accuracy, and domain importance** of the Medini ML-Astrology engine. 

While Round 6 proved that causal inference (DoubleML) and kinematic trajectories carry profound signal in astrological data, it also revealed significant methodological leaks (in-sample contrastive evaluation) and reliance on weak baselines (natural karakas). This plan outlines an exhaustive roadmap to harden the models, scale the architectures that worked, and discard what didn't.

> [!IMPORTANT]
> **User Review Required**
> This plan proposes major shifts in methodology, specifically overhauling the Phase 3 Embeddings, migrating to Functional Lordship baselines, and scaling the Causal Inference engine. Please review the proposed phases below and approve or suggest pivots before execution begins.

---

## 1. Methodological Hardening (Increasing Accuracy)

Round 6 contained data leaks and architectural shortcuts that artificially inflated (or deflated) metrics. We must fix these to ensure the engine's outputs are scientifically bulletproof.

### 1.1 Fix Contrastive Embeddings Data Leak (Phase 3 Redux)
The reported K=5 Nearest Neighbor Jaccard similarity of 0.888 (+0.797 lift) is currently flawed due to in-sample evaluation. The K-NN search was performed on the same 5,085 people whose event fingerprints were used to construct the training pairs.
- **Action**: Split the 5,085 event cohort into a strict 80/20 train/eval split. 
- **Action**: Retrain the SimCLR encoder strictly on the 80%. Evaluate K=5 Jaccard NN *only* on the 20% held-out set. If the lift holds, the embeddings are valid; if not, we must add graph-based regularization.
#### [MODIFY] `app/medini/ml/contrastive_embeddings.py`

### 1.2 Implement Functional Lordship Baselines (Phase 2 & 8)
Currently, Survival Analysis (Phase 2) and MoE (Phase 8) use "Natural Karakas" (e.g., Venus = marriage, Sun = authority) as baselines. True Vedic astrology relies heavily on "Functional Lords" (e.g., the Lord of the 7th house, or planets occupying the 7th).
- **Action**: Add a `FunctionalLordship` calculator to the core ephemeris logic (`app.core`). 
- **Action**: Update the Vimshottari Hazard Baseline in Phase 2 to use the Dasha lord's relationship to the 7th/10th house rather than generic karakas.
#### [MODIFY] `app/medini/ml/survival_analysis.py`
#### [NEW] `app/core/lordships.py`

### 1.3 Continuous Treatment Causal Inference (Phase 6 Upgrade)
The DoubleML Causal Inference currently binarizes continuous variables at the median (e.g., `dist_mars_jupiter > median`). This destroys variance and non-linear threshold effects (e.g., exact orbs).
- **Action**: Upgrade EconML `LinearDML` to a Continuous Treatment model (e.g., `NonParamDML` or orthogonal random forests).
- **Action**: Sweep the top 50 continuous kinematic features across all 10 major event classes.
#### [MODIFY] `app/medini/ml/causal_inference.py`

---

## 2. Architectural Scaling (Increasing Importance)

We will double down on the architectures that proved highly effective in Round 6.

### 2.1 4D Spacetime Kinematic Modeling (Spatial-Temporal Network)
Phase 11 proved that ±90-day transit trajectories beat instantaneous snapshots (+0.085 AUC). However, flattening planetary positions into a 1D array loses physical realism.
- **Action**: We will model all planets' motion in 4D space-time: `(X, Y, Z, t)` or `(Longitude, Latitude, Distance, Time)` across the transit window.
- **Action**: Use a **Spatial-Temporal Graph Neural Network (ST-GNN)** or a **3D/4D Convolutional network** over a 180-day continuous ephemeris timeseries. This allows the engine to natively learn true spatial proximities (including declination, true geometric distance, speed, and retrograde loops) and observe aspects forming and separating in actual 3D space over time.
#### [MODIFY] `app/medini/ml/transit_trajectory.py`

### 2.2 LLM LoRA Fine-Tuning (Phase 9 Realization)
We have a 5,664-record QA dataset mapping Markdown charts to real life events.
- **Action**: Write a training script (`train_llm.py`) using HuggingFace `peft` and `trl` to LoRA fine-tune a small reasoning model (e.g., Llama-3 8B or Qwen-2).
- **Action**: Update the FastAPI `/interpret/chart` endpoint to route to this specialized adapter via Ollama or vLLM.
#### [NEW] `app/medini/ml/train_llm.py`
#### [MODIFY] `app/llm/interpreter.py`

### 2.3 The "BPHS Causal Audit" Suite
Phase 7's raw-rate Bayesian checks were theoretically flawed because they ignored confounders.
- **Action**: Merge Phase 6 (Causal DML) and Phase 7 (Rules).
- **Action**: Encode 100+ classical rules from the Brihat Parashara Hora Shastra (BPHS). Run every rule's antecedent through the DoubleML Causal engine to produce a master `bphs_causal_audit.csv`, creating the first statistically rigorous, confounder-adjusted audit of classical Vedic astrology in history.
#### [MODIFY] `app/medini/ml/bayesian_rule_validation.py` (Refactoring to use DML logic)

---

## 3. The Continuous Space-Time Paradigm (De-quantization)

Deep research into the astronomical origins of Vedic astrology reveals a profound philosophical pivot for this project. The traditional systems—12 Houses, 27 Nakshatras, Divisional Charts, and Dasha periods—are fundamentally **ancient quantization techniques** (lossy data compression). Before computers, sages discretized continuous spatial coordinates and temporal flows into discrete bins to make astrological rules transmissible via oral tradition. 

Modern ML does not need lossy compression. We will test the hypothesis that providing the raw, continuous observational data natively to the ML engine will outperform the ancient quantized bins.

### 3.1 Spatial De-quantization (Bypassing Houses & Nakshatras)
- **Action**: Instead of feeding the model categorical bins (e.g., `moon_nakshatra = Ashwini`, `jupiter_house = 9`), we will provide the continuous 4D coordinates (as scoped in section 2.1). 
- **Action**: We will allow the ST-GNN to learn its own non-linear spatial decision boundaries. We will then mathematically project these learned ML boundaries back onto the 360-degree zodiac to see if the ML natively rediscovers the ancient 13°20' Nakshatra divisions, or if it finds more accurate, dynamic boundaries.

### 3.2 Temporal De-quantization (Fractal Vimshottari Dynamics)
Vimshottari Dasha is a recursive, self-similar fractal model of time (MD -> AD -> PD). 
- **Action**: Instead of treating Dasha periods as categorical states (`dasha_lord = Venus`), we will encode time continuously as a "Fractal Dasha Vector." This involves mapping a person's exact age to a multi-dimensional wave function that represents the overlapping, continuous gravitational/temporal influence of the nested Dasha lords.

---

## 4. Data Acquisition & Pipeline

The models are currently starved for larger sample sizes (only 5k charts have usable event data).

### 4.1 Scale the Astro-Databank Corpus
- **Action**: Run the `app.medini.etl.scraper` to exhaust the Wayback Machine CDX index for all AA-rated charts, aiming to increase the event cohort from 5k to 15k+ rows.
- **Action**: Retrain the Vedic Tensor on the new corpus.

### 3.2 Acquire Synastry (Couple) Data
Phase 12 built a robust synastry feature extractor (100-feature pairwise + Ashtakoot), but we lack data to train a compatibility model.
- **Action**: Investigate sources for married/divorced couple birth data to bootstrap the Synastry ML pipeline.

---

## Open Questions

1. **Hardware for LLM**: Do we have access to local GPU acceleration (DirectML/CUDA) to run the LoRA fine-tuning for Phase 9 locally, or should I prep the script for cloud execution?
2. **DoubleML Compute Time**: Sweeping 50 features across 10 classes with Continuous Treatment DML might take several hours. Are you okay with a long-running batch job for the BPHS Causal Audit?
3. **Priority**: Should we tackle the Methodological Fixes (Accuracy) first, or immediately start building the Kinematic CNN (Importance)?

## Verification Plan

### Automated Tests
- `pytest` on the new `FunctionalLordship` calculator to ensure mathematical correctness of 7th lord and dispositor assignments.
- Test the new Contrastive Embedding split: Ensure K=5 NN is strictly evaluated on the held-out `test_idx`.

### Manual Verification
- Review the `bphs_causal_audit.csv` to see which classical rules survive the continuous causal scrutiny.
- Check the validation loss curve on the new Kinematic 1D CNN vs the old baseline.
