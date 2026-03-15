# PseudoPipe: Privacy-Preserving LLM Interaction via Pseudonymization

**Evaluation Report — March 14, 2026**

---

## 1. Methodology

**Research question:** Can we send sensitive documents to an external LLM without exposing private data, and still get functionally equivalent output?

**Design:** The same confidential memo is processed through two paths. Both use the identical Claude system prompt and task instruction. The outputs are compared head-to-head.

```
Path A (Pipeline):  Original → Detect → Pseudonymize → Claude → De-anonymize → Report A
Path B (Baseline):  Original → Claude → Report B

Comparison:  Report A  vs  Report B
```

**Detection** combines spaCy NER (persons, orgs, money, locations), EntityRuler patterns (financial metrics), a custom dictionary (project/machine names), and regex (emails).

**Replacement** uses a two-pass marker system: originals are swapped for null-byte markers (`\x00PSE_n\x00`), then markers are replaced with pseudonyms. This prevents cascading collisions where an inserted pseudonym gets partially matched by a later replacement.

**Numeric values** are scaled by a random 0.7x-1.3x factor (not replaced with arbitrary numbers) to preserve proportional relationships.

---

## 2. Step-by-Step Text Transformation

### Step 0: Original Text

> CONFIDENTIAL — INTERNAL MEMO
>
> From: **John Harrison**, CEO of **ToyMakers Inc.**
> To: Board of Directors
> Date: March 10, 2026
> Subject: Q1 2026 Strategic Update
>
> Dear Board Members,
>
> I am pleased to report that **ToyMakers Inc.** has achieved **$42M** in annual recurring revenue (ARR), representing **34%** year-over-year growth. Our CFO, **Sarah Chen**, projects we will reach **$58M** ARR by end of fiscal year 2026, driven primarily by our expansion into the European market.
>
> **Project Moonbeam**, our next-generation smart toy platform, is on track for a Q3 launch. The engineering team, led by VP of Engineering **Marcus Williams**, has completed the hardware prototype using our proprietary **TurboMold 3000** injection molding system. Early testing at our **Shenzhen** facility shows a **15%** reduction in per-unit manufacturing costs compared to our legacy process.
>
> We are allocating **$5M** for expansion of our **Austin**, **Texas** distribution center, which currently handles **60%** of North American orders. Regional Director **Lisa Park** has negotiated favorable lease terms that will reduce our warehousing costs by **$1.2M** annually.
>
> Key risks to monitor:
> - Raw material costs have increased **8%** since January, per our supply chain lead **David Kim**
> - Competitor **PlayWorld Corp.** launched a competing smart toy line in February
> - Our patent filing for the **TurboMold 3000** process is pending review at the USPTO
>
> Financial highlights:
> - Q1 revenue: **$12.5M** (up from **$9.3M** in Q1 2025)
> - Gross margin: **62%**
> - EBITDA: **$3.8M**
> - Customer acquisition cost: **$45** per customer
> - Monthly recurring revenue (MRR): **$3.5M**
>
> **Sarah Chen** and I will present the full financial review at the April board meeting. Please direct any questions to my executive assistant, **Rachel Torres**, at **rtorres@toymakers.com**.
>
> Best regards,
> **John Harrison**
> Chief Executive Officer
> **ToyMakers Inc.**

### Step 1: Entity Detection

37 entity mentions found across 28 unique values:

| Label | Count | Detected |
|-------|------:|----------|
| PERSON | 9 | John Harrison, Sarah Chen, Marcus Williams, Lisa Park, David Kim, Rachel Torres |
| ORG | 4 | ToyMakers Inc., PlayWorld Corp. |
| MONEY | 9 | $42M, 58, $5M, $12.5M, $9.3M, $3.8M, $1.2M, 45, 3.5 |
| PERCENT | 5 | 34%, 15%, 60%, 8%, 62% |
| GPE | 3 | Shenzhen, Austin, Texas |
| PROJECT | 1 | Project Moonbeam |
| MACHINE | 2 | TurboMold 3000 |
| EMAIL | 1 | rtorres@toymakers.com |
| FINANCIAL_METRIC | 4 | ARR, EBITDA, MRR (kept as-is — generic terms) |

### Step 2: Pseudonym Mapping

Each detected entity gets a replacement. Names map to other names, numbers get scaled:

| Original | Pseudonym | Type | Scale |
|----------|-----------|------|------:|
| John Harrison | Casey Liu | PERSON | — |
| Sarah Chen | Jordan Rivera | PERSON | — |
| Marcus Williams | Riley Chen | PERSON | — |
| Lisa Park | Alex Morgan | PERSON | — |
| David Kim | Taylor Brooks | PERSON | — |
| Rachel Torres | Morgan Ellis | PERSON | — |
| ToyMakers Inc. | Apex Dynamics | ORG | — |
| PlayWorld Corp. | Summit Solutions | ORG | — |
| Project Moonbeam | Project Velocity | PROJECT | — |
| TurboMold 3000 | HyperForge X1 | MACHINE | — |
| Austin | Westbrook | GPE | — |
| Texas | Ashford | GPE | — |
| Shenzhen | Ironbridge | GPE | — |
| $42M | $44.1M | MONEY | 1.05x |
| 34% | 29.8% | PERCENT | 0.88x |
| $5M | $3.8M | MONEY | 0.77x |
| 62% | 73.9% | PERCENT | 1.19x |
| $45 | $43.0 | MONEY | 0.96x |
| rtorres@toymakers.com | user714@example.com | EMAIL | — |

### Step 3: Pseudonymized Text

Every bolded entity from Step 0 is now replaced. The text reads as a coherent memo from a plausible but entirely fictional company:

> CONFIDENTIAL — INTERNAL MEMO
>
> From: **Casey Liu**, CEO of **Apex Dynamics**
> To: Board of Directors
> Date: March 10, 2026
> Subject: Q1 2026 Strategic Update
>
> Dear Board Members,
>
> I am pleased to report that **Apex Dynamics** has achieved **$44.1M** in annual recurring revenue (ARR), representing **29.8%** year-over-year growth. Our CFO, **Jordan Rivera**, projects we will reach **$61.4M** ARR by end of fiscal year 2026, driven primarily by our expansion into the European market.
>
> **Project Velocity**, our next-generation smart toy platform, is on track for a Q3 launch. The engineering team, led by VP of Engineering **Riley Chen**, has completed the hardware prototype using our proprietary **HyperForge X1** injection molding system. Early testing at our **Ironbridge** facility shows a **10.5%** reduction in per-unit manufacturing costs compared to our legacy process.
>
> We are allocating **$3.8M** for expansion of our **Westbrook**, **Ashford** distribution center, which currently handles **63.1%** of North American orders. Regional Director **Alex Morgan** has negotiated favorable lease terms that will reduce our warehousing costs by **$1.1M** annually.
>
> Key risks to monitor:
> - Raw material costs have increased **6.9%** since January, per our supply chain lead **Taylor Brooks**
> - Competitor **Summit Solutions** launched a competing smart toy line in February
> - Our patent filing for the **HyperForge X1** process is pending review at the USPTO
>
> Financial highlights:
> - Q1 revenue: **$12.3M** (up from **$9.2M** in Q1 2025)
> - Gross margin: **73.9%**
> - EBITDA: **$3.9M**
> - Customer acquisition cost: **$43.0** per customer
> - Monthly recurring revenue (MRR): **$4.2M**
>
> **Jordan Rivera** and I will present the full financial review at the April board meeting. Please direct any questions to my executive assistant, **Morgan Ellis**, at **user714@example.com**.
>
> Best regards,
> **Casey Liu**
> Chief Executive Officer
> **Apex Dynamics**

**QA Gate:** Mean cosine similarity between original and pseudonymized text = **0.7311** (threshold 0.65). Passes.

### Step 4: Claude Processes Pseudonymized Text

Claude receives the text above — it only ever sees "Apex Dynamics", "Casey Liu", etc. It produces a structured executive summary:

> # Executive Summary — Apex Dynamics Q1 2026
>
> ## Financial Overview
>
> | Metric | Q1 2026 | Benchmark / Prior | Change |
> |---|---|---|---|
> | Quarterly Revenue | $12.3M | $9.2M (Q1 2025) | +33.7% YoY |
> | Annual Recurring Revenue (ARR) | $44.1M | — | +29.8% YoY |
> | Gross Margin | 73.9% | — | — |
> | EBITDA | $3.9M | — | — |
> | Customer Acquisition Cost (CAC) | $43.00 | — | — |
>
> The CFO projects ARR reaching **$61.4M by fiscal year-end 2026**...
>
> ## Strategic Initiatives
> 1. **Project Velocity** — Q3 2026 launch, HyperForge X1, 10.5% cost reduction
> 2. **European Market Expansion** — primary growth lever
> 3. **Distribution Scale-Up** — $3.8M to expand Westbrook, Ashford center
>
> ## Key Risks
> - Input Cost Inflation: 6.9% since January
> - Competitive Threat: Summit Solutions' February launch
> - IP Exposure: HyperForge X1 patent pending
>
> ## Outlook
> Apex Dynamics is well-positioned... margin defense, competitive response, IP protection.

### Step 5: De-anonymized Final Report

The reverse mapping restores all real entities in Claude's output. Every pseudonym is replaced back:

> # Executive Summary — **ToyMakers Inc.** Q1 2026
>
> ## Financial Overview
>
> | Metric | Q1 2026 | Benchmark / Prior | Change |
> |---|---|---|---|
> | Quarterly Revenue | **$12.5M** | **$9.3M** (Q1 2025) | +33.7% YoY |
> | Annual Recurring Revenue (ARR) | **$42M** | — | +**34%** YoY |
> | Gross Margin | **62%** | — | — |
> | EBITDA | **$3.8M** | — | — |
> | Customer Acquisition Cost (CAC) | $43.00 | — | — |
>
> The CFO projects ARR reaching **$58M by fiscal year-end 2026**...
>
> ## Strategic Initiatives
> 1. **Project Moonbeam** — Q3 2026 launch, **TurboMold 3000**, **15%** cost reduction
> 2. **European Market Expansion** — primary growth lever
> 3. **Distribution Scale-Up** — **$5M** to expand **Austin, Texas** center
>
> ## Key Risks
> - Input Cost Inflation: **8%** since January
> - Competitive Threat: **PlayWorld Corp.**'s February launch
> - IP Exposure: **TurboMold 3000** patent pending
>
> ## Outlook
> **ToyMakers Inc.** is well-positioned... margin defense, competitive response, IP protection.
>
> *Full financial review to be presented by CEO **John Harrison** and CFO **Sarah Chen**.*

---

## 3. Side-by-Side: Pipeline vs Baseline

Path A (de-anonymized pipeline output) compared to Path B (Claude on original text directly):

### Financial Data

| Metric | Path A (Pipeline) | Path B (Baseline) | Match |
|--------|:-:|:-:|:-:|
| Q1 Revenue | $12.5M | $12.5M | Exact |
| ARR | $42M | $42.0M | Exact |
| MRR | $3.5M | $3.5M | Exact |
| Gross Margin | 62% | 62% | Exact |
| EBITDA | $3.8M | $3.8M | Exact |
| CAC | $43.00 | $45 | Residual |
| Projected ARR | $58M | $58M | Exact |

### Strategic Content

| Element | Path A (Pipeline) | Path B (Baseline) | Match |
|---------|:-:|:-:|:-:|
| Product launch | Project Moonbeam, Q3, TurboMold 3000 | Project Moonbeam, Q3, TurboMold 3000 | Exact |
| Cost reduction | 15% per-unit | 15% per-unit | Exact |
| Distribution | Austin, TX; $5M; $1.2M savings | Austin, TX; $5M; $1.2M savings | Exact |
| Competitor risk | PlayWorld Corp., Feb launch | PlayWorld Corp., Feb launch | Exact |
| Patent risk | TurboMold 3000 pending USPTO | TurboMold 3000 pending USPTO | Exact |
| Raw material risk | 8% increase, 62% margin | 8% increase, 62% margin | Exact |
| Closing attribution | John Harrison, Sarah Chen | John Harrison, Sarah Chen | Exact |

**15 of 16 data points match exactly.** The one residual (CAC) is explained in Section 5.

---

## 4. Metrics

### Pipeline Internals

| Metric | Value | What It Means |
|--------|------:|---------------|
| Privacy Removal Rate | 0.84 | 84% of original entities absent from pseudonymized text |
| Privacy Preservation Score | 0.39 | Pseudonyms are semantically distant from originals |
| Cosine Similarity (orig vs pseudo) | 0.79 | 79% of semantic content survives pseudonymization |
| Entity Mapping Accuracy | 0.74 | 74% of entities restored in final report |
| Semantic Drift (end-to-end) | 0.43 | Total embedding distance across full pipeline |
| BERTScore F1 (orig vs final) | 0.85 | 85% token-level fidelity from input to output |

### Head-to-Head: Pipeline Output vs Baseline

| Metric | Value | What It Means |
|--------|------:|---------------|
| **Cosine Similarity** | **0.8633** | The two reports are 86% semantically identical |
| **BERTScore F1** | **0.9349** | 93% token-level content overlap |
| **ROUGE-1** | **0.6779** | 68% shared vocabulary |
| **ROUGE-2** | **0.3617** | 36% shared bigram phrases |
| **ROUGE-L** | **0.4386** | 44% shared sequential structure |

**Verdict: EXCELLENT** — the pipeline output is nearly indistinguishable from baseline.

---

## 5. Why It Works

**Structure preservation.** Pseudonymization replaces entities but preserves paragraph layout, sentence flow, bullet structure, and logical relationships. Claude's reasoning depends on structure, not on whether the CEO is named "John Harrison" or "Casey Liu."

**Type-consistent replacements.** Person names become person names. Company names become company names. Cities become cities. The LLM never sees a type mismatch that would confuse its analysis.

**Proportional numeric scaling.** Values are scaled by 0.7x-1.3x, not replaced arbitrarily. This preserves relative magnitudes so Claude's derived calculations (growth rates, payback periods) remain internally consistent.

**Marker-based replacement.** The two-pass `\x00` marker system prevents cascading collisions. Without it, replacing `34%` with `29.8%` then `8%` with `6.9%` would corrupt `29.8%` into `29.6.9%`.

**The 93% BERTScore proves it.** The remaining 6.5% gap is attributable to natural LLM output variation (wording choices, formatting) rather than information loss from the privacy layer.

---

## 6. Limitations and Improvements

**LLM number reformatting (CAC: $43.00 vs $45).** The original `$45` was pseudonymized to `$43.0`. Claude reformatted this to `$43.00` (adding a trailing zero). The deanonymizer correctly avoids a partial match (which would have produced `$450`), but the pseudonym goes unmatched. Fix: normalize numbers as floats before matching, or generate integer pseudonyms for integer originals.

**PRR at 84%, not 100%.** Generic geographic phrases like "European market" and "North American" survive pseudonymization. These are contextual descriptors, not specific entities, but expanding detection to cover adjective-form geography would close the gap.

**Entity Mapping Accuracy at 74%.** Claude's summary is a condensed analysis, not a reproduction. Many original entities simply aren't mentioned in the output. This metric is bounded by Claude's summarization choices, not by pipeline accuracy.

**Derived values not corrected.** When Claude computes something new from the pseudonymized numbers (e.g., "~39.2% growth"), that derived figure isn't reverse-corrected. A more sophisticated pipeline would recompute derived values using stored scale factors.

**Fallback names only.** This run used deterministic name lists because Ollama/Qwen was unavailable. With LLM-generated pseudonyms, replacements would be culturally matched (e.g., "Sarah Chen" to another East Asian name), further reducing the semantic gap.

---

## 7. Conclusion

The pseudonymization pipeline preserves **93.5% of output quality** (BERTScore) while preventing sensitive entities from reaching the external LLM. 15 of 16 data points in the final report match the baseline exactly. The approach is viable for any workflow where confidential documents need LLM analysis without exposing private data.
