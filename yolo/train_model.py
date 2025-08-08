from ultralytics import YOLO

# 1. 사전 훈련된 YOLOv8n 모델을 불러옵니다.
model = YOLO('yolov8s.pt')

# 2. 모델을 훈련시킵니다.
results = model.train(
    data='C:/project/pycham/yolo/smartfarm.v6-test1.yolov8/data.yaml',  # data.yaml 경로
    epochs=100,        # 전체 에포크 수
    imgsz=640,         # 입력 이미지 크기
    batch=4,           # 배치 크기 (CPU 환경에서는 4~8 추천)
    workers=4,         # 데이터 로딩용 워커 수 (CPU 코어와 메모리 상황에 맞게 조정)
)

print(f"훈련이 완료되었습니다. 결과는 다음 경로에 저장되었습니다: {results.save_dir}")
