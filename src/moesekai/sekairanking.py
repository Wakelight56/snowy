import asyncio
import os
from datetime import datetime, timedelta
from os.path import join as pjoin

from astrbot.api import logger

from ..utils.webdriver import PlaywrightPage
from ..config import get_global_config, Config
from ..utils.lifecycle import on_initialize
from ..handlers.base import CmdHandler, HandlerContext
from ..handlers.sekai import SekaiCmdHandler
from astrbot.api.event import AstrMessageEvent

sekairanking_lock: asyncio.Lock = asyncio.Lock()
config: Config | None = None
@on_initialize()
def initialize_sekai_ranking():
    print("init ranking")
    global config
    config = get_global_config()

def _get_screenshot_path(ctx: HandlerContext) -> str:
    return pjoin(config.data_path, f"sekairanking/screenshots/{ctx.region}.png")


def _is_cache_valid(ctx: HandlerContext, screenshot_path: str) -> bool:
    if not os.path.exists(screenshot_path):
        return False
    cache_duration = int(config.sekairanking.cache_duration or 0)
    if cache_duration <= 0:
        return True
    mtime = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
    return datetime.now() - mtime <= timedelta(seconds=cache_duration)


async def get_sekairanking_img(ctx: HandlerContext, refresh: bool = False):
    """获取榜线截图结果。"""
    screenshot_path = _get_screenshot_path(ctx)
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

    async with sekairanking_lock:
        if not refresh and _is_cache_valid(ctx, screenshot_path):
            yield ctx.event.image_result(os.path.abspath(screenshot_path))
            return
        try:
            yield ctx.event.plain_result(f"正在下载 {ctx.region} 的榜线预测截图")
            await screenshot_sekairanking_page(ctx, screenshot_path)
            logger.info(f"下载 {ctx.region} 的榜线预测截图成功")
        except Exception as e:
            logger.error(f"下载图片失败: {e}，尝试返回缓存图片")
            # 检查是否是浏览器相关的错误
            if "BrowserType.launch" in str(e) or "Executable doesn't exist" in str(e):
                yield ctx.event.plain_result("浏览器初始化失败，请确保已安装 Playwright 浏览器：python -m playwright install")
                if os.path.exists(screenshot_path):
                    yield ctx.event.image_result(os.path.abspath(screenshot_path))
                else:
                    yield ctx.event.plain_result("没有缓存图片可用")
                return

    if os.path.exists(screenshot_path):
        yield ctx.event.image_result(os.path.abspath(screenshot_path))
    else:
        yield ctx.event.plain_result(f"下载 {ctx.region} 的榜线预测截图失败，没有缓存图片可用")


async def screenshot_sekairanking_page(ctx: HandlerContext, screenshot_path: str):
    url: str = config.sekairanking.base_url
    if not url.endswith("/"):
        url += "/"
    if ctx.region == "cn":
        url = f"{url}simple"
    else:
        url = f"{url}{ctx.region}/simple"

    async with PlaywrightPage() as page:
        await page.goto(url, wait_until="domcontentloaded", timeout=config.sekairanking.timeout * 1000)
        await page.set_viewport_size(
            {
                "width": config.sekairanking.page_size[0],
                "height": config.sekairanking.page_size[1],
            },
        )
        await page.screenshot(path=screenshot_path, full_page=True)


print("注册skp指令")
pjsk_skp = SekaiCmdHandler(
    [
        "/pjsk sk predict",
        "/pjsk board predict",
        "/sk预测",
        "/榜线预测",
        "/skp",
        "/prediction",
        "/预测",
    ],
    prefix_args=["", "wl"],
)
@pjsk_skp.handle()
async def _(ctx):
    refresh = False
    args = []
    for token in ctx.get_args().split():
        if token.casefold() == "refresh":
            refresh = True
            continue
        args.append(token)
    ctx.arg_text = " ".join(args)

    async for result in get_sekairanking_img(ctx=ctx, refresh=refresh):
        yield result

# 注册dhelp指令
print("注册dhelp指令")

# 为dhelp创建一个单独的处理器，不需要区服前缀
class HelpCmdHandler(CmdHandler):
    """帮助命令处理器，不需要区服前缀"""
    
    def __init__(self, commands: list[str]):
        super().__init__(commands)
        print(f"注册帮助指令 {commands[0]}")
    
    def parse_context(self, event: AstrMessageEvent) -> HandlerContext | None:
        message = self._normalize_spaces(event.get_message_str())
        body = message.strip()
        if not body:
            return None
        
        # 直接匹配命令，不需要区服前缀
        for command in self.commands:
            if body.casefold() == command.casefold():
                ctx = HandlerContext(event)
                ctx.region = "cn"  # 设置默认区服
                ctx.trigger_cmd = command
                ctx.original_trigger_cmd = command
                return ctx
        return None

pjsk_dhelp = HelpCmdHandler(
    [
        "dhelp",
        "帮助",
    ]
)

@pjsk_dhelp.handle()
async def _(ctx):
    # 使用纯文本方式返回帮助信息，避免图片乱码问题
    help_text = """Moesekai 插件帮助

个人信息查询:
  cn 个人信息
  jp grxx
  cn个人信息
  jpgrxx

榜线预测:
  cn skp
  jp 预测
  cnskp
  jp预测

强制刷新:
  cn skp refresh
  cnskprefresh

查看帮助:
  dhelp
  帮助"""
    
    # 返回纯文本结果
    yield ctx.event.plain_result(help_text)