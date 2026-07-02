import httpx
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import re


class Assessment:
    def __init__(self, name: str, url: str, test_type: str, description: str = "", 
                 duration: str = "", languages: List[str] = None, 
                 job_levels: List[str] = None, categories: List[str] = None):
        self.name = name
        self.url = url
        self.test_type = test_type  # K=Knowledge, P=Personality, S=Skills, A=Aptitude
        self.description = description
        self.duration = duration
        self.languages = languages or []
        self.job_levels = job_levels or []
        self.categories = categories or []
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Assessment':
        """Create Assessment from SHL catalog data dictionary."""
        # Map keys to test types
        test_type = cls._infer_test_type_from_keys(data.get("keys", []))
        
        # Clean job levels
        job_levels = data.get("job_levels", [])
        
        # Clean languages
        languages = data.get("languages", [])
        
        # Use keys as categories
        categories = data.get("keys", [])
        
        return cls(
            name=data.get("name", ""),
            url=data.get("link", ""),
            test_type=test_type,
            description=data.get("description", ""),
            duration=data.get("duration", ""),
            languages=languages,
            job_levels=job_levels,
            categories=categories
        )
    
    @staticmethod
    def _infer_test_type_from_keys(keys: List[str]) -> str:
        """Infer test type from keys."""
        if not keys:
            return "K"
        
        keys_str = " ".join(keys).lower()
        
        if "personality" in keys_str or "behavior" in keys_str:
            return "P"
        elif "ability" in keys_str or "aptitude" in keys_str or "reasoning" in keys_str:
            return "A"
        elif "simulations" in keys_str:
            return "S"
        elif "knowledge" in keys_str or "skills" in keys_str:
            return "K"
        elif "competencies" in keys_str or "development" in keys_str:
            return "S"
        else:
            return "K"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "url": self.url,
            "test_type": self.test_type,
            "description": self.description,
            "duration": self.duration,
            "languages": self.languages,
            "job_levels": self.job_levels,
            "categories": self.categories
        }


class SHLCatalog:
    BASE_URL = "https://www.shl.com/solutions/products/productcatalog/"
    
    def __init__(self):
        self.assessments: List[Assessment] = []
    
    async def scrape_catalog(self) -> List[Assessment]:
        """Scrape the SHL product catalog for Individual Test Solutions."""
        print("Scraping SHL catalog...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, get the main catalog page
            response = await client.get(self.BASE_URL)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Look for assessment cards/links
            # The catalog structure may vary, so we'll try multiple selectors
            assessment_links = []
            
            # Try to find links to individual assessment pages
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Filter for assessment pages (adjust pattern based on actual structure)
                if '/solutions/products/' in href and href not in assessment_links:
                    full_url = href if href.startswith('http') else f"https://www.shl.com{href}"
                    assessment_links.append(full_url)
            
            print(f"Found {len(assessment_links)} potential assessment links")
            
            # Limit to reasonable number for demo (in production, scrape all)
            assessment_links = assessment_links[:50]
            
            # Scrape each assessment page
            for i, url in enumerate(assessment_links):
                try:
                    print(f"Scraping assessment {i+1}/{len(assessment_links)}: {url}")
                    assessment = await self._scrape_assessment_page(client, url)
                    if assessment:
                        self.assessments.append(assessment)
                    time.sleep(0.5)  # Be respectful to the server
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    continue
        
        print(f"Successfully scraped {len(self.assessments)} assessments")
        return self.assessments
    
    async def _scrape_assessment_page(self, client: httpx.AsyncClient, url: str) -> Optional[Assessment]:
        """Scrape a single assessment page."""
        try:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract name (usually in h1 or title)
            name = ""
            h1 = soup.find('h1')
            if h1:
                name = h1.get_text(strip=True)
            else:
                name = soup.title.get_text(strip=True) if soup.title else url.split('/')[-1]
            
            # Determine test type from content
            text = soup.get_text().lower()
            test_type = self._infer_test_type(text)
            
            # Extract description
            description = ""
            desc_elem = soup.find('meta', attrs={'name': 'description'})
            if desc_elem:
                description = desc_elem.get('content', '')
            else:
                # Try to find first paragraph
                p = soup.find('p')
                if p:
                    description = p.get_text(strip=True)
            
            # Extract duration if available
            duration = self._extract_duration(text)
            
            # Extract languages
            languages = self._extract_languages(text)
            
            # Extract job levels
            job_levels = self._extract_job_levels(text)
            
            # Extract categories
            categories = self._extract_categories(text)
            
            return Assessment(
                name=name,
                url=url,
                test_type=test_type,
                description=description,
                duration=duration,
                languages=languages,
                job_levels=job_levels,
                categories=categories
            )
        except Exception as e:
            print(f"Error scraping assessment page {url}: {e}")
            return None
    
    def _infer_test_type(self, text: str) -> str:
        """Infer test type from content."""
        if 'personality' in text or 'opq' in text.lower():
            return 'P'
        elif 'knowledge' in text or 'java' in text or 'programming' in text or 'technical' in text:
            return 'K'
        elif 'aptitude' in text or 'numerical' in text or 'verbal' in text or 'reasoning' in text:
            return 'A'
        elif 'skill' in text or 'competency' in text:
            return 'S'
        else:
            return 'K'  # Default to Knowledge
    
    def _extract_duration(self, text: str) -> str:
        """Extract duration from text."""
        # Look for patterns like "30 minutes", "1 hour", etc.
        patterns = [
            r'(\d+)\s*(?:minutes?|mins?)',
            r'(\d+)\s*(?:hours?|hrs?)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract available languages."""
        languages = []
        common_langs = ['english', 'spanish', 'french', 'german', 'chinese', 'japanese', 'portuguese']
        for lang in common_langs:
            if lang in text:
                languages.append(lang.capitalize())
        return languages
    
    def _extract_job_levels(self, text: str) -> List[str]:
        """Extract job levels."""
        levels = []
        level_terms = ['entry', 'junior', 'mid', 'senior', 'executive', 'manager', 'director', 'individual contributor']
        for term in level_terms:
            if term in text:
                levels.append(term.capitalize())
        return levels
    
    def _extract_categories(self, text: str) -> List[str]:
        """Extract assessment categories."""
        categories = []
        category_terms = ['it', 'sales', 'customer service', 'leadership', 'administrative', 'finance', 'engineering']
        for term in category_terms:
            if term in text:
                categories.append(term.capitalize())
        return categories
    
    def save_to_json(self, filepath: str):
        """Save catalog to JSON file."""
        data = [a.to_dict() for a in self.assessments]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_json(self, filepath: str):
        """Load catalog from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Check if data is in SHL catalog format
        if data and isinstance(data, list) and "keys" in data[0]:
            self.assessments = [Assessment.from_dict(item) for item in data]
        else:
            self.assessments = [Assessment(**item) for item in data]
    
    def search(self, query: str, max_results: int = 10) -> List[Assessment]:
        """Simple keyword search over assessments."""
        query_lower = query.lower()
        scored = []
        
        for assessment in self.assessments:
            score = 0
            # Search in name
            if query_lower in assessment.name.lower():
                score += 10
            # Search in description
            if query_lower in assessment.description.lower():
                score += 5
            # Search in categories
            for cat in assessment.categories:
                if query_lower in cat.lower():
                    score += 3
            # Search in job levels
            for level in assessment.job_levels:
                if query_lower in level.lower():
                    score += 2
            
            if score > 0:
                scored.append((score, assessment))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:max_results]]
