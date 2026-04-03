import face_recognition
import os
import numpy as np
import cv2


def load_image_as_rgb(path):
    # cv2.imread는 한글 경로 못 읽으므로 바이트로 먼저 읽기
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 읽을 수 없습니다")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def load_encodings(children):
    """기준사진 목록에서 얼굴 인코딩 추출"""
    encodings = {}
    errors = {}
    for child in children:
        name = child['name']
        photos = child['photos']
        enc_list = []
        fail_reasons = []
        for p in photos:
            fname = os.path.basename(p)
            if not os.path.exists(p):
                fail_reasons.append(f"{fname}: 파일 없음")
                continue
            fsize = os.path.getsize(p)
            if fsize == 0:
                fail_reasons.append(f"{fname}: 빈 파일 (0bytes)")
                continue
            try:
                img = load_image_as_rgb(p)
            except Exception as e:
                fail_reasons.append(f"{fname}: 이미지 로드 실패 - {e} ({fsize}bytes)")
                continue
            try:
                encs = face_recognition.face_encodings(img)
                if encs:
                    enc_list.append(encs[0])
                else:
                    fail_reasons.append(f"{fname}: 얼굴 미검출 (shape={img.shape}, dtype={img.dtype})")
            except Exception as e:
                fail_reasons.append(f"{fname}: {e} (shape={img.shape}, dtype={img.dtype}, contiguous={img.flags['C_CONTIGUOUS']})")
        if enc_list:
            encodings[name] = enc_list
        else:
            errors[name] = fail_reasons
    return encodings, errors


def classify_photo(img_path, encodings, tolerance=0.45):
    """사진에서 인식된 아이 이름 목록 반환"""
    img = load_image_as_rgb(img_path)
    locs = face_recognition.face_locations(img)
    encs = face_recognition.face_encodings(img, locs)

    found = set()
    for fe in encs:
        for name, ref_encs in encodings.items():
            matches = face_recognition.compare_faces(ref_encs, fe, tolerance=tolerance)
            if any(matches):
                found.add(name)
    return list(found)