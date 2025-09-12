# UI Components Service for Watch Media Server
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class UIComponentsService:
    def __init__(self):
        self.animations = self._get_animation_configs()
        self.themes = self._get_theme_configs()
        self.layouts = self._get_layout_configs()
        self.components = self._get_component_configs()
    
    def _get_animation_configs(self) -> Dict:
        """Get animation configurations"""
        return {
            'fade_in': {
                'duration': '0.3s',
                'timing': 'ease-in-out',
                'keyframes': {
                    '0%': {'opacity': '0', 'transform': 'translateY(10px)'},
                    '100%': {'opacity': '1', 'transform': 'translateY(0)'}
                }
            },
            'slide_up': {
                'duration': '0.4s',
                'timing': 'cubic-bezier(0.4, 0, 0.2, 1)',
                'keyframes': {
                    '0%': {'opacity': '0', 'transform': 'translateY(20px)'},
                    '100%': {'opacity': '1', 'transform': 'translateY(0)'}
                }
            },
            'scale_in': {
                'duration': '0.2s',
                'timing': 'ease-out',
                'keyframes': {
                    '0%': {'opacity': '0', 'transform': 'scale(0.9)'},
                    '100%': {'opacity': '1', 'transform': 'scale(1)'}
                }
            },
            'bounce': {
                'duration': '0.6s',
                'timing': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
                'keyframes': {
                    '0%': {'transform': 'scale(0.3)'},
                    '50%': {'transform': 'scale(1.05)'},
                    '70%': {'transform': 'scale(0.9)'},
                    '100%': {'transform': 'scale(1)'}
                }
            },
            'pulse': {
                'duration': '2s',
                'timing': 'ease-in-out',
                'iteration': 'infinite',
                'keyframes': {
                    '0%': {'opacity': '1'},
                    '50%': {'opacity': '0.5'},
                    '100%': {'opacity': '1'}
                }
            },
            'shake': {
                'duration': '0.5s',
                'timing': 'ease-in-out',
                'keyframes': {
                    '0%, 100%': {'transform': 'translateX(0)'},
                    '10%, 30%, 50%, 70%, 90%': {'transform': 'translateX(-5px)'},
                    '20%, 40%, 60%, 80%': {'transform': 'translateX(5px)'}
                }
            }
        }
    
    def _get_theme_configs(self) -> Dict:
        """Get theme configurations"""
        return {
            'light': {
                'primary': '#667eea',
                'secondary': '#764ba2',
                'accent': '#f093fb',
                'background': '#ffffff',
                'surface': '#f8fafc',
                'text': '#2d3748',
                'text_secondary': '#4a5568',
                'border': '#e2e8f0',
                'shadow': 'rgba(0, 0, 0, 0.1)',
                'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'card_bg': '#ffffff',
                'hover_bg': '#f7fafc'
            },
            'dark': {
                'primary': '#667eea',
                'secondary': '#764ba2',
                'accent': '#f093fb',
                'background': '#1a1a2e',
                'surface': '#16213e',
                'text': '#e2e8f0',
                'text_secondary': '#a0aec0',
                'border': '#2d3748',
                'shadow': 'rgba(0, 0, 0, 0.3)',
                'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'card_bg': '#2d2d2d',
                'hover_bg': '#404040'
            },
            'ocean': {
                'primary': '#0ea5e9',
                'secondary': '#06b6d4',
                'accent': '#8b5cf6',
                'background': '#0f172a',
                'surface': '#1e293b',
                'text': '#f1f5f9',
                'text_secondary': '#94a3b8',
                'border': '#334155',
                'shadow': 'rgba(0, 0, 0, 0.4)',
                'gradient': 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
                'card_bg': '#1e293b',
                'hover_bg': '#334155'
            },
            'sunset': {
                'primary': '#f97316',
                'secondary': '#ec4899',
                'accent': '#8b5cf6',
                'background': '#1c1917',
                'surface': '#292524',
                'text': '#fafaf9',
                'text_secondary': '#a8a29e',
                'border': '#44403c',
                'shadow': 'rgba(0, 0, 0, 0.4)',
                'gradient': 'linear-gradient(135deg, #f97316 0%, #ec4899 100%)',
                'card_bg': '#292524',
                'hover_bg': '#44403c'
            }
        }
    
    def _get_layout_configs(self) -> Dict:
        """Get layout configurations"""
        return {
            'grid': {
                'columns': {
                    'mobile': 2,
                    'tablet': 3,
                    'desktop': 4,
                    'large': 6
                },
                'gap': '20px',
                'padding': '20px'
            },
            'list': {
                'item_height': '120px',
                'gap': '10px',
                'padding': '20px'
            },
            'masonry': {
                'columns': {
                    'mobile': 2,
                    'tablet': 3,
                    'desktop': 4
                },
                'gap': '20px',
                'padding': '20px'
            },
            'carousel': {
                'items_per_view': {
                    'mobile': 1,
                    'tablet': 2,
                    'desktop': 3
                },
                'gap': '20px',
                'autoplay': True,
                'autoplay_delay': 5000
            }
        }
    
    def _get_component_configs(self) -> Dict:
        """Get component configurations"""
        return {
            'media_card': {
                'aspect_ratio': '2/3',
                'border_radius': '12px',
                'shadow': '0 4px 20px rgba(0, 0, 0, 0.1)',
                'hover_scale': '1.05',
                'transition': 'all 0.3s ease',
                'overlay_opacity': '0.8'
            },
            'button': {
                'border_radius': '8px',
                'padding': '12px 24px',
                'font_weight': '600',
                'transition': 'all 0.2s ease',
                'hover_scale': '1.02',
                'active_scale': '0.98'
            },
            'modal': {
                'backdrop_blur': '8px',
                'backdrop_opacity': '0.5',
                'border_radius': '16px',
                'shadow': '0 20px 60px rgba(0, 0, 0, 0.3)',
                'max_width': '90vw',
                'max_height': '90vh'
            },
            'input': {
                'border_radius': '8px',
                'padding': '12px 16px',
                'border_width': '2px',
                'focus_scale': '1.02',
                'transition': 'all 0.2s ease'
            },
            'progress_bar': {
                'height': '8px',
                'border_radius': '4px',
                'animation_duration': '0.3s',
                'glow_effect': True
            }
        }
    
    def get_animation_css(self, animation_name: str) -> str:
        """Generate CSS for animation"""
        if animation_name not in self.animations:
            return ""
        
        animation = self.animations[animation_name]
        keyframes = []
        
        for percentage, properties in animation['keyframes'].items():
            props = []
            for prop, value in properties.items():
                props.append(f"    {prop}: {value};")
            keyframes.append(f"  {percentage} {{\n" + "\n".join(props) + "\n  }")
        
        css = f"""
@keyframes {animation_name} {{
{chr(10).join(keyframes)}
}}

.{animation_name} {{
    animation: {animation_name} {animation['duration']} {animation['timing']};
    animation-fill-mode: both;
}}
"""
        
        if 'iteration' in animation:
            css += f".{animation_name} {{ animation-iteration-count: {animation['iteration']}; }}\n"
        
        return css
    
    def get_theme_css(self, theme_name: str) -> str:
        """Generate CSS variables for theme"""
        if theme_name not in self.themes:
            return ""
        
        theme = self.themes[theme_name]
        css_vars = []
        
        for var, value in theme.items():
            css_vars.append(f"  --{var.replace('_', '-')}: {value};")
        
        return f"""
.theme-{theme_name} {{
{chr(10).join(css_vars)}
}}
"""
    
    def get_component_css(self, component_name: str) -> str:
        """Generate CSS for component"""
        if component_name not in self.components:
            return ""
        
        component = self.components[component_name]
        css_props = []
        
        for prop, value in component.items():
            if prop.startswith('hover_') or prop.startswith('active_') or prop.startswith('focus_'):
                continue
            css_props.append(f"  {prop.replace('_', '-')}: {value};")
        
        css = f"""
.{component_name} {{
{chr(10).join(css_props)}
}}
"""
        
        # Add hover effects
        hover_props = []
        for prop, value in component.items():
            if prop.startswith('hover_'):
                hover_prop = prop.replace('hover_', '').replace('_', '-')
                hover_props.append(f"  {hover_prop}: {value};")
        
        if hover_props:
            css += f"""
.{component_name}:hover {{
{chr(10).join(hover_props)}
}}
"""
        
        # Add active effects
        active_props = []
        for prop, value in component.items():
            if prop.startswith('active_'):
                active_prop = prop.replace('active_', '').replace('_', '-')
                active_props.append(f"  {active_prop}: {value};")
        
        if active_props:
            css += f"""
.{component_name}:active {{
{chr(10).join(active_props)}
}}
"""
        
        return css
    
    def get_responsive_css(self) -> str:
        """Generate responsive CSS utilities"""
        return """
/* Responsive Grid System */
.grid-responsive {
    display: grid;
    gap: var(--grid-gap, 20px);
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

@media (max-width: 768px) {
    .grid-responsive {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 15px;
    }
}

@media (max-width: 480px) {
    .grid-responsive {
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 10px;
    }
}

/* Responsive Typography */
.text-responsive {
    font-size: clamp(14px, 2.5vw, 18px);
    line-height: 1.6;
}

.heading-responsive {
    font-size: clamp(20px, 4vw, 32px);
    line-height: 1.2;
}

/* Responsive Spacing */
.spacing-responsive {
    padding: clamp(10px, 3vw, 30px);
    margin: clamp(5px, 2vw, 20px);
}

/* Responsive Images */
.img-responsive {
    width: 100%;
    height: auto;
    object-fit: cover;
}

/* Responsive Containers */
.container-responsive {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 clamp(15px, 5vw, 40px);
}

/* Responsive Flexbox */
.flex-responsive {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(10px, 2vw, 20px);
}

@media (max-width: 768px) {
    .flex-responsive {
        flex-direction: column;
    }
}
"""
    
    def get_utility_classes(self) -> str:
        """Generate utility CSS classes"""
        return """
/* Utility Classes */
.animate-fade-in { animation: fadeIn 0.3s ease-in-out; }
.animate-slide-up { animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.animate-scale-in { animation: scaleIn 0.2s ease-out; }
.animate-bounce { animation: bounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55); }
.animate-pulse { animation: pulse 2s ease-in-out infinite; }
.animate-shake { animation: shake 0.5s ease-in-out; }

.hover-lift { transition: transform 0.3s ease; }
.hover-lift:hover { transform: translateY(-5px); }

.hover-glow { transition: box-shadow 0.3s ease; }
.hover-glow:hover { box-shadow: 0 0 20px rgba(102, 126, 234, 0.5); }

.glass-effect {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.gradient-text {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.text-shadow { text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3); }
.box-shadow { box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); }
.box-shadow-lg { box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2); }

.rounded-sm { border-radius: 4px; }
.rounded { border-radius: 8px; }
.rounded-lg { border-radius: 12px; }
.rounded-xl { border-radius: 16px; }
.rounded-full { border-radius: 50%; }

.opacity-0 { opacity: 0; }
.opacity-25 { opacity: 0.25; }
.opacity-50 { opacity: 0.5; }
.opacity-75 { opacity: 0.75; }
.opacity-100 { opacity: 1; }

.transition-all { transition: all 0.3s ease; }
.transition-colors { transition: color 0.3s ease, background-color 0.3s ease; }
.transition-transform { transition: transform 0.3s ease; }
.transition-opacity { transition: opacity 0.3s ease; }

.cursor-pointer { cursor: pointer; }
.cursor-not-allowed { cursor: not-allowed; }
.cursor-grab { cursor: grab; }
.cursor-grabbing { cursor: grabbing; }

.select-none { user-select: none; }
.select-text { user-select: text; }
.select-all { user-select: all; }

.overflow-hidden { overflow: hidden; }
.overflow-auto { overflow: auto; }
.overflow-scroll { overflow: scroll; }

.truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
"""
    
    def get_all_css(self) -> str:
        """Get all CSS for UI components"""
        css_parts = []
        
        # Add animations
        for animation_name in self.animations:
            css_parts.append(self.get_animation_css(animation_name))
        
        # Add themes
        for theme_name in self.themes:
            css_parts.append(self.get_theme_css(theme_name))
        
        # Add components
        for component_name in self.components:
            css_parts.append(self.get_component_css(component_name))
        
        # Add responsive CSS
        css_parts.append(self.get_responsive_css())
        
        # Add utility classes
        css_parts.append(self.get_utility_classes())
        
        return "\n".join(css_parts)
    
    def get_theme_switcher_html(self) -> str:
        """Generate theme switcher HTML"""
        return """
<div class="theme-switcher">
    <button class="theme-toggle" id="themeToggle" title="Toggle Theme">
        <i class="fas fa-moon" id="themeIcon"></i>
    </button>
    <div class="theme-menu" id="themeMenu">
        <div class="theme-option" data-theme="light">
            <div class="theme-preview light-preview"></div>
            <span>Light</span>
        </div>
        <div class="theme-option" data-theme="dark">
            <div class="theme-preview dark-preview"></div>
            <span>Dark</span>
        </div>
        <div class="theme-option" data-theme="ocean">
            <div class="theme-preview ocean-preview"></div>
            <span>Ocean</span>
        </div>
        <div class="theme-option" data-theme="sunset">
            <div class="theme-preview sunset-preview"></div>
            <span>Sunset</span>
        </div>
    </div>
</div>
"""
    
    def get_loading_spinner_html(self, size: str = 'medium', color: str = 'primary') -> str:
        """Generate loading spinner HTML"""
        sizes = {
            'small': '20px',
            'medium': '40px',
            'large': '60px'
        }
        
        return f"""
<div class="loading-spinner spinner-{size} spinner-{color}">
    <div class="spinner-ring"></div>
    <div class="spinner-ring"></div>
    <div class="spinner-ring"></div>
    <div class="spinner-ring"></div>
</div>
"""

# UI Components service instance
ui_components_service = UIComponentsService()
