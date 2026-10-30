# Miku 表情包

**简体中文** | [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.4.0-blue)](https://github.com/AstrBotDevs/AstrBot)

[![九种情绪表情总览](https://raw.githubusercontent.com/hqcx123/magical-miku-bot/main/demo/sticker_preview.png)](https://github.com/hqcx123/magical-miku-bot)

给 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 用的表情包插件：让 bot 在回复里按情绪发本地表情图。

> **非官方同人项目**。初音未来（Hatsune Miku）为 Crypton Future Media 的角色，本插件与其无任何关联，仅供学习与个人非商业使用。

## 工作方式

LLM 在回复末尾写一个标记，插件把标记换成图片：

```
LLM 输出： 诶嘿，被夸了呢[表情:害羞]
实际发送： 诶嘿，被夸了呢 + （一张害羞表情图）
```

可用标记：`[表情:开心]` `[表情:害羞]` `[表情:得意]` `[表情:生气]` `[表情:委屈]` `[表情:吃瓜]` `[表情:晚安]` `[表情:爱心]` `[表情:惊讶]`

一条消息最多一个标记，放在最后。文件夹为空时静默跳过。

## 安装

1. 把插件目录放到 AstrBot 的 `data/plugins/` 下（或在插件市场一键安装）
2. 准备表情图，按情绪放进 `stickers/<情绪>/`
3. 重载插件

**本插件不附带图片**（版权原因）。官方贴纸、游戏素材属于各自发行商，请勿分发。建议使用自己绘制或 AI 生成的原创图。

## 自动收集（可选）

在指定群里自动收集别人发的图，用视觉模型判断情绪后入库：

1. 把 `main.py` 里的 `ALLOWED_GROUPS` 改成你的群号
2. 确认 AstrBot 的默认模型**支持图片输入**（视觉模型）
3. 限制：每天最多 30 张、单张 ≤ 2MB、按 MD5 去重

图片会上传给模型做分类，仅在你指定的群生效。不需要这功能就不用改。

收集到的图片、计数状态统一存放在 AstrBot 的 `data/plugin_data/miku_sticker/` 目录下，不会写进插件目录，升级或迁移插件时可随数据目录一起备份。

## 依赖

- AstrBot >= 4.4.0
- 自动收集功能需要支持视觉的模型

## 许可

[MIT](LICENSE)

## 交流群

使用中遇到问题、想提建议，或者只是想聊聊 Miku，都欢迎进群：

- QQ 群号：**1005773100**（在 QQ 里直接搜索群号即可加入；群二维码 7 天过期，因此不在此处放图）

不方便加群的话，也可以直接在 GitHub [Issues](https://github.com/hqcx123/miku-sticker/issues) 反馈，方便其他人搜到同样的问题。
