# library_manager/inventory.py
"""
LibraryInventory class: maintains a list of Book objects,
supports add/search/list, and JSON persistence.
"""

import json
from pathlib import Path
from typing import List, Optional
import logging

from library_manager.book import Book

logger = logging.getLogger(__name__)

class LibraryInventory:
    """
    Manages a collection of Book objects, supports add/search/display,
    and save/load to a JSON file.
    """

    def __init__(self, storage_path: Path):
        """
        Initialize with a Path object pointing to the JSON storage file.
        If file exists, attempt to load it; otherwise start with empty list.
        """
        self.storage_path = storage_path
        self.books: List[Book] = []
        self._ensure_storage()
        self.load_from_file()

    def _ensure_storage(self):
        """Ensure the parent directory exists."""
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created data directory: {self.storage_path.parent}")

    def add_book(self, title: str, author: str, isbn: str) -> Book:
        """
        Create and add a new Book to inventory.
        If ISBN already exists, raise ValueError.
        """
        if self.search_by_isbn(isbn) is not None:
            raise ValueError(f"A book with ISBN {isbn} already exists.")
        book = Book(title=title.strip(), author=author.strip(), isbn=isbn.strip())
        self.books.append(book)
        logger.info(f"Added book: {book}")
        self.save_to_file()
        return book

    def search_by_title(self, query: str) -> List[Book]:
        """
        Search for books by title substring (case-insensitive).
        Returns list of matching Book objects.
        """
        q = query.strip().lower()
        return [b for b in self.books if q in b.title.lower()]

    def search_by_isbn(self, isbn: str) -> Optional[Book]:
        """Return a Book matching the ISBN, or None."""
        for b in self.books:
            if b.isbn == isbn.strip():
                return b
        return None

    def display_all(self) -> List[str]:
        """Return list of string representations of all books."""
        return [str(b) for b in self.books]

    def issue_book(self, isbn: str) -> bool:
        """Attempt to issue a book by ISBN. Returns True on success."""
        book = self.search_by_isbn(isbn)
        if book is None:
            raise LookupError(f"No book found with ISBN {isbn}.")
        if book.issue():
            logger.info(f"Issued book: {book}")
            self.save_to_file()
            return True
        else:
            logger.info(f"Attempted to issue already issued book: {book}")
            return False

    def return_book(self, isbn: str) -> bool:
        """Attempt to return a book by ISBN. Returns True on success."""
        book = self.search_by_isbn(isbn)
        if book is None:
            raise LookupError(f"No book found with ISBN {isbn}.")
        if book.return_book():
            logger.info(f"Returned book: {book}")
            self.save_to_file()
            return True
        else:
            logger.info(f"Attempted to return a book that was not issued: {book}")
            return False

    def save_to_file(self):
        """Save current inventory to JSON file atomically."""
        try:
            data = [b.to_dict() for b in self.books]
            # Write atomically using a temp file
            tmp_path = self.storage_path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self.storage_path)
            logger.info(f"Saved {len(self.books)} books to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save to {self.storage_path}: {e}")
            raise

    def load_from_file(self):
        """Load inventory from JSON file. Handles missing/corrupt files gracefully."""
        if not self.storage_path.exists():
            logger.info(f"No storage file found at {self.storage_path}. Starting with empty inventory.")
            self.books = []
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate and convert to Book objects
            loaded_books = []
            for entry in data:
                # Basic validation
                if not all(k in entry for k in ("title", "author", "isbn", "status")):
                    logger.error(f"Invalid entry in storage file: {entry}")
                    continue
                loaded_books.append(Book(
                    title=entry["title"],
                    author=entry["author"],
                    isbn=str(entry["isbn"]),
                    status=entry.get("status", "available")
                ))
            self.books = loaded_books
            logger.info(f"Loaded {len(self.books)} books from {self.storage_path}")
        except json.JSONDecodeError:
            logger.error(f"Storage file {self.storage_path} is not valid JSON. Starting with empty inventory.")
            self.books = []
        except Exception as e:
            logger.error(f"Error loading storage file {self.storage_path}: {e}")
            self.books = []