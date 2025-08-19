import cv2

def main():
    cap = cv2.VideoCapture(0)  # 기본 카메라 index
    if not cap.isOpened():
        print("카메라를 열 수 없습니다. 인덱스(0) 외에 다른 카메라를 시도해 보세요.")
        # 간단한 대안 시도
        for idx in range(1, 5):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                print(f"카메라 {idx} 열림!")
                break
        else:
            print("다양한 카메라를 시도해도 열리지 않습니다.")
            return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다. 카메라 상태를 확인하고 다시 시도하세요.")
            break

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()