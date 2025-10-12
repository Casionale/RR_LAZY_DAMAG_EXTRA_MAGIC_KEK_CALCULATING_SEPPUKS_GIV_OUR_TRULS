import os

import cv2
import joblib
import numpy as np
from PIL import Image
from skimage.exposure import exposure
from skimage.feature import hog
from skimage import color
import sys

def extract_features(path):
    try:
        # Открываем изображение через Pillow (работает с кириллицей)
        img = Image.open(path).convert("RGB")
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        return None

    img = img.resize((64, 64))
    img = np.array(img)
    gray = color.rgb2gray(img)
    features = hog(gray, pixels_per_cell=(8, 8), cells_per_block=(2, 2), feature_vector=True)
    return features


def main():
    if len(sys.argv) < 2:
        print("Использование: python check.py путь_к_изображению")
        exit(1)
    img_path = sys.argv[1]
    features = extract_features(img_path)
    if features is None:
        exit(1)
    model = joblib.load("avatar_model.pkl")
    prob = model.predict_proba([features])[0]
    pred = model.predict([features])[0]
    print(f"Вероятность 'подходит': {prob[0]:.2f}")
    print(f"Вероятность 'не подходит': {prob[1]:.2f}")
    if pred == 0:
        print("✅ Изображение похоже на шаблон (good)")
    else:
        print("❌ Изображение не похоже (bad)")


def extract_features(path, visualize=False):
    """Извлекает HOG-признаки (на 64x64), при необходимости возвращает визуализацию и оригинал"""
    try:
        img = Image.open(path).convert("RGB")
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        return (None, None, None) if visualize else None

    orig_size = img.size  # (width, height)
    img_resized = img.resize((64, 64))
    img_resized = np.array(img_resized)
    gray = color.rgb2gray(img_resized)

    if visualize:
        features, hog_image = hog(
            gray,
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2),
            feature_vector=True,
            visualize=True
        )
        hog_image = exposure.rescale_intensity(hog_image, in_range=(0, 10))
        return features, hog_image, np.array(img), orig_size
    else:
        features = hog(gray, pixels_per_cell=(8, 8), cells_per_block=(2, 2), feature_vector=True)
        return features


def checking_avatars_by_model(filepath, save_dir=None, alpha=0.6, output_size=None):
    """
    Проверяет изображение моделью и сохраняет наложение HOG поверх оригинала.
    - alpha — прозрачность наложения (0..1)
    - output_size — (ширина, высота), если нужно жёстко масштабировать, напр. (150, 150)
    """
    features, hog_image, orig_img, orig_size = extract_features(filepath, visualize=True)
    if features is None:
        return None, None, None

    model = joblib.load("avatar_model.pkl")
    prob = model.predict_proba([features])[0]
    pred = model.predict([features])[0]
    similarity = prob[0] * 100  # вероятность класса "good"

    saved_path = None
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(filepath)
        save_name = f"{similarity:.2f}_{filename}"
        save_path = os.path.join(save_dir, save_name)

        # Подготовка изображений
        hog_norm = (hog_image - hog_image.min()) / (hog_image.max() - hog_image.min())
        hog_color = cv2.applyColorMap((hog_norm * 255).astype(np.uint8), cv2.COLORMAP_JET)

        # Масштабируем визуализацию до оригинала
        orig_h, orig_w = orig_img.shape[:2]
        hog_resized = cv2.resize(hog_color, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

        # Наложение
        orig_bgr = cv2.cvtColor(orig_img, cv2.COLOR_RGB2BGR)
        overlay = cv2.addWeighted(orig_bgr, 1 - alpha, hog_resized, alpha, 0)

        # Добавляем подпись
        text = f"{similarity:.2f}% similarity"
        cv2.putText(overlay, text, (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Масштабирование вывода (если указано)
        if output_size:
            overlay = cv2.resize(overlay, output_size, interpolation=cv2.INTER_AREA)

        cv2.imwrite(save_path, overlay)
        saved_path = save_path

    return prob, pred, saved_path


if __name__ == "__main__":
    main()

