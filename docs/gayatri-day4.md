   # Gayatri — Day 4: Memory on vs. off

   ## What I ran
   `python scripts/compare_memory.py --seed 11 --ticks 10 --out results/day4-memory`
   Same seed run twice: memory on (normal retrieval) and memory off (empty memory). Baseline mode, 0 provider calls.

   ## Results
   - 50 decisions compared (5 residents × 10 ticks): 50 same, 0 different.
   - Memory on example (Ethan, tick 10): gathered wood; given recent and relevant event IDs.
   - Memory off example (Ethan, tick 10): gathered wood; given no events.
   - Full results: `results/day4-memory/comparison.json`

   ## What this means
   The baseline follows fixed rules. It receives memory but does not use it, so identical decisions are expected. This shows retrieval works and the comparison is set up. It does not show that memory changes behavior. A real comparison needs the live Groq planner.