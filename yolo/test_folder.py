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
model_path = r"C:\project\pycham\yolo\runs\detect\8n\train\weights\best.pt"
image_dir = r"C:\project\pycham\yolo\images"
output_dir = r"/runs/predict(8n-train-best.pt)"
os.makedirs(output_dir, exist_ok=True)

# ✅ 한글 폰트 설정 (Windows)
font_path = r"C:\Windows\Fonts\malgun.ttf"
font = ImageFont.truetype(font_path, 32)

# ✅ matplotlib 한글 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ✅ 신뢰도 저장용
class_confidence = defaultdict(list)

# ✅ 이미지 전체 예측
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

    # ✅ 바운딩 박스 및 한글 텍스트 그리기 (겹침 방지)
    for i, box in enumerate(boxes):
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # ✅ 신뢰도 저장
        class_confidence[cls_id].append(conf)

        # ✅ 라벨 텍스트
        label = class_names.get(cls_id, f"클래스 {cls_id}")
        text = f"클래스: {label}, 신뢰도: {int(conf * 100)}%"

        # ✅ 텍스트 위치(박스 위쪽, 겹침 방지)
        text_bbox = font.getbbox(text)
        text_height = text_bbox[3] - text_bbox[1]
        text_y = max(y1 - (text_height + 5), 0) + i * (text_height + 5)

        # ✅ 텍스트 및 박스
        draw.rectangle([x1, y1, x2, y2], outline="blue", width=3)
        draw.text((x1, text_y), text, font=font, fill=(255, 0, 0))

    # ✅ 결과 저장
    result_img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    save_path = os.path.join(output_dir, file_name.replace('.jpg', '_result.jpg'))
    cv2.imwrite(save_path, result_img)

# ✅ 클래스별 평균 신뢰도(%) 계산
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

# ✅ 그래프 그리기
plt.figure(figsize=(8, 6))
plt.bar(x_labels, [mean_conf.get(k, 0) for k in range(3)])
plt.ylabel("평균 신뢰도 (%)")
plt.xlabel("클래스")
plt.ylim(0, 100)
plt.title("클래스별 평균 신뢰도 (%)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "overall_confidence_plot.jpg"))
plt.close()

print("✅ 모든 이미지 처리 및 그래프 저장이 완료되었습니다.")
