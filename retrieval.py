from typing import List, Dict, Optional
from catalog import Assessment, SHLCatalog
import re


class RetrievalSystem:
    """Retrieval system for SHL assessments."""
    
    def __init__(self, catalog: SHLCatalog):
        self.catalog = catalog
    
    def retrieve(
        self,
        query: str,
        job_level: Optional[str] = None,
        test_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Assessment]:
        """Retrieve assessments based on query and filters."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored = []
        
        for assessment in self.catalog.assessments:
            score = 0
            name_lower = assessment.name.lower()
            desc_lower = assessment.description.lower()
            
            # Word-level matching in name (higher weight)
            name_words = set(name_lower.split())
            matching_name_words = query_words & name_words
            score += len(matching_name_words) * 15
            
            # Exact phrase match in name (highest weight)
            if query_lower in name_lower:
                score += 20
            
            # Word-level matching in description
            desc_words = set(desc_lower.split())
            matching_desc_words = query_words & desc_words
            score += len(matching_desc_words) * 5
            
            # Exact phrase match in description
            if query_lower in desc_lower:
                score += 10
            
            # Job level matching
            if job_level:
                job_level_lower = job_level.lower()
                for level in assessment.job_levels:
                    if job_level_lower in level.lower():
                        score += 8
                # Also check in description
                if job_level_lower in desc_lower:
                    score += 4
            
            # Test type filtering
            if test_types:
                if assessment.test_type in test_types:
                    score += 6
                else:
                    score -= 5  # Penalize if it doesn't match requested types
            
            # Category matching
            if categories:
                for cat in categories:
                    cat_lower = cat.lower()
                    for assessment_cat in assessment.categories:
                        if cat_lower in assessment_cat.lower():
                            score += 7
                    # Also check in description
                    if cat_lower in desc_lower:
                        score += 3
            
            # Special boosting for leadership selection scenarios
            if "selection" in query_lower and ("leadership" in query_lower or "executive" in query_lower or "director" in query_lower):
                # Boost OPQ32r and related reports
                if "opq" in name_lower or "personality" in name_lower:
                    score += 25
                if "leadership" in name_lower or "competency" in name_lower:
                    score += 20
            
            # Special boosting for leadership/management roles
            if "leadership" in query_lower or "management" in query_lower or "executive" in query_lower:
                if "leadership" in name_lower or "management" in name_lower:
                    score += 15
            
            # Base score for any match to ensure we return something
            if score > 0:
                scored.append((score, assessment))
        
        # If no matches, return all assessments with low scores
        if not scored:
            for assessment in self.catalog.assessments:
                scored.append((1, assessment))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:max_results]]
    
    def compare(self, assessment_names: List[str]) -> Dict[str, Dict]:
        """Compare assessments by name."""
        comparisons = {}
        
        for name in assessment_names:
            # Find assessment by name (fuzzy match)
            assessment = self._find_by_name(name)
            if assessment:
                comparisons[name] = {
                    "name": assessment.name,
                    "url": assessment.url,
                    "test_type": assessment.test_type,
                    "description": assessment.description,
                    "duration": assessment.duration,
                    "languages": assessment.languages,
                    "job_levels": assessment.job_levels,
                    "categories": assessment.categories
                }
        
        return comparisons
    
    def _find_by_name(self, name: str) -> Optional[Assessment]:
        """Find assessment by name (fuzzy match)."""
        name_lower = name.lower()
        
        # Exact match first
        for assessment in self.catalog.assessments:
            if name_lower == assessment.name.lower():
                return assessment
        
        # Partial match
        for assessment in self.catalog.assessments:
            if name_lower in assessment.name.lower() or assessment.name.lower() in name_lower:
                return assessment
        
        return None
    
    def get_all_test_types(self) -> List[str]:
        """Get all unique test types in catalog."""
        return list(set(a.test_type for a in self.catalog.assessments))
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories in catalog."""
        categories = set()
        for assessment in self.catalog.assessments:
            categories.update(assessment.categories)
        return list(categories)
    
    def get_all_job_levels(self) -> List[str]:
        """Get all unique job levels in catalog."""
        levels = set()
        for assessment in self.catalog.assessments:
            levels.update(assessment.job_levels)
        return list(levels)
