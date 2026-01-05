start:
	fastapi dev state_agent.py

# 安装playwright浏览器
install-browser:
	pip install playwright
	playwright install chromium

# 爬取小红书宝宝辅食（默认10个）
crawl:
	python crawl_xiaohongshu.py

# 爬取小红书宝宝辅食（20个帖子）
crawl-more:
	python crawl_xiaohongshu.py --max 20

# 无头模式爬取（不显示浏览器）
crawl-headless:
	python crawl_xiaohongshu.py --headless --max 15

.PHONY: start install-browser crawl crawl-more crawl-headless
