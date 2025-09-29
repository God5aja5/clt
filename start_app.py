from production import init_production
init_production()

import os
from app import create_app

app, db = create_app()

print('Starting production app on port 8080...')
app.run(host='0.0.0.0', port=8080, debug=False)