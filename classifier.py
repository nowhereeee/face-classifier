import os
import numpy as np
import cv2
from deepface import DeepFace

MODEL_NAME = "ArcFace"
DETECTOR = "retinaface"


def load_image_bgr(path):
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 읽을 수 없습니다")
    return img


def get_embedding(img_bgr):
    """BGR numpy 배열에서 얼굴 임베딩 추출"""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    result = DeepFace.represent(
        img_path=img_rgb,
        model_name=MODEL_NAME,
        detector_backend=DETECTOR,
        enforce_detection=True,
    )
    if not result:
        return None
    return np.array(result[0]["embedding"])


def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_encodings(children):
    encodings = {}
    errors = {}

    for child in children:
        name = child["name"]
        enc_list = []
        fail_reasons = []

        for p in child["photos"]:
            fname = os.path.basename(p)
            if not os.path.exists(p):
                fail_reasons.append(f"{fname}: 파일 없음")
                continue
            if os.path.getsize(p) == 0:
                fail_reasons.append(f"{fname}: 빈 파일")
                continue
            try:
                img = load_image_bgr(p)
                emb = get_embedding(img)
                if emb is not None:
                    enc_list.append(emb)
                else:
                    fail_reasons.append(f"{fname}: 얼굴 미검출")
            except Exception as e:
                fail_reasons.append(f"{fname}: {e}")

        if enc_list:
            encodings[name] = enc_list
        else:
            errors[name] = fail_reasons

    return encodings, errors


def classify_photo(img_path, encodings, tolerance=0.4):
    try:
        img = load_image_bgr(img_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = DeepFace.represent(
            img_path=img_rgb,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR,
            enforce_detection=False,
        )
    except Exception:
        return []

    found = set()
    for r in results:
        emb = np.array(r["embedding"])
        for name, ref_encs in encodings.items():
            sims = [cosine_similarity(emb, ref) for ref in ref_encs]
            if max(sims) >= tolerance:
                found.add(name)
    return list(found)
