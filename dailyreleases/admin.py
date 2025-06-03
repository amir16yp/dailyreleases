from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime, timedelta
import psutil
import os
import sqlite3
import configparser
from functools import wraps
from pathlib import Path
from .Config import CONFIG
from .Cache import Cache
from .Generator import Generator
from .PREdbs import PREdbs
from discord_webhook import DiscordWebhook

# Get the package directory
PACKAGE_DIR = Path(__file__).parent

# Initialize Flask app with correct template and static folders
app = Flask(__name__,
            template_folder=str(PACKAGE_DIR / 'templates'),
            static_folder=str(PACKAGE_DIR / 'static'))
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize components
generator = Generator()
predb_handler = PREdbs()

def get_admin_config():
    """Get admin config with defaults if not set"""
    if 'admin' not in CONFIG.CONFIG:
        CONFIG.CONFIG['admin'] = {}
    
    admin_config = CONFIG.CONFIG['admin']
    defaults = {
        'username': 'admin',
        'password': 'changeme',
        'host': '127.0.0.1',
        'port': '5000'
    }
    
    # Set defaults for any missing values
    for key, value in defaults.items():
        if key not in admin_config:
            admin_config[key] = value
    
    return admin_config

def check_auth(username, password):
    """Check if the username/password combination is valid."""
    admin_config = get_admin_config()
    return (username == admin_config['username'] and 
            password == admin_config['password'])

def authenticate():
    """Send a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_db_connection():
    """Create a new database connection for each request"""
    try:
        conn = sqlite3.connect(CONFIG.DATA_DIR.joinpath("cache.sqlite"))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        raise

@app.route('/')
@requires_auth
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering template: {e}")
        return "Error loading admin panel", 500

@app.route('/api/stats/releases')
@requires_auth
def release_stats():
    try:
        # Get releases from the last 7 days
        cutoff_timestamp = (datetime.utcnow() - timedelta(days=7)).timestamp()
        
        # Query cache for releases
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count, 
                       strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as date,
                       group_name
                FROM pres 
                WHERE timestamp > ?
                GROUP BY date, group_name
                ORDER BY date DESC
            """, (cutoff_timestamp,))
            
            releases = cursor.fetchall()
            
            # Process the data
            stats = {
                'total_releases': len(releases),
                'releases_by_date': {},
                'releases_by_group': {}
            }
            
            for release in releases:
                date = release['date']
                group = release['group_name']
                count = release['count']
                
                # Add to releases by date
                if date not in stats['releases_by_date']:
                    stats['releases_by_date'][date] = 0
                stats['releases_by_date'][date] += count
                
                # Add to releases by group
                if group not in stats['releases_by_group']:
                    stats['releases_by_group'][group] = 0
                stats['releases_by_group'][group] += count
            
            return jsonify(stats)
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"Error getting release stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats/system')
@requires_auth
def system_stats():
    try:
        process = psutil.Process(os.getpid())
        
        stats = {
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'memory_info': {
                'rss': process.memory_info().rss / 1024 / 1024,  # Convert to MB
                'vms': process.memory_info().vms / 1024 / 1024   # Convert to MB
            },
            'disk_usage': {
                'total': psutil.disk_usage('/').total / 1024 / 1024 / 1024,  # Convert to GB
                'used': psutil.disk_usage('/').used / 1024 / 1024 / 1024,    # Convert to GB
                'free': psutil.disk_usage('/').free / 1024 / 1024 / 1024     # Convert to GB
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Error getting system stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats/cache')
@requires_auth
def cache_stats():
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Get total number of entries
            cursor.execute("SELECT COUNT(*) FROM pres")
            total_entries = cursor.fetchone()[0]
            
            # Get entries by age
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN timestamp > strftime('%s', 'now', '-1 day') THEN 'Last 24 hours'
                        WHEN timestamp > strftime('%s', 'now', '-7 day') THEN 'Last 7 days'
                        WHEN timestamp > strftime('%s', 'now', '-30 day') THEN 'Last 30 days'
                        ELSE 'Older'
                    END as age_group,
                    COUNT(*) as count
                FROM pres
                GROUP BY age_group
            """)
            
            age_stats = dict(cursor.fetchall())
            
            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0] / 1024 / 1024  # Convert to MB
            
            stats = {
                'total_entries': total_entries,
                'entries_by_age': age_stats,
                'database_size_mb': db_size
            }
            
            return jsonify(stats)
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"Error getting cache stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/config')
@requires_auth
def get_config():
    try:
        # Return a safe version of the config (excluding sensitive data)
        safe_config = {
            'main': dict(CONFIG.CONFIG['main']),
            'logging': dict(CONFIG.CONFIG['logging']),
            'web': dict(CONFIG.CONFIG['web']),
            'admin': {
                'host': get_admin_config()['host'],
                'port': get_admin_config()['port'],
                'username': get_admin_config()['username']
            }
        }
        
        # Add discord section with webhook URLs
        if 'discord' in CONFIG.CONFIG:
            safe_config['discord'] = {
                'webhook_url': CONFIG.CONFIG['discord'].get('webhook_url', [])
            }
        
        return jsonify(safe_config)
    except Exception as e:
        app.logger.error(f"Error getting config: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/config/<section>/<key>', methods=['GET', 'PUT'])
@requires_auth
def config_value(section, key):
    try:
        if request.method == 'GET':
            if section == 'admin':
                admin_config = get_admin_config()
                if key in admin_config:
                    return jsonify({
                        'value': admin_config[key],
                        'type': 'text'  # Default type
                    })
            elif section in CONFIG.CONFIG and key in CONFIG.CONFIG[section]:
                value = CONFIG.CONFIG[section][key]
                # Handle webhook URLs specially
                if key == 'webhook_url':
                    if isinstance(value, str):
                        value = [url.strip() for url in value.split(',') if url.strip()]
                    elif not isinstance(value, list):
                        value = []
                return jsonify({
                    'value': value,
                    'type': 'text'  # Default type
                })
            return jsonify({'error': 'Setting not found'}), 404
        
        elif request.method == 'PUT':
            if section == 'admin':
                if 'admin' not in CONFIG.CONFIG:
                    CONFIG.CONFIG['admin'] = {}
                section_config = CONFIG.CONFIG['admin']
            elif section not in CONFIG.CONFIG:
                return jsonify({'error': 'Section not found'}), 404
            else:
                section_config = CONFIG.CONFIG[section]
            
            data = request.get_json()
            if not data or 'value' not in data:
                return jsonify({'error': 'No value provided'}), 400
            
            # Handle webhook URLs specially
            if key == 'webhook_url':
                value = data['value']
                if isinstance(value, list):
                    # Filter out empty strings and strip whitespace
                    value = [url.strip() for url in value if url.strip()]
                    # Convert to comma-separated string for config storage
                    section_config[key] = ','.join(value)
                else:
                    value = value.strip()
                    section_config[key] = value if value else ''
            else:
                section_config[key] = str(data['value'])
            
            # Save to file
            with open(CONFIG.CONFIG_FILE, 'w') as configfile:
                CONFIG.CONFIG.write(configfile)
            
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error handling config value: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test-webhook', methods=['POST'])
@requires_auth
def test_webhook():
    try:
        data = request.get_json()
        if not data or 'webhook_url' not in data:
            return jsonify({'error': 'No webhook URL provided'}), 400
        
        webhook_url = data['webhook_url'].strip()
        if not webhook_url:
            return jsonify({'error': 'Invalid webhook URL'}), 400
        
        # Create a test message
        title = "Test Message"
        test_content = "This is a test message from the Daily Releases admin panel."
        
        # Send the test message
        webhook = DiscordWebhook(url=webhook_url, content=title)
        webhook.add_file(test_content.encode(), filename=title + '.txt')
        response = webhook.execute()
        
        if response.status_code == 204:  # Discord returns 204 on success
            return jsonify({'success': True})
        else:
            return jsonify({'error': f'Discord returned status code {response.status_code}'}), 500
            
    except Exception as e:
        app.logger.error(f"Error testing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def run_admin_panel(host='127.0.0.1', port=5000):
    # Use admin config values if available
    admin_config = get_admin_config()
    host = admin_config['host']
    port = int(admin_config['port'])
    
    # Enable debug mode for development
    app.debug = True
    
    # Run the Flask app
    app.run(host=host, port=port) 