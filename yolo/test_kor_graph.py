import os
from ultralytics import YOLO
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ✅ 클래스 이름(한글)
class_names = {
    0: '성장 전',
    1: '성장 중',
    2: '성장 완료'
}

# ✅ 경로 설정
model_path = r"C:\project\pycham\yolo\runs\detect\8n\train1\weights\best.pt"
image_dir = r"C:\project\pycham\yolo\images"
output_dir = r"C:\project\pycham\yolo\runs\detect\predict"
os.makedirs(output_dir, exist_ok=True)

# ✅ 한글 폰트 설정 (Windows)
font_path = r"C:\Windows\Fonts\malgun.ttf"
font = ImageFont.truetype(font_path, 32)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ✅ 신뢰도 저장용
class_confidence = defaultdict(list)

# ✅ YOLO 모델 로드
model = YOLO(model_path)
image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

for file_name in image_files:
    img_path = os.path.join(image_dir, file_name)
    results = model.predict(source=img_path, save=False)
    boxes = results[0].boxes

    # OpenCV → PIL 변환
    cv_img = cv2.imread(img_path)
    img_pil = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    for box in boxes:
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # ✅ YOLO 스타일 라벨 (예: 성장 전, 78%)
        label = class_names.get(cls_id, f"클래스 {cls_id}")
        text = f"{label}, {int(conf*100)}%"

        # ✅ 신뢰도 누적
        class_confidence[cls_id].append(conf)

        # ✅ 텍스트 배경(가독성 향상)
        text_bbox = font.getbbox(text)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        y_text = max(0, y1 - text_h - 5)
        text_bg = [x1, y_text, x1 + text_w, y_text + text_h]
        draw.rectangle(text_bg, fill=(0, 0, 255, 128))
        draw.text((x1, y_text), text, font=font, fill=(255,255,255))

        # ✅ 박스
        draw.rectangle([x1, y1, x2, y2], outline="blue", width=3)

    # 결과 저장
    result_img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    save_path = os.path.join(output_dir, file_name.replace('.jpg', '_result.jpg'))
    cv2.imwrite(save_path, result_img)

# ✅ 클래스별 평균 신뢰도(%) 계산 및 그래프 저장
mean_conf = {}
for k, v in class_confidence.items():
    if v:
        mean_conf[k] = np.mean(v) * 100
    else:
        mean_conf[k] = 0

# ✅ 그래프 x축 라벨에 퍼센트 추가
x_labels = []
for k in range(3):
    name = class_names.get(k, f"클래스 {k}")
    avg = mean_conf.get(k, 0)
    x_labels.append(f"{name}({avg:.2f}%)")

plt.figure(figsize=(8, 6))
plt.bar(x_labels, [mean_conf.get(k, 0) for k in range(3)])
plt.ylabel("평균 신뢰도 (%)")
plt.xlabel("클래스")
plt.ylim(0, 100)
plt.title("클래스별 평균 신뢰도 (%)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "overall_confidence_plot.jpg"))
plt.close()

print("✅ YOLO 스타일 라벨 이미지 & 신뢰도 그래프 저장 완료!")
