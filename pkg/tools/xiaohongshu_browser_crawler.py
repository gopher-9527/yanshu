"""
小红书浏览器自动化爬虫工具

通过浏览器自动化实时操作浏览器获取小红书内容。
支持：
1. 使用已登录的浏览器会话
2. 搜索关键词
3. 获取帖子完整内容（包括食材、做法等）
4. 分类保存到本地

使用 Playwright 进行浏览器自动化操作。
"""

import asyncio
import json
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class CrawledRecipe:
    """爬取的菜谱数据"""

    # 基础信息
    title: str
    author: str
    date: str
    likes: str
    url: str

    # 分类信息
    category: str = ""
    age_group: str = ""

    # 详细内容
    description: str = ""
    ingredients: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)

    # 媒体内容
    images: List[str] = field(default_factory=list)
    local_images: List[str] = field(default_factory=list)

    # 额外信息
    tags: List[str] = field(default_factory=list)
    comments_count: str = "0"
    collect_count: str = "0"

    # 元数据
    crawled_at: str = ""
    content_hash: str = ""


class XiaohongshuBrowserCrawler:
    """小红书浏览器自动化爬虫"""

    # 年龄分类
    AGE_GROUPS = {
        "6月龄": ["6月", "六月", "6个月"],
        "7-8月龄": ["7月", "8月", "七月", "八月", "7个月", "8个月"],
        "9-10月龄": ["9月", "10月", "九月", "十月", "9个月", "10个月"],
        "11-12月龄": ["11月", "12月", "十一月", "十二月", "11个月", "12个月"],
        "1岁以上": ["1岁", "一岁", "一周岁", "12月龄+", "1岁+"],
    }

    # 食物类型分类
    FOOD_TYPES = {
        "主食类": ["米糊", "米粉", "粥", "面条", "饭", "烩饭", "面", "米"],
        "蛋白质类": ["肉", "牛肉", "鸡肉", "猪肉", "鱼", "虾", "蛋", "豆腐"],
        "蔬菜类": ["蔬菜", "菜", "胡萝卜", "南瓜", "土豆", "山药", "西兰花", "菠菜"],
        "水果类": ["水果", "苹果", "香蕉", "梨", "橙", "草莓"],
        "手指食物": ["手指", "条", "棒", "块", "小饼"],
        "汤羹类": ["汤", "羹", "糊"],
        "烘焙类": ["松饼", "蛋糕", "饼干", "蒸糕", "糕"],
    }

    def __init__(
        self,
        output_dir: str = "baby_food_recipes",
        headless: bool = False,
        slow_mo: int = 100,
    ):
        """
        初始化爬虫

        Args:
            output_dir: 输出目录
            headless: 是否无头模式运行浏览器
            slow_mo: 操作延迟（毫秒），用于调试
        """
        self.output_dir = output_dir
        self.headless = headless
        self.slow_mo = slow_mo
        self.recipes: List[CrawledRecipe] = []
        self.browser = None
        self.context = None
        self.page = None
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "recipes"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "images"), exist_ok=True)

    def _classify_age_group(self, text: str) -> str:
        """根据文本分类年龄组"""
        for age_group, keywords in self.AGE_GROUPS.items():
            for keyword in keywords:
                if keyword in text:
                    return age_group
        return "通用"

    def _classify_food_type(self, text: str) -> str:
        """根据文本分类食物类型"""
        for food_type, keywords in self.FOOD_TYPES.items():
            for keyword in keywords:
                if keyword in text:
                    return food_type
        return "其他"

    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _parse_ingredients(self, text: str) -> List[str]:
        """从文本中解析食材列表"""
        ingredients = []
        patterns = [
            r"食材[：:]\s*(.+?)(?=做法|步骤|$)",
            r"材料[：:]\s*(.+?)(?=做法|步骤|$)",
            r"用料[：:]\s*(.+?)(?=做法|步骤|$)",
            r"准备[：:]\s*(.+?)(?=做法|步骤|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                ingredient_text = match.group(1)
                items = re.split(r"[,，、\n\r]+", ingredient_text)
                for item in items:
                    item = item.strip()
                    if item and len(item) < 50:
                        ingredients.append(item)
                break

        return ingredients

    def _parse_steps(self, text: str) -> List[str]:
        """从文本中解析制作步骤"""
        steps = []
        patterns = [
            r"做法[：:]\s*(.+?)(?=小贴士|tips|$)",
            r"步骤[：:]\s*(.+?)(?=小贴士|tips|$)",
            r"制作[：:]\s*(.+?)(?=小贴士|tips|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                steps_text = match.group(1)
                step_items = re.split(r"(?:\d+[.、)）]|\n)", steps_text)
                for item in step_items:
                    item = item.strip()
                    if item and len(item) > 5:
                        steps.append(item)
                break

        if not steps:
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if re.match(r"^\d+[.、)）]", line) or any(
                    verb in line for verb in ["加入", "搅拌", "蒸", "煮", "切", "放入"]
                ):
                    if len(line) > 5:
                        steps.append(re.sub(r"^\d+[.、)）]\s*", "", line))

        return steps

    def _parse_tips(self, text: str) -> List[str]:
        """从文本中解析小贴士"""
        tips = []
        patterns = [
            r"(?:小贴士|tips|温馨提示|注意)[：:]\s*(.+?)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                tips_text = match.group(1)
                items = re.split(r"[。\n]+", tips_text)
                for item in items:
                    item = item.strip()
                    if item and len(item) > 5:
                        tips.append(item)
                break

        return tips

    def _parse_tags(self, text: str) -> List[str]:
        """从文本中解析标签"""
        tags = re.findall(r"#([^#\s]+)#?", text)
        return list(set(tags))

    async def _init_browser(self):
        """初始化浏览器"""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            # 使用持久化上下文，保留登录状态
            user_data_dir = os.path.expanduser("~/.xiaohongshu_browser_data")
            os.makedirs(user_data_dir, exist_ok=True)

            print("[Browser] 正在启动浏览器...")

            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=self.headless,
                slow_mo=self.slow_mo,
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            # 设置默认超时
            self.context.set_default_timeout(60000)
            self.context.set_default_navigation_timeout(60000)

            # 创建新页面
            self.page = await self.context.new_page()

            # 设置页面超时
            self.page.set_default_timeout(60000)
            self.page.set_default_navigation_timeout(60000)

            print("[Browser] ✅ 浏览器已启动")
            return True

        except ImportError:
            print("[Browser] ❌ 错误: 请先安装 playwright")
            print("运行: pip install playwright && playwright install chromium")
            return False
        except Exception as e:
            print(f"[Browser] ❌ 启动浏览器失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _close_browser(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if hasattr(self, "playwright") and self.playwright:
            await self.playwright.stop()
        print("[Browser] 浏览器已关闭")

    async def check_login(self) -> bool:
        """检查是否已登录"""
        try:
            print("[Browser] 正在访问小红书...")
            await self.page.goto(
                "https://www.xiaohongshu.com/explore",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            print("[Browser] 页面已加载，等待内容渲染...")
            await asyncio.sleep(3)  # 等待页面完全渲染

            # 检查是否有用户头像或"我"按钮（已登录标志）
            user_link = await self.page.query_selector('a[href*="/user/profile/"]')
            if user_link:
                print("[Browser] ✅ 已登录")
                return True

            # 检查是否有登录按钮（未登录标志）
            login_btn = await self.page.query_selector('button:has-text("登录")')
            if login_btn:
                print("[Browser] ❌ 未登录")
                return False

            # 检查搜索框提示文字
            search_box = await self.page.query_selector('input[placeholder*="登录"]')
            if search_box:
                print("[Browser] ❌ 未登录（需要登录探索更多内容）")
                return False

            print("[Browser] ⚠️ 无法确定登录状态，尝试继续...")
            return True

        except Exception as e:
            print(f"[Browser] 检查登录状态失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def trigger_login(self):
        """触发登录弹窗"""
        try:
            # 方法1: 点击登录按钮
            login_btn = await self.page.query_selector('button:has-text("登录")')
            if login_btn:
                await login_btn.click()
                await asyncio.sleep(1)
                print("[Browser] 📱 已打开登录弹窗")
                return True

            # 方法2: 点击搜索框触发登录
            search_box = await self.page.query_selector('input[placeholder*="登录"]')
            if search_box:
                await search_box.click()
                await asyncio.sleep(1)
                print("[Browser] 📱 已触发登录弹窗")
                return True

            # 方法3: 尝试访问需要登录的页面
            await self.page.goto("https://www.xiaohongshu.com/notification")
            await asyncio.sleep(2)
            print("[Browser] 📱 已跳转到需要登录的页面")
            return True

        except Exception as e:
            print(f"[Browser] 触发登录失败: {e}")
            return False

    async def wait_for_login(self, timeout: int = 300):
        """等待用户手动登录

        使用 Playwright 的 pause() 功能，让用户可以在浏览器中自由操作。

        Args:
            timeout: 超时时间（秒）
        """
        print()
        print("=" * 60)
        print("📱 需要登录小红书")
        print("=" * 60)
        print()
        print("🔔 重要提示:")
        print("   1. 浏览器已打开，请在浏览器窗口中操作")
        print("   2. 点击「登录」按钮")
        print("   3. 使用小红书App扫描二维码")
        print("   4. 登录成功后，在终端按 Enter 键继续")
        print()
        print("=" * 60)

        # 触发登录弹窗
        await self.trigger_login()

        # 暂停程序，等待用户手动操作
        # 使用 input() 而不是 page.pause()，这样更简单
        print()
        input("👆 请在浏览器中完成登录，然后按 Enter 键继续...")
        print()

        # 检查登录状态
        await asyncio.sleep(2)
        user_link = await self.page.query_selector('a[href*="/user/profile/"]')
        if user_link:
            print("[Browser] ✅ 登录成功！")
            return True

        # 如果还没登录，再给用户一次机会
        print("[Browser] ⚠️ 似乎还未登录，再检查一次...")
        await self.page.reload()
        await asyncio.sleep(3)

        user_link = await self.page.query_selector('a[href*="/user/profile/"]')
        if user_link:
            print("[Browser] ✅ 登录成功！")
            return True

        print("[Browser] ❌ 登录失败，请确保已正确扫码登录")
        retry = input("是否重试？(y/n): ").strip().lower()
        if retry == 'y':
            return await self.wait_for_login(timeout)

        return False

    async def search(self, keyword: str) -> List[Dict[str, str]]:
        """搜索关键词

        Args:
            keyword: 搜索关键词

        Returns:
            搜索结果列表
        """
        print(f"[Browser] 搜索: {keyword}")

        # 导航到搜索页面
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        await self.page.goto(search_url)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)  # 等待动态内容加载

        # 获取搜索结果
        results = []
        note_cards = await self.page.query_selector_all('section[class*="note-item"]')

        if not note_cards:
            # 尝试其他选择器
            note_cards = await self.page.query_selector_all('div[class*="note-item"]')

        if not note_cards:
            # 尝试通用链接选择器
            note_cards = await self.page.query_selector_all(
                'a[href*="/explore/"], a[href*="/search_result/"]'
            )

        print(f"[Browser] 找到 {len(note_cards)} 个结果")

        for card in note_cards[:20]:  # 限制数量
            try:
                # 获取链接
                href = await card.get_attribute("href")
                if not href:
                    link = await card.query_selector("a")
                    if link:
                        href = await link.get_attribute("href")

                if not href:
                    continue

                # 构建完整URL
                if href.startswith("/"):
                    href = f"https://www.xiaohongshu.com{href}"

                # 获取标题
                title_elem = await card.query_selector(
                    'span[class*="title"], div[class*="title"], .note-content'
                )
                title = ""
                if title_elem:
                    title = await title_elem.inner_text()

                # 获取作者
                author_elem = await card.query_selector(
                    'span[class*="author"], a[class*="author"], .author-name'
                )
                author = ""
                if author_elem:
                    author = await author_elem.inner_text()

                # 获取点赞数
                likes_elem = await card.query_selector(
                    'span[class*="like"], span[class*="count"]'
                )
                likes = "0"
                if likes_elem:
                    likes = await likes_elem.inner_text()

                if title or href:
                    results.append(
                        {
                            "title": title.strip() if title else "",
                            "author": author.strip() if author else "",
                            "url": href,
                            "likes": likes.strip() if likes else "0",
                        }
                    )

            except Exception as e:
                print(f"[Browser] 解析搜索结果失败: {e}")
                continue

        return results

    async def get_note_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """获取笔记详情

        Args:
            url: 笔记URL

        Returns:
            笔记详情
        """
        try:
            print(f"[Browser] 获取笔记: {url[:50]}...")

            # 打开新标签页
            page = await self.context.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # 等待动态内容加载

            detail = {"url": url}

            # 获取标题
            title_elem = await page.query_selector(
                'div[class*="title"], h1, .note-content .title'
            )
            if title_elem:
                detail["title"] = await title_elem.inner_text()

            # 获取作者
            author_elem = await page.query_selector(
                'a[class*="author"], .author-name, a[href*="/user/profile/"] span'
            )
            if author_elem:
                detail["author"] = await author_elem.inner_text()

            # 获取正文内容
            content_elem = await page.query_selector(
                'div[class*="desc"], div[class*="content"], .note-text'
            )
            if content_elem:
                detail["description"] = await content_elem.inner_text()

            # 获取发布日期
            date_elem = await page.query_selector(
                'span[class*="date"], span[class*="time"], .publish-time'
            )
            if date_elem:
                detail["date"] = await date_elem.inner_text()

            # 获取点赞数
            likes_elem = await page.query_selector(
                'span[class*="like-count"], span[class*="count"]:first-of-type'
            )
            if likes_elem:
                detail["likes"] = await likes_elem.inner_text()

            # 获取评论数
            comments_elem = await page.query_selector(
                'span[class*="comment-count"], span[class*="count"]:nth-of-type(2)'
            )
            if comments_elem:
                detail["comments_count"] = await comments_elem.inner_text()

            # 获取收藏数
            collect_elem = await page.query_selector(
                'span[class*="collect-count"], span[class*="count"]:nth-of-type(3)'
            )
            if collect_elem:
                detail["collect_count"] = await collect_elem.inner_text()

            # 获取图片
            img_elems = await page.query_selector_all(
                'img[class*="note-image"], img[class*="swiper"], .carousel img'
            )
            images = []
            for img in img_elems:
                src = await img.get_attribute("src")
                if src and "xhscdn" in src:
                    images.append(src)
            detail["images"] = images

            # 获取标签
            tag_elems = await page.query_selector_all('a[href*="keyword="]')
            tags = []
            for tag in tag_elems:
                tag_text = await tag.inner_text()
                if tag_text.startswith("#"):
                    tags.append(tag_text.lstrip("#"))
            detail["tags"] = tags

            await page.close()
            return detail

        except Exception as e:
            print(f"[Browser] 获取笔记详情失败: {e}")
            return None

    def _create_recipe_from_detail(self, detail: Dict[str, Any]) -> CrawledRecipe:
        """从详情创建菜谱对象"""
        description = detail.get("description", "")
        title = detail.get("title", "")
        full_text = f"{title} {description}"

        return CrawledRecipe(
            title=title,
            author=detail.get("author", ""),
            date=detail.get("date", ""),
            likes=detail.get("likes", "0"),
            url=detail.get("url", ""),
            category=self._classify_food_type(full_text),
            age_group=self._classify_age_group(full_text),
            description=description,
            ingredients=self._parse_ingredients(description),
            steps=self._parse_steps(description),
            tips=self._parse_tips(description),
            images=detail.get("images", []),
            tags=detail.get("tags", []) + self._parse_tags(description),
            comments_count=detail.get("comments_count", "0"),
            collect_count=detail.get("collect_count", "0"),
            crawled_at=datetime.now().isoformat(),
            content_hash=self._generate_content_hash(detail.get("url", "")),
        )

    async def crawl(
        self,
        keyword: str = "宝宝辅食",
        max_notes: int = 10,
        get_details: bool = True,
        login_timeout: int = 300,
    ) -> List[CrawledRecipe]:
        """执行爬取

        Args:
            keyword: 搜索关键词
            max_notes: 最大爬取数量
            get_details: 是否获取详情
            login_timeout: 登录等待超时时间（秒）

        Returns:
            爬取的菜谱列表
        """
        # 初始化浏览器
        if not await self._init_browser():
            return []

        try:
            print()
            print("[Browser] 🔍 检查登录状态...")

            # 检查登录状态
            is_logged_in = await self.check_login()

            if not is_logged_in:
                print("[Browser] 📱 需要登录，正在打开登录页面...")

                # 等待用户登录
                if not await self.wait_for_login(timeout=login_timeout):
                    print("[Browser] ❌ 登录失败，终止爬取")
                    return []

                # 登录成功后，重新导航到首页
                print("[Browser] 🔄 登录成功，正在准备搜索...")
                await self.page.goto("https://www.xiaohongshu.com/explore")
                await asyncio.sleep(2)

            print()
            print(f"[Browser] 🔍 开始搜索: {keyword}")

            # 搜索
            search_results = await self.search(keyword)
            print(f"[Browser] 获取到 {len(search_results)} 个搜索结果")

            # 限制数量
            search_results = search_results[:max_notes]

            # 获取详情
            for i, result in enumerate(search_results):
                print(
                    f"[Browser] 处理 {i + 1}/{len(search_results)}: {result.get('title', '')[:30]}..."
                )

                if get_details:
                    detail = await self.get_note_detail(result["url"])
                    if detail:
                        # 合并搜索结果和详情
                        merged = {**result, **detail}
                        recipe = self._create_recipe_from_detail(merged)
                        self.recipes.append(recipe)
                else:
                    # 只使用搜索结果信息
                    recipe = CrawledRecipe(
                        title=result.get("title", ""),
                        author=result.get("author", ""),
                        date="",
                        likes=result.get("likes", "0"),
                        url=result.get("url", ""),
                        crawled_at=datetime.now().isoformat(),
                        content_hash=self._generate_content_hash(result.get("url", "")),
                    )
                    self.recipes.append(recipe)

                # 延迟，避免被反爬
                await asyncio.sleep(1)

            print(f"[Browser] 爬取完成，共 {len(self.recipes)} 个菜谱")
            return self.recipes

        finally:
            await self._close_browser()

    def save_to_json(self, filename: str = "recipes.json") -> str:
        """保存为JSON"""
        filepath = os.path.join(self.output_dir, filename)
        data = {
            "created_at": datetime.now().isoformat(),
            "source": "小红书浏览器自动化爬取",
            "total_count": len(self.recipes),
            "recipes": [asdict(r) for r in self.recipes],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Save] 已保存到: {filepath}")
        return filepath

    def save_to_markdown(self, filename: str = "菜谱大全.md") -> str:
        """保存为Markdown"""
        filepath = os.path.join(self.output_dir, filename)

        lines = [
            "# 🍼 宝宝辅食菜谱大全",
            "",
            "> 数据来源：小红书浏览器自动化爬取",
            f"> 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> 共收录 **{len(self.recipes)}** 个菜谱",
            "",
            "---",
            "",
        ]

        for recipe in self.recipes:
            lines.append(f"## {recipe.title}")
            lines.append("")
            lines.append(f"- 👤 **作者**：{recipe.author}")
            lines.append(f"- ❤️ **点赞**：{recipe.likes}")
            lines.append(f"- 📁 **分类**：{recipe.category} | {recipe.age_group}")

            if recipe.tags:
                lines.append(
                    f"- 🏷️ **标签**：{', '.join(['#' + t for t in recipe.tags])}"
                )

            lines.append(f"- 🔗 **原文**：[查看原文]({recipe.url})")
            lines.append("")

            if recipe.description:
                lines.append("### 📝 内容")
                lines.append("")
                lines.append(recipe.description)
                lines.append("")

            if recipe.ingredients:
                lines.append("### 🥬 食材")
                lines.append("")
                for ing in recipe.ingredients:
                    lines.append(f"- {ing}")
                lines.append("")

            if recipe.steps:
                lines.append("### 👩‍🍳 制作步骤")
                lines.append("")
                for i, step in enumerate(recipe.steps, 1):
                    lines.append(f"{i}. {step}")
                lines.append("")

            if recipe.tips:
                lines.append("### 💡 小贴士")
                lines.append("")
                for tip in recipe.tips:
                    lines.append(f"- {tip}")
                lines.append("")

            lines.append("---")
            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"[Save] 已保存到: {filepath}")
        return filepath

    def save_individual_recipes(self, subdir: str = "recipes") -> str:
        """保存单独的菜谱文件"""
        recipes_dir = os.path.join(self.output_dir, subdir)
        os.makedirs(recipes_dir, exist_ok=True)

        for i, recipe in enumerate(self.recipes):
            safe_title = re.sub(r'[<>:"/\\|?*]', "", recipe.title)[:30]
            filename = f"{i + 1:02d}_{safe_title}.md"
            filepath = os.path.join(recipes_dir, filename)

            content = f"""# {recipe.title}

- 👤 作者：{recipe.author}
- 📅 日期：{recipe.date}
- ❤️ 点赞：{recipe.likes}
- 📁 分类：{recipe.category} | {recipe.age_group}
- 🔗 原文：[查看原文]({recipe.url})

**标签**：{" ".join(["#" + t for t in recipe.tags])}

---

## 📝 内容

{recipe.description}
"""

            if recipe.ingredients:
                content += "\n## 🥬 食材\n\n"
                for ing in recipe.ingredients:
                    content += f"- {ing}\n"

            if recipe.steps:
                content += "\n## 👩‍🍳 制作步骤\n\n"
                for j, step in enumerate(recipe.steps, 1):
                    content += f"{j}. {step}\n"

            if recipe.tips:
                content += "\n## 💡 小贴士\n\n"
                for tip in recipe.tips:
                    content += f"- {tip}\n"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"[Save] 已保存 {len(self.recipes)} 个单独菜谱到: {recipes_dir}")
        return recipes_dir

    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 50)
        print("📊 宝宝辅食菜谱爬取摘要")
        print("=" * 50)
        print(f"总菜谱数: {len(self.recipes)}")

        with_content = sum(1 for r in self.recipes if r.description)
        with_ingredients = sum(1 for r in self.recipes if r.ingredients)
        with_steps = sum(1 for r in self.recipes if r.steps)

        print("\n📄 内容统计:")
        print(f"  - 有详细描述: {with_content}个")
        print(f"  - 有食材列表: {with_ingredients}个")
        print(f"  - 有制作步骤: {with_steps}个")

        # 按年龄分类
        by_age: Dict[str, int] = {}
        for recipe in self.recipes:
            age = recipe.age_group or "通用"
            by_age[age] = by_age.get(age, 0) + 1

        print("\n📅 按月龄分类:")
        for age, count in sorted(by_age.items()):
            print(f"  - {age}: {count}个")

        # 按食物类型分类
        by_category: Dict[str, int] = {}
        for recipe in self.recipes:
            cat = recipe.category or "其他"
            by_category[cat] = by_category.get(cat, 0) + 1

        print("\n🍳 按食物类型分类:")
        for cat, count in sorted(by_category.items()):
            print(f"  - {cat}: {count}个")

        print("=" * 50 + "\n")


async def main():
    """主函数"""
    crawler = XiaohongshuBrowserCrawler(
        output_dir="baby_food_recipes",
        headless=False,  # 设置为False以便观察和手动登录
        slow_mo=100,
    )

    # 执行爬取
    recipes = await crawler.crawl(
        keyword="宝宝辅食",
        max_notes=10,  # 爬取10个帖子
        get_details=True,
    )

    if recipes:
        # 打印摘要
        crawler.print_summary()

        # 保存到文件
        crawler.save_to_json()
        crawler.save_to_markdown()
        crawler.save_individual_recipes()

        print("✅ 爬取完成！")
    else:
        print("❌ 未获取到任何内容")


if __name__ == "__main__":
    asyncio.run(main())
