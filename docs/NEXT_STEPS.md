# Người làm tiếp bắt đầu từ đâu?

Đầu tiên chạy demo.py theo README, mở Markdown và report_data.json. Không cần
đọc lịch sử trao đổi hoặc có quyền CVAT để thử render.

| Phần | Đầu vào | Công việc tiếp theo |
|---|---|---|
| Xử lý / BI | report_data.json + DATA_CONTRACT | Thiết kế bảng, export CSV nếu cần, KPI theo quy tắc nhóm chốt |
| Báo cáo | JSON + sample_output | Hoàn thiện bố cục, tóm tắt và phần đề xuất hành động |
| QA/QC | scores đang unavailable | Chốt nguồn điểm, thang điểm, ai chấm, đối tượng và thời điểm chấm |
| DevOps | src/sync.py | Workflow có Secrets, lịch thứ 5/Chủ nhật, lưu artifact và báo lỗi |
| Nhóm trưởng | Markdown + metadata | Chốt kỳ, giờ nộp, quy trình review và dữ liệu nào được công khai |
| Đánh giá đề tài | Chưa có nhật ký soạn/nộp | Ghi giờ bắt đầu/kết thúc soạn và giờ nộp để đo trước/sau, số lần nộp sau 12:00 |

Phần integration đã có API, snapshot, annotations, liên kết task/job và bản
nháp bốn mục. Không cần chờ điểm chấm để làm bố cục hoặc automation, nhưng
không tự bịa điểm/KPI khi chưa có nghiệp vụ.

Khi yêu cầu thêm dữ liệu, gửi: tên trường, ý nghĩa, kiểu dữ liệu mong muốn,
nguồn dự kiến và ví dụ hợp lệ. Báo bug với lệnh chạy, phiên bản Python, manifest
đã loại thông tin nhạy cảm; không đính kèm token/.env.

Dataset offline là giả lập. Muốn test task dùng shapes thật, điền task đó trong
.env hoặc --task-id; save trên CVAT và kiểm tra counts.annotations.
