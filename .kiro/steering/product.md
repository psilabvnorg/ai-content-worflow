# Product Overview

TikTok News Video Generator - An automated pipeline that converts Vietnamese news articles into TikTok-ready vertical videos (9:16 aspect ratio).

## Core Functionality

- Crawls news articles from Vietnamese news sites (VnExpress, Tien Phong)
- Summarizes content using Qwen3:4B via Ollama (chunked processing for long articles)
- Generates Vietnamese voice-over using VieNeu-TTS (GPU-accelerated)
- Creates auto-subtitles with Whisper + AI alignment
- Composes final video with pan effects, blurred backgrounds, and PowerPoint intro templates
- Outputs TikTok-ready 1080x1920 MP4 (~60-90 seconds)

## Target Users

Vietnamese content creators who want to automate news video production for TikTok.

## Key Features

- Multiple Vietnamese voice options (male/female, Northern/Southern accents)
- PowerPoint-based customizable intro templates
- Background music with typing SFX during intro
- B-roll video support
- Summary export in text and JSON formats
