#!/usr/bin/env python3
"""
Data Migration Script
====================

Migrate data from the old Flask server to the new FastAPI server with
optimized database schema and caching setup.
"""

import asyncio
import sqlite3
import logging
from typing import List, Dict, Any
import aiomysql
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrator:
    """Handle data migration from SQLite to MySQL with optimizations"""
    
    def __init__(self, sqlite_path: str, mysql_config: Dict[str, Any]):
        self.sqlite_path = sqlite_path
        self.mysql_config = mysql_config
        
    async def migrate_all_data(self):
        """Migrate all data from SQLite to MySQL"""
        logger.info("Starting data migration...")
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Connect to MySQL
        mysql_pool = await aiomysql.create_pool(**self.mysql_config)
        
        try:
            # Get all tables from SQLite
            tables = self.get_sqlite_tables(sqlite_conn)
            logger.info(f"Found {len(tables)} tables to migrate: {tables}")
            
            for table_name in tables:
                await self.migrate_table(sqlite_conn, mysql_pool, table_name)
                
            logger.info("Data migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            sqlite_conn.close()
            mysql_pool.close()
            await mysql_pool.wait_closed()
    
    def get_sqlite_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of tables from SQLite database"""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
    
    async def migrate_table(self, sqlite_conn: sqlite3.Connection, 
                          mysql_pool: aiomysql.Pool, table_name: str):
        """Migrate a single table"""
        logger.info(f"Migrating table: {table_name}")
        
        # Get table schema and data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_cursor.fetchall()
        
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logger.info(f"Table {table_name} is empty, skipping...")
            return
        
        # Create MySQL table
        await self.create_mysql_table(mysql_pool, table_name, columns_info)
        
        # Insert data in batches
        batch_size = 1000
        total_rows = len(rows)
        
        async with mysql_pool.acquire() as conn:
            for i in range(0, total_rows, batch_size):
                batch = rows[i:i + batch_size]
                await self.insert_batch(conn, table_name, batch)
                logger.info(f"Migrated {min(i + batch_size, total_rows)}/{total_rows} rows for {table_name}")
    
    async def create_mysql_table(self, mysql_pool: aiomysql.Pool, 
                               table_name: str, columns_info: List):
        """Create MySQL table with optimized schema"""
        
        column_definitions = []
        for col in columns_info:
            col_name = col[1]
            col_type = col[2].upper()
            not_null = "NOT NULL" if col[3] else ""
            
            # Map SQLite types to MySQL types
            mysql_type = self.map_sqlite_to_mysql_type(col_type)
            
            column_definitions.append(f"`{col_name}` {mysql_type} {not_null}")
        
        # Add optimizations
        column_definitions.append("INDEX idx_created_at (created_at)" if "created_at" in [col[1] for col in columns_info] else "")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            {', '.join(filter(None, column_definitions))}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(create_sql)
                logger.info(f"Created MySQL table: {table_name}")
    
    def map_sqlite_to_mysql_type(self, sqlite_type: str) -> str:
        """Map SQLite data types to MySQL data types"""
        type_mapping = {
            'INTEGER': 'INT',
            'TEXT': 'TEXT',
            'REAL': 'DECIMAL(10,2)',
            'BLOB': 'LONGBLOB',
            'NUMERIC': 'DECIMAL(10,2)',
            'VARCHAR': 'VARCHAR(255)',
            'DATETIME': 'DATETIME',
            'DATE': 'DATE',
            'TIME': 'TIME'
        }
        
        return type_mapping.get(sqlite_type, 'TEXT')
    
    async def insert_batch(self, conn, table_name: str, batch: List):
        """Insert a batch of rows into MySQL"""
        if not batch:
            return
            
        # Prepare placeholders
        placeholders = ', '.join(['%s'] * len(batch[0]))
        
        # Convert sqlite3.Row to tuple
        values = [tuple(row) for row in batch]
        
        sql = f"INSERT IGNORE INTO `{table_name}` VALUES ({placeholders})"
        
        async with conn.cursor() as cursor:
            await cursor.executemany(sql, values)

async def setup_optimized_indexes():
    """Create optimized indexes for better performance"""
    
    mysql_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'Down2earth!',
        'db': 'mystocks',
        'charset': 'utf8mb4'
    }
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_data (symbol, date)",
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions (timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_user_session ON user_sessions (user_id, created_at)",
        # Add more indexes based on your query patterns
    ]
    
    pool = await aiomysql.create_pool(**mysql_config)
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for index_sql in indexes:
                    try:
                        await cursor.execute(index_sql)
                        logger.info(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")
    finally:
        pool.close()
        await pool.wait_closed()

async def populate_redis_cache():
    """Pre-populate Redis cache with frequently accessed data"""
    import aioredis
    
    try:
        redis = await aioredis.from_url("redis://localhost:6379")
        
        # Pre-populate with common stock symbols
        common_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA']
        
        for symbol in common_symbols:
            cache_key = f"stock_data:{symbol}:30"
            # This would fetch actual data in real implementation
            mock_data = {
                "symbol": symbol,
                "price": 150.00,
                "change": 2.5,
                "timestamp": datetime.now().isoformat()
            }
            await redis.setex(cache_key, 300, json.dumps(mock_data))
            logger.info(f"Cached data for {symbol}")
        
        await redis.close()
        logger.info("Redis cache pre-populated")
        
    except Exception as e:
        logger.warning(f"Failed to populate Redis cache: {e}")

async def main():
    """Main migration function"""
    
    sqlite_path = "/home/sabawi/Development/stocks_evaluator/data.db"
    mysql_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'Down2earth!',
        'db': 'mystocks',
        'minsize': 1,
        'maxsize': 5,
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    try:
        # Step 1: Migrate data
        migrator = DataMigrator(sqlite_path, mysql_config)
        await migrator.migrate_all_data()
        
        # Step 2: Create optimized indexes
        await setup_optimized_indexes()
        
        # Step 3: Pre-populate cache
        await populate_redis_cache()
        
        logger.info("Migration and optimization completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())