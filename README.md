# Mentor report integration demo

Bộ demo phần tích hợp của đề tài **Tự động soạn báo cáo trước phiên mentor**.
Người nhận có thể test ngay bằng dữ liệu giả lập, không cần tài khoản CVAT hoặc token.
Repo này dùng để thử nghiệm/bàn giao; chưa thay thế repo chung và chưa tự động
soạn đầy đủ điểm QA hoặc đo thời gian nộp báo cáo.

## 1. Chạy demo offline trước

Mở terminal tại thư mục repo, dùng Python 3.10+:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ingestion.txt
.\.venv\Scripts\python.exe demo.py
```

Không cần activate venv hoặc tạo `.env` cho demo offline. `demo.py` không gọi API,
copy fixtures vào thư mục output mới rồi tạo báo cáo. Xem đường dẫn `Report:`.
Dataset sample_data hoàn toàn giả lập: task 1001 có hai annotation jobs, một
completed và một in progress; một ground-truth job; shapes và tracks; một ca khó,
một câu hỏi chung. Không chứa dữ liệu tài khoản thật của Duy.

Kết quả mong đợi: báo cáo bốn mục, tiến độ **1/2 annotation jobs = 50% theo job**,
3 shapes, 1 track, 1 tag, 2 bản ghi shape trong track; ca khó #2 và câu hỏi #3.
Điểm chấm để trống có lý do. Issue thử #1 và issue task khác #4 bị loại.
Các URL example.com chỉ minh họa, không trỏ tới task thật.

`sample_output/` có bản xuất mẫu để đối chiếu. Mỗi lần chạy chỉ tạo file trong
`data/` đã gitignore; không sửa fixtures, nên các thành viên chạy độc lập.

## 2. Thử API thật khi đã hiểu output

```powershell
Copy-Item .env.example .env
```

Chỉ copy nếu chưa có `.env`. Điền CVAT_TOKEN của chính người chạy, task có quyền
đọc, CVAT_ORG (trống cho workspace cá nhân), và repo GitHub muốn lấy.
Save annotation trên CVAT trước khi chạy. Repo public không cần GitHub token;
repo private cần quyền đọc. Không gửi token hoặc commit `.env`.

```powershell
.\.venv\Scripts\python.exe src/sync.py --session "Phiên mentor thử"
```

Script chỉ đọc, không sửa CVAT/GitHub. Mỗi lần lưu vào data/raw/<UTC timestamp>.
Kiểm tra manifest sources và annotations failed_jobs. Exit code 1 báo lỗi nguồn,
annotations hoặc liên kết; output có thể chỉ đầy đủ một phần.

## 3. Người làm tiếp nhận gì?

| File output | Vai trò |
|---|---|
| report_data.json | Đầu vào chính cho xử lý/BI/soạn báo cáo |
| manifest.json | Kiểm tra nguồn, phạm vi, thời điểm và lỗi |
| MENTOR_REPORT_DRAFT.md | Nhóm trưởng rà soát/chỉnh trước phiên mentor |
| cvat.json, github.json, links.json | Đối chiếu raw và kết quả xác minh liên kết |

Đọc [DATA_CONTRACT.md](docs/DATA_CONTRACT.md) để hiểu trường dữ liệu và
[NEXT_STEPS.md](docs/NEXT_STEPS.md) để biết phần cần tiếp tục.

## 4. Code nằm ở đâu?

`collect.py` gọi API; `verify_link.py` tách/xác minh tham chiếu;
`report.py` chuẩn hóa và render Markdown; `sync.py` điều phối toàn bộ.
Tên sync hiện nghĩa là gom dữ liệu local, không phải đồng bộ hai chiều.
`tracker-templates/` là file mẫu cho repo tracker riêng, không tự đăng lên GitHub.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Không cần token cho tests. Test mock không chứng minh quyền hoặc schema của task thật.

## 5. Giới hạn cần nhớ

- `null` không phải 0; verified chỉ xác minh quan hệ task/job, không phải chất lượng.
- Số shape/track không phải frame hoàn thành; chưa nội suy tracks.
- Điểm chấm và % frame hoàn thành chưa triển khai.
- Chưa tự chạy lịch thứ 5/Chủ nhật, ghi giờ nộp hoặc đo thời gian soạn trước/sau.
- Hiện chạy một task; chưa gom nhiều task thành batch hay tính thay đổi giữa kỳ.
- GitHub ca khó/câu hỏi dùng issue open có label ca-kho/mentor-question.
- Payload ảnh không tải; comments lấy raw nhưng chưa tổng hợp vào báo cáo.

## 6. Bàn giao về repo chung sau khi nhóm thử

Nhóm thử offline, sau đó API thật nếu cần và ghi lại lỗi/nhu cầu thêm trường.
Thống nhất DATA_CONTRACT và NEXT_STEPS trước khi đưa code qua một nhánh/PR của
repo chung. Repo demo hiện là bản copy code tại thời điểm bàn giao; cần đồng bộ
có chủ đích khi sửa, không duy trì hai bản code âm thầm khác nhau.
