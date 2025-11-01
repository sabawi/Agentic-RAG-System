"""
Academic Research API Client

Handles communication with Semantic Scholar, arXiv, and PubMed APIs.

Features:
- Multi-API search with result aggregation
- Automatic domain detection (CS vs Medical vs General)
- Rate limiting compliance
- Result deduplication
- Smart source selection
"""

import aiohttp
import asyncio
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.academic_config import AcademicConfig
import logging
import re

logger = logging.getLogger(__name__)


class AcademicResearchClient:
    """
    Client for academic research APIs.

    Supports:
    - Semantic Scholar (citation-ranked papers)
    - arXiv (preprints in CS/Math/Physics)
    - PubMed (biomedical research)
    """

    def __init__(self):
        self.config = AcademicConfig
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_times = {
            'semantic_scholar': 0,
            'arxiv': 0,
            'pubmed': 0
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _rate_limit(self, api: str):
        """Enforce rate limiting for specific API."""
        limits = {
            'semantic_scholar': self.config.SEMANTIC_SCHOLAR_RATE_LIMIT,
            'arxiv': self.config.ARXIV_RATE_LIMIT,
            'pubmed': self.config.PUBMED_RATE_LIMIT
        }

        current_time = time.time()
        time_since_last = current_time - self.last_request_times[api]
        required_interval = limits.get(api, 1.0)

        if time_since_last < required_interval:
            sleep_time = required_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_times[api] = time.time()

    def search_papers(self, query: str, sources: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for academic papers (synchronous wrapper).

        Args:
            query: Search query
            sources: List of sources to search ('semantic_scholar', 'arxiv', 'pubmed')
                    If None, auto-detect based on query
            limit: Maximum results per source

        Returns:
            List of paper dictionaries
        """
        try:
            # Auto-detect sources if not specified
            if sources is None:
                sources = self._detect_sources(query)

            # Run async search
            try:
                loop = asyncio.get_running_loop()
                # Already in async context - use thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._search_papers_async(query, sources, limit)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop - safe to use asyncio.run
                return asyncio.run(self._search_papers_async(query, sources, limit))

        except Exception as e:
            logger.error(f"Error in search_papers: {e}")
            raise

    def _detect_sources(self, query: str) -> List[str]:
        """
        Auto-detect which sources to search based on query.

        Args:
            query: Search query

        Returns:
            List of source names
        """
        query_lower = query.lower()

        # Medical/biomedical keywords -> PubMed
        medical_keywords = [
            'disease', 'cancer', 'treatment', 'clinical', 'patient', 'medical',
            'drug', 'therapy', 'diagnosis', 'health', 'medicine', 'biology',
            'gene', 'protein', 'cell', 'covid', 'virus', 'infection'
        ]

        # CS/ML/Physics keywords -> arXiv + Semantic Scholar
        tech_keywords = [
            'algorithm', 'machine learning', 'deep learning', 'neural', 'ai',
            'artificial intelligence', 'computer', 'software', 'quantum',
            'physics', 'mathematics', 'optimization', 'model', 'training'
        ]

        is_medical = any(keyword in query_lower for keyword in medical_keywords)
        is_tech = any(keyword in query_lower for keyword in tech_keywords)

        if is_medical and not is_tech:
            return ['pubmed', 'semantic_scholar']
        elif is_tech and not is_medical:
            return ['semantic_scholar', 'arxiv']
        else:
            # General or ambiguous - use all sources
            return ['semantic_scholar', 'arxiv', 'pubmed']

    async def _search_papers_async(self, query: str, sources: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        Async implementation of paper search.
        """
        try:
            tasks = []

            # Create tasks for each source
            if 'semantic_scholar' in sources:
                tasks.append(self._search_semantic_scholar(query, limit))
            if 'arxiv' in sources:
                tasks.append(self._search_arxiv(query, limit))
            if 'pubmed' in sources:
                tasks.append(self._search_pubmed(query, limit))

            # Execute all searches in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Combine and deduplicate results
            all_papers = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"API search failed: {result}")
                    continue
                if isinstance(result, list):
                    all_papers.extend(result)

            # Deduplicate by title similarity
            deduplicated = self._deduplicate_papers(all_papers)

            # Sort by relevance score (citation count, recency)
            sorted_papers = self._rank_papers(deduplicated)

            return sorted_papers[:limit * len(sources)]  # Return more results when multiple sources

        finally:
            await self._close_session()

    async def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Semantic Scholar API."""
        try:
            await self._rate_limit('semantic_scholar')
            session = await self._get_session()

            url = f"{self.config.SEMANTIC_SCHOLAR_BASE_URL}/paper/search"
            params = {
                'query': query,
                'limit': min(limit, self.config.MAX_RESULTS_PER_SOURCE),
                'fields': ','.join(self.config.SEMANTIC_SCHOLAR_FIELDS)
            }

            headers = self.config.get_headers('semantic_scholar')

            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Semantic Scholar API returned status {response.status}")
                    return []

                data = await response.json()
                papers = data.get('data', [])

                # Normalize to common format
                normalized = []
                for paper in papers:
                    normalized.append({
                        'source': 'Semantic Scholar',
                        'title': paper.get('title', 'Untitled'),
                        'authors': [a.get('name', '') for a in paper.get('authors', [])],
                        'abstract': paper.get('abstract', ''),
                        'year': paper.get('year'),
                        'publication_date': paper.get('publicationDate'),
                        'url': paper.get('url', ''),
                        'pdf_url': paper.get('openAccessPdf', {}).get('url') if paper.get('openAccessPdf') else None,
                        'citation_count': paper.get('citationCount', 0),
                        'influential_citations': paper.get('influentialCitationCount', 0),
                        'journal': paper.get('journal', {}).get('name') if paper.get('journal') else None,
                        'publication_types': paper.get('publicationTypes', [])
                    })

                logger.info(f"Semantic Scholar: Found {len(normalized)} papers")
                return normalized

        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            return []

    async def _search_arxiv(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search arXiv API."""
        try:
            await self._rate_limit('arxiv')
            session = await self._get_session()

            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': min(limit, self.config.MAX_RESULTS_PER_SOURCE),
                'sortBy': self.config.ARXIV_DEFAULT_SORT,
                'sortOrder': 'descending'
            }

            async with session.get(self.config.ARXIV_BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"arXiv API returned status {response.status}")
                    return []

                xml_content = await response.text()
                papers = self._parse_arxiv_xml(xml_content)

                logger.info(f"arXiv: Found {len(papers)} papers")
                return papers

        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []

    def _parse_arxiv_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv XML response."""
        papers = []

        try:
            # Parse XML
            root = ET.fromstring(xml_content)

            # Define namespaces
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            # Find all entry elements
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                published_elem = entry.find('atom:published', ns)
                updated_elem = entry.find('atom:updated', ns)
                id_elem = entry.find('atom:id', ns)

                # Get authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)

                # Get PDF link
                pdf_url = None
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        pdf_url = link.get('href')
                        break

                # Extract year from published date
                year = None
                if published_elem is not None and published_elem.text:
                    try:
                        year = int(published_elem.text[:4])
                    except:
                        pass

                papers.append({
                    'source': 'arXiv',
                    'title': title_elem.text.strip() if title_elem is not None else 'Untitled',
                    'authors': authors,
                    'abstract': summary_elem.text.strip() if summary_elem is not None else '',
                    'year': year,
                    'publication_date': published_elem.text if published_elem is not None else None,
                    'url': id_elem.text if id_elem is not None else '',
                    'pdf_url': pdf_url,
                    'citation_count': 0,  # arXiv doesn't provide citation counts
                    'influential_citations': 0,
                    'journal': 'arXiv Preprint',
                    'publication_types': ['Preprint']
                })

        except Exception as e:
            logger.error(f"Error parsing arXiv XML: {e}")

        return papers

    async def _search_pubmed(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search PubMed API."""
        try:
            # PubMed requires two API calls: search + fetch
            pmids = await self._pubmed_search(query, limit)

            if not pmids:
                return []

            papers = await self._pubmed_fetch(pmids)
            logger.info(f"PubMed: Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []

    async def _pubmed_search(self, query: str, limit: int) -> List[str]:
        """Search PubMed for PMIDs."""
        try:
            await self._rate_limit('pubmed')
            session = await self._get_session()

            url = f"{self.config.PUBMED_BASE_URL}/esearch.fcgi"
            params = {
                'db': self.config.PUBMED_DATABASE,
                'term': query,
                'retmax': min(limit, self.config.MAX_RESULTS_PER_SOURCE),
                'retmode': 'json',
                'sort': 'relevance'
            }

            if self.config.PUBMED_API_KEY:
                params['api_key'] = self.config.PUBMED_API_KEY

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"PubMed search returned status {response.status}")
                    return []

                data = await response.json()
                pmids = data.get('esearchresult', {}).get('idlist', [])
                return pmids

        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []

    async def _pubmed_fetch(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch PubMed article details by PMIDs."""
        try:
            await self._rate_limit('pubmed')
            session = await self._get_session()

            url = f"{self.config.PUBMED_BASE_URL}/esummary.fcgi"
            params = {
                'db': self.config.PUBMED_DATABASE,
                'id': ','.join(pmids),
                'retmode': 'json'
            }

            if self.config.PUBMED_API_KEY:
                params['api_key'] = self.config.PUBMED_API_KEY

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"PubMed fetch returned status {response.status}")
                    return []

                data = await response.json()
                result = data.get('result', {})

                papers = []
                for pmid in pmids:
                    article = result.get(pmid)
                    if not article:
                        continue

                    # Parse authors
                    authors = [a.get('name', '') for a in article.get('authors', [])]

                    # Extract year
                    year = None
                    pub_date = article.get('pubdate', '')
                    if pub_date:
                        year_match = re.search(r'(\d{4})', pub_date)
                        if year_match:
                            year = int(year_match.group(1))

                    papers.append({
                        'source': 'PubMed',
                        'title': article.get('title', 'Untitled'),
                        'authors': authors,
                        'abstract': '',  # Summary endpoint doesn't include abstract
                        'year': year,
                        'publication_date': pub_date,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'pdf_url': None,  # PubMed doesn't directly provide PDFs
                        'citation_count': 0,  # Not provided in summary
                        'influential_citations': 0,
                        'journal': article.get('source', ''),
                        'publication_types': article.get('pubtype', [])
                    })

                return papers

        except Exception as e:
            logger.error(f"PubMed fetch error: {e}")
            return []

    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate papers by title similarity."""
        if not papers:
            return []

        unique_papers = []
        seen_titles = set()

        for paper in papers:
            title = paper.get('title', '').lower().strip()

            # Normalize title (remove punctuation, extra spaces)
            normalized_title = re.sub(r'[^\w\s]', '', title)
            normalized_title = re.sub(r'\s+', ' ', normalized_title)

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_papers.append(paper)

        logger.info(f"Deduplication: {len(papers)} -> {len(unique_papers)} papers")
        return unique_papers

    def _rank_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank papers by relevance score."""
        def score_paper(paper):
            score = 0

            # Citation count (heavy weight)
            citations = paper.get('citation_count', 0)
            score += citations * 10

            # Influential citations (very heavy weight)
            influential = paper.get('influential_citations', 0)
            score += influential * 50

            # Recency bonus
            year = paper.get('year')
            if year:
                current_year = datetime.now().year
                recency = max(0, current_year - year)
                score += max(0, 100 - recency * 10)  # Newer papers get bonus

            # Source priority (Semantic Scholar > arXiv > PubMed for general relevance)
            source_priority = {
                'Semantic Scholar': 20,
                'arXiv': 15,
                'PubMed': 10
            }
            score += source_priority.get(paper.get('source', ''), 0)

            return score

        ranked = sorted(papers, key=score_paper, reverse=True)
        return ranked
