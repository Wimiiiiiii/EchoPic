import matplotlib
matplotlib.use('Agg') # Doit être appelé AVANT d'importer pyplot ou pylab

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import numpy as np
import os
from PIL import Image
from werkzeug.utils import secure_filename
import torch
import pickle

app = Flask(__name__)
app.secret_key = 'dev_secret_key_12345'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['LOAD_FOLDER'] = 'image.orig/'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max file size
features_path = 'features/'

# Create necessary directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join('static', 'rp_curves'), exist_ok=True)


def euclidean_distance(vec1, vec2):
    return np.sqrt(np.sum((vec1 - vec2) ** 2))

def getkVoisins(features_dict, query_name, k):
    """
    Trouve les `k` voisins les plus proches d'une image requête en utilisant la distance euclidienne.

    - `features_dict` : Dictionnaire {nom_fichier: feature_vector}
    - `query_name` : Nom du fichier de l'image requête (sans extension)
    - `k` : Nombre de voisins à retourner.

    Retourne :
    - Liste des `k` noms d'images les plus proches avec leur distance.
    """
    if query_name not in features_dict:
        raise ValueError(f"L'image requête '{query_name}' n'existe pas dans les features !")

    query_feature = features_dict[query_name]
    distances_name = []

    for name, feature_vector in features_dict.items():
        dist = euclidean_distance(query_feature, feature_vector)  # Distance euclidienne
        distances_name.append((name, dist))  # Stocker le nom et la distance

    # Trier par distance croissante et récupérer les `k` plus proches
    distances_name.sort(key=lambda x: x[1])

    return distances_name[:k]  # Retourner les `k` plus proches voisins



def Compute_RP( top, nom_image_requete, images_proches):
    """
    Calcule et enregistre la courbe Rappel-Précision (RP) pour une image requête avec un `top` donné.

    - `RP_file` : Chemin du fichier où enregistrer les valeurs RP.
    - `top` : Nombre d'images les plus proches analysées.
    - `nom_image_requete` : Nom de l'image requête (ex: "107").
    - `nom_images_non_proches` : Liste des noms des images non proches (ex: ["102", "205", ...]).

    Résultat :
    - Fichier `.txt` contenant les valeurs de RP.
    """

    # 📌 Initialisation
    rappel_precision = []
    rp = []

    position1 = int(os.path.splitext(os.path.basename(nom_image_requete))[0]) // 100  # Identifier le groupe de l'image requête

    # 📌 Boucle pour déterminer si chaque image est pertinente ou non
    for j in range(top):
        position2 = int(os.path.splitext(os.path.basename(images_proches[j]))[0]) // 100  # Groupe de l'image voisine
        if position1 == position2:
            rappel_precision.append("pertinent")
        else:
            rappel_precision.append("non pertinent")

    # 📌 Boucle pour calculer le Rappel et la Précision
    val = 0  # Nombre d'images pertinentes accumulées
    for i in range(top):
        if rappel_precision[i] == "pertinent":
            val += 1  # Augmenter si l'image est pertinente

        precision = (val / (i + 1)) * 100  # Précision en pourcentage
        rappel = (val / top) * 100  # Rappel en pourcentage
        rp.append(f"{precision} {rappel}")  # Stocker les valeurs

    RP_file = str(int(os.path.splitext(os.path.basename(nom_image_requete))[0])) + 'RP.txt'
    # 📌 Sauvegarde dans un fichier texte
    with open(RP_file, 'w') as s:
        for a in rp:
            s.write(str(a) + '\n')

    print(f"✅ RP enregistré dans {RP_file}")
    return RP_file


def Display_RP(fichier, model_name):
    """
    Génère et sauvegarde la courbe Rappel-Précision (RP) à partir d'un fichier texte.

    Args:
        fichier (str): Chemin du fichier contenant les valeurs RP
        model_name (str): Nom du modèle utilisé

    Returns:
        str: Chemin de l'image générée
    """
    import matplotlib.pyplot as plt
    # Charger les données depuis le fichier `.txt`
    x, y = [], []

    with open(fichier, 'r') as csvfile:
        for line in csvfile:
            values = line.strip().split()
            if len(values) == 2:
                x.append(float(values[0]))  # Précision
                y.append(float(values[1]))  # Rappel

    # Convertir en tensor PyTorch
    x_tensor = torch.tensor(x)
    y_tensor = torch.tensor(y)

    # Créer la figure
    plt.figure(figsize=(8, 6))
    plt.plot(y_tensor, x_tensor, 'C1', label=model_name)
    plt.xlabel('Rappel (Recall)')
    plt.ylabel('Précision (Precision)')
    plt.title("Courbe Rappel/Précision (RP)")
    plt.legend()
    plt.grid(True)

    # Sauvegarder la figure
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
    # Ici, vous pourriez ajouter une logique pour vérifier si l'utilisateur est connecté
    # avant de rendre le template. Pour l'instant, on le rend directement.
    return render_template('search.html')

def combine_results(all_results, top_k):
    """
    Combine les résultats de plusieurs modèles en utilisant un système de vote pondéré.
    
    Args:
        all_results: Liste de listes de résultats (chaque sous-liste contient les résultats d'un modèle)
        top_k: Nombre de résultats à retourner
    
    Returns:
        Liste des meilleurs résultats combinés
    """
    # Dictionnaire pour stocker les scores combinés
    combined_scores = {}
    
    # Pour chaque modèle
    for model_results in all_results:
        # Pour chaque résultat du modèle
        for idx, result in enumerate(model_results):
            path = result['path']
            score = result['score'] 
            
            if path in combined_scores:
                combined_scores[path]['score'] += score
                combined_scores[path]['count'] += 1
            else:
                combined_scores[path] = {'score': score, 'count': 1}
    
    # Normaliser les scores en fonction du nombre de modèles qui ont trouvé chaque image
    final_results = []
    for path, data in combined_scores.items():
        normalized_score = data['score'] / data['count']
        final_results.append({
            'path': path,
            'score': normalized_score,
        })
    
    # Trier par score décroissant et retourner les top_k
    final_results.sort(key=lambda x: x['score'])
    return final_results[:top_k]

@app.route('/search', methods=['POST'])
def search():
    print("--- Début de la requête /search ---") # DEBUG
    print(f"Données du formulaire (request.form): {request.form}") # DEBUG
    print(f"Fichiers reçus (request.files): {request.files}") # DEBUG
    print("--- Début de la requête /search ---")
    
    # Récupération des modèles sélectionnés
    selected_models = request.form.getlist('models')
    if not selected_models:
        flash("Veuillez sélectionner au moins un modèle.", 'error')
        return redirect(url_for('search_interface'))
    


    top_k_str = request.form.get('top_k')
    try:
        top_k = int(top_k_str)
    except ValueError:
        flash(f"La valeur de top_k ('{top_k_str}') n'est pas un nombre valide.", 'error')
        return redirect(url_for('search_interface'))

    if 'image' not in request.files:
        print("DEBUG: 'image' non trouvé dans request.files") # DEBUG
        flash('Aucun champ de fichier image (name="image") trouvé dans la requête.', 'error')
        return redirect(url_for('search_interface'))

    file = request.files['image']
    print(f"DEBUG: Objet fichier récupéré: {file}") # DEBUG

    if not file or file.filename == '':
        print(f"DEBUG: Fichier non sélectionné ou nom de fichier vide (file.filename: '{file.filename}')") # DEBUG
        flash('Aucun fichier image n\'a été sélectionné dans le formulaire.', 'error')
        return redirect(url_for('search_interface'))

    filename_secure = secure_filename(file.filename)
    print(f"DEBUG: Nom de fichier sécurisé: {filename_secure}") # DEBUG
    
    # Construction de la clé pour la recherche dans le PKL
    # Clés PKL attendues : 'image.orig/nomfichier.jpg'
    filename_secure_with_path = os.path.join(app.config['LOAD_FOLDER'], filename_secure).replace('\\', '/')
    print(f"DEBUG: Clé construite pour la recherche PKL (query_name): {filename_secure_with_path}") # DEBUG
    all_model_results = []

    
    try:
        # Sauvegarde du fichier téléversé
        upload_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_secure)
        file.save(upload_filepath)
        print(f"DEBUG: Fichier téléversé sauvegardé ici: {upload_filepath}") # DEBUG

        for model_name in selected_models:
            features_file_path = os.path.join(features_path, model_name + '.pkl')
            if not os.path.exists(features_file_path):
                flash(f"Le fichier de caractéristiques pour le modèle '{model_name}' est introuvable.", 'error')
                continue

            with open(features_file_path, 'rb') as f:
                loaded_features = pickle.load(f)
                if isinstance(loaded_features, list):
                    loaded_features = dict(loaded_features)
           
            # Ajustement de la clé pour le modèle VIT
            query_name = filename_secure_with_path
            if model_name == 'VIT':
                query_name = os.path.splitext(filename_secure)[0]

            similar_items = getkVoisins(loaded_features, query_name, top_k)
           
            # Préparation des résultats pour ce modèle
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

        # Combinaison des résultats de tous les modèles
        combined_results = combine_results(all_model_results, top_k)
        
        # Chemin pour l'image requête
        query_image_path = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER'].strip('/')), filename_secure).replace('\\', '/')
        
        # Extraction des noms de fichiers pour la courbe RP
        similar_filenames = [result['path'].split('/')[-1] for result in combined_results]
        
        # Génération de la courbe RP pour les résultats combinés
        rp_file = Compute_RP(top_k, filename_secure, similar_filenames)
        rp_image_path = Display_RP(rp_file, "Résultats combinés")

        return render_template('results.html',
                             model_name=selected_models,
                             query_image=query_image_path,
                             results=combined_results,
                             models=selected_models,
                             top_k=top_k,
                             rp_curves= rp_image_path)

    except Exception as e:
        print(f"ERREUR: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de la recherche: {str(e)}', 'error')
        return redirect(url_for('search_interface'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 