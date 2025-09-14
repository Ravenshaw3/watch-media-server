#!/usr/bin/env python3
"""
Console Interface for Watch Media Server
Provides command-line management capabilities
"""

import os
import sys
import json
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

class ConsoleInterface:
    def __init__(self, media_manager):
        self.media_manager = media_manager
        self.running = True
    
    def run(self):
        """Main console loop"""
        print("Watch Media Server - Console Interface")
        print("Type 'help' for available commands")
        print("-" * 50)
        
        while self.running:
            try:
                command = input("watch> ").strip().lower()
                if not command:
                    continue
                
                if command == 'help':
                    self.show_help()
                elif command == 'quit' or command == 'exit':
                    self.running = False
                elif command == 'scan':
                    self.scan_library()
                elif command == 'list':
                    self.list_media()
                elif command == 'stats':
                    self.show_stats()
                elif command == 'settings':
                    self.show_settings()
                elif command.startswith('set '):
                    self.set_setting(command[4:])
                elif command.startswith('search '):
                    self.search_media(command[7:])
                elif command.startswith('play '):
                    self.play_media(command[5:])
                elif command == 'cleanup':
                    self.cleanup_database()
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
    
    def show_help(self):
        """Show available commands"""
        commands = [
            ("help", "Show this help message"),
            ("scan", "Scan media library for new files"),
            ("list", "List all media files"),
            ("stats", "Show library statistics"),
            ("settings", "Show current settings"),
            ("set <key> <value>", "Set a configuration value"),
            ("search <query>", "Search for media files"),
            ("play <id>", "Play media file by ID"),
            ("cleanup", "Clean up database (remove non-existent files)"),
            ("quit/exit", "Exit the console")
        ]
        
        print("\nAvailable Commands:")
        print("-" * 30)
        for cmd, desc in commands:
            print(f"{cmd:<20} - {desc}")
        print()
    
    def scan_library(self):
        """Scan the media library"""
        print("Scanning media library...")
        try:
            self.media_manager.scan_media_library()
            print("Library scan completed successfully!")
        except Exception as e:
            print(f"Error scanning library: {e}")
    
    def list_media(self):
        """List media files"""
        try:
            files = self.media_manager.get_media_files(limit=20)
            if not files:
                print("No media files found.")
                return
            
            print(f"\nMedia Files (showing first 20):")
            print("-" * 80)
            print(f"{'ID':<4} {'Type':<8} {'Title':<30} {'Size':<10} {'Added':<12}")
            print("-" * 80)
            
            for file in files:
                size_mb = file['file_size'] / (1024 * 1024) if file['file_size'] else 0
                added_date = file['added_date'][:10] if file['added_date'] else 'Unknown'
                title = file['title'][:27] + '...' if len(file['title']) > 30 else file['title']
                
                print(f"{file['id']:<4} {file['media_type']:<8} {title:<30} {size_mb:.1f}MB {added_date:<12}")
            
            print(f"\nTotal files: {len(files)}")
            
        except Exception as e:
            print(f"Error listing media: {e}")
    
    def show_stats(self):
        """Show library statistics"""
        try:
            conn = sqlite3.connect(self.media_manager.db_path)
            cursor = conn.cursor()
            
            # Total files
            cursor.execute("SELECT COUNT(*) FROM media_files")
            total_files = cursor.fetchone()[0]
            
            # By type
            cursor.execute("SELECT media_type, COUNT(*) FROM media_files GROUP BY media_type")
            by_type = dict(cursor.fetchall())
            
            # Total size
            cursor.execute("SELECT SUM(file_size) FROM media_files")
            total_size = cursor.fetchone()[0] or 0
            total_size_gb = total_size / (1024 * 1024 * 1024)
            
            # Most played
            cursor.execute("SELECT title, play_count FROM media_files ORDER BY play_count DESC LIMIT 5")
            most_played = cursor.fetchall()
            
            conn.close()
            
            print("\nLibrary Statistics:")
            print("-" * 30)
            print(f"Total Files: {total_files}")
            print(f"Total Size: {total_size_gb:.2f} GB")
            print("\nBy Type:")
            for media_type, count in by_type.items():
                print(f"  {media_type}: {count}")
            
            if most_played:
                print("\nMost Played:")
                for title, count in most_played:
                    if count > 0:
                        print(f"  {title}: {count} times")
            
        except Exception as e:
            print(f"Error getting stats: {e}")
    
    def show_settings(self):
        """Show current settings"""
        settings = [
            'library_path', 'auto_scan', 'scan_interval', 
            'supported_formats', 'transcode_enabled', 'max_resolution'
        ]
        
        print("\nCurrent Settings:")
        print("-" * 40)
        for setting in settings:
            value = self.media_manager.get_setting(setting)
            print(f"{setting:<20}: {value}")
        print()
    
    def set_setting(self, command):
        """Set a configuration value"""
        try:
            parts = command.split(' ', 1)
            if len(parts) != 2:
                print("Usage: set <key> <value>")
                return
            
            key, value = parts
            self.media_manager.set_setting(key, value)
            print(f"Setting '{key}' updated to '{value}'")
            
        except Exception as e:
            print(f"Error setting configuration: {e}")
    
    def search_media(self, query):
        """Search for media files"""
        try:
            conn = sqlite3.connect(self.media_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, media_type, title, file_path 
                FROM media_files 
                WHERE title LIKE ? OR file_name LIKE ?
                ORDER BY title
            """, (f'%{query}%', f'%{query}%'))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                print(f"No results found for '{query}'")
                return
            
            print(f"\nSearch Results for '{query}':")
            print("-" * 60)
            print(f"{'ID':<4} {'Type':<8} {'Title':<30} {'Path':<20}")
            print("-" * 60)
            
            for result in results:
                id, media_type, title, path = result
                title = title[:27] + '...' if len(title) > 30 else title
                path = os.path.basename(path)
                print(f"{id:<4} {media_type:<8} {title:<30} {path:<20}")
            
        except Exception as e:
            print(f"Error searching: {e}")
    
    def play_media(self, file_id):
        """Play media file by ID"""
        try:
            conn = sqlite3.connect(self.media_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, title FROM media_files WHERE id = ?", (file_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print(f"Media file with ID {file_id} not found")
                return
            
            file_path, title = result
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return
            
            print(f"Playing: {title}")
            print(f"File: {file_path}")
            
            # Update play count
            self.media_manager.update_play_count(int(file_id))
            
            # Try to open with default system player
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
            
        except Exception as e:
            print(f"Error playing media: {e}")
    
    def cleanup_database(self):
        """Clean up database by removing non-existent files"""
        try:
            conn = sqlite3.connect(self.media_manager.db_path)
            cursor = conn.cursor()
            
            # Get all file paths
            cursor.execute("SELECT id, file_path FROM media_files")
            files = cursor.fetchall()
            
            removed_count = 0
            for file_id, file_path in files:
                if not os.path.exists(file_path):
                    cursor.execute("DELETE FROM media_files WHERE id = ?", (file_id,))
                    removed_count += 1
            
            conn.commit()
            conn.close()
            
            print(f"Cleanup completed. Removed {removed_count} non-existent files from database.")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == '__main__':
    # This would be imported from the main app
    from app import MediaManager
    media_manager = MediaManager()
    console = ConsoleInterface(media_manager)
    console.run()
