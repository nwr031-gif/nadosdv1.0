"""
Database manager for SQLite with SQLAlchemy.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from nados.config import get_config


Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, db_path: Optional[str] = None, echo: bool = False) -> None:
        self.db_path = db_path or get_config().database.path
        self.echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database engine and create tables."""
        if self._initialized:
            return
        
        # Ensure directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self._engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=self.echo,
            connect_args={"check_same_thread": False},
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        
        # Import models to register them
        from nados.persistence import models  # noqa: F401
        
        # Create tables
        Base.metadata.create_all(self._engine)
        
        # Run migrations
        self._run_migrations()
        
        self._initialized = True
    
    def _run_migrations(self) -> None:
        """Run database migrations."""
        # Use raw connection to avoid recursion
        with self._engine.connect() as conn:
            # Check current schema version
            result = conn.execute(text("PRAGMA user_version")).scalar()
            current_version = result or 0
            
            target_version = 1
            
            if current_version < target_version:
                # Migration from version 0 to 1
                # Tables are created by Base.metadata.create_all
                conn.execute(text(f"PRAGMA user_version = {target_version}"))
                conn.commit()
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        if not self._initialized:
            self.initialize()
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """Get a session (caller must close)."""
        if not self._initialized:
            self.initialize()
        return self._session_factory()
    
    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
    
    def backup(self, backup_path: str) -> None:
        """Create a backup of the database."""
        import shutil
        shutil.copy2(self.db_path, backup_path)
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        with self.session() as session:
            session.execute(text("VACUUM"))


_db_manager: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database(db_path: Optional[str] = None, echo: bool = False) -> DatabaseManager:
    """Initialize the global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(db_path, echo)
    _db_manager.initialize()
    return _db_manager