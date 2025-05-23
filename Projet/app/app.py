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
app.config['LOAD_FOLDER'] = 'image.orig/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
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

    return distances_name[:k][0]  # Retourner les `k` plus proches voisins



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

@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        top_k = int(request.form.get('top_k', 10))
        model_name = request.form.get('model', 'ResNet50')
        query_name = request.form.get('query_name', '')

        file = request.files[f'{query_name}']
        if file.filename == '':
            flash('Aucun fichier sélectionné', 'error')
            return redirect(url_for('index'))

        try:
            with open(features_path + model_name + '.pkl', 'rb') as f:
                loaded_features = pickle.load(f)

            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Recherche d'images similaires
                similar_images = getkVoisins(loaded_features, query_name, top_k)
                
                # Calcul de la courbe RP
                rp_file = Compute_RP(top_k, query_name, similar_images)
                
                # Générer l'image de la courbe RP
                rp_image_path = Display_RP(rp_file, model_name)
                
                # Préparation des résultats pour l'affichage
                results = []
                for img_name, distance in similar_images:
                    score = 1 / (1 + distance)  # Conversion de la distance en score (0-1)
                    results.append({
                        'path': img_name + '.jpg',
                        'score': score
                    })

                return render_template('results.html', 
                                     query_image=filename,
                                     results=results,
                                     model_name=model_name,
                                     top_k=top_k,
                                     rp_image=rp_image_path)

        except Exception as e:
            flash(f'Erreur lors de la recherche: {str(e)}', 'error')
            return redirect(url_for('index'))

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 