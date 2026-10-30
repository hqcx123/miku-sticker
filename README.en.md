# Miku Sticker

**English** | [简体中文](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.4.0-blue)](https://github.com/AstrBotDevs/AstrBot)

![Nine emotion stickers](https://raw.githubusercontent.com/hqcx123/magical-miku-bot/main/demo/sticker_preview.png)

An [AstrBot](https://github.com/AstrBotDevs/AstrBot) plugin that lets your bot send local stickers based on emotion tags in its reply.

> **Unofficial fan project.** Hatsune Miku is a character of Crypton Future Media. Not affiliated with Crypton or any official party. For personal, non-commercial use only.

## How it works

The LLM writes a tag at the end of its reply; the plugin replaces it with an image:

```
LLM output:  Hehe, that's a nice compliment[表情:害羞]
Sent:        Hehe, that's a nice compliment + (a shy sticker)
```

Available tags: `[表情:开心]` happy, `[表情:害羞]` shy, `[表情:得意]` smug, `[表情:生气]` angry, `[表情:委屈]` aggrieved, `[表情:吃瓜]` popcorn, `[表情:晚安]` goodnight, `[表情:爱心]` love, `[表情:惊讶]` surprised.

One tag per message, placed last. If the folder is empty, the tag is silently dropped.

## Install

1. Place this directory under AstrBot's `data/plugins/` (or install from the plugin marketplace)
2. Put your own images into `stickers/<emotion>/`
3. Reload plugins

**No sticker images are bundled** (copyright). Official stickers and game assets belong to their publishers and must not be redistributed. Use your own artwork or AI-generated images.

## Optional: auto-collection

Collect images posted in specified groups and classify them with a vision model:

1. Set `ALLOWED_GROUPS` in `main.py` to your group IDs
2. Make sure the default model accepts image input
3. Limits: 30 images/day, <= 2MB each, MD5 deduplication

Images are uploaded to the model for classification, only in the groups you specify.

Collected images and the daily counter are stored under AstrBot's `data/plugin_data/miku_sticker/`, not inside the plugin directory, so they survive plugin upgrades and can be backed up together with your data folder.

## Requirements

- AstrBot >= 4.4.0
- Auto-collection requires a vision-capable model

## License

[MIT](LICENSE)
