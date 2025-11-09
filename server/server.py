import os
import tempfile
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store generated HTML in memory
slides_cache = {}

@app.route('/convert', methods=['POST'])
def convert_markdown():
    """
    Accepts filename and markdown content, converts to Reveal JS slides via pandoc,
    and stores the resulting HTML.
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        markdown_content = data.get('content')
        
        if not filename or not markdown_content:
            return jsonify({'error': 'Missing filename or content'}), 400
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save markdown file
            md_path = os.path.join(tmpdir, filename)
            with open(md_path, 'w') as f:
                f.write(markdown_content)
            
            # Convert markdown to Reveal JS HTML using pandoc
            html_filename = filename.replace('.md', '.html')
            html_path = os.path.join(tmpdir, html_filename)
            
            subprocess.run([
                'pandoc',
                md_path,
                '-t', 'revealjs',
                '-o', html_path,
                '-s'
            ], check=True)
            
            # Read the generated HTML
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Store in cache
            slides_id = html_filename.replace('.html', '')
            slides_cache[slides_id] = html_content
            
            return jsonify({
                'id': slides_id,
                'url': f'/slides/{slides_id}'
            }), 200
    
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Pandoc conversion failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/slides/<slides_id>', methods=['GET'])
def get_slides(slides_id):
    """Serve the rendered slides."""
    if slides_id not in slides_cache:
        return jsonify({'error': 'Slides not found'}), 404
    
    return slides_cache[slides_id], 200, {'Content-Type': 'text/html'}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)