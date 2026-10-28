# Hosting and budget status

Recorded for Eric’s Day 1 task, October 19, 2026.

Updated October 27: [the Day 0–4 audit](day0-day4-audit.md) now verifies live Groq access and real MiniLM CPU retrieval. The local key remains ignored. Classifier training/loading and combined deployment RAM measurements are still pending; this does not approve a hosting purchase.

- Current development cost: **$0 for this implementation**. The starter runs locally in baseline mode, downloads no model weights and makes no paid API calls.
- Model plan: the optional Groq adapter is implemented and tested with mocked responses. Eric still needs to add the server key and verify actual Qwen access and account limits using `python scripts/check_groq.py --live`. See the [Day 1–3 audit](day1-day3-audit.md). No provider calls were made during the audit because no key was configured.
- Paid hosting budget: **not set / not approved**. No paid resources, subscriptions or billing accounts were created.
- Deployment target: static frontend + CPU backend. Eric/Rylee will measure app + classifier + embedding-model RAM before choosing a service/size. Both small model integrations are still future work.
- Permanent storage and backend cold starts must be checked before calling a hosted preview durable or always available.

Until an explicit budget is agreed, use local development and free resources within their limits. Record the selected service, measured RAM, estimated cost, owner and approval here before activating a paid plan.
