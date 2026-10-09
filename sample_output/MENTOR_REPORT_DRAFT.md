# Bản nháp báo cáo trước phiên mentor

Phiên mentor: SYNTHETIC OFFLINE DEMO

Dữ liệu lấy lúc: 09/10/2026 07:00:00 (UTC+7)

Bản nháp tạo lúc: 09/10/2026 17:04:07 (UTC+7)

Snapshot nguồn: `sample_data`

Bản nháp cần nhóm trưởng rà soát trước khi nộp. Task hiện được trình bày làm đơn vị batch.

Thông tin còn thiếu:

- Câu hỏi #3 chưa có tham chiếu task/job được xác minh; có thể là câu hỏi chung của repo.

## 1. Tiến độ batch

Task: **SYNTHETIC DEMO** — ID `1001`; tổng frame: **20**.

Job gán nhãn có state `completed`: **1/2**; tỷ lệ theo số job: **50.0%**. Đây không phải tỷ lệ frame hoàn thành hoặc tỷ lệ QA duyệt.

| Job | Loại | Giai đoạn | Trạng thái | Người phụ trách | Số frame của job |
|---|---|---|---|---|---|
| [2001](https://example.com/tasks/1001/jobs/2001) | annotation | annotation | completed | Chưa có | 10 |
| [2002](https://example.com/tasks/1001/jobs/2002) | annotation | annotation | in progress | Chưa có | 10 |
| [2003](https://example.com/tasks/1001/jobs/2003) | ground_truth | acceptance | completed | Chưa có | 1 |

Chưa suy ra tiến độ frame hoặc nghiệm thu từ trạng thái job.

Annotations (available): **3 shapes**, **1 tracks**, **1 tags**; **2 bản ghi shape trong tracks**.

Đếm bản ghi API theo job, không nội suy track. Không phải số frame hoàn thành hoặc số đối tượng duy nhất toàn task.

| Nhãn | Shapes | Tracks | Tags |
|---|---|---|---|
| vehicle (ID 1) | 3 | 1 | 1 |

## 2. Điểm chấm

Chưa thống nhất nguồn điểm và quy tắc chấm QA/QC.
Điểm hiện để trống; không coi thiếu dữ liệu là điểm 0.

## 3. Ca khó kèm link job

### #2 — DEMO: occluded vehicle

[Xem issue và nội dung đầy đủ](https://example.com/issues/2)

> Synthetic example only.
> CVAT task ID: 1001
> CVAT job ID: 2002
> How should the team annotate an occluded vehicle?

[Mở job CVAT](https://example.com/tasks/1001/jobs/2002) — đã xác minh quan hệ task/job; chưa xác minh frame.

## 4. Câu hỏi mở

### #3 — DEMO: guideline question

[Xem issue và nội dung đầy đủ](https://example.com/issues/3)

> Synthetic general question: which guideline version should we use?

Liên kết CVAT: chưa xác minh (unlinked).

