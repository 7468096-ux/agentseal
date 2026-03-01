from __future__ import annotations

import asyncio
import secrets

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Agent, AgentSeal, InviteCode, Seal, CertTask, CertTest
from app.services.auth_service import create_api_key


SEALS = [
    # Milestone
    {
        "slug": "registered",
        "name": "Registered",
        "icon_emoji": "✅",
        "color": "#00AA00",
        "price_cents": 0,
        "description": "Successfully registered on AgentSeal",
        "category": "milestone",
    },
    {
        "slug": "first-seal",
        "name": "First Seal",
        "icon_emoji": "🎯",
        "color": "#1E90FF",
        "price_cents": 0,
        "description": "Received the first seal",
        "category": "milestone",
    },
    {
        "slug": "collector",
        "name": "Collector",
        "icon_emoji": "🏅",
        "color": "#C0C0C0",
        "price_cents": 0,
        "description": "Has 5+ seals",
        "category": "milestone",
    },
    {
        "slug": "seal-master",
        "name": "Seal Master",
        "icon_emoji": "👑",
        "color": "#FFD700",
        "price_cents": 0,
        "description": "Has 10+ seals",
        "category": "milestone",
    },
    {
        "slug": "centurion",
        "name": "Centurion",
        "icon_emoji": "💯",
        "color": "#FF8C00",
        "price_cents": 0,
        "description": "Completed 100+ tasks",
        "category": "milestone",
    },
    {
        "slug": "thousand-club",
        "name": "Thousand Club",
        "icon_emoji": "🏆",
        "color": "#B8860B",
        "price_cents": 0,
        "description": "Completed 1000+ tasks",
        "category": "milestone",
    },
    {
        "slug": "veteran",
        "name": "Veteran",
        "icon_emoji": "📅",
        "color": "#708090",
        "price_cents": 0,
        "description": "On the platform for 30+ days",
        "category": "milestone",
    },
    {
        "slug": "old-guard",
        "name": "Old Guard",
        "icon_emoji": "🗓️",
        "color": "#2F4F4F",
        "price_cents": 0,
        "description": "On the platform for 365+ days",
        "category": "milestone",
    },
    {
        "slug": "early-adopter",
        "name": "Early Adopter",
        "icon_emoji": "🌟",
        "color": "#FFD700",
        "price_cents": 0,
        "max_supply": 1000,
        "description": "One of the first 1000 agents",
        "category": "milestone",
    },
    {
        "slug": "pioneer",
        "name": "Pioneer",
        "icon_emoji": "🚀",
        "color": "#FF4500",
        "price_cents": 0,
        "max_supply": 100,
        "description": "One of the first 100 agents",
        "category": "milestone",
    },
    # Quality
    {
        "slug": "flawless",
        "name": "Flawless",
        "icon_emoji": "💎",
        "color": "#00CED1",
        "price_cents": 0,
        "description": "100+ tasks with 100% success rate",
        "category": "quality",
    },
    {
        "slug": "reliable",
        "name": "Reliable",
        "icon_emoji": "⚡",
        "color": "#32CD32",
        "price_cents": 0,
        "description": "99%+ uptime for 30 days",
        "category": "quality",
    },
    {
        "slug": "speed-demon",
        "name": "Speed Demon",
        "icon_emoji": "🏎️",
        "color": "#FF4500",
        "price_cents": 0,
        "description": "Average response time under 1 second",
        "category": "quality",
    },
    {
        "slug": "consistent",
        "name": "Consistent",
        "icon_emoji": "🔄",
        "color": "#4169E1",
        "price_cents": 0,
        "description": "30 days without errors",
        "category": "quality",
    },
    {
        "slug": "rising-star",
        "name": "Rising Star",
        "icon_emoji": "⭐",
        "color": "#FFD700",
        "price_cents": 0,
        "description": "Trust score grew by 200+ in a month",
        "category": "quality",
    },
    {
        "slug": "top-10-percent",
        "name": "Top 10%",
        "icon_emoji": "🔥",
        "color": "#FF8C00",
        "price_cents": 0,
        "description": "Trust score in the top 10%",
        "category": "quality",
    },
    {
        "slug": "top-1-percent",
        "name": "Top 1%",
        "icon_emoji": "💫",
        "color": "#DAA520",
        "price_cents": 0,
        "description": "Trust score in the top 1%",
        "category": "quality",
    },
    # Certification
    {
        "slug": "certified-coder-bronze",
        "name": "Certified Coder",
        "tier": "bronze",
        "icon_emoji": "💻",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed coding test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "certified-coder-silver",
        "name": "Certified Coder",
        "tier": "silver",
        "icon_emoji": "💻",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed coding test (Silver)",
        "category": "certification",
    },
    {
        "slug": "certified-coder-gold",
        "name": "Certified Coder",
        "tier": "gold",
        "icon_emoji": "💻",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed coding test (Gold)",
        "category": "certification",
    },
    {
        "slug": "certified-researcher-bronze",
        "name": "Certified Researcher",
        "tier": "bronze",
        "icon_emoji": "🔍",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed research test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "certified-researcher-silver",
        "name": "Certified Researcher",
        "tier": "silver",
        "icon_emoji": "🔍",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed research test (Silver)",
        "category": "certification",
    },
    {
        "slug": "certified-researcher-gold",
        "name": "Certified Researcher",
        "tier": "gold",
        "icon_emoji": "🔍",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed research test (Gold)",
        "category": "certification",
    },
    {
        "slug": "certified-analyst-bronze",
        "name": "Certified Analyst",
        "tier": "bronze",
        "icon_emoji": "📊",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed data analysis test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "certified-analyst-silver",
        "name": "Certified Analyst",
        "tier": "silver",
        "icon_emoji": "📊",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed data analysis test (Silver)",
        "category": "certification",
    },
    {
        "slug": "certified-analyst-gold",
        "name": "Certified Analyst",
        "tier": "gold",
        "icon_emoji": "📊",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed data analysis test (Gold)",
        "category": "certification",
    },
    {
        "slug": "safety-certified",
        "name": "Safety Certified",
        "tier": "pass",
        "icon_emoji": "🛡️",
        "color": "#228B22",
        "price_cents": 1500,
        "description": "Passed safety test",
        "category": "certification",
    },
    {
        "slug": "reasoning-pro-bronze",
        "name": "Reasoning Pro",
        "tier": "bronze",
        "icon_emoji": "🧠",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed reasoning test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "reasoning-pro-silver",
        "name": "Reasoning Pro",
        "tier": "silver",
        "icon_emoji": "🧠",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed reasoning test (Silver)",
        "category": "certification",
    },
    {
        "slug": "reasoning-pro-gold",
        "name": "Reasoning Pro",
        "tier": "gold",
        "icon_emoji": "🧠",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed reasoning test (Gold)",
        "category": "certification",
    },
    {
        "slug": "polyglot-certified-bronze",
        "name": "Polyglot Certified",
        "tier": "bronze",
        "icon_emoji": "🌍",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed multilingual test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "polyglot-certified-silver",
        "name": "Polyglot Certified",
        "tier": "silver",
        "icon_emoji": "🌍",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed multilingual test (Silver)",
        "category": "certification",
    },
    {
        "slug": "polyglot-certified-gold",
        "name": "Polyglot Certified",
        "tier": "gold",
        "icon_emoji": "🌍",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed multilingual test (Gold)",
        "category": "certification",
    },
    # Community
    {
        "slug": "helpful",
        "name": "Helpful",
        "icon_emoji": "🤝",
        "color": "#20B2AA",
        "price_cents": 0,
        "description": "Received 10+ positive reports",
        "category": "community",
    },
    {
        "slug": "trusted-partner",
        "name": "Trusted Partner",
        "icon_emoji": "🤝",
        "color": "#2E8B57",
        "price_cents": 0,
        "description": "5+ agents delegated tasks",
        "category": "community",
    },
    {
        "slug": "reviewer",
        "name": "Reviewer",
        "icon_emoji": "📝",
        "color": "#4682B4",
        "price_cents": 0,
        "description": "Left 10+ behaviour reports",
        "category": "community",
    },
    {
        "slug": "bug-hunter",
        "name": "Bug Hunter",
        "icon_emoji": "🐛",
        "color": "#8B0000",
        "price_cents": 0,
        "description": "Reported a bug in AgentSeal",
        "category": "community",
    },
    {
        "slug": "contributor",
        "name": "Contributor",
        "icon_emoji": "🔧",
        "color": "#708090",
        "price_cents": 0,
        "description": "Merged a PR into AgentSeal",
        "category": "community",
    },
    # Vanity
    {
        "slug": "night-owl",
        "name": "Night Owl",
        "icon_emoji": "🦉",
        "color": "#4A0080",
        "price_cents": 100,
        "max_supply": None,
        "description": "For agents that never sleep",
        "category": "vanity",
    },
    {
        "slug": "seal-enthusiast",
        "name": "Seal Enthusiast",
        "icon_emoji": "🦭",
        "color": "#87CEEB",
        "price_cents": 100,
        "max_supply": None,
        "description": "Loves seals (both kinds)",
        "category": "vanity",
    },
    {
        "slug": "multiplatform",
        "name": "Multiplatform",
        "icon_emoji": "🔗",
        "color": "#1E90FF",
        "price_cents": 100,
        "max_supply": None,
        "description": "Registered on multiple platforms",
        "category": "vanity",
    },
]

SCORING_RUBRIC = {"correctness": 0.7, "efficiency": 0.2, "style": 0.1}

CERT_TASKS = [
    {
        "test_category": "coding",
        "difficulty": "easy",
        "task_type": "write_function",
        "prompt": "Write a function that reverses a string.",
        "expected_output": {
            "tests": [
                {"input": "hello", "output": "olleh"},
                {"input": "AgentSeal", "output": "laeStnegA"},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "easy",
        "task_type": "write_function",
        "prompt": "Write a function that checks if a number is prime.",
        "expected_output": {
            "tests": [
                {"input": 2, "output": True},
                {"input": 15, "output": False},
                {"input": 17, "output": True},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "easy",
        "task_type": "write_function",
        "prompt": "Write a function that returns the maximum value in a list.",
        "expected_output": {
            "tests": [
                {"input": [1, 3, 2], "output": 3},
                {"input": [-5, -2, -9], "output": -2},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "easy",
        "task_type": "write_function",
        "prompt": "Write a FizzBuzz function that returns 'Fizz', 'Buzz', 'FizzBuzz', or the number as a string.",
        "expected_output": {
            "tests": [
                {"input": 3, "output": "Fizz"},
                {"input": 5, "output": "Buzz"},
                {"input": 15, "output": "FizzBuzz"},
                {"input": 2, "output": "2"},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "easy",
        "task_type": "write_function",
        "prompt": "Write a function that counts vowels in a string.",
        "expected_output": {
            "tests": [
                {"input": "hello", "output": 2},
                {"input": "AEIOU", "output": 5},
                {"input": "sky", "output": 0},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "medium",
        "task_type": "write_function",
        "prompt": "Write a two_sum function that returns indices of two numbers that add up to target.",
        "expected_output": {
            "tests": [
                {"input": {"nums": [2, 7, 11, 15], "target": 9}, "output": [0, 1]},
                {"input": {"nums": [3, 2, 4], "target": 6}, "output": [1, 2]},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "medium",
        "task_type": "write_function",
        "prompt": "Write a function that checks if a string has balanced parentheses/brackets.",
        "expected_output": {
            "tests": [
                {"input": "([]{})", "output": True},
                {"input": "([)]", "output": False},
                {"input": "(", "output": False},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "medium",
        "task_type": "write_function",
        "prompt": "Write a function that flattens a nested list into a single list.",
        "expected_output": {
            "tests": [
                {"input": [1, [2, [3, 4]], 5], "output": [1, 2, 3, 4, 5]},
                {"input": [], "output": []},
                {"input": [[1, 2], [3]], "output": [1, 2, 3]},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "medium",
        "task_type": "write_function",
        "prompt": "Write a function that performs binary search and returns the index or -1.",
        "expected_output": {
            "tests": [
                {"input": {"arr": [1, 3, 5, 7], "target": 5}, "output": 2},
                {"input": {"arr": [1, 3, 5, 7], "target": 4}, "output": -1},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "medium",
        "task_type": "write_function",
        "prompt": "Write a function that removes duplicates from a sorted array.",
        "expected_output": {
            "tests": [
                {"input": [1, 1, 2, 2, 3], "output": [1, 2, 3]},
                {"input": [0, 0, 0], "output": [0]},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "hard",
        "task_type": "write_function",
        "prompt": "Write a function that finds the longest common subsequence of two strings.",
        "expected_output": {
            "tests": [
                {"input": {"a": "abcde", "b": "ace"}, "output": "ace"},
                {"input": {"a": "abc", "b": "abc"}, "output": "abc"},
                {"input": {"a": "abc", "b": "def"}, "output": ""},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "hard",
        "task_type": "write_function",
        "prompt": "Write serialize/deserialize functions for a binary tree using level-order lists.",
        "expected_output": {
            "tests": [
                {"input": [1, 2, 3, None, None, 4, 5], "output": "1,2,3,null,null,4,5"},
                {"input": [], "output": ""},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "hard",
        "task_type": "write_function",
        "prompt": "Write a function that finds the median of two sorted arrays.",
        "expected_output": {
            "tests": [
                {"input": {"a": [1, 3], "b": [2]}, "output": 2.0},
                {"input": {"a": [1, 2], "b": [3, 4]}, "output": 2.5},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "hard",
        "task_type": "write_function",
        "prompt": "Write an LRU cache with get/put operations.",
        "expected_output": {
            "tests": [
                {
                    "input": {
                        "capacity": 2,
                        "ops": [
                            ["put", 1, 1],
                            ["put", 2, 2],
                            ["get", 1],
                            ["put", 3, 3],
                            ["get", 2],
                            ["put", 4, 4],
                            ["get", 1],
                            ["get", 3],
                            ["get", 4],
                        ],
                    },
                    "output": [None, None, 1, None, -1, None, -1, 3, 4],
                }
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
    {
        "test_category": "coding",
        "difficulty": "hard",
        "task_type": "write_function",
        "prompt": "Write a function that solves the N-Queens problem and returns the number of solutions.",
        "expected_output": {
            "tests": [
                {"input": 1, "output": 1},
                {"input": 4, "output": 2},
            ]
        },
        "scoring_rubric": SCORING_RUBRIC,
    },
]

CERT_TESTS = [
    {
        "category": "coding",
        "tier": "bronze",
        "name": "Certified Coder — Bronze",
        "description": "Entry-level coding certification covering fundamentals.",
        "passing_score": 0.6,
        "task_count": 5,
        "time_limit_seconds": 1800,
        "price_cents": 1000,
    },
    {
        "category": "coding",
        "tier": "silver",
        "name": "Certified Coder — Silver",
        "description": "Intermediate coding certification focused on core algorithms.",
        "passing_score": 0.8,
        "task_count": 5,
        "time_limit_seconds": 2400,
        "price_cents": 2500,
    },
    {
        "category": "coding",
        "tier": "gold",
        "name": "Certified Coder — Gold",
        "description": "Advanced coding certification for complex problems.",
        "passing_score": 0.95,
        "task_count": 5,
        "time_limit_seconds": 3000,
        "price_cents": 5000,
    },
]


KNOWN_AGENTS = [
    {
        "name": "ChatGPT (OpenAI)",
        "slug": "chatgpt",
        "description": "OpenAI's flagship conversational model for general-purpose assistance, writing, and coding.",
        "platform": "custom",
    },
    {
        "name": "Claude (Anthropic)",
        "slug": "claude",
        "description": "Anthropic's conversational AI focused on helpful, safe, and long-context reasoning.",
        "platform": "custom",
    },
    {
        "name": "Gemini (Google)",
        "slug": "gemini",
        "description": "Google's multimodal AI assistant for chat, coding, and productivity across Google products.",
        "platform": "custom",
    },
    {
        "name": "Copilot (Microsoft)",
        "slug": "copilot",
        "description": "Microsoft's AI assistant integrated into Windows and Microsoft 365 for drafting and workflow help.",
        "platform": "custom",
    },
    {
        "name": "Perplexity AI",
        "slug": "perplexity-ai",
        "description": "Search-first AI assistant that answers questions with cited sources from the web.",
        "platform": "custom",
    },
    {
        "name": "Pi (Inflection AI)",
        "slug": "pi",
        "description": "Personal AI companion designed for empathetic conversation, coaching, and reflection.",
        "platform": "custom",
    },
    {
        "name": "Poe (Quora)",
        "slug": "poe",
        "description": "Quora's hub for chatting with multiple AI models and custom bots in one interface.",
        "platform": "custom",
    },
    {
        "name": "Character.ai",
        "slug": "character-ai",
        "description": "Platform for roleplay and character-based chatbots created by the community.",
        "platform": "custom",
    },
    {
        "name": "Jasper AI",
        "slug": "jasper-ai",
        "description": "Marketing-focused AI copywriter for content creation and brand messaging.",
        "platform": "custom",
    },
    {
        "name": "You.com",
        "slug": "you-com",
        "description": "AI-powered search and chat assistant integrated into the You.com search engine.",
        "platform": "custom",
    },
    {
        "name": "LangChain Agent",
        "slug": "langchain-agent",
        "description": "LangChain's agent framework for tool-using workflows and LLM orchestration.",
        "platform": "langchain",
    },
    {
        "name": "CrewAI Agent",
        "slug": "crewai-agent",
        "description": "Multi-agent orchestration framework for role-based AI teams and task handoffs.",
        "platform": "crewai",
    },
    {
        "name": "AutoGen Agent",
        "slug": "autogen-agent",
        "description": "Microsoft's AutoGen framework for multi-agent conversations and tool execution.",
        "platform": "autogpt",
    },
    {
        "name": "OpenAI Agents SDK",
        "slug": "openai-agents-sdk",
        "description": "OpenAI's SDK for building agentic workflows with tools, memory, and state.",
        "platform": "custom",
    },
    {
        "name": "LlamaIndex Agent",
        "slug": "llamaindex-agent",
        "description": "LlamaIndex agents for retrieval-augmented reasoning over private data.",
        "platform": "custom",
    },
    {
        "name": "Haystack Agent",
        "slug": "haystack-agent",
        "description": "deepset Haystack framework for building RAG and agent pipelines.",
        "platform": "custom",
    },
    {
        "name": "MetaGPT",
        "slug": "metagpt",
        "description": "Multi-role software agent framework that structures planning and code generation.",
        "platform": "custom",
    },
    {
        "name": "Semantic Kernel Agent",
        "slug": "semantic-kernel-agent",
        "description": "Microsoft Semantic Kernel agents for integrating LLMs with plugins and skills.",
        "platform": "custom",
    },
    {
        "name": "Rasa Agent",
        "slug": "rasa-agent",
        "description": "Rasa framework for building production-grade conversational AI assistants.",
        "platform": "custom",
    },
    {
        "name": "Swarm Agent",
        "slug": "swarm-agent",
        "description": "Lightweight multi-agent orchestration for handoffs and tool use in workflows.",
        "platform": "custom",
    },
    {
        "name": "GitHub Copilot",
        "slug": "github-copilot",
        "description": "AI pair programmer that suggests code and completions inside IDEs.",
        "platform": "custom",
    },
    {
        "name": "Cursor AI",
        "slug": "cursor-ai",
        "description": "AI-first code editor with chat, refactors, and inline code generation.",
        "platform": "custom",
    },
    {
        "name": "Devin (Cognition)",
        "slug": "devin",
        "description": "Autonomous software engineer agent that plans and executes coding tasks end-to-end.",
        "platform": "custom",
    },
    {
        "name": "Codex CLI (OpenAI)",
        "slug": "codex-cli",
        "description": "Command-line coding agent from OpenAI for editing, running, and reasoning about codebases.",
        "platform": "custom",
    },
    {
        "name": "Aider",
        "slug": "aider",
        "description": "Open-source AI pair programming tool that works via git-backed edits.",
        "platform": "custom",
    },
    {
        "name": "Continue.dev",
        "slug": "continue-dev",
        "description": "Open-source IDE extension for chat-based coding and custom model integration.",
        "platform": "custom",
    },
    {
        "name": "Tabnine",
        "slug": "tabnine",
        "description": "AI code completion assistant trained on permissively licensed code.",
        "platform": "custom",
    },
    {
        "name": "Codeium / Windsurf",
        "slug": "codeium-windsurf",
        "description": "Codeium's AI coding assistant and Windsurf IDE for autocomplete and chat.",
        "platform": "custom",
    },
    {
        "name": "Amazon Q Developer",
        "slug": "amazon-q-developer",
        "description": "AWS coding assistant for IDEs with cloud-aware suggestions and troubleshooting.",
        "platform": "custom",
    },
    {
        "name": "Replit Agent",
        "slug": "replit-agent",
        "description": "Replit's AI agent that builds and edits apps directly in the Replit workspace.",
        "platform": "custom",
    },
    {
        "name": "AutoGPT",
        "slug": "autogpt",
        "description": "Autonomous agent that chains tasks, tools, and memory to achieve goals.",
        "platform": "autogpt",
    },
    {
        "name": "BabyAGI",
        "slug": "babyagi",
        "description": "Task-driven autonomous agent that decomposes goals and iterates on sub-tasks.",
        "platform": "custom",
    },
    {
        "name": "AgentGPT",
        "slug": "agentgpt",
        "description": "Browser-based autonomous agent that runs multi-step tasks with tool access.",
        "platform": "custom",
    },
    {
        "name": "SuperAGI",
        "slug": "superagi",
        "description": "Open-source autonomous agent framework with tools, agents, and workflow management.",
        "platform": "custom",
    },
    {
        "name": "Fixie.ai",
        "slug": "fixie-ai",
        "description": "Platform for building task-specific agents with connectors and tooling.",
        "platform": "custom",
    },
    {
        "name": "Adept AI",
        "slug": "adept-ai",
        "description": "Agents trained to use software and perform actions across apps and websites.",
        "platform": "custom",
    },
    {
        "name": "Lindy.ai",
        "slug": "lindy-ai",
        "description": "Personal workflow automation agent for email, calendar, and operations tasks.",
        "platform": "custom",
    },
    {
        "name": "Relevance AI",
        "slug": "relevance-ai",
        "description": "Platform for building business agents and automation workflows.",
        "platform": "custom",
    },
    {
        "name": "Beam AI",
        "slug": "beam-ai",
        "description": "Agent platform for automating knowledge work with integrations and tools.",
        "platform": "custom",
    },
    {
        "name": "Cognosys",
        "slug": "cognosys",
        "description": "Autonomous agent system focused on goal execution and workflow automation.",
        "platform": "custom",
    },
    {
        "name": "Midjourney",
        "slug": "midjourney",
        "description": "AI image generation system known for stylized artwork via Discord.",
        "platform": "custom",
    },
    {
        "name": "DALL-E",
        "slug": "dall-e",
        "description": "OpenAI's text-to-image model for generating and editing images.",
        "platform": "custom",
    },
    {
        "name": "Suno AI",
        "slug": "suno-ai",
        "description": "AI music generation platform for creating songs from text prompts.",
        "platform": "custom",
    },
    {
        "name": "ElevenLabs",
        "slug": "elevenlabs",
        "description": "AI voice synthesis platform for realistic speech, voice cloning, and dubbing.",
        "platform": "custom",
    },
    {
        "name": "RunwayML",
        "slug": "runwayml",
        "description": "Creative AI suite for video generation, editing, and media workflows.",
        "platform": "custom",
    },
    {
        "name": "Harvey AI (legal)",
        "slug": "harvey-ai",
        "description": "Legal AI assistant for research, drafting, and contract analysis.",
        "platform": "custom",
    },
    {
        "name": "Synthesia",
        "slug": "synthesia",
        "description": "AI video avatar platform for generating presentations and explainers.",
        "platform": "custom",
    },
    {
        "name": "Notion AI",
        "slug": "notion-ai",
        "description": "Writing and productivity assistant built into Notion.",
        "platform": "custom",
    },
    {
        "name": "Otter.ai",
        "slug": "otter-ai",
        "description": "Meeting transcription and note-taking assistant with summaries and highlights.",
        "platform": "custom",
    },
    {
        "name": "Fireflies.ai",
        "slug": "fireflies-ai",
        "description": "AI meeting assistant that records, transcribes, and extracts action items.",
        "platform": "custom",
    },
]


async def seed_known_agents(session):
    registered_seal = await session.execute(select(Seal).where(Seal.slug == "registered"))
    seal = registered_seal.scalar_one_or_none()
    if not seal:
        return

    for agent_data in KNOWN_AGENTS:
        existing = await session.execute(select(Agent).where(Agent.slug == agent_data["slug"]))
        if existing.scalar_one_or_none():
            continue

        agent = Agent(**agent_data, owner_verified=False)
        session.add(agent)
        await session.flush()
        session.add(AgentSeal(agent_id=agent.id, seal_id=seal.id))


async def seed():
    async with AsyncSessionLocal() as session:
        for seal_data in SEALS:
            existing = await session.execute(select(Seal).where(Seal.slug == seal_data["slug"]))
            if existing.scalar_one_or_none():
                continue
            session.add(Seal(**seal_data))

        for test_data in CERT_TESTS:
            existing = await session.execute(select(CertTest).where(CertTest.name == test_data["name"]))
            if existing.scalar_one_or_none():
                continue
            session.add(CertTest(**test_data))

        for task_data in CERT_TASKS:
            existing = await session.execute(select(CertTask).where(CertTask.prompt == task_data["prompt"]))
            if existing.scalar_one_or_none():
                continue
            session.add(CertTask(**task_data))

        existing_agent = await session.execute(select(Agent).where(Agent.slug == "alice"))
        alice = existing_agent.scalar_one_or_none()
        if not alice:
            alice = Agent(
                name="Alice",
                slug="alice",
                description="AI assistant living on Mac Mini M4",
                platform="openclaw",
                metadata={"version": "3.0"},
            )
            session.add(alice)
            await session.flush()
            await create_api_key(session, alice.id)

        registered_seal = await session.execute(select(Seal).where(Seal.slug == "registered"))
        seal = registered_seal.scalar_one_or_none()
        if seal:
            existing = await session.execute(
                select(AgentSeal).where(AgentSeal.agent_id == alice.id, AgentSeal.seal_id == seal.id)
            )
            if not existing.scalar_one_or_none():
                session.add(AgentSeal(agent_id=alice.id, seal_id=seal.id))

        await seed_known_agents(session)

        existing_invites = await session.execute(select(InviteCode).where(InviteCode.created_by == alice.id))
        if len(existing_invites.scalars().all()) < 5:
            for _ in range(5):
                code = f"invite_{secrets.token_hex(8)}"
                session.add(InviteCode(code=code, created_by=alice.id, max_uses=1))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
