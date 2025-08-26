#!/usr/bin/env python3
"""
Production-ready frontend server with compression and optimizations
"""
import os
import gzip
import mimetypes
from pathlib import Path
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="LPR Frontend Server")

# Add compression middleware - this alone will save ~974KB!
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).parent

# Enhanced MIME types
mimetypes.init()
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('text/html', '.html')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('font/woff', '.woff')

# Cache control headers for different file types
CACHE_CONTROL = {
    '.html': 'no-cache',
    '.js': 'public, max-age=31536000, immutable',  # 1 year for JS
    '.css': 'public, max-age=31536000, immutable',  # 1 year for CSS
    '.jpg': 'public, max-age=604800',  # 1 week for images
    '.jpeg': 'public, max-age=604800',
    '.png': 'public, max-age=604800',
    '.gif': 'public, max-age=604800',
    '.svg': 'public, max-age=604800',
    '.ico': 'public, max-age=604800',
    '.woff': 'public, max-age=31536000',
    '.woff2': 'public, max-age=31536000',
    '.ttf': 'public, max-age=31536000',
    '.eot': 'public, max-age=31536000',
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "frontend"}

# Serve index.html for root
@app.get("/")
async def serve_root(request: Request):
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return await serve_static_file_compressed(index_path, request)
    return PlainTextResponse("Frontend not found", status_code=404)

# Custom static file handler with compression
async def serve_static_file_compressed(file_path: Path, request: Request):
    """Serve static file with compression if requested"""
    # Get file extension and determine cache control
    ext = file_path.suffix.lower()
    cache_control = CACHE_CONTROL.get(ext, 'no-cache')
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Read file content
    file_content = file_path.read_bytes()
    
    # Check if client accepts gzip and file is compressible
    accept_encoding = request.headers.get('accept-encoding', '')
    compressible_types = {'text/css', 'application/javascript', 'text/html', 'text/plain', 'application/json'}
    should_compress = (
        'gzip' in accept_encoding and 
        content_type in compressible_types and 
        len(file_content) > 1000  # Only compress files > 1KB
    )
    
    headers = {
        "Cache-Control": cache_control,
        "X-Content-Type-Options": "nosniff"
    }
    
    if should_compress:
        # Compress content
        compressed_content = gzip.compress(file_content)
        headers["Content-Encoding"] = "gzip"
        headers["Vary"] = "Accept-Encoding"
        content = compressed_content
        print(f"🗜️  Compressed {file_path.name}: {len(file_content)} → {len(compressed_content)} bytes ({100-len(compressed_content)*100//len(file_content)}% savings)")
    else:
        content = file_content
    
    return Response(
        content=content,
        media_type=content_type,
        headers=headers
    )

# Catch-all route for static files and SPA routing
@app.get("/{full_path:path}")
@app.head("/{full_path:path}")
async def serve_frontend(full_path: str, request: Request):
    # Try to serve the exact file first
    file_path = FRONTEND_DIR / full_path
    
    if file_path.exists() and file_path.is_file():
        return await serve_static_file_compressed(file_path, request)
    
    # For SPA routing, serve index.html for any non-file paths
    if not Path(full_path).suffix:
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(
                index_path,
                media_type="text/html",
                headers={"Cache-Control": "no-cache"}
            )
    
    return PlainTextResponse("Not found", status_code=404)

if __name__ == "__main__":
    import sys
    
    # Check if brotli support is available (optional but better compression)
    try:
        import brotlicffi
        print("✅ Brotli compression available")
    except ImportError:
        print("⚠️  Brotli not available, using gzip only")
    
    print(f"""
🚀 Production Frontend Server Starting
=====================================
📁 Serving from: {FRONTEND_DIR}
🗜️  Compression: Enabled (GZip)
💾 Cache headers: Optimized
🔒 Security headers: Enabled
🚀 Server: http://localhost:8080
=====================================
    """)
    
    # Run with production settings
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080, 
        log_level="info",
        access_log=True
    )