import os
from ultralytics import YOLO
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import platform

# ✅ 그래프 클래스 이름만(그래프용)
class_names = {
    0: '성장 전',
    1: '성장 중',
    2: '성장 완료'
}

# ✅ 경로 설정
model_path = r"C:\project\pycham\yolo\train\weights\best.pt"
image_dir = r"C:\project\pycham\yolo\images"
output_dir = r"C:\project\pycham\yolo\runs\predict"
os.makedirs(output_dir, exist_ok=True)

# ✅ 한글폰트(윈도우) - 숫자만 쓸 땐 기본폰트여도 무방하지만 호환 위해 유지
font_path = r"C:\Windows\Fonts\malgun.ttf"
font = ImageFont.truetype(font_path, 28)

# ✅ 그래프 한글 폰트
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# ✅ 모델 로드
model = YOLO(model_path)

# ✅ 이미지 리스트
image_exts = ['.jpg', '.jpeg', '.png', '.bmp']
image_list = [f for f in os.listdir(image_dir) if os.path.splitext(f)[1].lower() in image_exts]

class_confidence = defaultdict(list)

for image_name in image_list:
    image_path = os.path.join(image_dir, image_name)
    results = model.predict(source=image_path, save=False)

    if len(results[0].boxes) == 0:
        continue

    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    used_y = []

    for box in results[0].boxes:
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # YOLO 형식: 클래스ID,신뢰도%
        text = f"{cls_id},{int(conf * 100)}%"
        text_x = x1
        text_y = y1 - 32 if y1 - 32 > 0 and (y1 - 32) not in used_y else y1 + 3
        used_y.append(text_y)

        # 텍스트 박스 크기 구하기
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.rectangle([text_x, text_y, text_x + text_w, text_y + text_h], fill="blue")
        draw.text((text_x, text_y), text, font=font, fill="white")

        # 박스 그리기
        draw.rectangle([x1, y1, x2, y2], outline="blue", width=3)

        # 그래프용
        class_confidence[cls_id].append(conf)

    result_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    out_name = os.path.splitext(image_name)[0] + '_result.jpg'
    out_path = os.path.join(output_dir, out_name)
    cv2.imwrite(out_path, result_bgr)
    print(f"✅ {out_name} 저장")

# ✅ 클래스별 평균 신뢰도(%) 계산
mean_conf = {}
for k, v in class_confidence.items():
    if v:
        mean_conf[k] = np.mean(v) * 100
    else:
        mean_conf[k] = 0

# ✅ 그래프 x축 라벨에 퍼센트 추가 (한글 포함, 그래프에만 사용)
x_labels = []
for k in range(3):
    avg = mean_conf.get(k, 0)
    x_labels.append(f"{k}({avg:.2f}%)")

plt.figure(figsize=(8, 6))
plt.bar(x_labels, [mean_conf.get(k, 0) for k in range(3)])
plt.ylabel("평균 신뢰도 (%)")
plt.xlabel("클래스")
plt.ylim(0, 100)
plt.title("클래스별 평균 신뢰도 (%)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "overall_confidence_plot.jpg"))
plt.close()

print("✅ 그래프 저장 완료!")
