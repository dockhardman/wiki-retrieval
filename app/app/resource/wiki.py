from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Text, Union

from mediawiki import MediaWiki
from mediawiki.exceptions import PageError
from pyassorted.asyncio import run_func

from app.config import logger
from app.exceptions import NotFound
from app.schema.models import Document


class WikiClient:
    max_timeout: int = 120
    default_timeout: int = 15
    max_top_k: int = 10
    max_sentences: int = 8
    max_chars: int = 4000

    def __init__(
        self,
        default_lang: Text = "en",
        top_k: int = 5,
        sentences: int = 4,
        chars: int = 0,
        timeout: float = default_timeout,
        concurrent: int = 2,
    ):
        self.default_lang = default_lang
        self.default_client = MediaWiki(lang=self.default_lang, timeout=timeout)
        self.lang_client_map: Dict[Text, MediaWiki] = {
            self.default_lang: self.default_client
        }
        self.top_k = min(top_k, self.max_top_k)
        self.sentences = min(sentences, self.max_sentences)
        self.chars = min(chars, self.max_chars)
        self.timeout = (
            self.default_timeout if timeout < 0 else min(timeout, self.max_timeout)
        )
        self.concurrent = int(concurrent) or None

    @property
    def supported_languages(self) -> Set[Text]:
        return set(self.default_client.supported_languages.keys())

    def get_client(self, lang: Optional[Text] = None) -> "MediaWiki":
        lang = lang.lower().strip() if lang else self.default_lang

        if lang not in self.supported_languages:
            raise ValueError(f"Language {lang} not supported.")

        if lang not in self.lang_client_map:
            self.lang_client_map[lang] = MediaWiki(lang=lang, timeout=self.timeout)

        return self.lang_client_map[lang]

    def query(
        self,
        query: Text,
        lang: Optional[Text] = None,
        top_k: Optional[int] = None,
        sentences: Optional[int] = None,
        chars: Optional[int] = None,
        timeout: Optional[float] = None,
        exclude_titles: Optional[List[Text]] = None,
    ) -> List[Document]:
        query = query.strip()
        lang = lang.lower().strip() if lang else self.default_lang
        top_k = min(top_k, self.max_top_k) if top_k else self.top_k
        sentences = min(sentences, self.max_sentences) if sentences else self.sentences
        chars = min(chars, self.max_chars) if chars else self.chars
        timeout = timeout or self.timeout

        wiki_client = self.get_client(lang=lang)

        (titles, suggestion) = wiki_client.search(
            query=query, results=top_k, suggestion=True
        )
        if suggestion:
            titles.append(suggestion)
        logger.debug(f"Query '{query}' to wiki({lang}) returned titles: {titles}")

        titles = [title for title in titles if title not in exclude_titles]

        title_to_content: Dict[Text, Optional[Union[Text, Exception]]] = {
            title: None for title in titles
        }
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            future_to_title = {
                executor.submit(
                    self._request_by_title,
                    wiki_client=wiki_client,
                    title=title,
                    sentences=sentences,
                    chars=chars,
                ): title
                for title in titles
            }
            for future in as_completed(future_to_title):
                title = future_to_title[future]
                try:
                    page_content = future.result()
                    title_to_content[title] = page_content
                except Exception as e:
                    title_to_content[title] = e

        docs: List[Document] = []
        for title, _content in title_to_content.items():
            if isinstance(_content, Exception):
                logger.exception(_content)
                continue

            if not _content:
                logger.error(f"Wiki page {title} not found.")
                continue

            content = _content or ""
            doc = Document(
                text=content,
                metadata=dict(name=title, title=title, source="wiki", lang=lang),
            )
            docs.append(doc)
        return docs

    async def async_query(
        self,
        query: Text,
        lang: Optional[Text] = None,
        top_k: Optional[int] = None,
        sentences: Optional[int] = None,
        chars: Optional[int] = None,
        timeout: Optional[float] = None,
        exclude_titles: Optional[List[Text]] = None,
    ) -> List[Document]:
        docs = await run_func(
            self.query,
            query=query,
            lang=lang,
            top_k=top_k,
            sentences=sentences,
            chars=chars,
            timeout=timeout,
            exclude_titles=exclude_titles,
        )
        return docs

    def _request_by_title(
        self, wiki_client: "MediaWiki", title: Text, sentences: int, chars: int
    ) -> Text:
        try:
            wiki_page = wiki_client.page(title)
            page_text = wiki_page.summarize(sentences=sentences, chars=chars)
            return page_text

        except PageError as e:
            raise NotFound(f"Wiki page {title} not found: {e}")

        except Exception as e:
            raise e
