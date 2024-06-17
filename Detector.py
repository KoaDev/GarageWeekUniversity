import cv2
import threading
import time
import os
from roboflow import Roboflow
import supervision as sv
import matplotlib

# Utiliser l'interface TkAgg de matplotlib
matplotlib.use('TkAgg')

# Variables globales pour contrôler la capture de la caméra
capturing = False
camera_thread = None
confidence_threshold = 35  # Seuil de confiance pour les prédictions
capture_duration = 10  # Durée de la capture en secondes
image_folder = "captured_images"

# Créer le dossier pour stocker les images capturées
if not os.path.exists(image_folder):
    os.makedirs(image_folder)


def analyze_image(image_path, confidence, plot=False):
    # Initialiser le modèle Roboflow
    rf = Roboflow(api_key="y8SiQHfVupkZR4eXOBhY")
    project = rf.workspace().project("-tdf0j")
    model = project.version(1).model

    # Prédire sur une image
    result = model.predict(image_path, confidence=confidence).json()

    # Extraire les étiquettes et les détections
    labels = [item["class"] for item in result["predictions"]]
    detections = sv.Detections.from_inference(result)

    # Initialiser les annotateurs
    label_annotator = sv.LabelAnnotator()
    mask_annotator = sv.MaskAnnotator()

    # Lire l'image
    image = cv2.imread(image_path)

    # Annoter l'image avec des masques et des étiquettes
    annotated_image = mask_annotator.annotate(scene=image, detections=detections)

    # Dictionnaire pour compter les objets par étiquette
    label_counts = {}
    undesirable_count = 0
    desirable_count = 0

    # Ajouter des boîtes englobantes autour des objets détectés
    for prediction in result["predictions"]:
        x1 = int(prediction["x"] - prediction["width"] / 2)
        y1 = int(prediction["y"] - prediction["height"] / 2)
        x2 = int(prediction["x"] + prediction["width"] / 2)
        y2 = int(prediction["y"] + prediction["height"] / 2)
        label = prediction["class"]

        # Dessiner la boîte englobante
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Dessiner l'étiquette
        cv2.putText(annotated_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        # Compter les objets par étiquette
        if label in label_counts:
            label_counts[label] += 1
        else:
            label_counts[label] = 1

        # Catégoriser les objets comme désirables ou indésirables
        if label == "bottle":
            undesirable_count += 1
        else:
            desirable_count += 1

    # Calculer le taux d'objets indésirables
    total_items = undesirable_count + desirable_count
    if total_items > 0:
        undesirable_rate = (undesirable_count / total_items) * 100
    else:
        undesirable_rate = 0

    # Afficher l'image annotée si nécessaire
    if plot:
        sv.plot_image(image=annotated_image, size=(16, 16))

    # Retourner les résultats
    return undesirable_rate, desirable_count, undesirable_count


def capture_images(confidence, duration):
    global capturing
    cap = cv2.VideoCapture(0)

    start_time = time.time()
    image_count = 0

    while capturing and (time.time() - start_time < duration):
        ret, frame = cap.read()
        if ret:
            # Sauvegarder l'image capturée temporairement
            image_path = os.path.join(image_folder, f"image_{image_count}.jpg")
            cv2.imwrite(image_path, frame)
            image_count += 1

            time.sleep(1)  # Attendre 1 seconde avant de capturer la prochaine image

    cap.release()
    print("Capture terminée")


def start_capture(confidence, duration):
    global capturing, camera_thread
    capturing = True
    camera_thread = threading.Thread(target=capture_images, args=(confidence, duration))
    camera_thread.start()


def stop_capture():
    global capturing, camera_thread
    capturing = False
    if camera_thread is not None:
        camera_thread.join()
        camera_thread = None


def get_undesirable_rates(confidence):
    undesirable_rates = []
    for image_file in os.listdir(image_folder):
        image_path = os.path.join(image_folder, image_file)
        rate, _, _ = analyze_image(image_path, confidence)
        undesirable_rates.append(rate)
    return undesirable_rates


def get_average_undesirable_rate(undesirable_rates):
    if len(undesirable_rates) > 0:
        return sum(undesirable_rates) / len(undesirable_rates)
    else:
        return 0


def get_object_counts(confidence):
    object_counts = []
    for image_file in os.listdir(image_folder):
        image_path = os.path.join(image_folder, image_file)
        _, desirable_count, undesirable_count = analyze_image(image_path, confidence)
        object_counts.append((desirable_count, undesirable_count))
    return object_counts


def plot_image(image_path, confidence):
    analyze_image(image_path, confidence, plot=True)


# Démarrer la capture d'images à partir de la caméra
start_capture(confidence_threshold, capture_duration)

# Attendre la fin de la capture
time.sleep(capture_duration)
stop_capture()

# Obtenir les taux d'indésirables pour chaque image
undesirable_rates = get_undesirable_rates(confidence_threshold)
print(f"Taux d'indésirables par photo: {undesirable_rates}")

# Calculer et afficher le taux d'indésirables moyen
average_undesirable_rate = get_average_undesirable_rate(undesirable_rates)
print(f"Moyenne des taux d'indésirables: {average_undesirable_rate:.2f}%")

# Obtenir le nombre d'objets détectés par image
object_counts = get_object_counts(confidence_threshold)
print(f"Nombre d'objets détectés par image: {object_counts}")

# Afficher le plot pour une image spécifique (exemple)
# plot_image(os.path.join(image_folder, "image_0.jpg"), confidence_threshold)
