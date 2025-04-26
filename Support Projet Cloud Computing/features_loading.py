# Dictionnaire reprenant les noms et chemins des descripteurs
descriptors_data = {
    'vgg16': 'static/features/VGG16.pkl',
    'resnet50': 'static/features/Resnet50.pkl',
    'mobilenet':'static/features/MobileNet.pkl'
}

# la fonction "features_data" permet de charger les descripteurs à partir du chemin de descripteurs en format pkl. 
features_data = {key: pickle.load(open(path, 'rb')) for key, path in descriptors_data.items()}

# Exemple de lecture des descripteurs provenant de l'architecture VGG16
features=features_data['vgg16']

# Il faudra ensuite itérer sur le tableau features pour appliquer la recherche