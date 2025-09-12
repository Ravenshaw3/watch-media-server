# Subtitle Service for Watch Media Server
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import json

class SubtitleService:
    def __init__(self):
        self.supported_formats = ['.srt', '.vtt', '.ass', '.ssa', '.sub']
        self.language_codes = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi'
        }
    
    def find_subtitles(self, media_file_path: str) -> List[Dict]:
        """Find subtitle files for a media file"""
        media_path = Path(media_file_path)
        media_dir = media_path.parent
        media_name = media_path.stem
        
        subtitles = []
        
        # Look for subtitle files in the same directory
        for subtitle_file in media_dir.glob(f"{media_name}*"):
            if subtitle_file.suffix.lower() in self.supported_formats:
                subtitle_info = self.parse_subtitle_file(subtitle_file)
                if subtitle_info:
                    subtitles.append(subtitle_info)
        
        # Also check for subtitles subdirectory
        subtitles_dir = media_dir / 'subtitles'
        if subtitles_dir.exists():
            for subtitle_file in subtitles_dir.glob(f"{media_name}*"):
                if subtitle_file.suffix.lower() in self.supported_formats:
                    subtitle_info = self.parse_subtitle_file(subtitle_file)
                    if subtitle_info:
                        subtitles.append(subtitle_info)
        
        return subtitles
    
    def parse_subtitle_file(self, subtitle_path: Path) -> Optional[Dict]:
        """Parse subtitle file and extract metadata"""
        try:
            # Extract language from filename
            language = self.extract_language_from_filename(subtitle_path.name)
            
            # Get file size
            file_size = subtitle_path.stat().st_size
            
            # Count subtitle entries
            entry_count = self.count_subtitle_entries(subtitle_path)
            
            return {
                'file_path': str(subtitle_path),
                'filename': subtitle_path.name,
                'language': language,
                'language_name': self.language_codes.get(language, language),
                'format': subtitle_path.suffix.lower(),
                'size': file_size,
                'entry_count': entry_count,
                'url': f"/api/subtitle/{subtitle_path.name}"
            }
        except Exception as e:
            print(f"Error parsing subtitle file {subtitle_path}: {e}")
            return None
    
    def extract_language_from_filename(self, filename: str) -> str:
        """Extract language code from filename"""
        # Common patterns: movie.en.srt, movie_eng.srt, movie.english.srt
        patterns = [
            r'\.([a-z]{2,3})\.',  # .en., .eng.
            r'_([a-z]{2,3})\.',   # _en., _eng.
            r'\.(english|spanish|french|german|italian|portuguese|russian|japanese|korean|chinese|arabic|hindi)\.',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename.lower())
            if match:
                lang = match.group(1)
                # Convert full language names to codes
                lang_map = {
                    'english': 'en', 'spanish': 'es', 'french': 'fr', 'german': 'de',
                    'italian': 'it', 'portuguese': 'pt', 'russian': 'ru', 'japanese': 'ja',
                    'korean': 'ko', 'chinese': 'zh', 'arabic': 'ar', 'hindi': 'hi'
                }
                return lang_map.get(lang, lang)
        
        return 'unknown'
    
    def count_subtitle_entries(self, subtitle_path: Path) -> int:
        """Count number of subtitle entries in file"""
        try:
            with open(subtitle_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if subtitle_path.suffix.lower() == '.srt':
                # Count SRT entries (numbered sequences)
                return len(re.findall(r'^\d+$', content, re.MULTILINE))
            elif subtitle_path.suffix.lower() == '.vtt':
                # Count VTT entries (timestamp lines)
                return len(re.findall(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', content))
            else:
                # For other formats, count lines that look like timestamps
                return len(re.findall(r'\d{2}:\d{2}:\d{2}', content))
        except Exception:
            return 0
    
    def convert_srt_to_vtt(self, srt_content: str) -> str:
        """Convert SRT subtitle content to VTT format"""
        lines = srt_content.strip().split('\n')
        vtt_lines = ['WEBVTT', '', '']
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Skip sequence numbers
            if line.isdigit():
                i += 1
                continue
            
            # Process timestamp line
            if '-->' in line:
                # Convert SRT timestamp format to VTT
                timestamp = line.replace(',', '.')
                vtt_lines.append(timestamp)
                i += 1
                
                # Collect subtitle text
                subtitle_text = []
                while i < len(lines) and lines[i].strip():
                    subtitle_text.append(lines[i].strip())
                    i += 1
                
                if subtitle_text:
                    vtt_lines.append('\n'.join(subtitle_text))
                    vtt_lines.append('')
            else:
                i += 1
        
        return '\n'.join(vtt_lines)
    
    def get_subtitle_content(self, subtitle_path: str, format: str = 'vtt') -> str:
        """Get subtitle content in specified format"""
        try:
            with open(subtitle_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if format.lower() == 'vtt' and subtitle_path.lower().endswith('.srt'):
                return self.convert_srt_to_vtt(content)
            elif format.lower() == 'srt' and subtitle_path.lower().endswith('.vtt'):
                # Convert VTT to SRT (basic conversion)
                return self.convert_vtt_to_srt(content)
            else:
                return content
        except Exception as e:
            print(f"Error reading subtitle file {subtitle_path}: {e}")
            return ''
    
    def convert_vtt_to_srt(self, vtt_content: str) -> str:
        """Convert VTT subtitle content to SRT format"""
        lines = vtt_content.strip().split('\n')
        srt_lines = []
        sequence = 1
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip WEBVTT header
            if line == 'WEBVTT' or not line:
                i += 1
                continue
            
            # Process timestamp line
            if '-->' in line:
                # Convert VTT timestamp format to SRT
                timestamp = line.replace('.', ',')
                srt_lines.append(str(sequence))
                srt_lines.append(timestamp)
                sequence += 1
                i += 1
                
                # Collect subtitle text
                subtitle_text = []
                while i < len(lines) and lines[i].strip():
                    subtitle_text.append(lines[i].strip())
                    i += 1
                
                if subtitle_text:
                    srt_lines.append('\n'.join(subtitle_text))
                    srt_lines.append('')
            else:
                i += 1
        
        return '\n'.join(srt_lines)
    
    def search_subtitles_online(self, media_title: str, language: str = 'en') -> List[Dict]:
        """Search for subtitles online (placeholder for future implementation)"""
        # This would integrate with subtitle APIs like OpenSubtitles
        # For now, return empty list
        return []
    
    def download_subtitle(self, subtitle_url: str, save_path: str) -> bool:
        """Download subtitle from URL"""
        try:
            import requests
            response = requests.get(subtitle_url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Error downloading subtitle from {subtitle_url}: {e}")
            return False
