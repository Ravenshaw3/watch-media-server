# TMDB API Service for Watch Media Server
import requests
import os
import json
from typing import Dict, List, Optional, Tuple
import re
from pathlib import Path

class TMDBService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('TMDB_API_KEY')
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p'
        self.session = requests.Session()
        self.session.params = {'api_key': self.api_key}
        
        # Cache for API responses
        self.cache = {}
        self.cache_file = 'tmdb_cache.json'
        self.load_cache()
    
    def load_cache(self):
        """Load cached API responses from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"Error loading TMDB cache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Save API responses to cache file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving TMDB cache: {e}")
    
    def get_cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key for API request"""
        return f"{endpoint}:{json.dumps(params, sort_keys=True)}"
    
    def make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make API request with caching"""
        if not self.api_key:
            return None
        
        params = params or {}
        cache_key = self.get_cache_key(endpoint, params)
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.cache[cache_key] = data
            self.save_cache()
            
            return data
        except Exception as e:
            print(f"TMDB API error for {endpoint}: {e}")
            return None
    
    def search_movie(self, title: str, year: int = None) -> Optional[dict]:
        """Search for a movie by title"""
        params = {'query': title}
        if year:
            params['year'] = year
        
        data = self.make_request('search/movie', params)
        if data and data.get('results'):
            return data['results'][0]  # Return first result
        return None
    
    def search_tv_show(self, title: str, year: int = None) -> Optional[dict]:
        """Search for a TV show by title"""
        params = {'query': title}
        if year:
            params['first_air_date_year'] = year
        
        data = self.make_request('search/tv', params)
        if data and data.get('results'):
            return data['results'][0]  # Return first result
        return None
    
    def get_movie_details(self, movie_id: int) -> Optional[dict]:
        """Get detailed movie information"""
        return self.make_request(f'movie/{movie_id}')
    
    def get_tv_details(self, tv_id: int) -> Optional[dict]:
        """Get detailed TV show information"""
        return self.make_request(f'tv/{tv_id}')
    
    def get_image_url(self, path: str, size: str = 'w500') -> str:
        """Get full image URL"""
        if not path:
            return ''
        return f"{self.image_base_url}/{size}{path}"
    
    def extract_year_from_filename(self, filename: str) -> Optional[int]:
        """Extract year from filename (e.g., 'Movie (2023).mp4' -> 2023)"""
        year_match = re.search(r'\((\d{4})\)', filename)
        if year_match:
            return int(year_match.group(1))
        
        # Also try 4-digit year at the end
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2030:  # Reasonable year range
                return year
        
        return None
    
    def clean_title(self, filename: str) -> str:
        """Clean filename to extract title"""
        # Remove file extension
        title = Path(filename).stem
        
        # Remove year in parentheses
        title = re.sub(r'\s*\(\d{4}\)', '', title)
        
        # Remove common video quality indicators
        quality_patterns = [
            r'\b(1080p|720p|480p|4K|HDRip|BRRip|WEBRip|BluRay|DVDRip)\b',
            r'\b(x264|x265|H\.264|H\.265)\b',
            r'\b(AC3|AAC|DTS|FLAC)\b'
        ]
        
        for pattern in quality_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Clean up extra spaces and special characters
        title = re.sub(r'[._-]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def get_media_metadata(self, file_path: str, media_type: str = 'movie') -> dict:
        """Get metadata for a media file"""
        filename = Path(file_path).name
        title = self.clean_title(filename)
        year = self.extract_year_from_filename(filename)
        
        metadata = {
            'title': title,
            'year': year,
            'poster_url': '',
            'backdrop_url': '',
            'overview': '',
            'rating': 0,
            'genres': [],
            'runtime': 0,
            'release_date': '',
            'imdb_id': '',
            'tmdb_id': None
        }
        
        if not self.api_key:
            return metadata
        
        try:
            if media_type == 'movie':
                result = self.search_movie(title, year)
                if result:
                    details = self.get_movie_details(result['id'])
                    if details:
                        metadata.update({
                            'title': details.get('title', title),
                            'year': details.get('release_date', '')[:4] if details.get('release_date') else year,
                            'poster_url': self.get_image_url(details.get('poster_path')),
                            'backdrop_url': self.get_image_url(details.get('backdrop_path'), 'w1280'),
                            'overview': details.get('overview', ''),
                            'rating': details.get('vote_average', 0),
                            'genres': [g['name'] for g in details.get('genres', [])],
                            'runtime': details.get('runtime', 0),
                            'release_date': details.get('release_date', ''),
                            'imdb_id': details.get('imdb_id', ''),
                            'tmdb_id': details.get('id')
                        })
            
            elif media_type == 'tv_show':
                result = self.search_tv_show(title, year)
                if result:
                    details = self.get_tv_details(result['id'])
                    if details:
                        metadata.update({
                            'title': details.get('name', title),
                            'year': details.get('first_air_date', '')[:4] if details.get('first_air_date') else year,
                            'poster_url': self.get_image_url(details.get('poster_path')),
                            'backdrop_url': self.get_image_url(details.get('backdrop_path'), 'w1280'),
                            'overview': details.get('overview', ''),
                            'rating': details.get('vote_average', 0),
                            'genres': [g['name'] for g in details.get('genres', [])],
                            'runtime': details.get('episode_run_time', [0])[0] if details.get('episode_run_time') else 0,
                            'release_date': details.get('first_air_date', ''),
                            'imdb_id': details.get('external_ids', {}).get('imdb_id', ''),
                            'tmdb_id': details.get('id')
                        })
        
        except Exception as e:
            print(f"Error getting metadata for {filename}: {e}")
        
        return metadata
    
    def download_poster(self, poster_url: str, save_path: str) -> bool:
        """Download poster image to local file"""
        if not poster_url:
            return False
        
        try:
            response = requests.get(poster_url, timeout=10)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Error downloading poster {poster_url}: {e}")
            return False
    
    def get_trending_movies(self, limit: int = 20) -> List[dict]:
        """Get trending movies"""
        data = self.make_request('trending/movie/week')
        if data and data.get('results'):
            return data['results'][:limit]
        return []
    
    def get_trending_tv(self, limit: int = 20) -> List[dict]:
        """Get trending TV shows"""
        data = self.make_request('trending/tv/week')
        if data and data.get('results'):
            return data['results'][:limit]
        return []
    
    def get_genres(self, media_type: str = 'movie') -> List[dict]:
        """Get list of genres"""
        endpoint = f'genre/{media_type}/list'
        data = self.make_request(endpoint)
        if data and data.get('genres'):
            return data['genres']
        return []
    
    def search_person(self, name: str) -> List[dict]:
        """Search for a person (actor/director)"""
        data = self.make_request('search/person', {'query': name})
        if data and data.get('results'):
            return data['results']
        return []
