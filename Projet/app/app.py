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
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024  # 3MB max file size
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

@app.route('/search', methods=['POST'])
def search():
    print("--- Début de la requête /search ---") # DEBUG
    print(f"Données du formulaire (request.form): {request.form}") # DEBUG
    print(f"Fichiers reçus (request.files): {request.files}") # DEBUG

    top_k_str = request.form.get('top_k')
    model_name = request.form.get('model')

    if not top_k_str or not model_name:
        flash(f"Paramètres manquants: top_k ('{top_k_str}') ou model ('{model_name}') non fournis par le formulaire.", 'error')
        return redirect(url_for('search_interface'))
    
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
    query_name_for_logic = os.path.join(app.config['LOAD_FOLDER'], filename_secure).replace('\\', '/')
    print(f"DEBUG: Clé construite pour la recherche PKL (query_name_for_logic): {query_name_for_logic}") # DEBUG

    try:
        features_file_path = os.path.join(features_path, model_name + '.pkl')
        print(f"DEBUG: Chemin du fichier PKL des caractéristiques: {features_file_path}") # DEBUG
        if not os.path.exists(features_file_path):
            flash(f"Le fichier de caractéristiques pour le modèle '{model_name}' est introuvable ici : {features_file_path}.", 'error')
            return redirect(url_for('search_interface'))
            
        with open(features_file_path, 'rb') as f:
            data_from_pkl = pickle.load(f)
        print(f"DEBUG: Type de données chargées depuis PKL: {type(data_from_pkl)}") # DEBUG

        if isinstance(data_from_pkl, list):
            # Essayer de convertir en dictionnaire si c'est une liste de paires (clé, valeur)
            try:
                loaded_features = dict(data_from_pkl)
                print(f"DEBUG: Données PKL (liste) converties en dictionnaire. Nombre d'entrées: {len(loaded_features)}")
            except (TypeError, ValueError) as e:
                flash(f"Le fichier PKL '{model_name}' ne contient pas une liste de paires clé-valeur valide. Erreur: {e}", 'error')
                return redirect(url_for('search_interface'))
        elif isinstance(data_from_pkl, dict):
            loaded_features = data_from_pkl
            print(f"DEBUG: Caractéristiques (dictionnaire) chargées pour le modèle '{model_name}'. Nombre d'entrées: {len(loaded_features)}")
            if model_name == 'VIT' and loaded_features:
                print(f"DEBUG: Quelques clés du PKL VIT (max 5): {list(loaded_features.keys())[:5]}")
        else:
            flash(f"Le format des données dans le fichier PKL '{model_name}' n'est pas reconnu (ni liste de paires, ni dictionnaire).", 'error')
            return redirect(url_for('search_interface'))

        # Sauvegarde du fichier téléversé
        upload_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_secure)
        file.save(upload_filepath)
        print(f"DEBUG: Fichier téléversé sauvegardé ici: {upload_filepath}") # DEBUG
        
        # Ajustement de la clé pour le modèle VIT
        current_query_name_for_logic = query_name_for_logic
        if model_name == 'VIT':
            # Pour VIT, les clés sont juste le nom du fichier sans extension, ex: "1"
            filename_without_ext = os.path.splitext(filename_secure)[0]
            current_query_name_for_logic = filename_without_ext
            print(f"DEBUG: Clé ajustée pour VIT: {current_query_name_for_logic}")

        similar_items = getkVoisins(loaded_features, current_query_name_for_logic, top_k)
        print(f"DEBUG: Voisins trouvés (top {top_k}): {similar_items}") # DEBUG
        
        similar_filenames_for_rp = [item[0] for item in similar_items]

        rp_file_generated_name = Compute_RP(top_k, filename_secure, similar_filenames_for_rp)
        print(f"DEBUG: Fichier RP texte généré: {rp_file_generated_name}") # DEBUG
        
        rp_image_path_generated = Display_RP(rp_file_generated_name, model_name)
        print(f"DEBUG: Image de la courbe RP générée: {rp_image_path_generated}") # DEBUG
        
        results = []
        for item_key, distance in similar_items:
            score = 1.0 / (1.0 + distance) if distance is not None and distance > -1 else 0 # distance peut etre 0
            
            # Construire le chemin d'affichage correctement
            image_display_path = item_key # Par défaut pour les modèles non-VIT
            if model_name == 'VIT':
                # Pour VIT, item_key est juste le nom (ex: "1"), reconstruire le chemin complet
                # Supposons que les images originales pour VIT sont des .jpg
                image_display_path = os.path.join(app.config['LOAD_FOLDER'], f"{item_key}.jpg").replace('\\', '/')
                print(f"DEBUG: [VIT] Chemin d'affichage pour {item_key}: {image_display_path}")
            
            results.append({
                'path': image_display_path, 
                'score': score
            })

        # Chemin pour afficher l'image téléversée, relatif à static/
        query_image_display_path = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER'].strip('/')), filename_secure).replace('\\', '/')
        print(f"DEBUG: Chemin d'affichage pour l'image requête: {query_image_display_path}") # DEBUG
        print("--- Fin de la requête /search (succès) ---")
        
        return render_template('results.html', 
                             query_image=query_image_display_path, 
                             results=results,
                             model_name=model_name,
                             top_k=top_k,
                             rp_image=rp_image_path_generated)

    except ValueError as ve:
        print(f"ERREUR (ValueError): {str(ve)}") # DEBUG
        flash(f"Erreur de données: L'image '{query_name_for_logic}' ne correspond à aucune entrée connue pour le modèle '{model_name}'. Assurez-vous d'utiliser une image du dataset original. Détail: {str(ve)}", 'warning')
        return redirect(url_for('search_interface'))
    except Exception as e:
        print(f"ERREUR (Exception générale): {type(e).__name__} - {str(e)}") # DEBUG
        import traceback
        traceback.print_exc() # Imprime la trace complète de l'erreur dans la console Flask
        flash(f'Erreur inattendue ({type(e).__name__}) lors de la recherche. Consultez les logs du serveur pour plus de détails.', 'error')
        return redirect(url_for('search_interface'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 