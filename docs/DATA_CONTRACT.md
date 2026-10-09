# Hợp đồng dữ liệu báo cáo v1

Consumer: module soạn báo cáo, nhóm trưởng hoặc phần BI của nhóm.
Producer: `src/sync.py` và `src/report.py`.
Output: `report_data.json` và `MENTOR_REPORT_DRAFT.md` trong cùng snapshot nguồn.

## Quy tắc chung

Issue tham chiếu task khác phạm vi chạy bị loại khỏi bản nháp và ghi
`metadata.excluded_issues.reason = other_task`; vẫn giữ trong github.json và
links.json. Câu hỏi không có task/job giữ lại như câu hỏi chung, kèm cảnh báo.
Các issue chưa có ID không được tự suy đoán thuộc task hiện tại.

- `schema_version = 1`; các trường mới được thêm để mở rộng v1, consumer bỏ qua
  trường không dùng. Thay ý nghĩa hoặc kiểu dữ liệu cần tăng version.
- `null`: chưa có hoặc chưa xác định, không phải số 0.
- Array rỗng cùng status `available`: không có bản ghi phù hợp quy ước ở snapshot.
- Status `unavailable`: không thể cung cấp dữ liệu; không được tính thành 0.
- ID task/job/issue là integer; timestamps là ISO 8601 UTC; Markdown hiển thị UTC+7.
- JSON nguồn giữ nguyên; dữ liệu chuẩn hóa không thay thế raw cho việc đối chiếu.

## Metadata

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `metadata.snapshot` | string | Thư mục chứa JSON nguồn và manifest |
| `snapshot_started_at`, `snapshot_finished_at` | string/null | Cửa sổ thu thập, không phải giờ nộp |
| `generated_at` | string | Lúc tạo bản nháp, không phải thời gian người dùng soạn |
| `mentor_session` | string/null | Tên kỳ, đặt bằng `--session` |
| `scope` | object | task_id, repo, cvat_host, org lấy từ manifest |
| `warnings` | string[] | Nguồn thiếu hoặc ca khó chưa xác minh liên kết |
| `excluded_issues` | object[] | Issue thử đã loại, có number và reason |

## Bốn mục báo cáo

| Mục/trường | Kiểu | Nguồn/ý nghĩa |
|---|---|---|
| `batch_progress.status` | string | available/unavailable |
| `task_id`, `task_name`, `total_frames` | integer/string/integer hoặc null | CVAT Task |
| `jobs` | object[] | Job ID, type, stage, state, assignee, frame_count, source_url |
| `jobs_by_stage`, `jobs_by_state` | object | Số jobs theo trạng thái, gồm các loại job đã lấy |
| `annotation_job_count` | integer | Chỉ đếm job có type annotation |
| `completed_annotation_job_count` | integer | Annotation job có state completed |
| `completed_annotation_job_percent` | number/null | completed annotation jobs / annotation jobs × 100; null nếu không có job |
| `completed_frames`, `completion_percent` | null | Chưa triển khai quy tắc tiến độ theo frame |
| `scores.status` | string | Hiện unavailable; nguồn điểm chưa chốt |
| `scores.value`, `method`, `source_url`, `scored_at` | null | Chưa có tích hợp điểm chấm |
| `scores.reason` | string | Lý do chưa cung cấp điểm |
| `edge_cases.status`, `open_questions.status` | string | available khi GitHub đã lấy được, unavailable khi thất bại |
| `edge_cases.items` | object[] | Issues mở có label ca-kho |
| `open_questions.items` | object[] | Issues mở có label mentor-question |

Tỷ lệ theo job chỉ là thống kê state CVAT, không phải tỷ lệ frame gán nhãn,
nghiệm thu QA hay tiến độ theo kế hoạch. Khi nguồn CVAT unavailable, không sử dụng
các count mặc định trong object để đưa ra kết luận.

Mỗi item ca khó/câu hỏi có number, title, description, labels, source_url, state,
author, updated_at, task_id, job_id, link_status, cvat_job_url và frame.
`cvat_job_url` chỉ được sinh khi quan hệ task/job verified. `frame` hiện luôn null;
không tự đọc frame từ văn bản. Link status: verified/mismatch/unlinked/
invalid_reference/verification_failed. verified không xác nhận chất lượng annotation.

## Cách sử dụng

### Bổ sung annotations

`cvat.json.annotations` là array theo job: `job_id`, `status`, `data` (payload
annotations nguyên bản khi success), hoặc thông tin lỗi khi failed. API:
`GET /api/jobs/{id}/annotations/`. Không tải ảnh. Cần Save trên CVAT trước khi lấy.

`report_data.json.annotations` chứa status available/partial/unavailable,
jobs (counts riêng), totals và by_label. Counts gồm shapes, tracks, tags và
track_shape_records (số bản ghi shape được lưu trong tracks, không phải số box
sau nội suy). by_label thống kê shapes/tracks/tags theo label_id và label_name.
Totals chỉ cộng jobs lấy thành công; partial không được coi là thống kê đầy đủ.
Job lỗi có counts null. Snapshot cũ không có annotations vẫn render được với
status unavailable. Phần annotations được thêm trong schema v1, không đổi trường cũ.

Không tính số frame hoàn thành từ annotations. Không deduplicate đối tượng giữa
jobs hoặc nội suy tracks; chưa thống kê skeleton elements hay intervals riêng.
Nếu job annotations lỗi, manifest có failed_jobs và sync exit code 1, trong khi
metadata task/jobs lấy được vẫn giữ success. Đọc cả nguồn và annotations status.

```powershell
.\.venv\Scripts\python.exe src/sync.py --session "Phiên mentor thứ 5"
```

Bên nhận đọc status trước rồi mới sử dụng số liệu. Raw comments đã thu thập nhưng
chưa được tổng hợp trong mô tả báo cáo; description hiện lấy nguyên body issue.
Mẫu issue chuẩn bị trong `tracker-templates/.github/ISSUE_TEMPLATE/`, cần đưa vào repo
tracker và tạo labels để nhóm sử dụng.

## Các phần vẫn cần quyết định nghiệp vụ

Nguồn và thang điểm QA; định nghĩa hoàn thành frame/batch; phạm vi nhiều task;
lịch và deadline phiên mentor; cách ghi nhận giờ bắt đầu soạn và giờ nộp chính thức.
Các chỉ tiêu thời gian trước/sau và nộp trễ chưa được tính bởi pipeline hiện tại.
