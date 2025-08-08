import os
import cv2
from ultralytics import YOLO

# 경로 설정
model_path = r'C:\project\pycham\yolo\runs\detect\8n\train\weights\best.pt'
image_folder = r'C:\project\pycham\yolo\images'
output_folder = r'C:\project\pycham\yolo\runs\detect\predict'
os.makedirs(output_folder, exist_ok=True)

# 모델 로드
try:
    model = YOLO(model_path)
    print("✅ 모델 로딩 성공")
except Exception as e:
    print(f"❌ 모델 로딩 실패: {e}")
    exit()

# 이미지 파일 목록 가져오기
img_exts = ['.jpg', '.jpeg', '.png', '.bmp']
image_files = [f for f in os.listdir(image_folder) if os.path.splitext(f)[1].lower() in img_exts]

# 예측 실행
print("\n--- 예측 시작 ---")
for i, filename in enumerate(image_files):
    img_path = os.path.join(image_folder, filename)

    try:
        results = model(img_path, conf=0.5, iou=0.4)
    except Exception as e:
        print(f"❌ 예측 실패 ({filename}): {e}")
        continue

    r = results[0]
    print(f"\n[이미지 {i + 1}] 처리 중: {img_path}")

    if not r.boxes:
        print(" -> 탐지된 객체 없음")
        continue

    # 결과 이미지 저장
    im_array = r.plot()
    save_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_result.jpg")
    cv2.imwrite(save_path, im_array)
    print(f" -> 저장됨: {save_path}")

    # 객체 정보 출력
    print(" -> 탐지된 객체:")
    for box in r.boxes:
        class_name = model.names[int(box.cls)]
        confidence = float(box.conf)
        print(f"    - {class_name}, 신뢰도: {confidence:.2f}")

print("\n✅ 모든 이미지 예측 완료")
