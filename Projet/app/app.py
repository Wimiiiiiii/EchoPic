from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import numpy as np
import os
import matplotlib.pyplot as plt
from PIL import Image
from werkzeug.utils import secure_filename
import torch
import pickle

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
db_path = 'image.orig/'
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024  # 3MB max file size
features_path = 'features/'

# Create necessary directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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
    # La méthode GET est maintenant gérée par /search_interface
    # request.method == 'POST' est donc toujours vrai ici
    top_k = int(request.form.get('top_k', 10)) # Assurez-vous que top_k est bien envoyé par le formulaire ou fournissez une valeur par défaut pertinente
    model_name = request.form.get('model', 'ResNet50')


    if 'image' not in request.files:
        flash('Aucun champ de fichier image dans la requête.', 'error')
        return redirect(url_for('search_interface'))

    file = request.files['image']

    if not file or file.filename == '':
        flash('Aucun fichier image sélectionné.', 'error')
        return redirect(url_for('search_interface'))

    filename_secure = secure_filename(file.filename)
    # Utiliser le nom du fichier uploadé (sans extension) comme query_name pour getkVoisins
    query_name_for_logic = os.path.splitext(filename_secure)[0]

    try:
        features_file_path = os.path.join(features_path, model_name + '.pkl')
        if not os.path.exists(features_file_path):
            flash(f"Le fichier de caractéristiques pour le modèle {model_name} est introuvable.", 'error')
            return redirect(url_for('search_interface'))
            
        with open(features_file_path, 'rb') as f:
            loaded_features = pickle.load(f)

        # Sauvegarder le fichier téléversé pour pouvoir l'afficher et potentiellement pour l'extraction de features si nécessaire
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_secure)
        file.save(filepath)
        print(loaded_features)
        # Recherche d'images similaires
        # getkVoisins attend que query_name_for_logic soit une clé dans loaded_features
        # Si l'image uploadée n'est pas dans le dataset précalculé, cela lèvera une ValueError ci-dessous.
        similar_items = getkVoisins(loaded_features, query_name_for_logic, top_k)
        
        # `similar_items` est maintenant une liste de (nom_fichier_sans_ext, distance)
        # Préparer la liste des noms de fichiers proches pour Compute_RP
        similar_filenames_for_rp = [item[0] + '.jpg' for item in similar_items] # Assumant .jpg, à adapter si besoin

        # Calcul de la courbe RP
        # nom_image_requete pour Compute_RP est le nom de base du fichier uploadé
        rp_file = Compute_RP(top_k, filename_secure, similar_filenames_for_rp)
        
        # Générer l'image de la courbe RP
        rp_image_path = Display_RP(rp_file, model_name)
        
        # Préparation des résultats pour l'affichage
        results = []
        for img_name_no_ext, distance in similar_items:
            score = 1.0 / (1.0 + distance) if distance is not None else 0 # Calcul du score, gère distance=None
            results.append({
                'path': os.path.join(db_path, img_name_no_ext + '.jpg'), # Assurez-vous que LOAD_FOLDER pointe vers les images du dataset
                'score': score
            })

        return render_template('results.html', 
                             query_image=os.path.join(app.config['UPLOAD_FOLDER'], filename_secure), # Chemin relatif pour l'affichage
                             results=results,
                             model_name=model_name,
                             top_k=top_k,
                             rp_image=rp_image_path)

    except ValueError as ve: # Erreur spécifique si query_name_for_logic n'est pas dans loaded_features
        flash(f"Erreur: L'image '{query_name_for_logic}' (ou ses caractéristiques) ne fait pas partie du jeu de données pré-calculé pour le modèle {model_name}. Détail: {str(ve)}", 'warning')
        return redirect(url_for('search_interface'))
    except Exception as e:
        flash(f'Erreur lors de la recherche: {str(e)}', 'error')
        return redirect(url_for('search_interface')) # Rediriger vers search_interface en cas d'erreur générale

    # Ce return ne devrait pas être atteint si tout est logique au-dessus
    return redirect(url_for('search_interface'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 