from dataclasses import dataclass


@dataclass(frozen=True)
class RSSSource:
    name: str
    url: str


RSS_SOURCES: list[RSSSource] = [
    RSSSource("OpenAI Blog",       "https://openai.com/blog/rss.xml"),
    RSSSource("Google AI Blog",    "https://blog.research.google/feeds/posts/default/-/AI"),
    RSSSource("HuggingFace Blog",  "https://huggingface.co/blog/feed.xml"),
    RSSSource("TechCrunch AI",     "https://techcrunch.com/category/artificial-intelligence/feed/"),
    RSSSource("Ars Technica AI",   "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    RSSSource("MIT Tech Review AI","https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    RSSSource("VentureBeat AI",    "https://venturebeat.com/category/ai/feed/"),
]

# Tavily 웹 검색 쿼리 목록
SEARCH_QUERIES: list[str] = [
    "AI artificial intelligence latest news",
    "LLM large language model release 2025",
    "generative AI breakthrough research",
]
