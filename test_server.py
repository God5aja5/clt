import os
from app import create_app

app, db = create_app()

if __name__ == '__main__':
    print('Starting Flask app on port 8080...')
    app.run(debug=False, host='0.0.0.0', port=8080)