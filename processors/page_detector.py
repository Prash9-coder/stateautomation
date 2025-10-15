from typing import List
from models.statement_schema import PageRange

class PageDetector:
    @staticmethod
    def filter_relevant_pages(page_ranges: List[PageRange]) -> List[PageRange]:
        """Keep only statement pages, filter out promotional/blank pages"""
        return [
            pr for pr in page_ranges 
            if pr.page_type in ["statement", "attachment"]
        ]
    
    @staticmethod
    def get_page_numbers(page_ranges: List[PageRange]) -> List[int]:
        """Get list of page numbers to keep"""
        pages = []
        for pr in page_ranges:
            pages.extend(range(pr.start, pr.end + 1))
        return sorted(set(pages))