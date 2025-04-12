import asyncio
import aiohttp
import random
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]


async def fetch_urls(session, search_content, start_day, end_day, page, retry=0):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        async with session.get(
                f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={search_content}&start={page}&pd=3&ds={start_day}&de={end_day}",
                headers=headers,
                timeout=10,
        ) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                ul = soup.select_one("div.group_news > ul.list_news")
                if not ul:
                    return []
                urls = [
                    a_tag["href"]
                    for li in ul.find_all("li")
                    for a_tag in li.select('div.news_area > div.news_info > div.info_group > a.info')
                    if "n.news.naver.com" in a_tag["href"]
                ]
                return urls
    except Exception as e:
        if retry < 3:
            await asyncio.sleep(1)
            return await fetch_urls(session, search_content, start_day, end_day, page, retry + 1)
    return []


async def crawl_urls(search_content, startday, endday, max_news, batch_size=10):
    url_set = set()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10)) as session:
        for start_day, end_day in zip(startday, endday):
            for page in tqdm(range(1, 2000, batch_size * 10), desc="Fetching URL batches"):
                tasks = [
                    fetch_urls(session, search_content, start_day, end_day, page + i * 10)
                    for i in range(batch_size)
                ]
                results = await asyncio.gather(*tasks)
                for urls in results:
                    url_set.update(urls)
                    if len(url_set) >= max_news:
                        return list(url_set)[:max_news]
                await asyncio.sleep(0.3)
            if len(url_set) >= max_news:
                break
    return list(url_set)[:max_news]


async def fetch_news_content(session, url, retry=0):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                company = soup.select_one("#ct > div.media_end_head.go_trans > div.media_end_head_top > a > img[alt]")
                title = soup.select_one("#ct > div.media_end_head.go_trans > div.media_end_head_title > h2")
                content = soup.select_one("article#dic_area")
                return {
                    "company": company["alt"] if company else "None",
                    "url": url,
                    "title": title.text if title else "None",
                    "content": content.text.strip() if content else "None",
                }
            else:
                print(f"HTTP 요청 실패: {url} (상태 코드: {response.status})")
    except Exception as e:
        print(f"오류 발생 (URL: {url}): {e}")
        if retry < 3:
            await asyncio.sleep(1)
            return await fetch_news_content(session, url, retry + 1)
    return {"company": "None", "url": url, "title": "None", "content": "None"}

async def crawl_news(search_content, startday, endday, max_news):
    urls = await crawl_urls(search_content, startday, endday, max_news)
    news_data = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10)) as session:
        for batch in tqdm([urls[i:i + 10] for i in range(0, len(urls), 10)], desc="Fetching News"):
            tasks = [fetch_news_content(session, url) for url in batch]
            news_data.extend(await asyncio.gather(*tasks))
            await asyncio.sleep(0.3)

    # --------------- 데이터 전처리 단계 -----------------
    df_news = pd.DataFrame(news_data)

    # 1. 중복 기사 제거
    df_news.drop_duplicates(subset=['title', 'content'], inplace=True)

    # 2. 너무 짧은 기사 제거 (본문이 50자 이하인 기사)
    df_news = df_news[df_news['content'].str.len() > 50]

    # 3. DataFrame을 리스트로 변환하여 반환
    processed_news = df_news.to_dict(orient="records")
    return processed_news


def start_crawling(search_content, startday, endday, max_news):
    return asyncio.run(crawl_news(search_content, startday, endday, max_news))
