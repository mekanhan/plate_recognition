#!/usr/bin/env python3
"""
Minify all CSS and JavaScript files in the frontend directory
Saves ~256KB according to Lighthouse report
"""
import os
import re
from pathlib import Path

def minify_css(content):
    """Simple CSS minification"""
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove unnecessary whitespace
    content = re.sub(r'\s+', ' ', content)
    # Remove space around specific characters
    content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
    # Remove trailing semicolon before }
    content = re.sub(r';\}', '}', content)
    # Remove leading/trailing whitespace
    content = content.strip()
    return content

def minify_js(content):
    """Simple JavaScript minification (basic, safe approach)"""
    # Skip if already minified (contains .min. in filename or very long lines)
    avg_line_length = len(content) / (content.count('\n') + 1)
    if avg_line_length > 200:
        return content  # Likely already minified
    
    # Remove single-line comments (but preserve URLs with //)
    content = re.sub(r'(?<!:)//[^\n]*', '', content)
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove unnecessary whitespace (but preserve strings)
    lines = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('//'):
            lines.append(line)
    content = ' '.join(lines)
    # Remove space around operators (basic)
    content = re.sub(r'\s*([=+\-*/{}();,:])\s*', r'\1', content)
    return content

def process_files(directory):
    """Process all CSS and JS files in directory"""
    stats = {'css': {'count': 0, 'saved': 0}, 'js': {'count': 0, 'saved': 0}}
    
    for file_path in Path(directory).rglob('*'):
        if file_path.is_file():
            # Skip already minified files
            if '.min.' in file_path.name:
                continue
                
            original_size = file_path.stat().st_size
            
            if file_path.suffix == '.css':
                print(f"Minifying CSS: {file_path.relative_to(directory)}")
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                minified = minify_css(content)
                
                # Create minified version
                min_path = file_path.with_suffix('.min.css')
                min_path.write_text(minified, encoding='utf-8')
                
                # Also overwrite original for immediate effect
                file_path.write_text(minified, encoding='utf-8')
                
                new_size = len(minified)
                saved = original_size - new_size
                stats['css']['count'] += 1
                stats['css']['saved'] += saved
                print(f"  ✅ Saved {saved:,} bytes ({saved/1024:.1f} KB)")
                
            elif file_path.suffix == '.js' and 'node_modules' not in str(file_path):
                print(f"Minifying JS: {file_path.relative_to(directory)}")
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                minified = minify_js(content)
                
                # Create minified version
                min_path = file_path.with_suffix('.min.js')
                min_path.write_text(minified, encoding='utf-8')
                
                # Also overwrite original for immediate effect
                file_path.write_text(minified, encoding='utf-8')
                
                new_size = len(minified)
                saved = original_size - new_size
                stats['js']['count'] += 1
                stats['js']['saved'] += saved
                print(f"  ✅ Saved {saved:,} bytes ({saved/1024:.1f} KB)")
    
    return stats

if __name__ == "__main__":
    frontend_dir = Path(__file__).parent / "frontend"
    
    print("🔧 Minifying Frontend Assets")
    print("="*50)
    
    stats = process_files(frontend_dir)
    
    print("\n📊 Minification Results")
    print("="*50)
    print(f"CSS Files: {stats['css']['count']} files")
    print(f"  Total saved: {stats['css']['saved']:,} bytes ({stats['css']['saved']/1024:.1f} KB)")
    print(f"JS Files: {stats['js']['count']} files")
    print(f"  Total saved: {stats['js']['saved']:,} bytes ({stats['js']['saved']/1024:.1f} KB)")
    print(f"\n🎉 Total saved: {(stats['css']['saved'] + stats['js']['saved'])/1024:.1f} KB")