import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img, save_img

# 1. 설정
input_folder = 'images'      # 원본 10장 폴더명
output_folder = 'augmented_images' # 증강 150장 저장 폴더명
os.makedirs(output_folder, exist_ok=True)
target_count = 150                 # 최종 증강 목표 개수

# 2. 증강기 세팅 (확대/축소, 밝기 포함)
datagen = ImageDataGenerator(
    zoom_range=0.3,                # 확대/축소 (30% 범위)
    brightness_range=[0.5, 1.5],   # 밝기 조절
    fill_mode='nearest'            # 빈 공간 채움
)

# 3. 원본 이미지 리스트 불러오기
image_files = [f for f in os.listdir(input_folder)
               if f.lower().endswith(('.jpg', '.jpeg', '.png','.webp'))]

if len(image_files) != 10:
    print("input_images 폴더에 이미지가 10장이어야 합니다.")
    exit()

img_shape = cv2.imread(os.path.join(input_folder, image_files[0])).shape

count = 0
aug_idx = 0

print("데이터 증강 중...")
while count < target_count:
    for fname in image_files:
        img_path = os.path.join(input_folder, fname)
        img = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)  # BGR -> RGB 변환

        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)

        # 증강 생성기에서 next()로 한 장씩 추출
        gen = datagen.flow(x, batch_size=1)
        for _ in range(2):  # 각 원본 당 2장씩 증강해서 20*2=20, while 반복으로 150장까지 반복됨
            batch = next(gen)
            aug_img = batch[0].astype(np.uint8)
            save_name = f"{os.path.splitext(fname)[0]}_aug_{aug_idx:03d}.jpg"
            save_path = os.path.join(output_folder, save_name)
            save_img(save_path, aug_img)
            count += 1
            aug_idx += 1
            if count >= target_count:
                break
        if count >= target_count:
            break

print(f"완료! 증강된 이미지: {count}장")