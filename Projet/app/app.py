# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import numpy as np
import os
from PIL import Image
from werkzeug.utils import secure_filename
import torch
import pickle
import psycopg2
from psycopg2 import Error
import json
from datetime import datetime
import ssl

# Configuration de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['LOAD_FOLDER'] = 'image.orig/'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max file size
app.config['FLASK_APP'] = 'app.py'
features_path = 'features/'

# Configuration SSL
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('certs/cert.pem', 'certs/key.pem')

# Create necessary directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join('static', 'rp_curves'), exist_ok=True)

# Configuration PostgreSQL
def get_db_connection():
    try:
        host = 'localhost' if os.getenv('FLASK_ENV') == 'development' else os.getenv('POSTGRES_HOST', 'db')
        
        connection = psycopg2.connect(
            host=host,
            user=os.getenv('POSTGRES_USER', 'echopic_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'echopic_password'),
            database=os.getenv('POSTGRES_DB', 'echopic_db'),
            port=os.getenv('POSTGRES_PORT', 5432)
        )
        return connection
    except Error as e:
        print(f"Erreur de connexion a PostgreSQL: {e}")
        return None

def save_rp_curve(query_image, model_name, rp_file_path, rp_image_path, top_k, models_used, search_params):
    try:
        print(f"Tentative de sauvegarde RP curve pour l'image: {query_image}")
        connection = get_db_connection()
        if connection is None:
            print("Erreur: Impossible de se connecter a la base de donnees")
            return False

        print("Connexion a la base de donnees etablie")
        cursor = connection.cursor()
        query = (
            "INSERT INTO rp_curves "
            "(query_image, model_name, rp_file_path, rp_image_path, top_k, models_used, search_params) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "RETURNING id"
        )
        values = (
            query_image,
            model_name,
            rp_file_path,
            rp_image_path,
            top_k,
            json.dumps(models_used),
            json.dumps(search_params)
        )
        print(f"Execution de la requete avec les valeurs: {values}")
        cursor.execute(query, values)
        connection.commit()
        inserted_id = cursor.fetchone()[0]
        print(f"Insertion reussie avec l'ID: {inserted_id}")
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"Erreur lors de la sauvegarde de la courbe RP: {e}")
        return False

def euclidean_distance(vec1, vec2):
    return np.sqrt(np.sum((vec1 - vec2) ** 2))

def getkVoisins(features_dict, query_name, k):
    if query_name not in features_dict:
        raise ValueError(f"L'image requete '{query_name}' n'existe pas dans les features!")

    query_feature = features_dict[query_name]
    distances_name = []

    for name, feature_vector in features_dict.items():
        dist = euclidean_distance(query_feature, feature_vector)
        distances_name.append((name, dist))

    distances_name.sort(key=lambda x: x[1])
    return distances_name[:k]

def Compute_RP(top, nom_image_requete, images_proches):
    rappel_precision = []
    rp = []

    # Ajuster top_k si nous avons moins d'images que demandé
    actual_top = min(top, len(images_proches))
    if actual_top < top:
        print(f"ATTENTION: Seulement {actual_top} images trouvées sur {top} demandées")

    position1 = int(os.path.splitext(os.path.basename(nom_image_requete))[0]) // 100

    # Utiliser actual_top au lieu de top
    for j in range(actual_top):
        position2 = int(os.path.splitext(os.path.basename(images_proches[j]))[0]) // 100
        if position1 == position2:
            rappel_precision.append("pertinent")
        else:
            rappel_precision.append("non pertinent")

    val = 0
    # Utiliser actual_top pour le calcul de rappel
    for i in range(actual_top):
        if rappel_precision[i] == "pertinent":
            val += 1

        precision = (val / (i + 1)) * 100
        rappel = (val / actual_top) * 100  # Utiliser actual_top ici aussi
        rp.append(f"{precision} {rappel}")

    RP_file = str(int(os.path.splitext(os.path.basename(nom_image_requete))[0])) + 'RP.txt'
    with open(RP_file, 'w') as s:
        for a in rp:
            s.write(str(a) + '\n')

    print(f"RP enregistre dans {RP_file}")
    return RP_file

def Display_RP(fichier, model_name):
    import matplotlib.pyplot as plt
    x, y = [], []

    with open(fichier, 'r') as csvfile:
        for line in csvfile:
            values = line.strip().split()
            if len(values) == 2:
                x.append(float(values[0]))
                y.append(float(values[1]))

    x_tensor = torch.tensor(x)
    y_tensor = torch.tensor(y)

    plt.figure(figsize=(8, 6))
    plt.plot(y_tensor, x_tensor, 'C1', label=model_name)
    plt.xlabel('Rappel (Recall)')
    plt.ylabel('Precision (Precision)')
    plt.title("Courbe Rappel/Precision (RP)")
    plt.legend()
    plt.grid(True)

    rp_image_path = os.path.join('static', 'rp_curves', f'{os.path.splitext(os.path.basename(fichier))[0]}.png')
    os.makedirs(os.path.dirname(rp_image_path), exist_ok=True)
    plt.savefig(rp_image_path)
    plt.close()

    return rp_image_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_interface')
def search_interface():
    return render_template('search.html')

def combine_results(all_results, top_k):
    combined_scores = {}
    
    for model_results in all_results:
        for idx, result in enumerate(model_results):
            path = result['path']
            score = result['score'] 
            
            if path in combined_scores:
                combined_scores[path]['score'] += score
                combined_scores[path]['count'] += 1
            else:
                combined_scores[path] = {'score': score, 'count': 1}
    
    final_results = []
    for path, data in combined_scores.items():
        normalized_score = data['score'] / data['count']
        final_results.append({
            'path': path,
            'score': normalized_score,
        })
    
    final_results.sort(key=lambda x: x['score'])
    return final_results[:top_k]

@app.route('/search', methods=['POST'])
def search():
    selected_models = request.form.getlist('models')
    if not selected_models:
        flash("Veuillez selectionner au moins un modele.", 'error')
        return redirect(url_for('search_interface'))

    top_k_str = request.form.get('top_k')
    try:
        top_k = int(top_k_str)
    except ValueError:
        flash(f"La valeur de top_k ('{top_k_str}') n'est pas un nombre valide.", 'error')
        return redirect(url_for('search_interface'))

    if 'image' not in request.files:
        flash('Aucun champ de fichier image (name="image") trouve dans la requete.', 'error')
        return redirect(url_for('search_interface'))

    file = request.files['image']

    if not file or file.filename == '':
        flash('Aucun fichier image n\'a ete selectionne dans le formulaire.', 'error')
        return redirect(url_for('search_interface'))

    filename_secure = secure_filename(file.filename)
    filename_secure_with_path = os.path.join(app.config['LOAD_FOLDER'], filename_secure).replace('\\', '/')
    all_model_results = []

    try:
        upload_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_secure)
        file.save(upload_filepath)

        for model_name in selected_models:
            features_file_path = os.path.join(features_path, model_name + '.pkl')
            if not os.path.exists(features_file_path):
                flash(f"Le fichier de caracteristiques pour le modele '{model_name}' est introuvable.", 'error')
                continue

            with open(features_file_path, 'rb') as f:
                loaded_features = pickle.load(f)
                if isinstance(loaded_features, list):
                    loaded_features = dict(loaded_features)
           
            query_name = filename_secure_with_path
            if model_name == 'VIT':
                query_name = os.path.splitext(filename_secure)[0]

            similar_items = getkVoisins(loaded_features, query_name, top_k)
           
            model_results = []
            for item_key, distance in similar_items:
                score = distance
                
                image_path = item_key
                if model_name == 'VIT':
                    image_path = os.path.join(app.config['LOAD_FOLDER'], f"{item_key}.jpg").replace('\\', '/')
                
                model_results.append({
                    'path': image_path,
                    'score': score
                })
            
            all_model_results.append(model_results)

        combined_results = combine_results(all_model_results, top_k)
        
        query_image_path = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER'].strip('/')), filename_secure).replace('\\', '/')
        
        similar_filenames = [result['path'].split('/')[-1] for result in combined_results]
        
        rp_file = Compute_RP(top_k, filename_secure, similar_filenames)
        rp_image_path = Display_RP(rp_file, "Resultats combines")

        search_params = {
            'timestamp': datetime.now().isoformat(),
            'top_k': top_k,
            'selected_models': selected_models
        }
        
        save_rp_curve(
            query_image=filename_secure,
            model_name="Resultats combines",
            rp_file_path=rp_file,
            rp_image_path=rp_image_path,
            top_k=top_k,
            models_used=selected_models,
            search_params=search_params
        )

        return render_template('results.html',
                             query_image=query_image_path,
                             results=combined_results,
                             models_name=selected_models,
                             top_k=top_k,
                             rp_curves=rp_image_path)

    except Exception as e:
        print(f"ERREUR: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de la recherche: {str(e)}', 'error')
        return redirect(url_for('search_interface'))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5443,
        debug=False,
        ssl_context=ssl_context
    ) 
    