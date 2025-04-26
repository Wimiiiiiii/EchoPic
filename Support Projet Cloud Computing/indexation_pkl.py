# Fonction d'indexation
def indexation(output_file, model, preprocess_input, folder_model):
    features = []
    for j in os.listdir(files):
        data = os.path.join(files, j)
        if not data.endswith(".jpg"):
            continue
        file_name = os.path.basename(data)
        image = load_img(data, target_size=(224, 224))
        image = img_to_array(image)
        image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
        image = preprocess_input(image)
        feature = model.predict(image)
        feature = np.array(feature[0])
        features.append((data, feature))
    with open(output_file, "wb") as output:
        pickle.dump(features, output)
# Chemin vers le dossier des images
files = './image.orig/'
# Génération des descripteurs
indexation("VGG16.pkl", model1, tf.keras.applications.vgg16.preprocess_input)