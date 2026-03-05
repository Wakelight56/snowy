from playwright.async_api import (
    async_playwright, 
    Browser, 
    Playwright, 
    BrowserType, 
    BrowserContext, 
    Page,
    Error as PlaywrightError
)
import os
from astrbot.api import logger
import asyncio

_playwright_instance: Playwright | None = None
_browser_type: BrowserType | None = NotImplementedError
_playwright_browser: Browser | None = None
_context_semaphore: asyncio.Semaphore | None = None

REMOTE_URL: str | None = None
BROWSER_TYPE: str = "chromium"
MAX_CONTEXTS = 8
# 配置选项，允许从环境变量或配置文件中读取
import os
# 尝试从环境变量读取配置
REMOTE_URL = os.getenv('PLAYWRIGHT_REMOTE_URL', REMOTE_URL)
BROWSER_TYPE = os.getenv('PLAYWRIGHT_BROWSER_TYPE', BROWSER_TYPE)

# 从配置文件读取配置
try:
    from ..config import get_global_config
    config = get_global_config()
    if hasattr(config, 'webdriver'):
        if hasattr(config.webdriver, 'remote_url') and config.webdriver.remote_url:
            REMOTE_URL = config.webdriver.remote_url
        if hasattr(config.webdriver, 'browser_type') and config.webdriver.browser_type:
            BROWSER_TYPE = config.webdriver.browser_type
except Exception:
    pass

async def _init_playwright_browser():
    global _playwright_instance, _browser_type, _playwright_browser, BROWSER_TYPE, REMOTE_URL
    # 检查浏览器的情况
    if _playwright_instance is None: 
        # 启动async_playwright实例
        _playwright_instance = await async_playwright().start()
        logger.info("初始化 Playwright 异步 API")
    _browser_type = getattr(_playwright_instance, BROWSER_TYPE)
    
    if REMOTE_URL:
        logger.info(f"正在连接远程 Playwright 浏览器: {REMOTE_URL}")
        try:
            if REMOTE_URL.startswith("ws://") or REMOTE_URL.startswith("wss://"):
                _playwright_browser = await _browser_type.connect(REMOTE_URL, timeout=30000)
            else:
                _playwright_browser = await _browser_type.connect_over_cdp(REMOTE_URL, timeout=30000)
            logger.info(f"成功连接至远程浏览器")
        except Exception as e:
            logger.error(f"连接远程浏览器失败: {e}")
            # 如果远程连接失败，尝试启动本地浏览器
            logger.info("尝试启动本地浏览器")
            await _launch_local_browser()
    else:
        await _launch_local_browser()

async def _launch_local_browser():
    global _playwright_browser, _browser_type
    # 清除本地临时文件
    try:
        if os.system("rm -rf /tmp/rust_mozprofile*") != 0:
            logger.error(f"清空WebDriver临时文件失败")
    except Exception as e:
        logger.error(f"清空临时文件时出错: {e}")
    # 启动浏览器
    try:
        _playwright_browser = await _browser_type.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
        )
        logger.info(f"启动本地 Playwright Browser")
    except Exception as e:
        logger.error(f"启动本地浏览器失败: {e}")
        logger.error("请确保已安装 Playwright 浏览器: python -m playwright install")
        raise

class PlaywrightPage:
    """
    异步上下文管理器，用于管理 Playwright 浏览器实例队列。
    """
    def __init__(self, context_options: dict | None = None):
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.context_options: dict = context_options if context_options is not None else { 
                'locale': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            }

    async def __aenter__(self) -> Page:
        global _playwright_instance, _browser_type, _playwright_browser, BROWSER_TYPE, REMOTE_URL, _context_semaphore
        # 检查浏览器的情况
        if _playwright_browser is None or not _playwright_browser.is_connected():
            await _init_playwright_browser()
        if _context_semaphore is None:
            _context_semaphore = asyncio.Semaphore(MAX_CONTEXTS)
        await _context_semaphore.acquire()
        try:
            self.context = await _playwright_browser.new_context(**self.context_options)
        except PlaywrightError as pe:
            # 在新建context时就发生异常，可以认为playwright本身出了问题，重启一下
            try:
                _playwright_browser.close()
            except Exception as e:
                logger.error(f"关闭 Playwright Browser 失败 {e}")
            _playwright_browser = None
            _context_semaphore.release()
            raise pe
        except: 
            # 出现异常时释放信号
            _context_semaphore.release()
            raise
        self.page = await self.context.new_page()
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 关闭上下文，自动清理
        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                logger.error(f"关闭 Playwright Page 失败 {e}")
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.error(f"关闭 Playwright Context 失败 {e}")
            finally:# 释放信号
                _context_semaphore.release()
        self.page = None
        self.context = None
        return False
    @classmethod
    async def start(cls, browser_type: str = "chromium", max_contexts: int = 8, remote_url:str = None):
        global MAX_CONTEXTS, BROWSER_TYPE, REMOTE_URL, _context_semaphore
        
        MAX_CONTEXTS = max_contexts
        BROWSER_TYPE = browser_type
        REMOTE_URL = remote_url
        _context_semaphore = asyncio.Semaphore(MAX_CONTEXTS)
        # 启动async_playwright实例
        await _init_playwright_browser()

    @classmethod
    async def stop(cls):
        global _playwright_browser, _playwright_instance
        if _playwright_browser is not None:
            try:
                await _playwright_browser.close()
                logger.info("Playwright Browser 已关闭。")
            except Exception as e:
                logger.error(f"关闭 Playwright Browser 失败: {e}")
        if _playwright_instance is not None:
            try:
                await _playwright_instance.stop()
                logger.info("Playwright 实例已停止。")
            except Exception as e:
                logger.error(f"停止 Playwright 实例失败: {e}")
