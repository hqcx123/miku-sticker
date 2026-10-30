import asyncio
import base64
import hashlib
import json
import os
import random
import re
import urllib.parse
from datetime import date
from pathlib import Path

import aiohttp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, StarTools, register

MARK = re.compile(r"\[表情[:：]\s*([^\[\]:：\s]+)\s*\]")

EMOTIONS = ["开心", "害羞", "得意", "生气", "委屈", "吃瓜", "晚安", "爱心", "惊讶"]

# 只在这些群里收集（用户已授权：图片会发给 DeepSeek 做情绪分类）
ALLOWED_GROUPS = {"123456789"}  # 改成你自己的群号，可写多个

DAILY_LIMIT = 30             # 每天最多收集张数
MAX_BYTES = 2 * 1024 * 1024  # 单张上限 2MB

CLASSIFY_PROMPT = (
    "这是 QQ 群里的一张图片。请判断它是否适合作为「初音未来」表情包使用"
    "（要求：初音未来、二次元角色、或风格可爱的表情图；真人照片、聊天截图、"
    "证件、文字图、商品图一律不适合）。\n"
    "如果是表情包，再从这些情绪里选出最贴切的一个："
    + "、".join(EMOTIONS)
    + "。\n"
    "只输出这一个词；如果不适合，只输出 none。不要解释。"
)


@register(
    "miku_sticker",
    "qq:2757001649(有趣的生命)",
    "表情发送 + 指定群自动收集表情并按情绪分类",
    "1.0.2",
)
class MikuSticker(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 自带素材目录（只读，用户手动放图）
        self.assets_dir = Path(__file__).parent / "stickers"
        # 持久化数据统一放到 data/plugin_data/miku_sticker/
        self.data_dir = self._resolve_data_dir(context)
        self.store_dir = self.data_dir / "stickers"
        self.collected = self.data_dir / "collected"
        self.state_file = self.data_dir / "state.json"

    @staticmethod
    def _resolve_data_dir(context: Context) -> Path:
        """获取插件数据目录，兼容不同版本的 AstrBot API。"""
        getter = getattr(context, "get_plugin_data_dir", None)
        if callable(getter):
            try:
                return Path(getter("miku_sticker"))
            except TypeError:
                return Path(getter())
        return Path(StarTools.get_data_dir("miku_sticker"))

    # ---------- 发送：识别 [表情:xxx] ----------
    @filter.on_decorating_result(priority=100)
    async def inject_sticker(self, event: AstrMessageEvent):
        result = event.get_result()
        if result is None or not result.chain:
            return
        chain = result.chain
        text = "".join(getattr(c, "text", "") or "" for c in chain)
        m = MARK.search(text)
        if not m:
            return
        for c in chain:
            t = getattr(c, "text", None)
            if t:
                c.text = MARK.sub("", t)
        emo = m.group(1)
        pics = []
        for folder in (self.assets_dir / emo, self.store_dir / emo):
            if folder.is_dir():
                pics.extend(
                    p
                    for p in folder.iterdir()
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp")
                )
        if not pics:
            return
        chain.append(Image.fromFileSystem(str(random.choice(pics))))

    # ---------- 收集：仅限白名单群 ----------
    @filter.event_message_type(filter.EventMessageType.ALL, priority=200)
    async def collect_sticker(self, event: AstrMessageEvent):
        try:
            comps = getattr(event.message_obj, "message", None) or []
            gid = ""
            try:
                gid = str(event.get_group_id() or "")
            except Exception:
                gid = ""
            self._debug(f"收到消息 gid={gid!r} 组件={[type(c).__name__ for c in comps]}")
            if gid not in ALLOWED_GROUPS:
                return

            items = []
            for comp in comps:
                if not isinstance(comp, Image):
                    continue
                raw = getattr(comp, "url", "") or getattr(comp, "file", "")
                if not isinstance(raw, str) or not raw:
                    continue
                self._debug(f"  图片地址={raw[:90]!r}")
                if raw.startswith("http"):
                    items.append(("http", raw))
                else:
                    path = self._local_path(raw)
                    if path:
                        items.append(("file", path))
                    else:
                        self._debug(f"  跳过：本地文件不可读 {raw[:80]}")
            if not items:
                self._debug("  没有可用图片")
                return
            asyncio.create_task(self._save_all(items))
        except Exception as e:  # 收集失败绝不能影响正常聊天
            self._debug(f"异常 {e}")
            logger.debug(f"[miku_sticker] 收集调度失败: {e}")

    def _local_path(self, raw):
        """把 Image 的 url/file 字段还原成本地绝对路径。"""
        candidates = []
        if raw.startswith("file://"):
            p = raw[7:]
            if p.startswith("/") and len(p) > 2 and p[2] == ":":
                p = p[1:]
            candidates.append(urllib.parse.unquote(p))
        else:
            candidates.append(raw)
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def _debug(self, msg):
        logger.debug(f"[miku_sticker] {msg}")

    async def _save_all(self, items):
        for kind, val in items:
            try:
                await self._save_one(kind, val)
            except Exception as e:
                self._debug(f"  保存失败 {e}")

    # ---------- 内部 ----------
    def _read_state(self):
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    async def _save_one(self, kind, val):
        state = self._read_state()
        today = str(date.today())
        if state.get(today, 0) >= DAILY_LIMIT:
            return

        if kind == "http":
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.get(val) as resp:
                    if resp.status != 200:
                        self._debug(f"  下载失败 HTTP {resp.status}")
                        return
                    data = await resp.read()
        else:
            try:
                data = Path(val).read_bytes()
            except Exception as e:
                self._debug(f"  读本地文件失败 {e}")
                return

        if not data or len(data) > MAX_BYTES or len(data) < 1200:
            self._debug(f"  跳过：大小不合适 {len(data) if data else 0}B")
            return

        digest = hashlib.md5(data).hexdigest()[:12]
        if any(self.store_dir.rglob(f"{digest}.*")) or any(
            self.collected.rglob(f"{digest}.*")
        ):
            self._debug("  跳过：已收集过")
            return  # 已收集过

        emotion = await self._classify(kind, val, data)
        dst = (self.store_dir / emotion) if emotion in EMOTIONS else self.collected
        dst.mkdir(parents=True, exist_ok=True)

        if data[:6] in (b"GIF87a", b"GIF89a"):
            ext = ".gif"
        elif data[:3] == b"\xff\xd8\xff":
            ext = ".jpg"
        elif data[:4] == b"RIFF":
            ext = ".webp"
        else:
            ext = ".png"
        (dst / f"{digest}{ext}").write_bytes(data)

        state[today] = state.get(today, 0) + 1
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )
        self._debug(f"  已保存 -> {dst.name}/{digest}{ext} 分类={emotion}")
        logger.info(
            f"[miku_sticker] 收集 1 张 -> {dst.name}/ ({state[today]}/{DAILY_LIMIT})"
        )

    def _mime(self, data):
        if data[:4] == b"RIFF":
            return "image/webp"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        if data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        return "image/png"

    async def _classify(self, kind, val, data):
        try:
            provider = self.context.get_using_provider()
            if provider is None:
                self._debug("  分类跳过：没有可用 provider")
                return "none"
            if kind == "http":
                ref = val
            else:
                b64 = base64.b64encode(data).decode()
                ref = f"data:{self._mime(data)};base64,{b64}"
            resp = await provider.text_chat(prompt=CLASSIFY_PROMPT, image_urls=[ref])
            text = (resp.completion_text or "").strip()
            self._debug(f"  模型回答: {text[:60]!r}")
            for e in EMOTIONS:
                if e in text:
                    return e
            return "none"
        except Exception as e:
            self._debug(f"  分类失败: {e}")
            logger.debug(f"[miku_sticker] 分类失败: {e}")
            return "none"

