from __future__ import annotations

from dataclasses import dataclass

from astrbot.api.event import AstrMessageEvent

from ..config import get_global_config, Config
from .base import CmdHandler, HandlerContext
from ..utils.lifecycle import on_initialize
from astrbot.api import logger

config: Config | None = None
@on_initialize()
def initialize_sekai():
    global config
    config = get_global_config()

@dataclass
class _CommandMatch:
    prefix_arg: str
    matched_trigger: str
    args: str


class SekaiCmdHandler(CmdHandler):
    """支持sekai命令处理器。"""

    def __init__(
        self,
        commands: list[str],
        prefix_args: list[str] | None = None,
        regions: list[str] | None = None,
    ):
        print(f"注册 sekai 指令 {commands[0]}")
        self.prefix_args = self._normalize_prefix_args(prefix_args or [""])
        self.limit_regions = [str(r).lower().strip() for r in (regions or []) if str(r).strip()]
        super().__init__(commands)

    @classmethod
    def _normalize_prefix_args(cls, prefix_args: list[str]) -> list[str]:
        normalized = []
        for item in prefix_args:
            value = cls._normalize_spaces(item).replace(" ", "")
            if value.startswith("/"):
                value = value[1:]
            normalized.append(value)
        normalized = list(dict.fromkeys(normalized))
        if "" not in normalized:
            normalized.append("")
        normalized.sort(key=len, reverse=True)
        return normalized

    def _get_regions(self) -> list[str]:
        allow_regions = [str(x).lower().strip() for x in config.sekairanking.allow_regions if str(x).strip()]
        if self.limit_regions:
            allow_regions = [r for r in allow_regions if r in self.limit_regions]
        allow_regions = list(dict.fromkeys(allow_regions))
        allow_regions.sort(key=len, reverse=True)
        return allow_regions

    def _extract_region(self, body: str, regions: list[str]) -> tuple[str | None, str]:
        # 首先尝试按空格分割
        first, _, rest = body.partition(" ")
        first_cf = first.casefold()
        for region in regions:
            if first_cf == region.casefold():
                return region, rest.strip()

        # 然后尝试无空格的情况，直接从开头提取区服
        body_cf = body.casefold()
        for region in regions:
            if body_cf.startswith(region.casefold()):
                remaining = body[len(region):].strip()
                # 即使剩余部分为空也返回，因为命令可能就在区服后面
                return region, remaining
        return None, ""

    @staticmethod
    def _is_command_head(text: str, command: str) -> bool:
        if len(text) < len(command):
            return False
        if text[:len(command)].casefold() != command.casefold():
            return False
        # 允许命令后面直接跟其他内容，不需要空格
        return True

    def _build_trigger_variants(self, prefix_arg: str, command: str) -> list[str]:
        variants = [f"{prefix_arg}{command}" if prefix_arg else command]
        if prefix_arg:
            variants.append(f"{prefix_arg} {command}")
        return list(dict.fromkeys(variants))

    def _match_command(self, body_without_region: str) -> _CommandMatch | None:
        for prefix_arg in self.prefix_args:
            for command in self.commands:
                for trigger in self._build_trigger_variants(prefix_arg, command):
                    if self._is_command_head(body_without_region, trigger):
                        args = body_without_region[len(trigger):].strip()
                        return _CommandMatch(prefix_arg=prefix_arg, matched_trigger=trigger, args=args)
        return None

    def parse_context(self, event: AstrMessageEvent) -> HandlerContext | None:
        message = self._normalize_spaces(event.get_message_str())
        # 不再要求消息以斜杠开头
        body = message.strip()
        if not body:
            return None

        regions = self._get_regions()
        if not regions:
            return None

        region, rest = self._extract_region(body, regions)
        if not region:
            return None

        matched = self._match_command(rest)
        if not matched:
            return None

        ctx = HandlerContext(event)
        ctx.region = region
        ctx.prefix_arg = matched.prefix_arg
        ctx.arg_text = matched.args
        ctx.trigger_cmd = f"{region}{matched.matched_trigger}"
        ctx.original_trigger_cmd = ctx.trigger_cmd
        return ctx

    def get_prefix_hint(self, event: AstrMessageEvent) -> str | None:
        message = self._normalize_spaces(event.get_message_str())
        # 不再要求消息以斜杠开头
        body = message.strip()
        if not body:
            return None

        # 尝试匹配命令，无论是带空格还是不带空格
        matched = self._match_command(body)
        if not matched:
            return None

        regions = self._get_regions()
        if not regions:
            return None
        # 提供无空格的示例
        example = f"{regions[0]}{matched.matched_trigger}"
        return (
            f"必须显式指定区服前缀。示例 {example}\n"
            f"当前支持区服：{', '.join(regions)}"
        )
