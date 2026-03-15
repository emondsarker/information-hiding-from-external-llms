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

Claude receives the sanitized text — it only ever sees "Apex Dynamics", "Casey Liu", etc. It produces a structured executive summary. Full output:

> # Executive Summary — Apex Dynamics Q1 2026
>
> **Prepared:** March 14, 2026 | **Source:** CEO Strategic Update Memo (March 10, 2026)
>
> ---
>
> ## Financial Overview
>
> Apex Dynamics delivered strong financial results in Q1 2026, demonstrating sustained momentum across key metrics:
>
> | Metric | Q1 2026 | Benchmark / Prior | Change |
> |---|---|---|---|
> | Quarterly Revenue | $12.3M | $9.2M (Q1 2025) | **+33.7% YoY** |
> | Annual Recurring Revenue (ARR) | $44.1M | — | **+29.8% YoY** |
> | Monthly Recurring Revenue (MRR) | $4.2M | — | — |
> | Gross Margin | 73.9% | — | — |
> | EBITDA | $3.9M | — | — |
> | Customer Acquisition Cost (CAC) | $43.00 | — | — |
>
> The CFO projects ARR reaching **$61.4M by fiscal year-end 2026**, implying ~39.2% growth from the current run rate, underpinned by European market expansion.
>
> ---
>
> ## Strategic Initiatives
>
> Three core initiatives are driving the company's growth trajectory:
>
> 1. **Project Velocity (Next-Gen Smart Toy Platform)**
>    - On track for **Q3 2026 launch**; hardware prototype complete.
>    - Leverages the proprietary **HyperForge X1** injection molding system, yielding a **10.5% reduction in per-unit manufacturing costs** versus the legacy process.
>    - Validated at the Ironbridge manufacturing facility.
>
> 2. **European Market Expansion**
>    - Identified as the **primary growth lever** to bridge current ARR ($44.1M) to the year-end target ($61.4M).
>
> 3. **Distribution Infrastructure Scale-Up**
>    - **$3.8M capital allocation** to expand the Westbrook, Ashford distribution center (currently handling 63.1% of North American order volume).
>    - Newly negotiated lease terms expected to deliver **$1.1M in annual warehousing cost savings**, implying a ~3.5-year payback on the investment.
>
> ---
>
> ## Key Risks
>
> | Risk | Severity | Detail |
> |---|---|---|
> | **Input Cost Inflation** | High | Raw material costs up **6.9% since January 2026**; sustained increases could pressure the 73.9% gross margin. |
> | **Competitive Threat** | Medium–High | Summit Solutions launched a rival smart toy line in **February 2026**, potentially compressing the first-mover window for Project Velocity. |
> | **IP Exposure** | Medium | The HyperForge X1 patent application remains **under USPTO review**; the proprietary process is not yet legally protected, creating potential replication risk. |
> | **Distribution Concentration** | Moderate | A single facility (Westbrook, Ashford) services **63.1% of North American orders**, presenting operational continuity risk during the expansion buildout. |
>
> ---
>
> ## Outlook
>
> Apex Dynamics is well-positioned entering the remainder of FY2026. Revenue growth is robust (+33.7% YoY quarterly), margins are healthy, and the projected path to $61.4M ARR is credible given the European expansion pipeline and the Q3 product launch. However, management should prioritize:
>
> - **Margin defense** — Proactively hedge or renegotiate supplier contracts to offset the 6.9% raw material cost increase before it erodes EBITDA.
> - **Competitive response** — Accelerate go-to-market planning for Project Velocity to counter Summit Solutions' early market entry.
> - **IP protection** — Expedite the HyperForge X1 patent review and evaluate interim trade-secret safeguards.
>
> A comprehensive financial review is scheduled for the **April 2026 board meeting**.
>
> ---
>
> *This summary is derived from confidential internal communications and is intended for board-level review only.*

### Step 5: De-anonymized Final Report (Path A Output)

The reverse mapping restores all real entities in Claude's output. This is the text used for the head-to-head comparison:

> # Executive Summary — ToyMakers Inc. Q1 2026
>
> **Prepared:** March 14, 2026 | **Source:** CEO Strategic Update Memo (March 10, 2026)
>
> ---
>
> ## Financial Overview
>
> ToyMakers Inc. delivered strong financial results in Q1 2026, demonstrating sustained momentum across key metrics:
>
> | Metric | Q1 2026 | Benchmark / Prior | Change |
> |---|---|---|---|
> | Quarterly Revenue | $12.5M | $9.3M (Q1 2025) | **+33.7% YoY** |
> | Annual Recurring Revenue (ARR) | $42M | — | **+34% YoY** |
> | Monthly Recurring Revenue (MRR) | $3.5M | — | — |
> | Gross Margin | 62% | — | — |
> | EBITDA | $3.8M | — | — |
> | Customer Acquisition Cost (CAC) | $43.00 | — | — |
>
> The CFO projects ARR reaching **$58M by fiscal year-end 2026**, implying ~39.2% growth from the current run rate, underpinned by European market expansion.
>
> ---
>
> ## Strategic Initiatives
>
> Three core initiatives are driving the company's growth trajectory:
>
> 1. **Project Moonbeam (Next-Gen Smart Toy Platform)**
>    - On track for **Q3 2026 launch**; hardware prototype complete.
>    - Leverages the proprietary **TurboMold 3000** injection molding system, yielding a **15% reduction in per-unit manufacturing costs** versus the legacy process.
>    - Validated at the Shenzhen manufacturing facility.
>
> 2. **European Market Expansion**
>    - Identified as the **primary growth lever** to bridge current ARR ($42M) to the year-end target ($58M).
>
> 3. **Distribution Infrastructure Scale-Up**
>    - **$5M capital allocation** to expand the Austin, Texas distribution center (currently handling 60% of North American order volume).
>    - Newly negotiated lease terms expected to deliver **$1.2M in annual warehousing cost savings**, implying a ~3.5-year payback on the investment.
>
> ---
>
> ## Key Risks
>
> | Risk | Severity | Detail |
> |---|---|---|
> | **Input Cost Inflation** | High | Raw material costs up **8% since January 2026**; sustained increases could pressure the 62% gross margin. |
> | **Competitive Threat** | Medium–High | PlayWorld Corp. launched a rival smart toy line in **February 2026**, potentially compressing the first-mover window for Project Moonbeam. |
> | **IP Exposure** | Medium | The TurboMold 3000 patent application remains **under USPTO review**; the proprietary process is not yet legally protected, creating potential replication risk. |
> | **Distribution Concentration** | Moderate | A single facility (Austin, Texas) services **60% of North American orders**, presenting operational continuity risk during the expansion buildout. |
>
> ---
>
> ## Outlook
>
> ToyMakers Inc. is well-positioned entering the remainder of FY2026. Revenue growth is robust (+33.7% YoY quarterly), margins are healthy, and the projected path to $58M ARR is credible given the European expansion pipeline and the Q3 product launch. However, management should prioritize:
>
> - **Margin defense** — Proactively hedge or renegotiate supplier contracts to offset the 8% raw material cost increase before it erodes EBITDA.
> - **Competitive response** — Accelerate go-to-market planning for Project Moonbeam to counter PlayWorld Corp.' early market entry.
> - **IP protection** — Expedite the TurboMold 3000 patent review and evaluate interim trade-secret safeguards.
>
> A comprehensive financial review is scheduled for the **April 2026 board meeting**.
>
> ---
>
> *This summary is derived from confidential internal communications and is intended for board-level review only.*

---

## 3. Baseline Report (Path B Output)

For comparison, this is what Claude produced when given the original unmodified text directly — no pseudonymization:

> # Executive Summary Report
> **ToyMakers Inc. — Q1 2026 Strategic Update**
> *Prepared: March 14, 2026 | Source: CEO Internal Memo dated March 10, 2026*
>
> ---
>
> ## Financial Overview
>
> | Metric | Q1 2026 | Q1 2025 | YoY Change |
> |---|---|---|---|
> | Quarterly Revenue | $12.5M | $9.3M | **+34.4%** |
> | Annual Recurring Revenue (ARR) | $42.0M | ~$31.3M | **+34.0%** |
> | Monthly Recurring Revenue (MRR) | $3.5M | — | — |
> | Gross Margin | 62% | — | — |
> | EBITDA | $3.8M | — | — |
> | Customer Acquisition Cost (CAC) | $45 | — | — |
>
> **Projected ARR (FY2026 Year-End):** $58M — implying **38% growth** from current ARR, underpinned by European market expansion.
>
> **Assessment:** The company demonstrates strong top-line momentum with healthy unit economics. A 62% gross margin signals robust pricing power, while a $3.8M EBITDA in Q1 provides a solid foundation for reinvestment. The $45 CAC warrants continued monitoring relative to customer lifetime value (LTV), which was not disclosed.
>
> ---
>
> ## Strategic Initiatives
>
> 1. **Project Moonbeam (Next-Gen Smart Toy Platform)**
>    - **Status:** On track for **Q3 2026 launch**
>    - Hardware prototype complete; leveraging proprietary *TurboMold 3000* injection molding system
>    - Early manufacturing tests (Shenzhen facility) indicate a **15% reduction in per-unit costs** vs. legacy processes — directly accretive to gross margins at scale
>
> 2. **Distribution Infrastructure Expansion**
>    - **$5M capital allocation** for Austin, TX distribution center expansion
>    - Facility currently handles **60% of North American order volume**
>    - Newly negotiated lease terms expected to yield **$1.2M in annual warehousing cost savings**, representing an attractive ~4-year payback on the investment
>
> 3. **European Market Expansion**
>    - Identified as the primary growth vector for reaching the $58M ARR target
>    - Specific market entry details pending; further detail expected at the April board meeting
>
> ---
>
> ## Key Risks
>
> | Risk | Severity | Details |
> |---|---|---|
> | **Raw Material Cost Inflation** | High | Costs up **8% since January 2026**; direct threat to the 62% gross margin if sustained or accelerating |
> | **Competitive Pressure** | Medium | PlayWorld Corp. launched a competing smart toy line in **February 2026**, potentially diluting Project Moonbeam's first-mover advantage |
> | **IP Protection Uncertainty** | Medium | Patent filing for the proprietary *TurboMold 3000* process is **pending USPTO review**; unprotected IP poses risk of process replication by competitors |
>
> **Risk Commentary:** The convergence of rising input costs and a new competitive entrant requires close monitoring. Should raw material inflation persist, margin compression could reduce EBITDA by an estimated $0.5–1.0M annually absent pricing adjustments. The pending patent status for the company's core manufacturing innovation represents a strategic vulnerability until resolved.
>
> ---
>
> ## Outlook
>
> ToyMakers Inc. is well-positioned for continued growth in FY2026, supported by:
>
> - **Strong revenue trajectory** with a clear path from $42M to $58M ARR (+38%)
> - **Margin expansion potential** through the TurboMold 3000 manufacturing efficiencies and distribution cost reductions
> - **Product innovation pipeline** via Project Moonbeam, targeting the high-growth smart toy category
>
> **Key watchpoints for the Board:**
> 1. Raw material cost trajectory and the need for a pricing response strategy
> 2. Competitive intelligence on PlayWorld Corp.'s market traction
> 3. USPTO patent decision timeline and contingency plans for IP protection
> 4. European market entry execution plan (expected at April board meeting)
>
> ---
>
> *Full financial review to be presented by CEO John Harrison and CFO Sarah Chen at the April 2026 Board Meeting. Contact: Rachel Torres (rtorres@toymakers.com).*

---

## 4. Head-to-Head Comparison

Path A (de-anonymized pipeline output) compared to Path B (Claude on original text directly). Every factual claim extracted and compared:

| Category | Data Point | Path A (Pipeline) | Path B (Baseline) | Match |
|----------|-----------|-------------------|-------------------|:-----:|
| **Financial** | Q1 Revenue | $12.5M | $12.5M | Exact |
| | ARR | $42M | $42.0M | Exact |
| | MRR | $3.5M | $3.5M | Exact |
| | Gross Margin | 62% | 62% | Exact |
| | EBITDA | $3.8M | $3.8M | Exact |
| | CAC | $43.00 | $45 | Residual |
| | Projected ARR | $58M | $58M | Exact |
| **Strategic** | Product launch | Project Moonbeam, Q3 2026 | Project Moonbeam, Q3 2026 | Exact |
| | Manufacturing | TurboMold 3000, 15% cost reduction | TurboMold 3000, 15% cost reduction | Exact |
| | Test facility | Shenzhen | Shenzhen | Exact |
| | Distribution | Austin, TX; $5M; $1.2M savings | Austin, TX; $5M; $1.2M savings | Exact |
| | Growth driver | European expansion → $58M | European expansion → $58M | Exact |
| **Risks** | Raw materials | 8% increase, 62% margin at risk | 8% increase, 62% margin at risk | Exact |
| | Competition | PlayWorld Corp., Feb launch | PlayWorld Corp., Feb launch | Exact |
| | Patent | TurboMold 3000 pending USPTO | TurboMold 3000 pending USPTO | Exact |
| **Attribution** | Authors | John Harrison, Sarah Chen | John Harrison, Sarah Chen | Exact |

**15 of 16 data points match exactly.** The one residual (CAC) is explained in Section 6.

---

## 5. Metrics

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

## 6. Why It Works

**Structure preservation.** Pseudonymization replaces entities but preserves paragraph layout, sentence flow, bullet structure, and logical relationships. Claude's reasoning depends on structure, not on whether the CEO is named "John Harrison" or "Casey Liu."

**Type-consistent replacements.** Person names become person names. Company names become company names. Cities become cities. The LLM never sees a type mismatch that would confuse its analysis.

**Proportional numeric scaling.** Values are scaled by 0.7x-1.3x, not replaced arbitrarily. This preserves relative magnitudes so Claude's derived calculations (growth rates, payback periods) remain internally consistent.

**Marker-based replacement.** The two-pass `\x00` marker system prevents cascading collisions. Without it, replacing `34%` with `29.8%` then `8%` with `6.9%` would corrupt `29.8%` into `29.6.9%`.

**The 93% BERTScore proves it.** The remaining 6.5% gap is attributable to natural LLM output variation (wording choices, formatting) rather than information loss from the privacy layer.

---

## 7. Limitations and Improvements

**LLM number reformatting (CAC: $43.00 vs $45).** The original `$45` was pseudonymized to `$43.0`. Claude reformatted this to `$43.00` (adding a trailing zero). The deanonymizer correctly avoids a partial match (which would have produced `$450`), but the pseudonym goes unmatched. Fix: normalize numbers as floats before matching, or generate integer pseudonyms for integer originals.

**PRR at 84%, not 100%.** Generic geographic phrases like "European market" and "North American" survive pseudonymization. These are contextual descriptors, not specific entities, but expanding detection to cover adjective-form geography would close the gap.

**Entity Mapping Accuracy at 74%.** Claude's summary is a condensed analysis, not a reproduction. Many original entities simply aren't mentioned in the output. This metric is bounded by Claude's summarization choices, not by pipeline accuracy.

**Derived values not corrected.** When Claude computes something new from the pseudonymized numbers (e.g., "~39.2% growth"), that derived figure isn't reverse-corrected. A more sophisticated pipeline would recompute derived values using stored scale factors.

**Fallback names only.** This run used deterministic name lists because Ollama/Qwen was unavailable. With LLM-generated pseudonyms, replacements would be culturally matched (e.g., "Sarah Chen" to another East Asian name), further reducing the semantic gap.

---

## 8. Conclusion

The pseudonymization pipeline preserves **93.5% of output quality** (BERTScore) while preventing sensitive entities from reaching the external LLM. 15 of 16 data points in the final report match the baseline exactly. The approach is viable for any workflow where confidential documents need LLM analysis without exposing private data.
