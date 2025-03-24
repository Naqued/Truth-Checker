"""Utility for loading knowledge into the repository."""

import logging
import os
import json
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup

from truth_checker.domain.ports import KnowledgeRepository

logger = logging.getLogger(__name__)


async def load_from_json_file(
    repository: KnowledgeRepository,
    file_path: str
) -> int:
    """Load knowledge from a JSON file.
    
    Args:
        repository: The knowledge repository to load into
        file_path: Path to the JSON file
        
    Returns:
        Number of documents loaded
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different formats
        if isinstance(data, list):
            documents = data
        elif isinstance(data, dict) and 'documents' in data:
            documents = data['documents']
        else:
            documents = [data]
        
        # Add the documents
        doc_ids = []
        for doc in documents:
            doc_id = await repository.add_document(doc)
            if doc_id:
                doc_ids.append(doc_id)
        
        logger.info(f"Loaded {len(doc_ids)} documents from {file_path}")
        return len(doc_ids)
        
    except Exception as e:
        logger.error(f"Error loading from JSON file {file_path}: {e}")
        return 0


async def load_from_fact_check_sites(
    repository: KnowledgeRepository,
    urls: List[str],
    max_pages: int = 5
) -> int:
    """Load knowledge from fact-checking websites.
    
    Args:
        repository: The knowledge repository to load into
        urls: List of URLs to fact-checking site articles
        max_pages: Maximum number of pages to load per URL
        
    Returns:
        Number of documents loaded
    """
    loaded_count = 0
    
    for url in urls:
        try:
            logger.info(f"Loading fact-check content from {url}")
            
            # Fetch the content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main content (this will be site-specific)
            main_content = extract_fact_check_content(soup, url)
            if not main_content:
                logger.warning(f"Could not extract content from {url}")
                continue
                
            # Create a document
            document = {
                "content": main_content,
                "metadata": {
                    "source": url,
                    "source_type": "fact_checking_organization",
                    "date_retrieved": str(response.headers.get('date', '')),
                }
            }
            
            # Add to repository
            doc_id = await repository.add_document(document)
            if doc_id:
                loaded_count += 1
            
        except Exception as e:
            logger.error(f"Error loading from {url}: {e}")
    
    logger.info(f"Loaded {loaded_count} fact-check documents")
    return loaded_count


def extract_fact_check_content(soup: BeautifulSoup, url: str) -> str:
    """Extract the main content from a fact-checking page.
    
    This function needs customization for different fact-checking sites.
    
    Args:
        soup: BeautifulSoup parsed content
        url: The URL of the page
        
    Returns:
        Extracted content as text
    """
    content = ""
    
    # Extract title
    title_tag = soup.find('h1')
    if title_tag:
        content += f"Title: {title_tag.get_text().strip()}\n\n"
    
    # Extract for different fact-checking sites
    if "politifact.com" in url:
        # PolitiFact specific extraction
        verdict_tag = soup.find('div', class_='m-statement__quote')
        if verdict_tag:
            content += f"Claim: {verdict_tag.get_text().strip()}\n\n"
            
        rating_tag = soup.find('div', class_='m-statement__meter')
        if rating_tag:
            rating_text = rating_tag.get_text().strip()
            content += f"Rating: {rating_text}\n\n"
            
        article_tag = soup.find('article', class_='m-textblock')
        if article_tag:
            content += f"Analysis: {article_tag.get_text().strip()}\n\n"
            
    elif "factcheck.org" in url:
        # FactCheck.org specific extraction
        article_tag = soup.find('div', class_='entry-content')
        if article_tag:
            content += article_tag.get_text().strip()
            
    elif "snopes.com" in url:
        # Snopes specific extraction
        claim_tag = soup.find('div', class_='claim-text')
        if claim_tag:
            content += f"Claim: {claim_tag.get_text().strip()}\n\n"
            
        rating_tag = soup.find('div', class_='rating-wrapper')
        if rating_tag:
            content += f"Rating: {rating_tag.get_text().strip()}\n\n"
            
        article_tag = soup.find('div', class_='single-body')
        if article_tag:
            content += f"Analysis: {article_tag.get_text().strip()}\n\n"
            
    else:
        # Generic extraction - just get all paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            content += p.get_text().strip() + "\n\n"
    
    return content


async def populate_sample_knowledge(repository: KnowledgeRepository) -> int:
    """Populate the repository with some sample knowledge.
    
    Args:
        repository: The knowledge repository to populate
        
    Returns:
        Number of documents added
    """
    sample_documents = [
        {
            "content": "The Earth is approximately 4.54 billion years old, with an error range of about 50 million years. This age has been determined through radiometric dating of meteorite material and is consistent with the ages of the oldest-known terrestrial and lunar samples.",
            "metadata": {
                "source": "Scientific consensus",
                "source_type": "scientific_database",
                "topic": "Earth",
                "confidence": 0.95
            }
        },
        {
            "content": "Water boils at 100 degrees Celsius (212 degrees Fahrenheit) at standard atmospheric pressure (1 atmosphere). The boiling point can change based on atmospheric pressure - at higher elevations where pressure is lower, water boils at a lower temperature.",
            "metadata": {
                "source": "Basic physics knowledge",
                "source_type": "scientific_database",
                "topic": "Physics",
                "confidence": 0.99
            }
        },
        {
            "content": "The speed of light in a vacuum is 299,792,458 meters per second. This is a fundamental physical constant denoted by the symbol 'c'. According to Einstein's theory of relativity, this speed represents the maximum speed at which energy, matter, or information can travel through space.",
            "metadata": {
                "source": "Physics principles",
                "source_type": "scientific_database",
                "topic": "Physics",
                "confidence": 0.99
            }
        },
        {
            "content": "The capital of France is Paris. Paris is situated on the Seine River, in northern France, at the heart of the Île-de-France region. It is one of the world's most populous urban areas and one of the most visited cities worldwide.",
            "metadata": {
                "source": "Geographic knowledge",
                "source_type": "factual_database",
                "topic": "Geography",
                "confidence": 0.99
            }
        },
        {
            "content": "Mount Everest is Earth's highest mountain above sea level, located in the Mahalangur Himal sub-range of the Himalayas on the border between China and Nepal. Its elevation is 8,848.86 meters (29,031.7 ft) above sea level. The international border between China and Nepal runs across its summit point.",
            "metadata": {
                "source": "Geographic knowledge",
                "source_type": "factual_database",
                "topic": "Geography",
                "confidence": 0.99
            }
        },
        {
            "content": "Climate change is primarily caused by human activities, particularly the burning of fossil fuels which increases greenhouse gas concentrations in Earth's atmosphere. Scientific consensus on this fact is overwhelming, with more than a dozen independent scientific societies reaching this conclusion based on multiple lines of evidence.",
            "metadata": {
                "source": "Scientific consensus",
                "source_type": "scientific_database",
                "topic": "Climate",
                "confidence": 0.95
            }
        },
        {
            "content": "Vaccines are safe and effective for preventing infectious diseases. The benefits of vaccination greatly outweigh the risks. Side effects are generally minor and temporary. Serious side effects are extremely rare.",
            "metadata": {
                "source": "Medical consensus",
                "source_type": "scientific_database",
                "topic": "Medicine",
                "confidence": 0.95
            }
        },
        {
            "content": "The primary cause of lung cancer is smoking tobacco. About 80-90% of lung cancer cases are caused by smoking, and many of the remainder are caused by exposure to secondhand smoke, radon gas, asbestos, and other carcinogens.",
            "metadata": {
                "source": "Medical research",
                "source_type": "scientific_database",
                "topic": "Medicine",
                "confidence": 0.95
            }
        }
    ]
    
    # Add the sample documents
    doc_ids = []
    for doc in sample_documents:
        doc_id = await repository.add_document(doc)
        if doc_id:
            doc_ids.append(doc_id)
    
    logger.info(f"Added {len(doc_ids)} sample documents to knowledge repository")
    return len(doc_ids) 