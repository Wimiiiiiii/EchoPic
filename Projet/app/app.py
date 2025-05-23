from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

import os

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration du Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe utilisateur simple pour la démo
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Utilisateur de démo
users = {'admin': {'password': generate_password_hash('admin')}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and check_password_hash(users[username]['password'], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
@login_required
def search():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # TODO: Intégrer ici le code de recherche d'images
        # Pour l'instant, retournons une réponse de démo
        return jsonify({
            'message': 'Image uploaded successfully',
            'results': []  # À remplacer par les résultats réels
        })

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000) 