#!/usr/bin/env python3
"""
Database initialization script for NADOS Dv1.0.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nados.config import get_config
from nados.persistence import init_database


def main() -> int:
    """Initialize the database."""
    config = get_config()
    db_path = config.database.path
    
    print(f"Initializing database at: {db_path}")
    
    try:
        db = init_database(db_path, config.database.echo)
        print("Database initialized successfully!")
        
        # Verify tables
        with db.session() as session:
            from sqlalchemy import text
            tables = session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )).fetchall()
            print(f"Created tables: {[t[0] for t in tables]}")
        
        db.close()
        return 0
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())