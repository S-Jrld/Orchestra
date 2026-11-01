# SKILL ADAPTER: AGENT-REACH

> Unified internet, social media, and multimedia reach layer giving agents access to Twitter/X, Reddit, YouTube, GitHub, Bilibili, and web search without paid API keys.

## Overview
- **Trigger**: External fact checking, community sentiment, bug investigation via GitHub/Reddit/Twitter, video transcript extraction, or real-time web search.
- **Pipeline Stage**: `Discovery / Research`
- **Primary Agent**: `@researcher`
- **CLI**: `agent-reach`

## Supported Channels
- **Web**: Jina Reader markdown extraction
- **Video**: YouTube subtitles/metadata (`yt-dlp`), Bilibili
- **Code & Tech**: GitHub search (`gh`), V2EX, RSS
- **Social**: Twitter/X, Reddit, LinkedIn, XiaoHongShu

## Commands
- `agent-reach doctor`: Check channel backend availability
- `agent-reach setup`: Initialize default channels
- `agent-reach configure`: Manage local credentials/cookies
