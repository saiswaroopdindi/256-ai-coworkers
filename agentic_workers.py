#!/usr/bin/env python3
"""Executable prototype for the SJSU Agentic AI Coworkers assignment.

The prototype deliberately uses small, inspectable state machines and local tools so it
can run without an API key. A production version can replace the local summarizer and
catalog with model/API adapters while keeping the workflow, memory, and evaluation
observable.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parent
MEMORY_PATH = ROOT / ".agent_memory.json"


@dataclass
class LearnerProfile:
    name: str = "SJSU learner"
    interests: List[str] = field(default_factory=lambda: ["AI agents", "evaluation", "Python APIs"])
    target_role: str = "AI/ML Engineer Intern"
    active_gaps: List[str] = field(default_factory=lambda: ["observability", "production system design"])
    milestone: str = "Prepare a portfolio-ready agent system"


@dataclass
class Article:
    title: str
    source: str
    published: str
    url: str
    abstract: str
    tags: List[str]
    minutes: int


@dataclass
class Opportunity:
    category: str
    title: str
    organization: str
    url: str
    fit: str
    evidence_to_prepare: List[str]


@dataclass
class AgentEvent:
    timestamp: str
    agent: str
    state: str
    detail: str


class MemoryStore:
    """Small persistent memory layer shared by both workers."""

    def __init__(self, path: Path = MEMORY_PATH):
        self.path = path
        if path.exists():
            self.data = json.loads(path.read_text())
        else:
            self.data = {
                "profile": asdict(LearnerProfile()),
                "completed_briefs": [],
                "coaching_sessions": [],
                "events": [],
            }

    @property
    def profile(self) -> LearnerProfile:
        return LearnerProfile(**self.data["profile"])

    def write(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2) + "\n")

    def remember_event(self, event: AgentEvent) -> None:
        self.data["events"].append(asdict(event))
        self.data["events"] = self.data["events"][-100:]
        self.write()

    def remember_brief(self, brief: Dict[str, Any]) -> None:
        self.data["completed_briefs"].append(brief)
        self.data["completed_briefs"] = self.data["completed_briefs"][-30:]
        self.write()

    def remember_session(self, session: Dict[str, Any]) -> None:
        self.data["coaching_sessions"].append(session)
        self.data["coaching_sessions"] = self.data["coaching_sessions"][-30:]
        self.write()

    def update_gap(self, gap: str, resolved: bool = False) -> None:
        profile = self.data["profile"]
        gaps = profile.setdefault("active_gaps", [])
        if resolved:
            profile["active_gaps"] = [item for item in gaps if item != gap]
        elif gap not in gaps:
            gaps.append(gap)
        self.write()


class OpenAIAdapter:
    """Optional Responses API adapter using only the Python standard library."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def complete(self, instructions: str, input_text: str) -> str:
        if not self.enabled:
            return ""
        payload = json.dumps({"model": self.model, "instructions": instructions, "input": input_text}).encode()
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                data = json.loads(response.read())
            if data.get("output_text"):
                return data["output_text"].strip()
            chunks = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        chunks.append(content.get("text", ""))
            return "\n".join(chunks).strip()
        except (OSError, json.JSONDecodeError, KeyError):
            return ""


class ToolRegistry:
    """Tool layer. Each tool returns structured data and is logged by the agents."""

    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.model = OpenAIAdapter()
        self.tools: Dict[str, Callable[..., Any]] = {
            "retrieve_articles": self.retrieve_articles,
            "analyze_opportunity": self.analyze_opportunity,
            "retrieve_opportunities": self.retrieve_opportunities,
            "generate_coding_exercise": self.generate_coding_exercise,
            "summarize_article": self.summarize_article,
            "coach_feedback": self.coach_feedback,
            "score_relevance": self.score_relevance,
            "evaluate_answer": self.evaluate_answer,
            "save_memory": self.save_memory,
        }

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self.tools:
            raise KeyError(f"Unknown tool: {name}")
        return self.tools[name](**kwargs)

    def retrieve_articles(self) -> List[Article]:
        """Retrieve live RSS items when reachable, with verified fallback records."""
        live = self._retrieve_live_rss()
        if len(live) >= 3:
            return live
        catalog = [
            Article(
                "How we detect frontier model misalignment",
                "OpenAI",
                "2026-10-29",
                "https://openai.com/index/how-we-detect-frontier-model-misalignment/",
                "Monitoring agent reasoning, actions, and environmental effects helps detect unauthorized behavior and intervene earlier.",
                ["agents", "safety", "monitoring", "evaluation"], 5,
            ),
            Article(
                "Groundhog Day for AI agents: Prompt caching patterns for using OpenAI models on Amazon Bedrock",
                "AWS Machine Learning Blog",
                "2026-10-26",
                "https://aws.amazon.com/blogs/machine-learning/category/artificial-intelligence/amazon-machine-learning/",
                "Prompt caching can reduce repeated context cost and latency when an agent reuses tools, instructions, and history.",
                ["agents", "aws", "latency", "cost"], 5,
            ),
            Article(
                "Gemini at Work 2026: Introducing the Gemini agent",
                "Google Cloud Blog",
                "2026-10-08",
                "https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026",
                "Production agents need persistent memory, identity, authorization, sandboxing, network controls, and observability.",
                ["agents", "memory", "security", "observability"], 5,
            ),
            Article(
                "Advancing computer use with Ironclad",
                "OpenAI",
                "2026-10-06",
                "https://openai.com/index/advancing-computer-use-with-ironclad/",
                "Complex professional agents need business rules, multi-step execution, and verification against the original requirements.",
                ["agents", "computer-use", "evaluation", "workflows"], 5,
            ),
        ]
        return catalog

    def _retrieve_live_rss(self) -> List[Article]:
        feeds = [
            ("AWS Machine Learning Blog", "https://aws.amazon.com/blogs/machine-learning/feed/"),
            ("LangChain Blog", "https://blog.langchain.dev/rss/"),
            ("Google Cloud Blog", "https://cloud.google.com/feeds/blog.xml"),
        ]
        results: List[Article] = []
        for source, feed_url in feeds:
            try:
                request = urllib.request.Request(feed_url, headers={"User-Agent": "SJSU-AgenticCoworkers/1.0"})
                raw = urllib.request.urlopen(request, timeout=4).read()
                root = ET.fromstring(raw)
                items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for item in items[:4]:
                    def value(names: List[str]) -> str:
                        for name in names:
                            child = item.find(name) or item.find(f"{{http://www.w3.org/2005/Atom}}{name}")
                            if child is not None:
                                if child.text:
                                    return child.text.strip()
                                if child.attrib.get("href"):
                                    return child.attrib["href"]
                        return ""
                    title = html.unescape(value(["title"]))
                    link = value(["link"])
                    if not link:
                        link_node = item.find("{http://www.w3.org/2005/Atom}link")
                        link = link_node.attrib.get("href", "") if link_node is not None else ""
                    description = re.sub(r"<[^>]+>", " ", html.unescape(value(["description", "summary", "content"])))
                    description = re.sub(r"\s+", " ", description).strip()
                    published = value(["pubDate", "published", "updated"])[:16] or date.today().isoformat()
                    if title and link:
                        results.append(Article(title, source, published, link, description[:280] or "Fresh technical article from the source feed.", ["agents", "apis", "evaluation", "cloud"], 5))
            except (OSError, ET.ParseError, ValueError):
                continue
        unique: Dict[str, Article] = {item.url: item for item in results}
        return list(unique.values())[:8]

    def score_relevance(self, article: Article, profile: LearnerProfile) -> float:
        desired = {word.lower() for word in profile.interests + profile.active_gaps}
        tags = {word.lower() for word in article.tags}
        return round(len(desired & tags) / max(len(desired), 1), 3)

    def analyze_opportunity(self, target_role: str) -> Dict[str, Any]:
        opportunities = self.retrieve_opportunities(target_role)
        return {
            "role": target_role,
            "must_have": ["Python", "REST APIs", "evaluation", "system design", "clear communication"],
            "evidence": ["deployed project", "technical README", "measured experiment", "interview explanation"],
            "signals": ["agent workflow", "observability", "human approval", "failure recovery"],
            "opportunities": [asdict(item) for item in opportunities],
        }

    def retrieve_opportunities(self, target_role: str = "AI/ML Engineer Intern") -> List[Opportunity]:
        return [
            Opportunity("Internship/job", f"{target_role} search", "LinkedIn Jobs", "https://www.linkedin.com/jobs/search/?keywords=AI%20ML%20intern", "Search for Python, agents, evaluation, and API roles.", ["resume", "GitHub project", "system-design answer"]),
            Opportunity("SJSU career", "Student internships and employer events", "SJSU Career Center", "https://careercenter.sjsu.edu/", "Use SJSU advising and employer events to find current postings.", ["career profile", "target-role keywords", "questions for employer"]),
            Opportunity("Research", "Research Experiences for Undergraduates", "NSF REU", "https://www.nsf.gov/crssprgm/reu/", "Find research placements where Python, ML experiments, or evaluation are useful.", ["research interest statement", "transcript", "faculty-fit paragraph"]),
            Opportunity("Entrepreneurship", "Cofounder and startup exploration", "Y Combinator Co-Founder Matching", "https://www.ycombinator.com/cofounder-matching", "Test a learner analytics or agent-observability product idea with a potential cofounder.", ["problem statement", "prototype", "user interview notes"]),
        ]

    def generate_coding_exercise(self, gap: str) -> Dict[str, Any]:
        return {
            "title": "Implement an approval-aware agent trace",
            "prompt": "Write a Python function that accepts an agent action proposal and returns one of READY, AWAITING_APPROVAL, EXECUTING, SUCCEEDED, or FAILED. Reject external side effects without approval and record a trace event.",
            "constraints": ["Use a typed action dictionary", "Handle missing approval", "Return a trace list", "Include one retryable failure"],
            "success_criteria": ["Explicit state transition", "No side effect before approval", "Useful error message", "Testable output"],
            "why": f"This directly practices the active gap: {gap}.",
        }

    def summarize_article(self, article: Article, profile: LearnerProfile) -> str:
        prompt = f"Title: {article.title}\nSource: {article.source}\nArticle text or feed summary: {article.abstract}"
        generated = self.model.complete(
            "You are a technical learning agent. In two concise sentences, summarize the technical idea and give one practical takeaway for a learner preparing for an AI/ML engineering internship. Do not invent facts beyond the supplied text.",
            prompt,
        )
        return generated or article.abstract

    def coach_feedback(self, answer: str, assessment: Dict[str, Any]) -> str:
        generated = self.model.complete(
            "You are a rigorous but encouraging technical career coach. Give three concise sentences: one strength, one missing technical detail, and one next action. Use only the rubric result and learner answer.",
            json.dumps({"answer": answer, "assessment": assessment}),
        )
        if generated:
            return generated
        missing = ", ".join(assessment["missing"]) or "deeper tradeoff analysis"
        return f"You demonstrated {', '.join([key for key, value in assessment['rubric'].items() if value]) or 'a starting point'}. Strengthen {missing}. Next, implement and explain one test case that proves the agent behaves safely."

    def evaluate_answer(self, answer: str) -> Dict[str, Any]:
        text = answer.lower()
        rubric = {
            "states": any(token in text for token in ["state", "awaiting", "approval", "proposed"]),
            "guardrails": any(token in text for token in ["guardrail", "permission", "approve", "human", "side effect"]),
            "recovery": any(token in text for token in ["retry", "failure", "error", "rollback", "abort"]),
            "persistence": any(token in text for token in ["persist", "trace", "log", "store"]),
        }
        score = sum(rubric.values())
        missing = [key for key, present in rubric.items() if not present]
        return {"score": score, "out_of": len(rubric), "rubric": rubric, "missing": missing}

    def save_memory(self, key: str, value: Any) -> str:
        self.memory.data.setdefault("working_memory", {})[key] = value
        self.memory.write()
        return f"saved {key}"


class BaseAgent:
    name = "BaseAgent"

    def __init__(self, memory: MemoryStore, tools: ToolRegistry):
        self.memory = memory
        self.tools = tools
        self.events: List[AgentEvent] = []

    def transition(self, state: str, detail: str) -> None:
        event = AgentEvent(datetime.now(timezone.utc).isoformat(), self.name, state, detail)
        self.events.append(event)
        self.memory.remember_event(event)


class DailyTechUpgradeAgent(BaseAgent):
    name = "DailyTechUpgradeAgent"

    def run(self, today: Optional[str] = None) -> Dict[str, Any]:
        profile = self.memory.profile
        today = today or date.today().isoformat()
        self.transition("RETRIEVE", "Calling retrieve_articles tool")
        articles = self.tools.call("retrieve_articles")
        self.transition("RANK", f"Scoring {len(articles)} articles against interests and gaps")
        ranked = sorted(articles, key=lambda item: self.tools.call("score_relevance", article=item, profile=profile), reverse=True)
        selected = ranked[:3]
        self.transition("SUMMARIZE", "Generating technical summaries and learner-specific takeaways")
        recommendations = []
        for article in selected:
            relevance = self.tools.call("score_relevance", article=article, profile=profile)
            recommendations.append({
                **asdict(article),
                "summary": self.tools.call("summarize_article", article=article, profile=profile),
                "relevance": relevance,
                "learning_insight": self._insight(article, profile),
            })
        brief = {
            "date": today,
            "agent": self.name,
            "session_minutes": sum(item["minutes"] for item in recommendations),
            "learner_goal": profile.milestone,
            "recommendations": recommendations,
            "next_action": "Write one traceable state transition for a tool-using agent.",
            "model_mode": "OpenAI Responses API" if self.tools.model.enabled else "offline deterministic fallback",
            "events": [asdict(event) for event in self.events],
        }
        self.transition("REFLECT", "Checking time budget and goal alignment")
        self.tools.call("save_memory", key="last_learning_focus", value=[item["title"] for item in recommendations])
        self.transition("DONE", "Daily brief saved to shared memory")
        brief["events"] = [asdict(event) for event in self.events]
        self.memory.remember_brief(brief)
        return brief

    @staticmethod
    def _insight(article: Article, profile: LearnerProfile) -> str:
        gap = profile.active_gaps[0] if profile.active_gaps else "current goals"
        return f"This strengthens {profile.target_role} preparation by connecting {article.tags[0]} to your active gap: {gap}."


class CareerCoachAgent(BaseAgent):
    name = "nextLevelPersonalCoachForCareerLevel"

    def run(self, answer: Optional[str] = None, interactive: bool = False) -> Dict[str, Any]:
        profile = self.memory.profile
        self.transition("ANALYZE_OPPORTUNITY", f"Analyzing target role: {profile.target_role}")
        opportunity = self.tools.call("analyze_opportunity", target_role=profile.target_role)
        self.transition("PLAN_CHALLENGE", "Selecting a challenge from the learner's active gap")
        prompt = "An agent may search the web, but a human must approve external side effects. Describe the state transitions, guardrails, and recovery path."
        coding_exercise = self.tools.call("generate_coding_exercise", gap=profile.active_gaps[0] if profile.active_gaps else "agent reliability")
        if interactive and not answer:
            print(f"\nCoach prompt: {prompt}")
            answer = input("Your answer: ").strip()
        if answer is None:
            answer = ""
        self.transition("ASSESS", "Applying structured rubric to learner answer")
        assessment = self.tools.call("evaluate_answer", answer=answer)
        feedback = self.tools.call("coach_feedback", answer=answer, assessment=assessment)
        follow_up = ""
        follow_up_assessment: Dict[str, Any] = {}
        if interactive:
            follow_up = input("Follow-up: what would you log to prove the agent behaved safely? ").strip()
            follow_up_assessment = self.tools.call("evaluate_answer", answer=follow_up)
        plan = self._plan(assessment, opportunity)
        session = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.name,
            "target_role": profile.target_role,
            "prompt": prompt,
            "answer": answer,
            "assessment": assessment,
            "feedback": feedback,
            "model_mode": "OpenAI Responses API" if self.tools.model.enabled else "offline deterministic fallback",
            "follow_up": follow_up,
            "follow_up_assessment": follow_up_assessment,
            "opportunities": opportunity["opportunities"],
            "coding_exercise": coding_exercise,
            "interview_scenario": "Explain how you would observe, secure, and evaluate this agent in a production interview.",
            "strengths": self._strengths(assessment),
            "plan": plan,
            "events": [asdict(event) for event in self.events],
        }
        self.transition("MEMORIZE", "Updating active gap and next preparation action")
        if assessment["score"] >= 3:
            self.memory.update_gap("production system design", resolved=True)
        else:
            self.memory.update_gap("production system design")
        self.tools.call("save_memory", key="last_career_assessment", value=assessment)
        self.transition("DONE", "Career readiness session saved to shared memory")
        session["events"] = [asdict(event) for event in self.events]
        self.memory.remember_session(session)
        return session

    @staticmethod
    def _strengths(assessment: Dict[str, Any]) -> List[str]:
        return [key for key, present in assessment["rubric"].items() if present]

    @staticmethod
    def _plan(assessment: Dict[str, Any], opportunity: Dict[str, Any]) -> List[str]:
        tasks = [
            "Draw the state machine with Ready, ToolProposed, AwaitingApproval, Executing, Succeeded, and Failed.",
            "Implement a trace record for each tool call: input, approval, latency, result, and error.",
            "Explain the design in a 90-second interview answer and publish the measured mini-project.",
        ]
        if assessment["missing"]:
            tasks.insert(0, "Re-answer the prompt and explicitly cover: " + ", ".join(assessment["missing"]) + ".")
        return tasks


class AgentRouter:
    """Routes learner intent to one specialist and keeps a visible trace."""

    def __init__(self, memory: MemoryStore):
        tools = ToolRegistry(memory)
        self.memory = memory
        self.agents = {
            "daily": DailyTechUpgradeAgent(memory, tools),
            "coach": CareerCoachAgent(memory, tools),
        }

    def route(self, intent: str, **kwargs: Any) -> Dict[str, Any]:
        intent = intent.lower()
        if any(token in intent for token in ["article", "learn", "read", "daily", "technical"]):
            return self.agents["daily"].run(**kwargs)
        return self.agents["coach"].run(**kwargs)


def print_brief(result: Dict[str, Any]) -> None:
    print(f"\n{result['agent']} · {result['date']} · {result['session_minutes']} minute brief")
    print(f"Goal: {result['learner_goal']}\n")
    for index, item in enumerate(result["recommendations"], 1):
        print(f"{index}. {item['title']} — {item['source']} ({item['published']})")
        print(f"   {item['url']}")
        print(f"   {item.get('summary', item['abstract'])}")
        print(f"   Why it matters: {item['learning_insight']}\n")
    print(f"Next action: {result['next_action']}")
    print("Trace:", " → ".join(event["state"] for event in result["events"]))


def print_coaching(result: Dict[str, Any]) -> None:
    assessment = result["assessment"]
    print(f"\n{result['agent']} · {result['target_role']}")
    print(f"Prompt: {result['prompt']}")
    print(f"Score: {assessment['score']}/{assessment['out_of']}")
    print("Strengths:", ", ".join(result["strengths"]) or "none yet")
    print("Gaps:", ", ".join(assessment["missing"]) or "none")
    print("Coach feedback:", result["feedback"])
    if result.get("follow_up_assessment"):
        follow = result["follow_up_assessment"]
        print(f"Follow-up score: {follow['score']}/{follow['out_of']}")
    print("Opportunities:")
    for opportunity in result["opportunities"]:
        print(f"  - {opportunity['category']}: {opportunity['title']} — {opportunity['url']}")
    exercise = result["coding_exercise"]
    print(f"Coding exercise: {exercise['title']} — {exercise['prompt']}")
    print(f"Interview scenario: {result['interview_scenario']}")
    print("Preparation plan:")
    for index, task in enumerate(result["plan"], 1):
        print(f"  {index}. {task}")
    print("Trace:", " → ".join(event["state"] for event in result["events"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SJSU Agentic AI Coworkers prototype")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("daily", help="run DailyTechUpgradeAgent")
    coach = sub.add_parser("coach", help="run nextLevelPersonalCoachForCareerLevel")
    coach.add_argument("--answer", default="", help="answer to the system-design challenge")
    coach.add_argument("--interactive", action="store_true", help="ask the learner for an answer in the terminal")
    sub.add_parser("demo", help="run both agents end-to-end")
    sub.add_parser("memory", help="show shared learner memory")
    args = parser.parse_args()
    memory = MemoryStore()
    router = AgentRouter(memory)
    if args.command == "daily":
        print_brief(router.route("daily technical learning"))
    elif args.command == "coach":
        print_coaching(router.route("career coaching", answer=args.answer, interactive=args.interactive))
    elif args.command == "demo":
        print_brief(router.route("daily technical learning"))
        print_coaching(router.route("career coaching", answer="I would use a Proposed state, await human approval, then execute with permission checks. I would log the action and retry on transient failure."))
    else:
        print(json.dumps(memory.data, indent=2))


if __name__ == "__main__":
    main()
