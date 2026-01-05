#!/usr/bin/env python3
"""
小红书宝宝辅食爬虫命令行工具

使用方法:
    python crawl_xiaohongshu.py [选项]

示例:
    # 爬取10个帖子（默认）
    python crawl_xiaohongshu.py

    # 爬取20个帖子
    python crawl_xiaohongshu.py --max 20

    # 自定义关键词
    python crawl_xiaohongshu.py --keyword "宝宝辅食食谱"

    # 无头模式（不显示浏览器窗口）
    python crawl_xiaohongshu.py --headless

    # 指定输出目录
    python crawl_xiaohongshu.py --output my_recipes
"""

import argparse
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pkg.tools.xiaohongshu_browser_crawler import XiaohongshuBrowserCrawler


def main():
    parser = argparse.ArgumentParser(
        description="小红书宝宝辅食浏览器自动化爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python crawl_xiaohongshu.py                    # 使用默认设置爬取
  python crawl_xiaohongshu.py --max 20           # 爬取20个帖子
  python crawl_xiaohongshu.py --keyword "辅食"   # 自定义搜索关键词
  python crawl_xiaohongshu.py --headless         # 无头模式运行
        """,
    )

    parser.add_argument(
        "-k",
        "--keyword",
        type=str,
        default="宝宝辅食",
        help="搜索关键词 (默认: 宝宝辅食)",
    )

    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=10,
        help="最大爬取数量 (默认: 10)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="baby_food_recipes",
        help="输出目录 (默认: baby_food_recipes)",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行（不显示浏览器窗口）",
    )

    parser.add_argument(
        "--no-details",
        action="store_true",
        help="不获取帖子详情（只获取搜索结果）",
    )

    parser.add_argument(
        "--slow",
        type=int,
        default=100,
        help="操作延迟毫秒数 (默认: 100)",
    )

    parser.add_argument(
        "--login-timeout",
        type=int,
        default=300,
        help="登录等待超时时间秒数 (默认: 300)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🍼 小红书宝宝辅食浏览器自动化爬虫")
    print("=" * 60)
    print(f"  搜索关键词: {args.keyword}")
    print(f"  最大数量: {args.max}")
    print(f"  输出目录: {args.output}")
    print(f"  无头模式: {'是' if args.headless else '否'}")
    print(f"  获取详情: {'否' if args.no_details else '是'}")
    print(f"  登录超时: {args.login_timeout} 秒")
    print("=" * 60)
    print()

    # 检查playwright是否安装
    try:
        import importlib.util

        if importlib.util.find_spec("playwright") is None:
            raise ImportError("playwright not found")
    except ImportError:
        print("❌ 错误: 未安装 playwright")
        print()
        print("请运行以下命令安装:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print()
        sys.exit(1)

    # 创建爬虫实例
    crawler = XiaohongshuBrowserCrawler(
        output_dir=args.output,
        headless=args.headless,
        slow_mo=args.slow,
    )

    # 执行爬取
    async def run():
        recipes = await crawler.crawl(
            keyword=args.keyword,
            max_notes=args.max,
            get_details=not args.no_details,
            login_timeout=args.login_timeout,
        )

        if recipes:
            # 打印摘要
            crawler.print_summary()

            # 保存到文件
            crawler.save_to_json()
            crawler.save_to_markdown()
            crawler.save_individual_recipes()

            print()
            print("✅ 爬取完成！")
            print(f"📂 文件保存在: {args.output}/")
        else:
            print("❌ 未获取到任何内容")
            sys.exit(1)

    asyncio.run(run())


if __name__ == "__main__":
    main()
