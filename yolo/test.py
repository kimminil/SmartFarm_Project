import os
import matplotlib.pyplot as plt
import platform
from ultralytics import YOLO
from pathlib import Path

# ✅ 한글 폰트 설정
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# ✅ 경로 설정
model_path = r"C:\project\pycham\yolo\runs\detect\8n\train\weights\best.pt"
data_yaml = r"C:\project\pycham\yolo\smartfarm.v6-test1.yolov8\data.yaml"

# ✅ 모델 로드
try:
    model = YOLO(model_path)
    print("✅ 모델 로딩 성공")
except Exception as e:
    print(f"❌ 모델 로딩 실패: {e}")
    exit()

# ✅ 검증 실행
print("\n📊 검증 시작...")
val_results = model.val(data=data_yaml, split='val', save_json=True)
metrics_dict = val_results.results_dict  # 괄호 ❌

# ✅ 가장 최근 생성된 val 폴더 자동 탐색
val_base = Path(r"C:\project\pycham\yolo\runs\detect")
val_folders = sorted(val_base.glob("val*"), key=os.path.getmtime, reverse=True)
output_folder = str(val_folders[0]) if val_folders else str(val_base / "val")
print(f"📁 val 폴더: {output_folder}")

# ✅ Precision, Recall 가져오기
precision = metrics_dict['metrics/precision(B)']
recall = metrics_dict['metrics/recall(B)']

# ✅ F1-score 계산
if precision + recall > 0:
    f1_score = 2 * (precision * recall) / (precision + recall)
else:
    f1_score = 0.0

# ✅ 검증 지표 출력
print("\n--- 검증 지표 ---")
print(f"mAP@0.5     : {metrics_dict['metrics/mAP50(B)']:.3f}")
print(f"mAP@0.5:0.95: {metrics_dict['metrics/mAP50-95(B)']:.3f}")
print(f"Precision   : {precision:.3f}")
print(f"Recall      : {recall:.3f}")
print(f"F1-score    : {f1_score:.3f} (직접 계산)")

# ✅ 📈 곡선 그래프 저장 (val 폴더로)
metrics_names = ["mAP@0.5", "mAP@0.5:0.95", "Precision", "Recall", "F1-score"]
metrics_values = [
    metrics_dict['metrics/mAP50(B)'],
    metrics_dict['metrics/mAP50-95(B)'],
    precision,
    recall,
    f1_score
]

plt.figure(figsize=(8, 5))
plt.plot(metrics_names, metrics_values, marker='o', color='blue', linestyle='-', linewidth=2)
for i, value in enumerate(metrics_values):
    plt.text(i, value + 0.02, f"{value:.3f}", ha='center')

plt.title("YOLOv8 검증 지표 곡선 그래프")
plt.ylabel("값")
plt.ylim(0, 1.1)
plt.grid(True)
plt.tight_layout()

line_chart_path = os.path.join(output_folder, "val_metrics_line.png")
plt.savefig(line_chart_path)
plt.close()
print(f"📈 곡선 그래프 저장됨: {line_chart_path}")

print("\n✅ 검증 완료")
