---
name: agent_reach
description: >-
  Use for external internet intelligence, social media scraping, community thread analysis,
  video transcript extraction, and web search across 13+ platforms without paid APIs.
---

# /agent-reach (External Intelligence & Reach Layer)

> Unified internet, social media, and multimedia reach layer giving agents access to Twitter/X, Reddit, YouTube, GitHub, Bilibili, and web search without paid API keys.

## Overview
- **Trigger**: External fact checking, community sentiment, bug investigation via GitHub/Reddit/Twitter, video transcript extraction, or real-time web search.
- **Pipeline Stage**: `Discovery / Research`
- **Primary Agent**: `@researcher`
- **Binary / CLI**: `agent-reach`

## Supported Channels
1. **Default (Zero Setup / Public)**:
   - **Web Reader**: URL reading and markdown extraction via Jina Reader.
   - **YouTube**: Subtitle/transcript fetching and metadata parsing via `yt-dlp`.
   - **GitHub**: Repository, PR, and issue search via `gh` CLI.
   - **RSS Feeds**: Technical blogs and publication feeds.
   - **V2EX & Exa**: Technical forums and semantic web search.
2. **Authenticated / Cookies (Optional)**:
   - **Social**: Twitter/X, Reddit, LinkedIn.
   - **Video/Media**: Bilibili, Douyin, XiaoHongShu, Xiaoyuzhou (podcasts).

## Operational Workflow

```
1. Pre-Flight Check (agent-reach doctor --json)
   Verify which channel backends are active and ready.
       │
       ▼
2. Scoped Query Dispatch
   Execute targeted channel queries; retrieve structured JSON outputs.
       │
       ▼
3. Token-Dense Extraction (Caveman Filtering)
   Strip decorative fluff, HTML boilerplate, and irrelevant comments.
   Retain verbatim URLs, code snippets, timestamps, and quotes.
       │
       ▼
4. Source Attribution
   Deliver findings to @orchestrator with explicit channel and author attribution.
```

## CLI Reference
- `agent-reach doctor`: Inspect active backends, channel status, and environment health.
- `agent-reach setup`: Configure default channels and dependencies.
- `agent-reach configure`: Manage local browser cookies or credentials in `~/.agent-reach/`.
