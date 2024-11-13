from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/verify', methods=['POST'])
def verify():
    # Mock response data
    response_data = {
        'valid': 'true',
        'mrn': '423445',
        'fin': '42344500003'
    }
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(port=5001)