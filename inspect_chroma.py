import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

DB_PATH = os.path.join("chroma_db", "chroma.sqlite3")

if not os.path.exists(DB_PATH):
    print("❌ chroma.sqlite3 not found. Run the app first and upload a chat.")
    exit()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Show all tables
print("=" * 60)
print("[TABLES] IN CHROMA.SQLITE3")
print("=" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(f"  → {t[0]}")

# 2. Show Collections
print("\n" + "=" * 60)
print("[COLLECTIONS] (Your Chat Uploads)")
print("=" * 60)
try:
    cursor.execute("SELECT id, name, dimension FROM collections;")
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  ID: {r[0]} | Name: {r[1]} | Dimensions: {r[2]}")
    else:
        print("  ⚠️ No collections found. Upload a chat first.")
except Exception as e:
    print(f"  Error: {e}")

# 3. Show Embedding Metadata (user, date)
print("\n" + "=" * 60)
print("[METADATA] EMBEDDING METADATA (First 20 rows)")
print("=" * 60)
try:
    cursor.execute("SELECT id, key, string_value FROM embedding_metadata LIMIT 20;")
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  Embedding ID: {r[0]} | Key: {r[1]} | Value: {r[2]}")
    else:
        print("  ⚠️ No metadata found.")
except Exception as e:
    print(f"  Error: {e}")

# 4. Show Embeddings count
print("\n" + "=" * 60)
print("[COUNT] EMBEDDINGS")
print("=" * 60)
try:
    cursor.execute("SELECT COUNT(*) FROM embeddings;")
    count = cursor.fetchone()[0]
    print(f"  Total messages indexed: {count}")
except Exception as e:
    print(f"  Error: {e}")

# 5. Show raw documents (stored strings)
print("\n" + "=" * 60)
print("[DOCUMENTS] SAMPLE (First 10 messages)")
print("=" * 60)
try:
    cursor.execute("SELECT id, document FROM embeddings LIMIT 10;")
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  [{r[0]}] {r[1]}")
    else:
        print("  ⚠️ No documents found.")
except Exception as e:
    print(f"  Error: {e}")

conn.close()
print("\n✅ Done.")
