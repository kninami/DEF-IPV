import flask
import os
from functools import wraps
from stegano_processor import ImageSteganographer

app = flask.Flask(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = flask.request.form.get('token')

        if not token:
            return flask.jsonify({'error': 'No token provided'}), 401
        
        if token != os.getenv("API_TOKEN"):
            return flask.jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html')

@app.route('/results', methods=['GET'])
@token_required
def results():
    data = {}
    return flask.jsonify({
        'success': True,
        'data': data
    })

@app.route('/process', methods=['POST'])
@token_required
def process_image():
    try:
        steganographer = ImageSteganographer()
        steganographer.process()
        
        return flask.jsonify({
            'success': True,
            'message': 'Image successfully processed',
            'stego_image': steganographer.stego_image_name
        })
        
    except Exception as e:
        return flask.jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)