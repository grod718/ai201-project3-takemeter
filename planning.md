# TakeMeter — Planning Document

> Written before data collection, per project spec.
> Last updated: June 2026

---

## 1. Community

**Chosen community:** AI/tech discourse across r/MachineLearning, r/LocalLLaMA, r/artificial, r/ChatGPT, and r/singularity.

**Why this community:** These subreddits produce a high volume of text-heavy posts where discourse quality varies enormously — from rigorous technical arguments citing benchmarks and papers, to confident assertions with no evidence, to genuine help-seeking questions. The distinctions between these post types matter deeply to community members: a confident claim with no supporting evidence ("LLMs are just autocomplete") is treated very differently than a post that walks through actual model performance data. This community is a good fit for classification because the posts are substantive, public, and vary meaningfully along the quality axis I'm measuring.

**Personal relevance:** As someone building AI consulting services and studying AI engineering, I read this discourse regularly. That domain knowledge makes labeling faster and more consistent.

---

## 2. Label Taxonomy

### `analysis`
**Definition:** The post makes a structured argument supported by specific, verifiable evidence — benchmarks, paper citations, documented results, or step-by-step technical reasoning. The core claim could be checked or falsified by another reader using the evidence provided.

**Example 1:**
> "GPT-4 scored 86.4% on MMLU when released. Claude 3 Opus scored 86.8%. A 0.4% difference on a saturated benchmark isn't meaningful — both models are ceiling-constrained, not meaningfully differentiated on general knowledge tasks."

**Example 2:**
> "The Chinchilla paper showed models were undertrained relative to their parameter count. GPT-3 used ~300B tokens for 175B params; optimal would've been ~3.5T. That's why smaller, better-trained models like Mistral 7B punch above their weight."

---

### `hot_take`
**Definition:** A bold, confident opinion about AI/tech stated without substantive supporting evidence. The post asserts rather than argues — framing is often provocative, and the claim would be genuinely contested by many in the community.

**Example 1:**
> "LLMs are just autocomplete and anyone calling this 'intelligence' doesn't understand what intelligence means. We're nowhere near AGI and the people hyping this are embarrassing the field."

**Example 2:**
> "Honestly, Anthropic is miles ahead of OpenAI right now. Claude just feels smarter. OpenAI has become a marketing company."

---

### `question`
**Definition:** The post primarily asks for information, explanation, recommendations, or debugging help. The author's goal is to receive knowledge from others, not to share or argue a position.

**Example 1:**
> "What's actually the difference between RAG and fine-tuning for a domain-specific chatbot? I've seen people recommend both and I can't figure out when to use which."

**Example 2:**
> "Has anyone successfully run Llama 3 70B on consumer hardware? I have a 4090 and 64GB RAM — is quantized inference fast enough to be usable?"

---

## 3. Hard Edge Cases

### Primary edge case: `analysis` vs `hot_take`

**The problem post:**
> "LLM progress has clearly hit a wall. Pre-training on internet data is running out of steam — Ilya said as much at NeurIPS 2024. Test-time compute is the only interesting direction left, and even that has limits."

**Why it's hard:** The post cites a real source (Ilya Sutskever at NeurIPS 2024) but uses it decoratively. The conclusion ("clearly hit a wall") is asserted with confidence, not derived from the cited evidence. One name-drop does not constitute a structured argument.

**Decision rule:** If the evidence provided would support the claim even after removing all opinion language — i.e., a skeptic could follow the reasoning independently — label it `analysis`. If the evidence is decorative (a single name-drop, a vague reference) while the core claim is asserted without logical steps, label it `hot_take`. The post above → `hot_take`.

**Shorthand test:** Can I imagine a skeptic saying "okay, I read your evidence and I'm convinced"? If yes → `analysis`. If the evidence is there just to sound credible but wouldn't actually convince anyone → `hot_take`.

### Secondary edge case: `question` vs `hot_take`

Some posts open with a question but are clearly fishing for validation of an opinion:
> "Am I wrong that OpenAI's safety team is basically just PR at this point?"

**Decision rule:** If the question is genuine (the author would accept multiple answers), label `question`. If the question is rhetorical and the author is clearly asserting a position, label `hot_take`.

---

## 4. Data Collection Plan

**Sources:** Reddit API (PRAW) scraping r/MachineLearning, r/LocalLLaMA, r/artificial, r/ChatGPT, r/singularity. Manual backup entries via scripts/manual_entry.py for any high-quality posts found while browsing.

**Target per label:**
- `analysis`: ~70 examples (35%)
- `hot_take`: ~80 examples (40%)
- `question`: ~50 examples (25%)

*analysis is deliberately targeted at 35% because it's the hardest to find — not every post cites evidence. hot_take is most abundant in AI discourse.*

**Imbalance fallback:** After initial scrape, if any label is under 20% of the total:
1. Add more targeted subreddits (e.g., r/Futurology for hot_takes, r/learnmachinelearning for questions)
2. Use manual_entry.py to add curated examples from specific post types
3. Do not oversample or duplicate — collect new real examples

**Text length cap:** Posts over 1,500 characters will be truncated to the first 1,000 characters before training, to stay within DistilBERT's 512-token limit.

---

## 5. Evaluation Metrics

**Primary metric: per-class F1 score**

Accuracy alone is misleading if labels are imbalanced. For example, a model that always predicts `hot_take` on a dataset that's 40% hot_take would show 40% accuracy — which looks meaningful but is useless.

**Metrics I will report:**
- Overall accuracy (both models)
- Per-class precision, recall, and F1 (both models)
- Macro-averaged F1 (treats all classes equally regardless of size)
- Confusion matrix for the fine-tuned model

**Why macro F1 specifically:** Because all three labels matter equally for a community moderation tool. A model that nails `hot_take` but misses `analysis` is not useful.

**Baseline comparison rationale:** The zero-shot LLM baseline (Groq llama-3.3-70b-versatile) tells us how hard the task is without training. Fine-tuning should meaningfully improve macro F1, especially on `analysis` vs `hot_take` — the hardest boundary.

---

## 6. Definition of Success

**Threshold for "genuinely useful":**
- Fine-tuned model macro F1 ≥ 0.70 across all three labels
- No individual class F1 below 0.60 (a class that scores below this is too unreliable to act on)
- Fine-tuned model outperforms zero-shot baseline by at least 10 percentage points on macro F1

**What "good enough for deployment" looks like:**
A classifier that meets the above thresholds could plausibly be used in a community tool that flags posts for human review — not as a final judge, but as a filter. A post predicted as `analysis` with 85%+ confidence could be surfaced as high-quality; a post predicted as `hot_take` with high confidence could be tagged for context.

**What would make me reject the model:**
If `analysis` F1 < 0.55, the model can't distinguish reasoned argument from confident assertion — the most valuable distinction in the taxonomy. That's a failure.

---

## 7. AI Tool Plan

### Label stress-testing
Before annotating 200 examples, I'll give Claude my label definitions and edge case decision rule, and ask it to generate 10 posts that sit at the boundary between `analysis` and `hot_take`. If it produces posts I can't cleanly classify, I'll tighten the definitions before annotating.

### Annotation assistance
I may use an LLM to pre-label a batch of 50–60 examples before reviewing them myself. If I do:
- I'll provide the full label definitions and edge case rules as context
- I'll review and correct every pre-assigned label individually — no bulk acceptance
- I'll track which rows were pre-labeled in the `notes` column (value: "pre-labeled:llm")
- This will be disclosed in the AI usage section of the README

### Failure analysis
After fine-tuning, I'll paste the list of misclassified test examples into Claude and ask it to identify systematic patterns — e.g., "is the model failing on short posts?" or "is it confusing analysis and hot_take specifically when the post cites a person's name?" I'll verify any identified patterns by re-reading the examples myself before including them in the evaluation report.

---

## Hard Annotation Decisions (filled in during Milestone 3)

After labeling all 247 examples, I reviewed the dataset for posts that sat closest to a label boundary — these are the cases that best stress-test the taxonomy.

| # | Post excerpt | Labels considered | Final label | Reason |
|---|---|---|---|---|
| 1 | *"According to Meta's Llama 3 paper, their models were post-trained using 10M+ human preference annotations — roughly 5x more than Llama 2. The quality jump from 2 to 3 is largely attributed to this expanded RLHF dataset rather than architectural changes."* | `analysis` vs `hot_take` | `analysis` | This post is short, which made me initially suspicious it might be a hot_take dressed up with one fact. But the claim ("quality jump is attributed to RLHF data, not architecture") is a specific, checkable assertion directly supported by the cited number. A skeptic could verify the 10M figure and evaluate the claim. Length alone isn't disqualifying — what matters is whether the evidence does real argumentative work. |
| 2 | *"The Llama community gatekeeping around 'responsible use' licenses is performative. The models are already everywhere. The licenses change nothing."* | `hot_take` vs `analysis` | `hot_take` | This post references something real (Llama's responsible-use license) but provides no actual evidence that licenses "change nothing" — no download numbers, no enforcement data, nothing falsifiable. It's an assertion wrapped in a real topic, not an argument. This is the clearest example of my decision rule from Milestone 1: the evidence is decorative, not load-bearing. |
| 3 | *"If your AI product doesn't work without GPT-4, you don't have a product — you have a feature request to OpenAI."* | `hot_take` vs `analysis` | `hot_take` | This is a sharp, quotable claim about vendor lock-in risk in AI startups — a real and reasonable concern. But it's stated as a maxim, not derived from any specific case, data point, or example. I almost second-guessed myself because the *underlying point* is one I'd consider well-reasoned in other contexts — but the post itself doesn't do the reasoning. This taught me to separate "do I agree with this claim" from "does this post argue for it," which is the actual axis the taxonomy measures. |

**Pattern observed across all three:** the hardest boundary by far is `analysis` vs `hot_take`, exactly as predicted in Milestone 1. The deciding factor was never length or topic — it was always whether the cited fact was actually doing argumentative work, or just lending borrowed credibility to an assertion. `question` turned out to be much easier to separate from the other two; rhetorical/opinion-fishing questions (e.g., "Am I wrong that X...") were rare or absent in this dataset, which is worth noting as a limitation — the synthetic generation process may have produced cleaner question/non-question boundaries than real Reddit data would.

---

## Stretch Features Plan

*(Update this section before starting any stretch feature)*

- [ ] Inter-annotator reliability — get a second person to label 30 examples
- [ ] Confidence calibration — analyze whether model confidence correlates with accuracy
- [ ] Error pattern analysis — systematic failure mode writeup
- [ ] Deployed interface — Gradio or Streamlit classifier app
