# OpenRouter model shortlist

Checked against OpenRouter on **17 November 2026**. Prices are USD per 1M input/output tokens and can change; pin explicit model IDs and recheck before the demo. “Typical latency” is OpenRouter’s displayed provider P50 where available, not a service guarantee.

OpenRouter recommends strict JSON Schema plus `require_parameters: true` and local validation for structured extraction; plain JSON mode is weaker ([structured-output guide, accessed 17 Nov 2026](https://openrouter.ai/blog/tutorials/structured-output-llm/)). The current adapter uses JSON mode and Pydantic validation, so TASK-002 must empirically decide reliability.

| Model ID | Price in/out | Context | Structured JSON | Vision/PDF | Typical latency | Free-tier limit | Fit |
|---|---:|---:|---|---|---|---|---|
| `anthropic/claude-haiku-5.5` | $0.10 / $0.50 | 1M | Yes, JSON Schema and tools | Yes | ~0.9–2.8 s across listed providers | No `:free` variant; paid provider limits | **Recommended default:** low cost, multiple providers, strong document/finance performance and strict output support ([model page](https://openrouter.ai/anthropic/claude-haiku-5.5)). |
| `google/gemini-3.6-flash` | $0.75 / $3.75 | 1M | Listed with structured outputs | Yes | ~1.4 s standard providers | No `:free` variant; paid provider limits | Higher-cost comparison candidate with fast multimodal document capability ([model page](https://openrouter.ai/google/gemini-3.6-flash)). |
| `inference-net/schematron-v2-small` | $0.05 / $0.23 | 128K | JSON Schema required; no tools | No documented vision | ~0.63 s | No free variant | Extraction specialist and **cheap fallback** after the adapter supports `json_schema`; OpenRouter currently shows a material structured-output error rate, so keep Pydantic retry ([model page](https://openrouter.ai/inference-net/schematron-v2-small/api)). |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | $0 / $0 | 256K | Tools yes; `response_format` not enforced | Yes: image/audio/video | Provider-dependent | 20 RPM and 50/day; 1,000/day after $10 credits | Free multimodal experiment/fallback, not default: free capacity and unenforced JSON reduce demo reliability ([model page](https://openrouter.ai/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning/providers)). |

Free variants share OpenRouter’s cap of 20 requests/minute and 50/day, rising to 1,000/day after at least $10 credits; failed attempts count ([OpenRouter free models, accessed 17 Nov 2026](https://openrouter.ai/collections/free-models)). Paid models inherit provider limits rather than a plan-wide request cap.

## Recommendation

Run TASK-002 first with `anthropic/claude-haiku-5.5` and `google/gemini-3.6-flash`; choose the higher extraction accuracy if the cost remains negligible for four invoices. Default to Haiku 5.5 on current price/latency. Use Schematron only after adding strict-schema requests, and keep Nemotron free as a non-demo fallback for image-only experiments. Classification can continue through the same selected model for integration simplicity; a dedicated decision model is an optimisation, not required for the hackathon.
