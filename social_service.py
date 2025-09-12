# Social Features Service for Watch Media Server
import os
import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SocialService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.init_social_tables()
    
    def init_social_tables(self):
        """Initialize social features database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                display_name TEXT,
                bio TEXT,
                avatar_url TEXT,
                cover_image_url TEXT,
                location TEXT,
                website TEXT,
                social_links TEXT DEFAULT '{}',
                preferences TEXT DEFAULT '{}',
                privacy_settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User relationships table (followers/following)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                following_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES users (id),
                FOREIGN KEY (following_id) REFERENCES users (id),
                UNIQUE(follower_id, following_id)
            )
        ''')
        
        # Media reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 10),
                review_text TEXT,
                is_public BOOLEAN DEFAULT 1,
                likes_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id),
                UNIQUE(user_id, media_id)
            )
        ''')
        
        # Review likes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                review_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (review_id) REFERENCES media_reviews (id),
                UNIQUE(user_id, review_id)
            )
        ''')
        
        # Media comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                parent_id INTEGER,
                comment_text TEXT NOT NULL,
                likes_count INTEGER DEFAULT 0,
                is_edited BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id),
                FOREIGN KEY (parent_id) REFERENCES media_comments (id)
            )
        ''')
        
        # Comment likes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comment_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comment_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (comment_id) REFERENCES media_comments (id),
                UNIQUE(user_id, comment_id)
            )
        ''')
        
        # Media sharing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                share_type TEXT DEFAULT 'public',
                share_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # User activity feed table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data TEXT DEFAULT '{}',
                is_public BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT DEFAULT '{}',
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User collections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                is_public BOOLEAN DEFAULT 0,
                media_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Collection items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection_id) REFERENCES user_collections (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id),
                UNIQUE(collection_id, media_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user_profile(self, user_id: int, profile_data: Dict) -> bool:
        """Create or update user profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, display_name, bio, avatar_url, cover_image_url, 
                 location, website, social_links, preferences, privacy_settings, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                profile_data.get('display_name'),
                profile_data.get('bio'),
                profile_data.get('avatar_url'),
                profile_data.get('cover_image_url'),
                profile_data.get('location'),
                profile_data.get('website'),
                json.dumps(profile_data.get('social_links', {})),
                json.dumps(profile_data.get('preferences', {})),
                json.dumps(profile_data.get('privacy_settings', {}))
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT up.*, u.username, u.email, u.created_at as user_created_at
                FROM user_profiles up
                JOIN users u ON up.user_id = u.id
                WHERE up.user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                profile = dict(result)
                # Parse JSON fields
                for field in ['social_links', 'preferences', 'privacy_settings']:
                    if profile.get(field):
                        try:
                            profile[field] = json.loads(profile[field])
                        except:
                            profile[field] = {}
                return profile
            
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def follow_user(self, follower_id: int, following_id: int) -> bool:
        """Follow a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_relationships (follower_id, following_id)
                VALUES (?, ?)
            ''', (follower_id, following_id))
            
            conn.commit()
            conn.close()
            
            # Create notification
            self.create_notification(
                following_id,
                'follow',
                'New Follower',
                f'Someone started following you!',
                {'follower_id': follower_id}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error following user: {e}")
            return False
    
    def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """Unfollow a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM user_relationships 
                WHERE follower_id = ? AND following_id = ?
            ''', (follower_id, following_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error unfollowing user: {e}")
            return False
    
    def get_followers(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's followers"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, up.display_name, up.avatar_url, ur.created_at as followed_at
                FROM user_relationships ur
                JOIN users u ON ur.follower_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE ur.following_id = ?
                ORDER BY ur.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting followers: {e}")
            return []
    
    def get_following(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get users that a user is following"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, up.display_name, up.avatar_url, ur.created_at as followed_at
                FROM user_relationships ur
                JOIN users u ON ur.following_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE ur.follower_id = ?
                ORDER BY ur.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting following: {e}")
            return []
    
    def create_review(self, user_id: int, media_id: int, rating: int, review_text: str = None) -> bool:
        """Create a media review"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO media_reviews 
                (user_id, media_id, rating, review_text, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, media_id, rating, review_text))
            
            conn.commit()
            conn.close()
            
            # Add to activity feed
            self.add_activity(user_id, 'review', {
                'media_id': media_id,
                'rating': rating,
                'has_text': bool(review_text)
            })
            
            return True
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            return False
    
    def get_media_reviews(self, media_id: int, limit: int = 20) -> List[Dict]:
        """Get reviews for a media item"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mr.*, u.username, up.display_name, up.avatar_url
                FROM media_reviews mr
                JOIN users u ON mr.user_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE mr.media_id = ? AND mr.is_public = 1
                ORDER BY mr.created_at DESC
                LIMIT ?
            ''', (media_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting media reviews: {e}")
            return []
    
    def like_review(self, user_id: int, review_id: int) -> bool:
        """Like a review"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Add like
            cursor.execute('''
                INSERT OR IGNORE INTO review_likes (user_id, review_id)
                VALUES (?, ?)
            ''', (user_id, review_id))
            
            # Update likes count
            cursor.execute('''
                UPDATE media_reviews 
                SET likes_count = (
                    SELECT COUNT(*) FROM review_likes WHERE review_id = ?
                )
                WHERE id = ?
            ''', (review_id, review_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error liking review: {e}")
            return False
    
    def create_comment(self, user_id: int, media_id: int, comment_text: str, parent_id: int = None) -> bool:
        """Create a comment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO media_comments 
                (user_id, media_id, parent_id, comment_text)
                VALUES (?, ?, ?, ?)
            ''', (user_id, media_id, parent_id, comment_text))
            
            conn.commit()
            conn.close()
            
            # Add to activity feed
            self.add_activity(user_id, 'comment', {
                'media_id': media_id,
                'parent_id': parent_id,
                'is_reply': bool(parent_id)
            })
            
            return True
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            return False
    
    def get_media_comments(self, media_id: int, limit: int = 50) -> List[Dict]:
        """Get comments for a media item"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mc.*, u.username, up.display_name, up.avatar_url
                FROM media_comments mc
                JOIN users u ON mc.user_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE mc.media_id = ? AND mc.parent_id IS NULL
                ORDER BY mc.created_at DESC
                LIMIT ?
            ''', (media_id, limit))
            
            comments = []
            for row in cursor.fetchall():
                comment = dict(row)
                
                # Get replies
                cursor.execute('''
                    SELECT mc.*, u.username, up.display_name, up.avatar_url
                    FROM media_comments mc
                    JOIN users u ON mc.user_id = u.id
                    LEFT JOIN user_profiles up ON u.id = up.user_id
                    WHERE mc.parent_id = ?
                    ORDER BY mc.created_at ASC
                ''', (comment['id'],))
                
                comment['replies'] = [dict(reply) for reply in cursor.fetchall()]
                comments.append(comment)
            
            conn.close()
            return comments
        except Exception as e:
            logger.error(f"Error getting media comments: {e}")
            return []
    
    def create_collection(self, user_id: int, name: str, description: str = None, is_public: bool = False) -> int:
        """Create a user collection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_collections 
                (user_id, name, description, is_public)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, description, is_public))
            
            collection_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return collection_id
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return None
    
    def add_to_collection(self, collection_id: int, media_id: int) -> bool:
        """Add media to collection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO collection_items (collection_id, media_id)
                VALUES (?, ?)
            ''', (collection_id, media_id))
            
            # Update media count
            cursor.execute('''
                UPDATE user_collections 
                SET media_count = (
                    SELECT COUNT(*) FROM collection_items WHERE collection_id = ?
                )
                WHERE id = ?
            ''', (collection_id, collection_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding to collection: {e}")
            return False
    
    def get_user_collections(self, user_id: int, is_public: bool = None) -> List[Dict]:
        """Get user's collections"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM user_collections 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if is_public is not None:
                query += ' AND is_public = ?'
                params.append(is_public)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting user collections: {e}")
            return []
    
    def add_activity(self, user_id: int, activity_type: str, activity_data: Dict) -> bool:
        """Add activity to user's feed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_activity 
                (user_id, activity_type, activity_data)
                VALUES (?, ?, ?)
            ''', (user_id, activity_type, json.dumps(activity_data)))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding activity: {e}")
            return False
    
    def get_activity_feed(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's activity feed"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get activities from users that the current user follows
            cursor.execute('''
                SELECT ua.*, u.username, up.display_name, up.avatar_url
                FROM user_activity ua
                JOIN users u ON ua.user_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE ua.user_id IN (
                    SELECT following_id FROM user_relationships WHERE follower_id = ?
                ) AND ua.is_public = 1
                ORDER BY ua.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                activity = dict(row)
                try:
                    activity['activity_data'] = json.loads(activity['activity_data'])
                except:
                    activity['activity_data'] = {}
                results.append(activity)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting activity feed: {e}")
            return []
    
    def create_notification(self, user_id: int, notification_type: str, title: str, message: str, data: Dict = None) -> bool:
        """Create a notification"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications 
                (user_id, notification_type, title, message, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, notification_type, title, message, json.dumps(data or {})))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return False
    
    def get_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's notifications"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                notification = dict(row)
                try:
                    notification['data'] = json.loads(notification['data'])
                except:
                    notification['data'] = {}
                results.append(notification)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE notifications 
                SET is_read = 1 
                WHERE id = ? AND user_id = ?
            ''', (notification_id, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

# Social service instance
social_service = SocialService()
