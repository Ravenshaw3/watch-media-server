# Advanced Search Service for Watch Media Server
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import sqlite3

class SearchService:
    def __init__(self, db_path: str = 'watch_media.db'):
        self.db_path = db_path
        self.search_filters = {
            'year_range': None,
            'genres': [],
            'rating_min': 0,
            'rating_max': 10,
            'duration_min': 0,
            'duration_max': None,
            'file_size_min': 0,
            'file_size_max': None,
            'added_date_range': None,
            'play_count_min': 0,
            'play_count_max': None,
            'languages': [],
            'has_subtitles': None,
            'has_poster': None
        }
    
    def build_search_query(self, search_term: str = '', filters: Dict = None, 
                          sort_by: str = 'title', sort_order: str = 'ASC', 
                          limit: int = 50, offset: int = 0) -> tuple:
        """Build SQL query for advanced search"""
        filters = filters or {}
        
        # Base query
        query = """
        SELECT m.*, 
               CASE WHEN m.poster_url IS NOT NULL AND m.poster_url != '' THEN 1 ELSE 0 END as has_poster,
               (SELECT COUNT(*) FROM subtitles s WHERE s.media_id = m.id) as subtitle_count
        FROM media m
        WHERE 1=1
        """
        
        params = []
        
        # Text search
        if search_term:
            query += " AND (m.title LIKE ? OR m.file_name LIKE ? OR m.overview LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param])
        
        # Year range filter
        if filters.get('year_range'):
            year_start, year_end = filters['year_range']
            if year_start:
                query += " AND CAST(SUBSTR(m.release_date, 1, 4) AS INTEGER) >= ?"
                params.append(year_start)
            if year_end:
                query += " AND CAST(SUBSTR(m.release_date, 1, 4) AS INTEGER) <= ?"
                params.append(year_end)
        
        # Genre filter
        if filters.get('genres'):
            genre_conditions = []
            for genre in filters['genres']:
                genre_conditions.append("m.genres LIKE ?")
                params.append(f"%{genre}%")
            if genre_conditions:
                query += f" AND ({' OR '.join(genre_conditions)})"
        
        # Rating filter
        if filters.get('rating_min', 0) > 0:
            query += " AND m.rating >= ?"
            params.append(filters['rating_min'])
        
        if filters.get('rating_max', 10) < 10:
            query += " AND m.rating <= ?"
            params.append(filters['rating_max'])
        
        # Duration filter
        if filters.get('duration_min', 0) > 0:
            query += " AND m.duration >= ?"
            params.append(filters['duration_min'])
        
        if filters.get('duration_max'):
            query += " AND m.duration <= ?"
            params.append(filters['duration_max'])
        
        # File size filter
        if filters.get('file_size_min', 0) > 0:
            query += " AND m.file_size >= ?"
            params.append(filters['file_size_min'])
        
        if filters.get('file_size_max'):
            query += " AND m.file_size <= ?"
            params.append(filters['file_size_max'])
        
        # Added date filter
        if filters.get('added_date_range'):
            date_start, date_end = filters['added_date_range']
            if date_start:
                query += " AND m.created_at >= ?"
                params.append(date_start)
            if date_end:
                query += " AND m.created_at <= ?"
                params.append(date_end)
        
        # Play count filter
        if filters.get('play_count_min', 0) > 0:
            query += " AND m.play_count >= ?"
            params.append(filters['play_count_min'])
        
        if filters.get('play_count_max'):
            query += " AND m.play_count <= ?"
            params.append(filters['play_count_max'])
        
        # Media type filter
        if filters.get('media_type'):
            query += " AND m.media_type = ?"
            params.append(filters['media_type'])
        
        # Has subtitles filter
        if filters.get('has_subtitles') is not None:
            if filters['has_subtitles']:
                query += " AND subtitle_count > 0"
            else:
                query += " AND subtitle_count = 0"
        
        # Has poster filter
        if filters.get('has_poster') is not None:
            if filters['has_poster']:
                query += " AND has_poster = 1"
            else:
                query += " AND has_poster = 0"
        
        # Sorting
        valid_sort_fields = ['title', 'rating', 'duration', 'file_size', 'created_at', 'play_count', 'release_date']
        if sort_by in valid_sort_fields:
            query += f" ORDER BY m.{sort_by} {sort_order.upper()}"
        else:
            query += " ORDER BY m.title ASC"
        
        # Pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return query, params
    
    def search_media(self, search_term: str = '', filters: Dict = None, 
                    sort_by: str = 'title', sort_order: str = 'ASC',
                    limit: int = 50, offset: int = 0) -> List[Dict]:
        """Perform advanced search on media library"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query, params = self.build_search_query(search_term, filters, sort_by, sort_order, limit, offset)
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                if result.get('genres'):
                    try:
                        result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                    except:
                        result['genres'] = []
                else:
                    result['genres'] = []
                
                results.append(result)
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get title suggestions
            cursor.execute("""
                SELECT DISTINCT title FROM media 
                WHERE title LIKE ? AND title IS NOT NULL
                ORDER BY title
                LIMIT ?
            """, (f"%{query}%", limit))
            
            suggestions = [row[0] for row in cursor.fetchall()]
            
            # Get genre suggestions
            cursor.execute("""
                SELECT DISTINCT genres FROM media 
                WHERE genres LIKE ? AND genres IS NOT NULL
                LIMIT ?
            """, (f"%{query}%", limit // 2))
            
            for row in cursor.fetchall():
                try:
                    genres = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    for genre in genres:
                        if query.lower() in genre.lower() and genre not in suggestions:
                            suggestions.append(genre)
                except:
                    pass
            
            conn.close()
            return suggestions[:limit]
            
        except Exception as e:
            print(f"Suggestions error: {e}")
            return []
    
    def get_recently_added(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """Get recently added media"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        filters = {'added_date_range': [date_threshold, None]}
        return self.search_media(filters=filters, sort_by='created_at', sort_order='DESC', limit=limit)
    
    def get_trending_media(self, days: int = 30, limit: int = 20) -> List[Dict]:
        """Get trending media based on play count"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        filters = {'added_date_range': [date_threshold, None]}
        return self.search_media(filters=filters, sort_by='play_count', sort_order='DESC', limit=limit)
    
    def get_continue_watching(self, limit: int = 20) -> List[Dict]:
        """Get media that was partially watched (has resume position)"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # This would require a resume_positions table
            # For now, return media with play_count > 0 but not completed
            cursor.execute("""
                SELECT m.*, 
                       CASE WHEN m.poster_url IS NOT NULL AND m.poster_url != '' THEN 1 ELSE 0 END as has_poster
                FROM media m
                WHERE m.play_count > 0
                ORDER BY m.last_played DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('genres'):
                    try:
                        result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                    except:
                        result['genres'] = []
                else:
                    result['genres'] = []
                results.append(result)
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Continue watching error: {e}")
            return []
    
    def get_recommendations(self, media_id: int, limit: int = 10) -> List[Dict]:
        """Get recommendations based on similar media"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the source media
            cursor.execute("SELECT * FROM media WHERE id = ?", (media_id,))
            source_media = cursor.fetchone()
            
            if not source_media:
                return []
            
            source_media = dict(source_media)
            source_genres = json.loads(source_media.get('genres', '[]')) if source_media.get('genres') else []
            
            # Find similar media based on genres and rating
            recommendations = []
            for genre in source_genres:
                cursor.execute("""
                    SELECT m.*, 
                           CASE WHEN m.poster_url IS NOT NULL AND m.poster_url != '' THEN 1 ELSE 0 END as has_poster
                    FROM media m
                    WHERE m.id != ? 
                    AND m.genres LIKE ? 
                    AND m.rating >= ?
                    ORDER BY m.rating DESC, m.play_count DESC
                    LIMIT ?
                """, (media_id, f"%{genre}%", max(0, source_media.get('rating', 0) - 2), limit))
                
                for row in cursor.fetchall():
                    result = dict(row)
                    if result.get('genres'):
                        try:
                            result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                        except:
                            result['genres'] = []
                    else:
                        result['genres'] = []
                    
                    # Avoid duplicates
                    if not any(r['id'] == result['id'] for r in recommendations):
                        recommendations.append(result)
            
            conn.close()
            return recommendations[:limit]
            
        except Exception as e:
            print(f"Recommendations error: {e}")
            return []
    
    def get_search_filters(self) -> Dict:
        """Get available search filters and their options"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            filters = {
                'years': [],
                'genres': [],
                'languages': [],
                'media_types': []
            }
            
            # Get year range
            cursor.execute("""
                SELECT MIN(CAST(SUBSTR(release_date, 1, 4) AS INTEGER)) as min_year,
                       MAX(CAST(SUBSTR(release_date, 1, 4) AS INTEGER)) as max_year
                FROM media 
                WHERE release_date IS NOT NULL AND release_date != ''
            """)
            year_range = cursor.fetchone()
            if year_range and year_range[0] and year_range[1]:
                filters['years'] = list(range(year_range[0], year_range[1] + 1))
            
            # Get genres
            cursor.execute("SELECT DISTINCT genres FROM media WHERE genres IS NOT NULL")
            all_genres = set()
            for row in cursor.fetchall():
                try:
                    genres = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    all_genres.update(genres)
                except:
                    pass
            filters['genres'] = sorted(list(all_genres))
            
            # Get media types
            cursor.execute("SELECT DISTINCT media_type FROM media")
            filters['media_types'] = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return filters
            
        except Exception as e:
            print(f"Filter options error: {e}")
            return {}
    
    def save_search(self, name: str, search_term: str, filters: Dict) -> bool:
        """Save a search for later use"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create saved_searches table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    search_term TEXT,
                    filters TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT OR REPLACE INTO saved_searches (name, search_term, filters)
                VALUES (?, ?, ?)
            """, (name, search_term, json.dumps(filters)))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Save search error: {e}")
            return False
    
    def get_saved_searches(self) -> List[Dict]:
        """Get all saved searches"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM saved_searches ORDER BY created_at DESC")
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                try:
                    result['filters'] = json.loads(result['filters']) if result['filters'] else {}
                except:
                    result['filters'] = {}
                results.append(result)
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Get saved searches error: {e}")
            return []
