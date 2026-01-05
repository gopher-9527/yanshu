"""
小红书宝宝辅食爬虫工具

此工具用于从小红书搜索并收集宝宝辅食相关的内容，
然后将数据分类并生成菜谱存储到本地。

功能：
1. 爬取搜索结果列表
2. 爬取每篇笔记的详细内容（材料、步骤、图片等）
3. 下载图片到本地
4. 生成分类整理的菜谱文档

注意：
1. 需要先在浏览器中登录小红书账号
2. 由于小红书有反爬虫机制，建议通过浏览器自动化工具进行操作
3. 请遵守小红书的使用条款，不要过度频繁请求
"""

import json
import os
import re
import hashlib
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class RecipeContent:
    """辅食菜谱完整内容"""

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
    description: str = ""  # 笔记正文描述
    ingredients: List[str] = field(default_factory=list)  # 食材列表
    steps: List[str] = field(default_factory=list)  # 制作步骤
    tips: List[str] = field(default_factory=list)  # 小贴士

    # 媒体内容
    images: List[str] = field(default_factory=list)  # 图片URL列表
    local_images: List[str] = field(default_factory=list)  # 本地图片路径
    video_url: Optional[str] = None  # 视频URL（如有）

    # 额外信息
    tags: List[str] = field(default_factory=list)  # 标签
    comments_count: str = "0"  # 评论数
    collect_count: str = "0"  # 收藏数

    # 抓取元数据
    crawled_at: str = ""  # 抓取时间
    content_hash: str = ""  # 内容哈希（用于去重）


class BabyFoodRecipeCollector:
    """宝宝辅食菜谱收集器"""

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

    def __init__(self, output_dir: str = "baby_food_recipes"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        self.recipes: List[RecipeContent] = []
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

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

        # 常见的食材标记模式
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
                # 分割食材（按换行、逗号、顿号等）
                items = re.split(r"[,，、\n\r]+", ingredient_text)
                for item in items:
                    item = item.strip()
                    if item and len(item) < 50:  # 过滤太长的文本
                        ingredients.append(item)
                break

        return ingredients

    def _parse_steps(self, text: str) -> List[str]:
        """从文本中解析制作步骤"""
        steps = []

        # 常见的步骤标记模式
        patterns = [
            r"做法[：:]\s*(.+?)(?=小贴士|tips|$)",
            r"步骤[：:]\s*(.+?)(?=小贴士|tips|$)",
            r"制作[：:]\s*(.+?)(?=小贴士|tips|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                steps_text = match.group(1)
                # 按数字编号分割
                step_items = re.split(r"(?:\d+[.、)）]|\n)", steps_text)
                for item in step_items:
                    item = item.strip()
                    if item and len(item) > 5:  # 过滤太短的文本
                        steps.append(item)
                break

        # 如果没找到明确的步骤标记，尝试按换行分割
        if not steps:
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # 检查是否像步骤（以数字开头或包含动词）
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
        # 匹配 #标签# 或 #标签 格式
        tags = re.findall(r"#([^#\s]+)#?", text)
        return list(set(tags))  # 去重

    def _download_image(self, url: str, recipe_id: str, index: int) -> Optional[str]:
        """下载图片到本地

        Args:
            url: 图片URL
            recipe_id: 菜谱ID（用于命名）
            index: 图片索引

        Returns:
            本地文件路径，失败返回None
        """
        if not url:
            return None

        try:
            # 确定文件扩展名
            ext = ".jpg"
            if ".png" in url.lower():
                ext = ".png"
            elif ".gif" in url.lower():
                ext = ".gif"
            elif ".webp" in url.lower():
                ext = ".webp"

            # 生成本地文件名
            filename = f"{recipe_id}_{index}{ext}"
            local_path = os.path.join(self.images_dir, filename)

            # 如果文件已存在，跳过下载
            if os.path.exists(local_path):
                return local_path

            # 下载图片
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request, timeout=30) as response:
                with open(local_path, "wb") as f:
                    f.write(response.read())

            print(f"  ✓ 已下载图片: {filename}")
            return local_path

        except Exception as e:
            print(f"  ✗ 下载图片失败: {url}, 错误: {e}")
            return None

    def add_recipe_with_content(
        self,
        title: str,
        author: str,
        date: str,
        likes: str,
        url: str,
        description: str = "",
        images: List[str] = None,
        video_url: str = None,
        comments_count: str = "0",
        collect_count: str = "0",
        download_images: bool = True,
    ) -> RecipeContent:
        """添加带完整内容的菜谱

        Args:
            title: 标题
            author: 作者
            date: 发布日期
            likes: 点赞数
            url: 原文链接
            description: 笔记正文（完整内容）
            images: 图片URL列表
            video_url: 视频URL
            comments_count: 评论数
            collect_count: 收藏数
            download_images: 是否下载图片到本地

        Returns:
            创建的菜谱对象
        """
        images = images or []

        # 合并标题和描述进行分类
        full_text = f"{title} {description}"
        age_group = self._classify_age_group(full_text)
        category = self._classify_food_type(full_text)

        # 解析内容
        ingredients = self._parse_ingredients(description)
        steps = self._parse_steps(description)
        tips = self._parse_tips(description)
        tags = self._parse_tags(description)

        # 生成唯一ID
        content_hash = self._generate_content_hash(f"{url}{title}")

        # 下载图片
        local_images = []
        if download_images and images:
            print(f"正在下载图片: {title[:30]}...")
            for i, img_url in enumerate(images):
                local_path = self._download_image(img_url, content_hash, i)
                if local_path:
                    local_images.append(local_path)

        recipe = RecipeContent(
            title=title,
            author=author,
            date=date,
            likes=likes,
            url=url,
            category=category,
            age_group=age_group,
            description=description,
            ingredients=ingredients,
            steps=steps,
            tips=tips,
            images=images,
            local_images=local_images,
            video_url=video_url,
            tags=tags,
            comments_count=comments_count,
            collect_count=collect_count,
            crawled_at=datetime.now().isoformat(),
            content_hash=content_hash,
        )

        self.recipes.append(recipe)
        return recipe

    def add_recipe(
        self,
        title: str,
        author: str,
        date: str,
        likes: str,
        url: str,
        description: str = None,
    ):
        """添加简单菜谱（兼容旧接口）"""
        return self.add_recipe_with_content(
            title=title,
            author=author,
            date=date,
            likes=likes,
            url=url,
            description=description or "",
            download_images=False,
        )

    def add_recipes_from_search_results(
        self, search_results: List[Dict], download_images: bool = False
    ):
        """从搜索结果批量添加菜谱"""
        for result in search_results:
            self.add_recipe_with_content(
                title=result.get("title", ""),
                author=result.get("author", ""),
                date=result.get("date", ""),
                likes=result.get("likes", "0"),
                url=result.get("url", ""),
                description=result.get("description", ""),
                images=result.get("images", []),
                video_url=result.get("video_url"),
                comments_count=result.get("comments_count", "0"),
                collect_count=result.get("collect_count", "0"),
                download_images=download_images,
            )

    def get_recipes_by_category(self) -> Dict[str, List[RecipeContent]]:
        """按食物类型分类获取菜谱"""
        categorized = {}
        for recipe in self.recipes:
            if recipe.category not in categorized:
                categorized[recipe.category] = []
            categorized[recipe.category].append(recipe)
        return categorized

    def get_recipes_by_age(self) -> Dict[str, List[RecipeContent]]:
        """按年龄分组获取菜谱"""
        by_age = {}
        for recipe in self.recipes:
            if recipe.age_group not in by_age:
                by_age[recipe.age_group] = []
            by_age[recipe.age_group].append(recipe)
        return by_age

    def save_to_json(self, filename: str = "recipes.json"):
        """保存菜谱到JSON文件（包含完整内容）"""
        filepath = os.path.join(self.output_dir, filename)
        data = {
            "created_at": datetime.now().isoformat(),
            "total_count": len(self.recipes),
            "recipes": [asdict(r) for r in self.recipes],
            "by_category": {
                cat: [asdict(r) for r in recipes]
                for cat, recipes in self.get_recipes_by_category().items()
            },
            "by_age": {
                age: [asdict(r) for r in recipes]
                for age, recipes in self.get_recipes_by_age().items()
            },
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"菜谱已保存到: {filepath}")
        return filepath

    def save_to_markdown(self, filename: str = "菜谱大全.md"):
        """保存菜谱到Markdown文件（包含完整内容）"""
        filepath = os.path.join(self.output_dir, filename)

        lines = [
            "# 🍼 宝宝辅食菜谱大全",
            "",
            "> 数据来源：小红书搜索「宝宝辅食」",
            f"> 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> 共收录 **{len(self.recipes)}** 个菜谱",
            "",
            "---",
            "",
            "## 目录",
            "",
        ]

        # 生成目录
        by_age = self.get_recipes_by_age()
        age_order = ["6月龄", "7-8月龄", "9-10月龄", "11-12月龄", "1岁以上", "通用"]
        for age in age_order:
            if age in by_age:
                lines.append(f"- [{age}](#{age.replace('-', '').replace('+', '')})")

        lines.extend(["", "---", ""])

        # 按年龄分组输出详细内容
        for age in age_order:
            if age not in by_age:
                continue

            recipes = by_age[age]
            lines.append(f"## 📅 {age} ({len(recipes)}个)")
            lines.append("")

            for recipe in sorted(
                recipes, key=lambda x: self._parse_likes(x.likes), reverse=True
            ):
                lines.append(f"### {recipe.title}")
                lines.append("")

                # 基础信息
                lines.append(f"- 👤 **作者**：{recipe.author}")
                lines.append(f"- ❤️ **点赞**：{recipe.likes}")
                lines.append(f"- 📁 **分类**：{recipe.category}")
                if recipe.tags:
                    lines.append(f"- 🏷️ **标签**：{', '.join(recipe.tags)}")
                lines.append(f"- 🔗 **原文**：[查看原文]({recipe.url})")
                lines.append("")

                # 描述/正文
                if recipe.description:
                    lines.append("#### 📝 内容")
                    lines.append("")
                    # 清理并格式化描述
                    desc = recipe.description.strip()
                    lines.append(desc)
                    lines.append("")

                # 食材
                if recipe.ingredients:
                    lines.append("#### 🥬 食材")
                    lines.append("")
                    for ing in recipe.ingredients:
                        lines.append(f"- {ing}")
                    lines.append("")

                # 步骤
                if recipe.steps:
                    lines.append("#### 👩‍🍳 制作步骤")
                    lines.append("")
                    for i, step in enumerate(recipe.steps, 1):
                        lines.append(f"{i}. {step}")
                    lines.append("")

                # 小贴士
                if recipe.tips:
                    lines.append("#### 💡 小贴士")
                    lines.append("")
                    for tip in recipe.tips:
                        lines.append(f"- {tip}")
                    lines.append("")

                # 图片（使用本地路径或原始URL）
                if recipe.local_images:
                    lines.append("#### 📸 图片")
                    lines.append("")
                    for i, img_path in enumerate(recipe.local_images):
                        rel_path = os.path.relpath(img_path, self.output_dir)
                        lines.append(f"![图片{i + 1}]({rel_path})")
                    lines.append("")
                elif recipe.images:
                    lines.append("#### 📸 图片")
                    lines.append("")
                    for i, img_url in enumerate(recipe.images[:3]):  # 最多显示3张
                        lines.append(f"![图片{i + 1}]({img_url})")
                    lines.append("")

                lines.append("---")
                lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"菜谱Markdown已保存到: {filepath}")
        return filepath

    def save_individual_recipes(self, subdir: str = "recipes"):
        """将每个菜谱保存为单独的Markdown文件"""
        recipes_dir = os.path.join(self.output_dir, subdir)
        os.makedirs(recipes_dir, exist_ok=True)

        for recipe in self.recipes:
            # 生成安全的文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', "", recipe.title)[:50]
            filename = f"{recipe.content_hash}_{safe_title}.md"
            filepath = os.path.join(recipes_dir, filename)

            lines = [
                f"# {recipe.title}",
                "",
                f"- 👤 作者：{recipe.author}",
                f"- 📅 日期：{recipe.date}",
                f"- ❤️ 点赞：{recipe.likes}",
                f"- 📁 分类：{recipe.category} | {recipe.age_group}",
                f"- 🔗 原文：[查看原文]({recipe.url})",
                "",
            ]

            if recipe.tags:
                lines.append(f"**标签**：{' '.join(['#' + t for t in recipe.tags])}")
                lines.append("")

            if recipe.description:
                lines.append("## 📝 内容")
                lines.append("")
                lines.append(recipe.description)
                lines.append("")

            if recipe.ingredients:
                lines.append("## 🥬 食材")
                lines.append("")
                for ing in recipe.ingredients:
                    lines.append(f"- {ing}")
                lines.append("")

            if recipe.steps:
                lines.append("## 👩‍🍳 制作步骤")
                lines.append("")
                for i, step in enumerate(recipe.steps, 1):
                    lines.append(f"{i}. {step}")
                lines.append("")

            if recipe.tips:
                lines.append("## 💡 小贴士")
                lines.append("")
                for tip in recipe.tips:
                    lines.append(f"- {tip}")
                lines.append("")

            if recipe.local_images:
                lines.append("## 📸 图片")
                lines.append("")
                for i, img_path in enumerate(recipe.local_images):
                    rel_path = os.path.relpath(img_path, recipes_dir)
                    lines.append(f"![图片{i + 1}]({rel_path})")
                lines.append("")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        print(f"已保存 {len(self.recipes)} 个独立菜谱到: {recipes_dir}")

    def _parse_likes(self, likes: str) -> int:
        """解析点赞数字符串为数字"""
        likes = str(likes).strip('"')
        if "万" in likes:
            return int(float(likes.replace("万", "")) * 10000)
        try:
            return int(likes)
        except (ValueError, TypeError):
            return 0

    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 50)
        print("📊 宝宝辅食菜谱收集摘要")
        print("=" * 50)
        print(f"总菜谱数: {len(self.recipes)}")

        # 统计有完整内容的菜谱
        with_content = sum(1 for r in self.recipes if r.description)
        with_ingredients = sum(1 for r in self.recipes if r.ingredients)
        with_steps = sum(1 for r in self.recipes if r.steps)
        with_images = sum(1 for r in self.recipes if r.local_images)

        print("\n📄 内容统计:")
        print(f"  - 有详细描述: {with_content}个")
        print(f"  - 有食材列表: {with_ingredients}个")
        print(f"  - 有制作步骤: {with_steps}个")
        print(f"  - 已下载图片: {with_images}个")

        print("\n📅 按月龄分类:")
        for age, recipes in sorted(self.get_recipes_by_age().items()):
            print(f"  - {age}: {len(recipes)}个")

        print("\n🍳 按食物类型分类:")
        for category, recipes in sorted(self.get_recipes_by_category().items()):
            print(f"  - {category}: {len(recipes)}个")
        print("=" * 50 + "\n")


def create_sample_data_with_content():
    """创建带完整内容的示例数据"""
    return [
        {
            "title": "🔥宝宝吃饭不用愁，一周营养烩饭安排～",
            "author": "拉菲成长记🍷",
            "date": "07-14",
            "likes": "5338",
            "url": "https://www.xiaohongshu.com/explore/686755da000000001201637e",
            "description": """周一到周五的宝宝营养烩饭来啦！每天换着花样做，宝宝超爱吃！

食材：米饭、各种蔬菜、肉类

做法：
1. 先把米饭煮好备用
2. 蔬菜切小丁，肉切碎
3. 锅中少油翻炒蔬菜和肉
4. 加入米饭一起翻炒均匀
5. 加少许清水焖煮5分钟即可

小贴士：可以根据宝宝月龄调整食材大小和软硬度

#宝宝辅食 #烩饭 #营养餐""",
            "images": [
                "https://sns-webpic-qc.xhscdn.com/202312/sample1.jpg",
                "https://sns-webpic-qc.xhscdn.com/202312/sample2.jpg",
            ],
            "comments_count": "128",
            "collect_count": "2156",
        },
        {
            "title": "8月龄宝宝一周辅食🥣，简单易做❗️",
            "author": "橘子泡泡挞",
            "date": "07-09",
            "likes": "8336",
            "url": "https://www.xiaohongshu.com/explore/686e3f8e000000001203e72c",
            "description": """8月龄宝宝的一周辅食安排！都是简单易做的，新手妈妈也能轻松上手！

📝 周一：南瓜米糊
食材：南瓜50g、米粉20g
做法：
1. 南瓜蒸熟压成泥
2. 米粉用温水冲调
3. 混合均匀即可

📝 周二：胡萝卜牛肉泥
食材：胡萝卜30g、牛肉20g
做法：
1. 牛肉煮熟切碎
2. 胡萝卜蒸熟压泥
3. 混合搅拌均匀

小贴士：
- 8月龄宝宝可以开始尝试颗粒状食物
- 注意观察宝宝是否过敏

#8月龄辅食 #宝宝辅食 #辅食日记""",
            "images": [
                "https://sns-webpic-qc.xhscdn.com/202312/sample3.jpg",
            ],
            "comments_count": "256",
            "collect_count": "4532",
        },
        {
            "title": "8-9月龄✨一周手指条不重样，营养好吃宝宝爱",
            "author": "是多宝吖",
            "date": "05-08",
            "likes": "1.4万",
            "url": "https://www.xiaohongshu.com/explore/681c89c5000000002100c51f",
            "description": """手指条是锻炼宝宝抓握能力的好帮手！分享一周不重样的手指条食谱～

🥕 周一：胡萝卜鸡肉条
食材：胡萝卜50g、鸡胸肉30g、鸡蛋1个、面粉适量
做法：
1. 胡萝卜蒸熟压泥
2. 鸡肉搅打成泥
3. 混合加蛋液和面粉
4. 搓成条状蒸15分钟

🥦 周二：西兰花土豆条
食材：西兰花30g、土豆50g
做法：
1. 食材蒸熟压泥混合
2. 搓成条状蒸熟

小贴士：
- 手指条要做成宝宝容易抓握的大小
- 蒸的时间根据粗细调整
- 可以冷冻保存一周

#手指食物 #宝宝辅食 #BLW""",
            "images": [],
            "comments_count": "890",
            "collect_count": "8765",
        },
        {
            "title": "超简单苹果松饼，零失败！！",
            "author": "澄子麻麻",
            "date": "10-18",
            "likes": "609",
            "url": "https://www.xiaohongshu.com/explore/68f30e030000000004016615",
            "description": """宝宝超爱的苹果松饼！无糖无油，健康又好吃！

食材：
- 苹果半个
- 鸡蛋1个
- 低筋面粉50g
- 配方奶30ml

做法：
1. 苹果去皮切小丁
2. 鸡蛋打散加入配方奶
3. 筛入低筋面粉搅拌均匀
4. 加入苹果丁
5. 平底锅小火煎至两面金黄

小贴士：一定要小火慢煎，不然外焦里生哦

#苹果松饼 #宝宝辅食 #烘焙""",
            "images": [],
            "comments_count": "45",
            "collect_count": "312",
        },
        {
            "title": "健脾养胃的山药芙蓉羹｜做法简单营养美味💯",
            "author": "默默妈妈",
            "date": "02-13",
            "likes": "2万",
            "url": "https://www.xiaohongshu.com/explore/67ade12e000000001801a05a",
            "description": """山药芙蓉羹，健脾养胃，宝宝肠胃不好的可以试试！

食材：
- 铁棍山药100g
- 鸡蛋1个
- 配方奶或清水适量

做法：
1. 山药去皮切段蒸熟（约15分钟）
2. 蒸熟的山药趁热压成泥
3. 鸡蛋打散
4. 山药泥加配方奶搅拌均匀
5. 倒入蛋液轻轻搅匀
6. 上锅蒸8分钟即可

小贴士：
- 铁棍山药更细腻
- 蛋液不要搅太用力，轻轻划圈
- 可以加点虾仁增加蛋白质

#山药辅食 #宝宝辅食 #健脾养胃""",
            "images": [],
            "comments_count": "1234",
            "collect_count": "15678",
        },
    ]


def main():
    """主函数"""
    # 创建收集器
    collector = BabyFoodRecipeCollector(
        output_dir=os.path.join(
            os.path.dirname(__file__), "..", "..", "baby_food_recipes"
        )
    )

    # 从示例数据加载（带完整内容）
    sample_data = create_sample_data_with_content()
    collector.add_recipes_from_search_results(sample_data, download_images=False)

    # 打印摘要
    collector.print_summary()

    # 保存到文件
    collector.save_to_json()
    collector.save_to_markdown()
    collector.save_individual_recipes()

    print("✅ 宝宝辅食菜谱收集完成！")


if __name__ == "__main__":
    main()
