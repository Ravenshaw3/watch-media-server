#!/usr/bin/env python3
"""
Generate icon files for Watch Media Server
"""

import os
from PIL import Image, ImageDraw
import io

def create_icon(size):
    """Create an icon of the specified size"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate dimensions
    center = size // 2
    radius = int(size * 0.4)
    
    # Create gradient effect (simplified)
    # Background circle with gradient-like effect
    for i in range(radius):
        alpha = int(255 * (1 - i / radius))
        color = (102, 126, 234, alpha)  # Blue gradient
        draw.ellipse([center - radius + i, center - radius + i, 
                     center + radius - i, center + radius - i], 
                    fill=color, outline=(255, 255, 255, 200))
    
    # Play button triangle
    triangle_size = int(size * 0.2)
    triangle_points = [
        (center - triangle_size, center - triangle_size),
        (center - triangle_size, center + triangle_size),
        (center + triangle_size, center)
    ]
    draw.polygon(triangle_points, fill=(255, 255, 255, 230))
    
    # Clock/watch elements
    clock_radius = int(size * 0.25)
    draw.ellipse([center - clock_radius, center - clock_radius,
                 center + clock_radius, center + clock_radius],
                fill=None, outline=(255, 255, 255, 180), width=2)
    
    # Clock hands
    hand_length = int(clock_radius * 0.7)
    # Hour hand (pointing up)
    draw.line([center, center, center, center - hand_length], 
             fill=(255, 255, 255, 200), width=2)
    # Minute hand (pointing right)
    draw.line([center, center, center + int(hand_length * 0.8), center], 
             fill=(255, 255, 255, 150), width=1)
    
    # Clock markers
    marker_size = max(1, size // 50)
    for angle in [0, 90, 180, 270]:
        import math
        x = center + int(clock_radius * 0.8 * math.cos(math.radians(angle)))
        y = center + int(clock_radius * 0.8 * math.sin(math.radians(angle)))
        draw.ellipse([x - marker_size, y - marker_size, x + marker_size, y + marker_size],
                    fill=(255, 255, 255, 200))
    
    return img

def main():
    """Generate all required icon sizes"""
    sizes = [16, 32, 152, 180]
    
    # Create images directory if it doesn't exist
    os.makedirs('static/images', exist_ok=True)
    
    for size in sizes:
        print(f"Generating {size}x{size} icon...")
        icon = create_icon(size)
        icon.save(f'static/images/icon-{size}x{size}.png')
    
    # Create favicon.ico (16x16)
    print("Generating favicon.ico...")
    favicon = create_icon(16)
    favicon.save('static/images/favicon.ico')
    
    # Create a larger version for general use
    print("Generating 192x192 icon...")
    icon_192 = create_icon(192)
    icon_192.save('static/images/icon-192x192.png')
    
    print("Generating 512x512 icon...")
    icon_512 = create_icon(512)
    icon_512.save('static/images/icon-512x512.png')
    
    print("All icons generated successfully!")

if __name__ == '__main__':
    main()
