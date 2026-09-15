import re
from typing import List, Optional, Tuple


class ParsedSearchQuery:
    def __init__(
        self,
        raw_query: str,
        fts_expression: str,
        domain_filter: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ):
        self.raw_query = raw_query
        self.fts_expression = fts_expression
        self.domain_filter = domain_filter
        self.keywords = keywords or []

    def __repr__(self) -> str:
        return f"<ParsedSearchQuery raw='{self.raw_query}' fts='{self.fts_expression}' domain='{self.domain_filter}'>"


class QueryParser:
    """
    Parses and sanitizes web search queries:
    - Extracts 'site:domain.com' directives
    - Preserves exact double-quoted phrases: "AI studio"
    - Sanitizes special characters for SQLite FTS5 safely
    """

    SITE_REGEX = re.compile(r"(?:site|domain):([^\s]+)", re.IGNORECASE)
    PHRASE_REGEX = re.compile(r'"([^"]+)"')

    @classmethod
    def parse(cls, raw_query: str) -> ParsedSearchQuery:
        text = (raw_query or "").strip()
        if not text:
            return ParsedSearchQuery(raw_query="", fts_expression="", domain_filter=None, keywords=[])

        # 1. Extract site: filter or auto-detect URL / domain query
        domain_filter: Optional[str] = None
        site_match = cls.SITE_REGEX.search(text)
        if site_match:
            domain_filter = site_match.group(1).lower().strip()
            text = cls.SITE_REGEX.sub("", text).strip()
        elif text.lower().startswith(("http://", "https://")):
            # User pasted a full URL into the search bar
            try:
                from urllib.parse import urlparse
                parsed_u = urlparse(text)
                if parsed_u.netloc:
                    domain_filter = parsed_u.netloc.lower().strip()
                    # If there is a subpath with keywords, extract them
                    path_slug = (parsed_u.path or "").strip("/")
                    if path_slug:
                        text = path_slug.replace("-", " ").replace("_", " ").replace("/", " ")
                    else:
                        text = ""
            except Exception:
                pass
        elif re.match(r"^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$", text):
            # User entered a bare domain e.g. "resumeforgeai.in" or "github.com/trending"
            parts = text.split("/", 1)
            domain_filter = parts[0].lower().strip()
            text = parts[1].replace("-", " ").replace("_", " ").replace("/", " ") if len(parts) > 1 else ""

        # 2. Extract exact double-quoted phrases
        phrases = cls.PHRASE_REGEX.findall(text)
        text_without_phrases = cls.PHRASE_REGEX.sub("", text)

        # 3. Clean and extract individual terms
        # Remove characters that can break FTS5 parser unless inside quotes
        clean_terms = re.findall(r"[\w\-]+", text_without_phrases)

        keywords = list(phrases) + [t for t in clean_terms if t.lower() not in ("and", "or", "not")]
        if not keywords and domain_filter:
            # If search was purely a domain/URL, include base domain term as keyword
            base_name = domain_filter.split(".")[0]
            if base_name and base_name not in ("www", "http", "https"):
                keywords.append(base_name)

        # 4. Construct FTS5 expression
        tokens: List[str] = []

        # Add exact phrases wrapped in double quotes
        for p in phrases:
            cleaned_p = p.replace('"', "").strip()
            if cleaned_p:
                tokens.append(f'"{cleaned_p}"')

        # Add individual keyword tokens
        for t in clean_terms:
            t_lower = t.lower()
            if t_lower in ("and", "or", "not"):
                tokens.append(t.upper())
            else:
                # Add prefix search or exact word token
                tokens.append(f'"{t}"')

        if not tokens:
            fts_expr = ""
        else:
            # Join with AND if no explicit boolean operators were provided
            joined: List[str] = []
            for i, token in enumerate(tokens):
                joined.append(token)
                if (
                    i < len(tokens) - 1
                    and token not in ("AND", "OR", "NOT")
                    and tokens[i + 1] not in ("AND", "OR", "NOT")
                ):
                    joined.append("AND")
            fts_expr = " ".join(joined)

        return ParsedSearchQuery(
            raw_query=raw_query,
            fts_expression=fts_expr,
            domain_filter=domain_filter,
            keywords=keywords,
        )


query_parser = QueryParser()
