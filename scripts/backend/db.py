import sqlite3
import threading
import time
import os

DB_PATH = "app.db"

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Rooms Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                created_at TEXT
            )
        ''')
        
        # Messages Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT,
                user TEXT,
                original_text TEXT,
                translated_text TEXT,
                timestamp TEXT,
                lang_code TEXT,
                audio_base64 TEXT,
                FOREIGN KEY(room_id) REFERENCES rooms(id)
            )
        ''')

        # Dubbing History Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dubbing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                video_path TEXT,
                audio_path TEXT,
                source_lang TEXT,
                target_lang TEXT,
                timestamp TEXT,
                type TEXT,
                srt_path TEXT,
                segments TEXT
            )
        ''')
        
        # Migration: Ensure segments column exists (if table already existed)
        try:
            self.cursor.execute("ALTER TABLE dubbing_history ADD COLUMN segments TEXT")
        except sqlite3.OperationalError:
            pass # Column likely already exists

        # Migration: Ensure session_id column exists
        try:
            self.cursor.execute("ALTER TABLE dubbing_history ADD COLUMN session_id TEXT")
        except sqlite3.OperationalError:
            pass # Column likely already exists

        # Migration: Ensure audio_base64 column exists in messages
        try:
            self.cursor.execute("ALTER TABLE messages ADD COLUMN audio_base64 TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Video Outputs Table for storing processed videos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                title TEXT,
                description TEXT,
                video_path TEXT,
                audio_path TEXT,
                source_lang TEXT,
                target_lang TEXT,
                quality_mode TEXT,
                duration REAL,
                file_size INTEGER,
                timestamp TEXT,
                type TEXT
            )
        ''')
        
        # Heartbeats for active participants
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS heartbeats (
                room_id TEXT,
                user TEXT,
                last_seen REAL,
                PRIMARY KEY (room_id, user)
            )
        ''')
            
        self.conn.commit()

    def update_heartbeat(self, room_id, user):
        with self._lock:
            self.cursor.execute('''
                INSERT OR REPLACE INTO heartbeats (room_id, user, last_seen)
                VALUES (?, ?, ?)
            ''', (room_id, user, time.time()))
            self.conn.commit()

    def get_participants(self, room_id, active_threshold=30):
        cutoff = time.time() - active_threshold
        with self._lock:
            self.cursor.execute('''
                SELECT user FROM heartbeats 
                WHERE room_id = ? AND last_seen > ?
            ''', (room_id, cutoff))
            return [row[0] for row in self.cursor.fetchall()]
            
        self.conn.commit()

    def add_message(self, room_id, user, original, translated, lang_code, audio_base64=None):
        timestamp = time.strftime("%H:%M:%S")
        with self._lock:
            # Ensure room exists
            self.cursor.execute("INSERT OR IGNORE INTO rooms (id, created_at) VALUES (?, ?)", (room_id, timestamp))
            
            self.cursor.execute('''
                INSERT INTO messages (room_id, user, original_text, translated_text, timestamp, lang_code, audio_base64)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (room_id, user, original, translated, timestamp, lang_code, audio_base64))
            self.conn.commit()

    def get_messages(self, room_id, limit=50):
        with self._lock:
            self.cursor.execute('''
                SELECT user, original_text, translated_text, timestamp, lang_code, audio_base64
                FROM messages 
                WHERE room_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ''', (room_id, limit))
            rows = self.cursor.fetchall()
            return rows[::-1] 

    def add_history_item(self, item, session_id):
        import json
        segments_json = json.dumps(item.get('segments', []))
        
        with self._lock:
            self.cursor.execute('''
                INSERT INTO dubbing_history (session_id, video_path, audio_path, source_lang, target_lang, timestamp, type, srt_path, segments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                item.get('video_path'),
                item.get('audio_path'),
                item.get('source_lang'),
                item.get('target_lang'),
                item.get('timestamp'),
                item.get('type'),
                item.get('srt'),
                segments_json
            ))
            self.conn.commit()

    def get_history(self, session_id):
        import json
        with self._lock:
            self.cursor.execute('SELECT * FROM dubbing_history WHERE session_id = ? ORDER BY id DESC', (session_id,))
            rows = self.cursor.fetchall()
            history = []
            for row in rows:
                # Handle potential JSON errors
                try:
                    # Index shifted by 1 because of session_id column if it was at index 1?
                    # Let's check schema: id, session_id, video_path...
                    # If table was newly created: 0:id, 1:session_id, 2:video...
                    # If migrated, session_id is last.
                    # SAFEST WAY: Fetch by column name or handle dynamic index.
                    # For now, assuming new schema or consistent migration order is tricky.
                    # Let's use row_factory or just assume migration appended it to end if it didn't exist.
                    
                    # Wait, if I use "SELECT *", the order depends on creation.
                    # Better to specify columns in SELECT.
                    pass
                except:
                    pass
            
            # RE-IMPLEMENTING get_history with explicit columns to be safe
            self.cursor.execute('''
                SELECT id, video_path, audio_path, source_lang, target_lang, timestamp, type, srt_path, segments 
                FROM dubbing_history 
                WHERE session_id = ? OR session_id IS NULL 
                ORDER BY id DESC
            ''', (session_id,))
            
            rows = self.cursor.fetchall()
            history = []
            for row in rows:
                try:
                    segs = json.loads(row[8]) if row[8] else []
                except:
                    segs = []
                    
                history.append({
                    'id': row[0],
                    'video_path': row[1],
                    'audio_path': row[2],
                    'source_lang': row[3],
                    'target_lang': row[4],
                    'timestamp': row[5],
                    'type': row[6],
                    'srt': row[7],
                    'segments': segs
                })
            return history

    def get_stats(self):
        with self._lock:
            self.cursor.execute("SELECT COUNT(*) FROM dubbing_history")
            total_dubs = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM video_outputs")
            total_videos = self.cursor.fetchone()[0]
            
            return {
                "total_dubs": total_dubs,
                "total_messages": total_messages,
                "total_videos": total_videos
            }
    
    def add_video_output(self, session_id, title, description, video_path, audio_path, 
                        source_lang, target_lang, quality_mode, duration, file_size, output_type):
        """Save processed video output to database"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self.cursor.execute('''
                INSERT INTO video_outputs (session_id, title, description, video_path, audio_path,
                                          source_lang, target_lang, quality_mode, duration, 
                                          file_size, timestamp, type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, title, description, video_path, audio_path, source_lang, 
                  target_lang, quality_mode, duration, file_size, timestamp, output_type))
            self.conn.commit()
            return self.cursor.lastrowid
    
    def get_video_outputs(self, session_id, limit=50):
        """Retrieve video outputs for a specific session"""
        with self._lock:
            self.cursor.execute('''
                SELECT id, title, description, video_path, audio_path, source_lang, target_lang,
                       quality_mode, duration, file_size, timestamp, type
                FROM video_outputs
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            ''', (session_id, limit))
            rows = self.cursor.fetchall()
            
            videos = []
            for row in rows:
                videos.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'video_path': row[3],
                    'audio_path': row[4],
                    'source_lang': row[5],
                    'target_lang': row[6],
                    'quality_mode': row[7],
                    'duration': row[8],
                    'file_size': row[9],
                    'timestamp': row[10],
                    'type': row[11]
                })
            return videos
