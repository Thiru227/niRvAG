"""
Speech-to-Text Route — ElevenLabs STT API
"""
from flask import Blueprint, request, jsonify
import os
import tempfile

stt_bp = Blueprint('stt', __name__)

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')


@stt_bp.route('/stt', methods=['POST'])
def speech_to_text():
    """Receive audio file, send to ElevenLabs STT, return text."""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    if not ELEVENLABS_API_KEY:
        return jsonify({"error": "ElevenLabs API key not configured"}), 500

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        import httpx

        # ElevenLabs STT API
        with open(tmp_path, 'rb') as f:
            response = httpx.post(
                'https://api.elevenlabs.io/v1/speech-to-text',
                headers={
                    'xi-api-key': ELEVENLABS_API_KEY,
                },
                files={
                    'audio': ('recording.webm', f, 'audio/webm'),
                },
                data={
                    'model_id': 'scribe_v1',
                },
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '')
            print(f"[STT] ✅ Transcribed: {text[:100]}")
            return jsonify({"text": text})
        else:
            print(f"[STT] ❌ ElevenLabs error {response.status_code}: {response.text[:200]}")
            return jsonify({"error": f"STT failed: {response.status_code}"}), 500

    except Exception as e:
        print(f"[STT] ❌ Exception: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
