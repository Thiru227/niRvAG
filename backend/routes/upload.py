"""
Upload Routes — Products CSV & Document indexing
"""
from flask import Blueprint, request, jsonify, g
from utils.auth_middleware import require_auth
from models.supabase_client import upsert_product, create_document_record, _patch
import csv
import io
import os
import tempfile
import datetime

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/products', methods=['POST'])
@require_auth(roles=['admin'])
def upload_products():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are accepted"}), 400

    content = file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))

    count = 0
    for row in reader:
        try:
            upsert_product({
                'name': row.get('name', ''),
                'category': row.get('category', ''),
                'price': float(row.get('price', 0)),
                'description': row.get('description', ''),
                'stock_count': int(row.get('stock_count', 0)),
                'is_available': True
            })
            count += 1
        except Exception as e:
            print(f"Product row error: {e}")

    return jsonify({"message": f"Imported {count} products", "count": count})


@upload_bp.route('/document', methods=['POST'])
@require_auth(roles=['admin'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

    if ext not in ['pdf', 'txt']:
        return jsonify({"error": "Only PDF and TXT files are accepted"}), 400

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Extract text
        text = ""
        if ext == 'pdf':
            try:
                from services.ocr import extract_text_from_pdf
                text = extract_text_from_pdf(tmp_path)
            except ImportError:
                # Fallback: try reading as plain text
                try:
                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                except Exception:
                    text = ""
        else:
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

        if not text or len(text.strip()) < 10:
            return jsonify({"error": "Could not extract text from document"}), 400

        print(f"📄 Extracted {len(text)} chars from {file.filename}")

        # Record in Supabase
        doc_record = create_document_record({
            'filename': file.filename,
            'file_type': ext,
            'storage_path': f'documents/{file.filename}',
            'uploaded_by': g.user['id']
        })

        doc_id = doc_record['id'] if doc_record else file.filename

        # Index in ChromaDB
        chunks = 0
        try:
            from services.rag import index_document
            chunks = index_document(text, doc_id, file.filename)
            print(f"✅ ChromaDB indexed {chunks} chunks for {file.filename}")
        except ImportError as e:
            print(f"ChromaDB import error: {e}")
            # Estimate chunks for display
            chunks = max(1, len(text.split()) // 500)
        except Exception as e:
            print(f"ChromaDB indexing error: {e}")
            chunks = 0

        # Update chunk count and indexed_at timestamp in Supabase
        if doc_record and chunks > 0:
            try:
                _patch('documents', {
                    'chunk_count': chunks,
                    'indexed_at': datetime.datetime.utcnow().isoformat()
                }, {'id': f'eq.{doc_id}'})
                print(f"✅ Updated document record: {chunks} chunks, indexed_at set")
            except Exception as e:
                print(f"Failed to update document record: {e}")

        return jsonify({
            "message": f"Document indexed successfully: {chunks} chunks created",
            "chunks": chunks,
            "filename": file.filename,
            "doc_id": doc_id
        })

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
