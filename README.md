# Agentic Coworkers · SJSU assignment prototype

This is a self-contained prototype of two personalized AI coworkers. It includes an executable agent workflow, persistent shared memory, structured tool calls, state transitions, and a browser dashboard for demonstrating the results.

- **DailyTechUpgradeAgent** — curates a three-item daily technical brief with source, reading time, technical takeaway, and personalization rationale.
- **nextLevelPersonalCoachForCareerLevel** — runs a technical system-design challenge, returns rubric-based feedback, surfaces readiness gaps, and generates a seven-day preparation plan.

The full assignment write-up is in [`SUBMISSION.md`](./SUBMISSION.md), including goals, architecture, sample results, evaluation, production implementation notes, and responsible-use considerations.

## Run the actual agents

```bash
python3 agentic_workers.py demo
```

Individual workers:

```bash
python3 agentic_workers.py daily
python3 agentic_workers.py coach --answer "I would create a proposed state, await approval, execute with permission checks, persist a trace, and retry transient failures."
python3 agentic_workers.py coach --interactive
python3 agentic_workers.py memory
```

The runner writes `.agent_memory.json`, which is the shared memory used by both agents. Each run records the workflow trace, recommendations, assessment, strengths, gaps, opportunities, coding exercise, and next actions. The daily agent attempts live RSS retrieval from AWS, LangChain, and Google Cloud, then uses verified authoritative fallback records if a feed is unavailable.

## Run it

Open `index.html` in a browser, or serve the folder with any static web server:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## How the prototype maps to the assignment

The four tabs cover all required deliverables:

1. **DailyTechUpgradeAgent** — agent goal, sample daily top three, summaries, source labels, reading duration, learning rationale, and learning log.
2. **nextLevelPersonalCoachForCareerLevel** — target role, readiness score, interactive technical prompt, feedback, knowledge gaps, and preparation plan.
3. **Architecture** — workflow from sources to router to specialist agents to outcomes, plus tools/data sources and shared learner memory.
4. **Evaluation** — measurable checks for source accuracy, knowledge transfer, career readiness, and a prototype test plan.

The UI is a visual demonstration; the Python runner is the executable agent implementation. The runner is dependency-free so it can be demonstrated without API keys.
