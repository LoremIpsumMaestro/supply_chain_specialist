#!/usr/bin/env python3
"""CLI script to ingest knowledge into the permanent knowledge base."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

import yaml

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.knowledge_service import knowledge_service
from backend.services.document_parser import PDFParser


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_knowledge(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load knowledge from JSON file.

    Expected format:
    {
      "knowledge_items": [
        {
          "title": "...",
          "category": "...",
          "subcategory": "...",
          "content": "...",
          "tags": ["tag1", "tag2"],
          "metadata": {...}
        }
      ]
    }
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = data.get('knowledge_items', [])
        logger.info(f"Loaded {len(items)} knowledge items from {file_path}")
        return items

    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return []


def load_yaml_knowledge(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load knowledge from YAML file.

    Expected format:
    knowledge_items:
      - title: "..."
        category: "..."
        subcategory: "..."
        content: "..."
        tags:
          - tag1
          - tag2
        metadata:
          key: value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        items = data.get('knowledge_items', [])
        logger.info(f"Loaded {len(items)} knowledge items from {file_path}")
        return items

    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        return []


def load_markdown_knowledge(
    file_path: Path,
    category: str,
    subcategory: str = None,
    tags: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load knowledge from Markdown file.

    Splits content by headers (# or ##) and creates one knowledge item per section.

    Args:
        file_path: Path to markdown file
        category: Category to assign
        subcategory: Optional subcategory
        tags: Optional tags to assign

    Returns:
        List of knowledge items
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        items = []

        # Split by headers (# Title or ## Title)
        sections = []
        current_section = {'title': '', 'content': ''}

        for line in content.split('\n'):
            if line.startswith('# ') or line.startswith('## '):
                # New section
                if current_section['content'].strip():
                    sections.append(current_section)

                # Extract title (remove # or ##)
                title = line.lstrip('#').strip()
                current_section = {'title': title, 'content': ''}
            else:
                current_section['content'] += line + '\n'

        # Add last section
        if current_section['content'].strip():
            sections.append(current_section)

        # Convert sections to knowledge items
        for section in sections:
            if not section['title']:
                section['title'] = f"Section from {file_path.name}"

            item = {
                'title': section['title'],
                'category': category,
                'content': section['content'].strip(),
            }

            if subcategory:
                item['subcategory'] = subcategory

            if tags:
                item['tags'] = tags

            item['metadata'] = {'source_file': str(file_path)}

            items.append(item)

        logger.info(f"Loaded {len(items)} sections from markdown file {file_path}")
        return items

    except Exception as e:
        logger.error(f"Error loading markdown file {file_path}: {e}")
        return []


def load_text_knowledge(
    file_path: Path,
    title: str,
    category: str,
    subcategory: str = None,
    tags: List[str] = None,
    chunk_size: int = 4000,
) -> List[Dict[str, Any]]:
    """
    Load knowledge from plain text file.

    Splits content into chunks if too long.

    Args:
        file_path: Path to text file
        title: Title for knowledge item
        category: Category to assign
        subcategory: Optional subcategory
        tags: Optional tags to assign
        chunk_size: Max characters per chunk

    Returns:
        List of knowledge items
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        items = []

        # Split by paragraphs
        paragraphs = content.split('\n\n')

        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + '\n\n'
            else:
                if current_chunk.strip():
                    item = {
                        'title': f"{title} (Part {chunk_idx + 1})" if chunk_idx > 0 else title,
                        'category': category,
                        'content': current_chunk.strip(),
                    }

                    if subcategory:
                        item['subcategory'] = subcategory

                    if tags:
                        item['tags'] = tags

                    item['metadata'] = {
                        'source_file': str(file_path),
                        'chunk_index': chunk_idx
                    }

                    items.append(item)
                    chunk_idx += 1

                current_chunk = para + '\n\n'

        # Add last chunk
        if current_chunk.strip():
            item = {
                'title': f"{title} (Part {chunk_idx + 1})" if chunk_idx > 0 else title,
                'category': category,
                'content': current_chunk.strip(),
            }

            if subcategory:
                item['subcategory'] = subcategory

            if tags:
                item['tags'] = tags

            item['metadata'] = {
                'source_file': str(file_path),
                'chunk_index': chunk_idx
            }

            items.append(item)

        logger.info(f"Loaded {len(items)} chunks from text file {file_path}")
        return items

    except Exception as e:
        logger.error(f"Error loading text file {file_path}: {e}")
        return []


def load_pdf_knowledge(
    file_path: Path,
    title: str,
    category: str,
    subcategory: str = None,
    tags: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load knowledge from PDF file using PDFParser.

    Args:
        file_path: Path to PDF file
        title: Base title for knowledge items (will append page numbers)
        category: Category to assign
        subcategory: Optional subcategory
        tags: Optional tags to assign

    Returns:
        List of knowledge items
    """
    try:
        # Read PDF file
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()

        # Parse PDF using PDFParser
        pdf_parser = PDFParser()
        chunks = pdf_parser.parse(pdf_bytes, file_path.name)

        items = []

        for chunk in chunks:
            # Extract page number from metadata
            page_num = chunk.metadata.get('page', 'unknown')
            chunk_index = chunk.metadata.get('chunk_index', 0)

            # Build title with page reference
            if chunk_index > 0:
                item_title = f"{title} - Page {page_num} (Part {chunk_index + 1})"
            else:
                item_title = f"{title} - Page {page_num}"

            item = {
                'title': item_title,
                'category': category,
                'content': chunk.content,
            }

            if subcategory:
                item['subcategory'] = subcategory

            if tags:
                item['tags'] = tags

            item['metadata'] = {
                'source_file': str(file_path),
                'page': page_num,
                'chunk_index': chunk_index,
                'file_type': 'pdf'
            }

            items.append(item)

        logger.info(f"Loaded {len(items)} chunks from PDF file {file_path}")
        return items

    except Exception as e:
        logger.error(f"Error loading PDF file {file_path}: {e}")
        return []


def ingest_from_file(
    file_path: str,
    file_type: str = None,
    category: str = None,
    subcategory: str = None,
    tags: List[str] = None,
    title: str = None,
) -> int:
    """
    Ingest knowledge from a file.

    Args:
        file_path: Path to file
        file_type: File type (json, yaml, markdown, text, pdf) - auto-detected if None
        category: Category (required for markdown/text/pdf)
        subcategory: Optional subcategory
        tags: Optional tags
        title: Title (required for text/pdf files)

    Returns:
        Number of items ingested
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return 0

    # Auto-detect file type
    if not file_type:
        ext = path.suffix.lower()
        type_map = {
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
            '.pdf': 'pdf',
        }
        file_type = type_map.get(ext)

    if not file_type:
        logger.error(f"Unknown file type for {file_path}. Please specify --type")
        return 0

    # Load knowledge items
    items = []

    if file_type == 'json':
        items = load_json_knowledge(path)

    elif file_type == 'yaml':
        items = load_yaml_knowledge(path)

    elif file_type == 'markdown':
        if not category:
            logger.error("Category required for markdown files (--category)")
            return 0
        items = load_markdown_knowledge(path, category, subcategory, tags)

    elif file_type == 'text':
        if not category or not title:
            logger.error("Category and title required for text files (--category, --title)")
            return 0
        items = load_text_knowledge(path, title, category, subcategory, tags)

    elif file_type == 'pdf':
        if not category or not title:
            logger.error("Category and title required for PDF files (--category, --title)")
            return 0
        items = load_pdf_knowledge(path, title, category, subcategory, tags)

    else:
        logger.error(f"Unsupported file type: {file_type}")
        return 0

    # Ingest items
    if items:
        count = knowledge_service.add_knowledge_batch(items)
        logger.info(f"Successfully ingested {count} knowledge items from {file_path}")
        return count
    else:
        logger.warning(f"No knowledge items to ingest from {file_path}")
        return 0


def list_categories():
    """List all categories in knowledge base."""
    categories = knowledge_service.list_categories()

    if categories:
        print("\nCategories in knowledge base:")
        for cat in categories:
            print(f"  - {cat}")
    else:
        print("\nNo categories found in knowledge base.")


def delete_category(category: str):
    """Delete all knowledge in a category."""
    confirm = input(f"Are you sure you want to delete all knowledge in category '{category}'? (yes/no): ")

    if confirm.lower() == 'yes':
        success = knowledge_service.delete_by_category(category)
        if success:
            print(f"Deleted all knowledge in category: {category}")
        else:
            print(f"Error deleting category: {category}")
    else:
        print("Cancelled.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Ingest knowledge into the permanent knowledge base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest from JSON file
  python ingest_knowledge.py --file knowledge.json

  # Ingest from YAML file
  python ingest_knowledge.py --file knowledge.yaml

  # Ingest from Markdown file
  python ingest_knowledge.py --file supply_chain_guide.md --category supply_chain --tags logistics inventory

  # Ingest from text file
  python ingest_knowledge.py --file lead_times.txt --category inventory --title "Lead Time Best Practices"

  # Ingest from PDF file
  python ingest_knowledge.py --file book.pdf --category supply_chain --title "Supply Chain Management" --tags forecasting

  # List categories
  python ingest_knowledge.py --list-categories

  # Delete category
  python ingest_knowledge.py --delete-category supply_chain
        """
    )

    parser.add_argument('--file', type=str, help='File to ingest')
    parser.add_argument('--type', type=str, choices=['json', 'yaml', 'markdown', 'text', 'pdf'], help='File type (auto-detected if not specified)')
    parser.add_argument('--category', type=str, help='Category (required for markdown/text/pdf)')
    parser.add_argument('--subcategory', type=str, help='Subcategory')
    parser.add_argument('--tags', nargs='+', help='Tags (space-separated)')
    parser.add_argument('--title', type=str, help='Title (required for text/pdf files)')
    parser.add_argument('--list-categories', action='store_true', help='List all categories')
    parser.add_argument('--delete-category', type=str, help='Delete all knowledge in a category')

    args = parser.parse_args()

    # Handle commands
    if args.list_categories:
        list_categories()

    elif args.delete_category:
        delete_category(args.delete_category)

    elif args.file:
        ingest_from_file(
            file_path=args.file,
            file_type=args.type,
            category=args.category,
            subcategory=args.subcategory,
            tags=args.tags,
            title=args.title,
        )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
