from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
import threading
import time

# Import your main RAG functions
from main import (
    process_uploaded_file,
    chat_query,
    clear_database,
    VECTOR_DB
)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state to track processing
processing_status = {
    'is_processing': False,
    'progress': 0,
    'message': '',
    'current_file': None
}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'RAG Chatbot API is running',
        'documents_loaded': len(VECTOR_DB) > 0,
        'chunks_count': len(VECTOR_DB)
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process it for RAG."""
    global processing_status

    try:
        # Check if a file is being processed
        if processing_status['is_processing']:
            return jsonify({
                'error': 'Another file is currently being processed. Please wait.'
            }), 429

        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Secure the filename
        filename = secure_filename(file.filename)

        # Save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Start processing in background thread
        def process_file_background():
            global processing_status
            try:
                processing_status.update({
                    'is_processing': True,
                    'progress': 0,
                    'message': 'Starting file processing...',
                    'current_file': filename
                })

                processing_status['message'] = 'Reading file...'
                processing_status['progress'] = 25

                # Process the file
                success = process_uploaded_file(file_path)

                processing_status['progress'] = 100

                if success:
                    processing_status['message'] = 'File processed successfully!'
                else:
                    processing_status['message'] = 'Failed to process file'

                # Keep status for a few seconds then reset
                time.sleep(2)
                processing_status.update({
                    'is_processing': False,
                    'progress': 0,
                    'message': '',
                    'current_file': None
                })

            except Exception as e:
                processing_status.update({
                    'is_processing': False,
                    'progress': 0,
                    'message': f'Error: {str(e)}',
                    'current_file': None
                })

        # Start background processing
        thread = threading.Thread(target=process_file_background)
        thread.daemon = True
        thread.start()

        return jsonify({
            'message': 'File upload started. Processing in background...',
            'filename': filename,
            'status': 'processing'
        })

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/upload/status', methods=['GET'])
def upload_status():
    """Get current upload/processing status."""
    return jsonify(processing_status)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat queries."""
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message'].strip()

        if not user_message:
            return jsonify({'error': 'Empty message'}), 400

        # Check if any documents are loaded
        if len(VECTOR_DB) == 0:
            return jsonify({
                'response': 'No documents have been uploaded yet. Please upload a document first to ask questions.',
                'sources': [],
                'chunks_used': 0
            })

        # Process the query
        result = chat_query(user_message)

        return jsonify({
            'response': result['response'],
            'sources': result['sources'],
            'chunks_used': result['chunks_used'],
            'query': user_message
        })

    except Exception as e:
        return jsonify({'error': f'Chat processing failed: {str(e)}'}), 500


@app.route('/api/clear', methods=['POST'])
def clear_documents():
    """Clear all loaded documents."""
    try:
        clear_database()

        # Also clear uploaded files
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

        return jsonify({
            'message': 'All documents and files cleared successfully',
            'chunks_count': len(VECTOR_DB)
        })

    except Exception as e:
        return jsonify({'error': f'Failed to clear documents: {str(e)}'}), 500


@app.route('/api/info', methods=['GET'])
def get_info():
    """Get current system information."""
    return jsonify({
        'documents_loaded': len(VECTOR_DB) > 0,
        'chunks_count': len(VECTOR_DB),
        'current_file': processing_status.get('current_file'),
        'is_processing': processing_status.get('is_processing'),
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024)
    })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("🚀 Starting RAG Chatbot API...")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📄 Supported formats:", ", ".join(ALLOWED_EXTENSIONS))
    print("🌐 API will be available at: http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  POST /api/upload     - Upload documents")
    print("  POST /api/chat       - Send chat messages")
    print("  GET  /api/info       - Get system info")
    print("  GET  /api/health     - Health check")
    print("  POST /api/clear      - Clear all documents")
    print("  GET  /api/upload/status - Get upload status")

    app.run(debug=True, host='0.0.0.0', port=5000)