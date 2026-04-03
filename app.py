import os
import sys
import json
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from classifier import load_encodings, classify_photo

if getattr(sys, 'frozen', False):
    # exe 실행 시: 사용자 데이터는 exe 옆, 템플릿은 PyInstaller 추출 폴더
    DATA_DIR = os.path.dirname(sys.executable)
    TEMPLATE_DIR = os.path.join(getattr(sys, '_MEIPASS', DATA_DIR), 'templates')
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(DATA_DIR, 'templates')

BASE_DIR = DATA_DIR

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'data', 'ref_photos')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
CONFIG_FILE = os.path.join(DATA_DIR, 'data', 'config.json')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'data'), exist_ok=True)

progress_state = {"total": 0, "done": 0, "log": [], "running": False}


# ── 설정 로드/저장 ──────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"children": [], "tolerance": 0.4}

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── 라우트 ─────────────────────────────────────────────────
@app.route('/')
def index():
    cfg = load_config()
    return render_template('index.html', children=cfg['children'], tolerance=cfg['tolerance'])


@app.route('/add_child', methods=['POST'])
def add_child():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({"ok": False, "msg": "이름을 입력하세요."})

    files = request.files.getlist('photos')
    if not files or files[0].filename == '':
        return jsonify({"ok": False, "msg": "기준사진을 선택하세요."})

    child_dir = os.path.join(app.config['UPLOAD_FOLDER'], name)
    os.makedirs(child_dir, exist_ok=True)

    saved = []
    for f in files:
        try:
            ext = os.path.splitext(f.filename)[1] or '.jpg'
            fn = str(uuid.uuid4()) + ext
            path = os.path.join(child_dir, fn)
            f.save(path)
            saved.append(path)
        except Exception as e:
            return jsonify({"ok": False, "msg": f"파일 저장 실패: {e}"})

    if not saved:
        return jsonify({"ok": False, "msg": "사진 저장에 실패했습니다."})

    cfg = load_config()
    cfg['children'] = [c for c in cfg['children'] if c['name'] != name]
    cfg['children'].append({"name": name, "photos": saved})
    save_config(cfg)

    return jsonify({"ok": True, "msg": f"'{name}' 등록 완료 ({len(saved)}장)", "count": len(saved)})


@app.route('/add_photos', methods=['POST'])
def add_photos():
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({"ok": False, "msg": "이름 없음"})

    files = request.files.getlist('photos')
    if not files or files[0].filename == '':
        return jsonify({"ok": False, "msg": "사진을 선택하세요."})

    child_dir = os.path.join(app.config['UPLOAD_FOLDER'], name)
    os.makedirs(child_dir, exist_ok=True)

    cfg = load_config()
    child = next((c for c in cfg['children'] if c['name'] == name), None)
    if not child:
        return jsonify({"ok": False, "msg": "등록되지 않은 아이입니다."})

    saved = list(child['photos'])
    for f in files:
        try:
            ext = os.path.splitext(f.filename)[1] or '.jpg'
            fn = str(uuid.uuid4()) + ext
            path = os.path.join(child_dir, fn)
            f.save(path)
            saved.append(path)
        except Exception as e:
            return jsonify({"ok": False, "msg": f"파일 저장 실패: {e}"})

    child['photos'] = saved
    save_config(cfg)
    return jsonify({"ok": True, "msg": f"{len(files)}장 추가 (총 {len(saved)}장)", "count": len(saved)})


@app.route('/remove_child', methods=['POST'])
def remove_child():
    name = request.json.get('name', '')
    cfg = load_config()
    cfg['children'] = [c for c in cfg['children'] if c['name'] != name]
    save_config(cfg)
    return jsonify({"ok": True})


@app.route('/reset_all', methods=['POST'])
def reset_all():
    cfg = load_config()
    cfg['children'] = []
    save_config(cfg)
    return jsonify({"ok": True})


@app.route('/start_classify', methods=['POST'])
def start_classify():
    global progress_state
    if progress_state['running']:
        return jsonify({"ok": False, "msg": "이미 분류 중입니다."})

    src_dir = request.json.get('src_dir', '').strip()
    tolerance = float(request.json.get('tolerance', 0.45))

    if not src_dir or not os.path.isdir(src_dir):
        return jsonify({"ok": False, "msg": "올바른 폴더 경로를 입력하세요."})

    cfg = load_config()
    cfg['tolerance'] = tolerance
    save_config(cfg)

    progress_state = {"total": 0, "done": 0, "log": [], "running": True}
    t = threading.Thread(target=run_classify, args=(src_dir, cfg['children'], tolerance), daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route('/progress')
def progress():
    return jsonify(progress_state)


def run_classify(src_dir, children, tolerance):
    global progress_state
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    def log(msg):
        progress_state['log'].append(msg)

    log("얼굴 인코딩 로딩 중...")
    encodings, errors = load_encodings(children)

    for name, reasons in errors.items():
        for r in reasons:
            log(f"⚠ [{name}] {r}")
        log(f"✖ [{name}] 기준사진에서 얼굴을 찾지 못해 분류에서 제외됩니다.")

    if not encodings:
        log("오류: 등록된 아이 중 얼굴 인코딩에 성공한 사람이 없습니다.")
        progress_state['running'] = False
        return

    log(f"{len(encodings)}명 인코딩 완료: {', '.join(encodings.keys())}")

    from pathlib import Path
    import shutil

    photos = [p for p in Path(src_dir).iterdir() if p.suffix.lower() in exts]
    if not photos:
        log("해당 폴더에 이미지 파일이 없습니다.")
        progress_state['running'] = False
        return

    progress_state['total'] = len(photos)
    log(f"총 {len(photos)}장 분류 시작...")

    unmatched = Path(src_dir) / "_미분류"
    unmatched.mkdir(exist_ok=True)
    for c in children:
        (Path(src_dir) / c['name']).mkdir(exist_ok=True)

    ok = 0
    for photo in photos:
        try:
            matched = classify_photo(str(photo), encodings, tolerance)
            if matched:
                for name in matched:
                    shutil.copy2(str(photo), str(Path(src_dir) / name / photo.name))
                log(f"✔ {photo.name} → {', '.join(matched)}")
                ok += 1
            else:
                shutil.copy2(str(photo), str(unmatched / photo.name))
                log(f"? {photo.name} → _미분류")
        except Exception as e:
            log(f"오류: {photo.name} — {e}")
        progress_state['done'] += 1

    log(f"\n완료! {ok}/{len(photos)}장 성공. 결과 폴더: {src_dir}")
    progress_state['running'] = False


@app.route('/shutdown', methods=['POST'])
def shutdown():
    os._exit(0)


if __name__ == '__main__':
    os.chdir(BASE_DIR)
    print("서버 시작: http://localhost:5000")
    app.run(debug=False, port=5000)