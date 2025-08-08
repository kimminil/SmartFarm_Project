from ultralytics import YOLO

def resume_training():
    """
    중단된 YOLOv8n 훈련을 마지막 체크포인트부터 재개합니다.
    """
    try:
        # --- 사용자 설정 ---
        last_weights_path = 'C:/project/pycham/yolo/runs/detect/train/weights/last.pt'  # 마지막 저장된 가중치 파일 경로
        data_config_path = 'C:/project/pycham/yolo/smartfarm.v6-test1.yolov8/data.yaml'  # data.yaml 경로
        total_epochs = 100   # 전체 에포크 수
        batch_size = 4       # CPU 환경에서는 너무 크게 하면 속도가 느릴 수 있음
        num_workers = 4      # 또는 8 (CPU 코어와 메모리 상황에 맞게 조정)
        # --- 설정 끝 ---

        # 1. 마지막 가중치로 모델 초기화
        model = YOLO(last_weights_path)
        print(f"'{last_weights_path}' 에서 훈련을 재개합니다.")

        # 2. 훈련 재개 (resume=True, device='cpu', workers, batch 등 포함)
        results = model.train(
            resume=True,
            data=data_config_path,
            epochs=total_epochs,
            imgsz=640,
            batch=batch_size,
            workers=num_workers,
            device='cpu',       # GPU를 쓰지 않고 CPU만 사용할 때 명시 (GPU 환경이면 생략 가능)
        )

        print(f"훈련이 성공적으로 완료되었습니다.")
        print(f"결과는 다음 경로에 저장되었습니다: {results.save_dir}")

    except FileNotFoundError:
        print(f"[오류] 가중치 파일을 찾을 수 없습니다: {last_weights_path}")
        print("파일 경로가 올바른지 다시 확인해주세요.")
    except Exception as e:
        print(f"훈련 중 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    resume_training()
