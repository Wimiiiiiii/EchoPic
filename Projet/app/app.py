from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import numpy as np
import os
import matplotlib.pyplot as plt
from PIL import Image
from werkzeug.utils import secure_filename
import torch


app = Flask(__name__)
app.config['LOAD_FOLDER'] = 'image.orig/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
features_path = 'features/'

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
    distances = []

    for name, feature_vector in features_dict.items():
        dist = euclidean_distance(query_feature, feature_vector)  # Distance euclidienne
        distances.append((name, dist))  # Stocker le nom et la distance

    # Trier par distance croissante et récupérer les `k` plus proches
    distances.sort(key=lambda x: x[1])

    return distances[:k]  # Retourner les `k` plus proches voisins

def recherche(query_name, features_dict, image_path, top):
    """
    Recherche les `top` images les plus similaires à une image requête.

    - `query_name` : Nom du fichier image requête (sans extension).
    - `features_dict` : Dictionnaire {nom_fichier: feature_vector}.
    - `image_dict` : Dictionnaire {nom_fichier: chemin_image}.
    - `top` : Nombre d'images similaires à retourner.

    Retourne :
    - `nom_image_requete` : Nom de l’image requête.
    - `nom_images_proches` : Liste des images similaires.
    """
    voisins = getkVoisins(features_dict, query_name, top)

    # Affichage de l'image requête
    plt.figure(figsize=(5, 5))
    plt.imshow(Image.open(image_path+"/"+query_name+".jpg"), cmap='gray', interpolation='none')
    plt.title("Image requête")

    print(f"Image requête : {query_name}")

    # Affichage des images proches
    plt.figure(figsize=(25, 25))
    plt.subplots_adjust(hspace=0.2, wspace=0.2)
    for j in range(min(top, len(voisins))):
        plt.subplot(top // 4, top // 5, j + 1)
        plt.imshow(Image.open(image_path+"/"+voisins[j][0]+".jpg"), cmap='gray', interpolation='none')
        plt.title(f"Image proche n°{j}")

    return query_name, voisins

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
    Affiche la courbe Rappel-Précision (RP) à partir d'un fichier texte contenant les valeurs.

    - `fichier` : Chemin du fichier `.txt` contenant les valeurs RP.

    La courbe affiche :
    - Axe X : Rappel (Recall)
    - Axe Y : Précision (Precision)
    """

    # Charger les données depuis le fichier `.txt`
    x, y = [], []

    with open(fichier, 'r') as csvfile:
        for line in csvfile:
            values = line.strip().split()
            if len(values) == 2:  # Vérifier que la ligne contient bien 2 valeurs
                x.append(float(values[0]))  # Précision
                y.append(float(values[1]))  # Rappel

    # Convertir en tensor PyTorch (optionnel si on veut les manipuler après)
    x_tensor = torch.tensor(x)
    y_tensor = torch.tensor(y)

    # Affichage de la courbe RP
    plt.figure(figsize=(8, 6))
    plt.plot(y_tensor, x_tensor, 'C1', label=model_name)
    plt.xlabel('Rappel (Recall)')
    plt.ylabel('Précision (Precision)')
    plt.title("Courbe Rappel/Précision (RP)")
    plt.legend()
    plt.grid(True)
    plt.show()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST', 'GET'])
def search():
    top_k = request.form.get('top_k', 10)
    model_name = request.form.get('model', 'ResNet50')



    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    import pickle
    with open(features_path + model_name+'.pkl', 'rb') as f:  # 'rb' = lecture binaire
        loaded_features = pickle.load(f)


    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        #TODO: Intégrer ici le code de recherche d'images
        nom_image_requete, nom_images_proches = recherche(filename, loaded_features, app.config['LOAD_FOLDER'], top=top_k)
        
        #RP result
        rp_tensor = Compute_RP(top_k, nom_image_requete, nom_images_proches)

        Display_RP(rp_tensor, model_name)
      
        return jsonify({
            'message': 'Image uploaded successfully',
            'results': [] 
        })
    
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 