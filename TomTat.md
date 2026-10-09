# Tổng quan output tích hợp CVAT–GitHub

**Đề tài:** Tự động soạn báo cáo trước phiên mentor  
**Phiên bản dữ liệu:** `schema_version = 1`  
**Phạm vi hiện tại:** thu thập dữ liệu, lưu snapshot, xác minh liên kết task/job và tạo bản nháp báo cáo.

## 1. Luồng xử lý

```text
CVAT Cloud + GitHub
        ↓
Thu thập dữ liệu nguồn
        ↓
Xác minh GitHub issue → CVAT task/job
        ↓
Chuẩn hóa thành report_data.json
        ↓
Tạo MENTOR_REPORT_DRAFT.md
```

Chương trình chỉ đọc dữ liệu và lưu local, chưa ghi ngược lên CVAT/GitHub.

## 2. Cấu trúc output

Mỗi lần chạy tạo một thư mục snapshot riêng:

```text
data/raw/<thời điểm UTC>/
├── cvat.json
├── github.json
├── links.json
├── manifest.json
├── report_data.json
└── MENTOR_REPORT_DRAFT.md
```

| File | Vai trò |
|---|---|
| `cvat.json` | Dữ liệu nguồn CVAT, gồm annotations theo job |
| `github.json` | Issues, labels và comments từ GitHub |
| `links.json` | Kết quả xác minh tham chiếu task/job trong issues |
| `manifest.json` | Phạm vi, thời điểm, trạng thái và số bản ghi của lần lấy |
| `report_data.json` | Đầu vào chính cho bên xử lý, BI và soạn báo cáo |
| `MENTOR_REPORT_DRAFT.md` | Bản nháp để nhóm trưởng đọc, chỉnh và review |

Dữ liệu nguồn được giữ để đối chiếu khi số liệu hoặc liên kết có vấn đề.
Snapshot gồm nhiều request liên tiếp, không bảo đảm mọi bản ghi thuộc đúng
một thời điểm nếu người dùng đang chỉnh sửa nguồn.

## 3. Quy tắc đọc dữ liệu

- `null`: chưa có hoặc chưa xác định; không phải số 0.
- Mảng rỗng với status `available`: không có bản ghi phù hợp tại lần lấy.
- `unavailable`: chưa cung cấp được dữ liệu; không được diễn giải thành 0.
- `partial`: chỉ có một phần dữ liệu, cần kiểm tra từng job.
- Timestamp JSON dùng ISO 8601 UTC; Markdown hiển thị giờ Việt Nam UTC+7.
- ID task/job/issue dùng số nguyên.
- `verified` chỉ xác nhận quan hệ task/job, không xác nhận chất lượng annotation.

Bên nhận cần kiểm tra `manifest.json` và status của từng mục trước khi tính toán.

## 4. manifest.json — thông tin lần thu thập

| Trường | Ý nghĩa |
|---|---|
| `schema_version` | Phiên bản cấu trúc |
| `started_at`, `finished_at` | Thời điểm bắt đầu/kết thúc thu thập |
| `scope.task_id` | Task CVAT được chọn |
| `scope.repo` | Repo GitHub được lấy dữ liệu |
| `scope.cvat_host` | Địa chỉ CVAT |
| `scope.org` | Workspace/organization được cấu hình |
| `sources.cvat`, `sources.github` | Kết quả lấy từng nguồn |
| `sources.<nguồn>.status` | `success` hoặc `failed` |
| `sources.<nguồn>.file` | Tên file dữ liệu khi thành công |
| `sources.<nguồn>.counts` | Số bản ghi theo nhóm dữ liệu |
| `sources.<nguồn>.started_at`, `finished_at` | Cửa sổ lấy từng nguồn |
| `sources.<nguồn>.error_type`, `error` | Thông tin lỗi nếu có |
| `sources.cvat.annotations.successful_jobs` | Số jobs lấy annotations thành công |
| `sources.cvat.annotations.failed_jobs` | Số jobs lấy annotations thất bại |
| `links.file` | File chứa kết quả liên kết |
| `links.counts` | Số liên kết theo từng trạng thái |

Nếu GitHub thất bại, mục `links` có thể ghi `status = skipped` và `reason`.

**Lưu ý:** CVAT có thể lấy thành công metadata task/jobs nhưng annotations của
một số jobs thất bại. Vì vậy cần kiểm tra thêm `annotations.failed_jobs`.

`counts.annotations` là số bản ghi kết quả lấy annotations theo job,
không phải tổng số đối tượng đã gán nhãn.

## 5. report_data.json — dữ liệu chuẩn hóa

```text
report_data.json
├── schema_version
├── metadata
├── batch_progress
├── scores
├── annotations
├── edge_cases
└── open_questions
```

### 5.1. metadata

| Trường | Ý nghĩa |
|---|---|
| `snapshot` | Đường dẫn snapshot nguồn |
| `snapshot_started_at`, `snapshot_finished_at` | Thời điểm thu thập |
| `generated_at` | Thời điểm tạo bản nháp |
| `mentor_session` | Tên phiên/kỳ báo cáo; có thể null |
| `scope` | Phạm vi task/repo |
| `warnings` | Các cảnh báo thiếu dữ liệu hoặc liên kết chưa xác minh |
| `excluded_issues` | Issues bị loại khỏi báo cáo |

Mỗi phần tử `excluded_issues` có `number`, `reason`; có thể thêm `task_id`.

Các lý do hiện tại:

- `api_test`: issue thử API.
- `other_task`: issue tham chiếu task khác phạm vi báo cáo.

`generated_at` không phải giờ nộp báo cáo hoặc thời gian người dùng soạn báo cáo.

### 5.2. batch_progress — tiến độ theo task/job

Hiện một task được trình bày như một batch thử; chưa gom nhiều task thành batch.

| Trường | Ý nghĩa |
|---|---|
| `status` | `available` hoặc `unavailable` |
| `task_id`, `task_name` | ID và tên task |
| `total_frames` | Tổng số frame của task |
| `jobs` | Danh sách jobs đã chuẩn hóa |
| `jobs_by_stage` | Số jobs theo stage |
| `jobs_by_state` | Số jobs theo state |
| `annotation_job_count` | Số jobs có type `annotation` |
| `completed_annotation_job_count` | Annotation jobs có state `completed` |
| `completed_annotation_job_percent` | Tỷ lệ completed theo số annotation jobs |
| `completed_frames` | Hiện null: chưa tính frame hoàn thành |
| `completion_percent` | Hiện null: chưa tính % hoàn thành theo frame |
| `note` | Giải thích giới hạn |

Công thức đang dùng:

```text
completed_annotation_job_percent
= completed_annotation_job_count / annotation_job_count × 100
```

Nếu không có annotation job, tỷ lệ để null.
Ground Truth jobs không tham gia công thức này.

Mỗi phần tử `jobs` gồm:

| Trường | Ý nghĩa |
|---|---|
| `job_id` | ID job |
| `type` | Loại job từ CVAT |
| `stage` | Giai đoạn công việc |
| `state` | Trạng thái công việc |
| `assignee` | Username người được giao; null nếu chưa có |
| `frame_count` | Số frame thuộc job |
| `source_url` | Link mở job trên CVAT |

Tỷ lệ theo job không phải % frame đã gán nhãn, tỷ lệ QA duyệt hoặc tiến độ
so với kế hoạch. Khi status unavailable, không sử dụng counts mặc định
để kết luận tiến độ.

### 5.3. scores — điểm chấm

| Trường | Giá trị hiện tại |
|---|---|
| `status` | `unavailable` |
| `value` | null |
| `method` | null |
| `source_url` | null |
| `scored_at` | null |
| `reason` | Chưa thống nhất nguồn điểm và quy tắc QA/QC |

Chưa tích hợp điểm reviewer hoặc CVAT Quality Reports.
Không được thay null bằng 0 hoặc suy ra điểm từ số annotations.

### 5.4. annotations — thống kê dữ liệu gán nhãn

| Trường | Ý nghĩa |
|---|---|
| `status` | `available`, `partial` hoặc `unavailable` |
| `jobs` | Kết quả và counts theo từng job |
| `totals` | Tổng bản ghi từ các jobs lấy thành công |
| `by_label` | Thống kê theo label |
| `note` | Giới hạn cách đếm |
| `reason` | Có khi snapshot chưa chứa annotations |

`totals` và `jobs[].counts` gồm:

| Trường | Ý nghĩa |
|---|---|
| `shapes` | Số shape độc lập |
| `tracks` | Số track |
| `tags` | Số tag |
| `track_shape_records` | Số bản ghi shape được lưu bên trong tracks |

Mỗi phần tử `jobs` có `job_id`, `status`, `counts`.
Job lấy thất bại có `counts = null`.

Mỗi phần tử `by_label` có:

```text
label_id
label_name
shapes
tracks
tags
```

Thống kê annotations cộng các loại jobs đã thu thập, không chỉ annotation jobs.
Không nội suy tracks, không loại trùng đối tượng giữa jobs, không tính skeleton
elements hoặc intervals thành nhóm thống kê riêng.

**Số annotations không phải số frame hoàn thành.**
Một track có thể trải qua nhiều frame; frame không có đối tượng vẫn có thể
đã được người gán nhãn kiểm tra.

### 5.5. edge_cases và open_questions

Hai mục có cùng cấu trúc:

```text
status
items[]
```

- `edge_cases`: issue mở có label `ca-kho`.
- `open_questions`: issue mở có label `mentor-question`.
- Issue có cả hai labels có thể xuất hiện ở cả hai mục.
- Issue thử API và issue tham chiếu task khác bị loại.
- Issue đóng vẫn giữ trong JSON nguồn nhưng không đưa vào hai mục này.

Mỗi phần tử `items` gồm:

| Trường | Ý nghĩa |
|---|---|
| `number` | Số issue |
| `title` | Tiêu đề |
| `description` | Body issue nguyên văn |
| `labels` | Danh sách tên labels |
| `source_url` | Link GitHub issue |
| `state` | Trạng thái issue |
| `author` | Tài khoản tạo issue |
| `updated_at` | Thời điểm cập nhật trên GitHub |
| `task_id`, `job_id` | ID đọc từ body; có thể null |
| `link_status` | Kết quả kiểm tra liên kết |
| `cvat_job_url` | Link job, chỉ sinh khi verified |
| `frame` | Hiện luôn null; chưa đọc/xác minh frame |

Issue chưa có task/job không được tự suy đoán thuộc task đang chạy.
Câu hỏi chung có thể được giữ lại và có cảnh báo chưa xác minh tham chiếu.
Comments hiện lưu trong raw, chưa tổng hợp vào `description`.

## 6. links.json — kết quả kiểm tra liên kết

Đây là array. Mỗi phần tử có các trường tùy kết quả:

| Trường | Ý nghĩa |
|---|---|
| `github_issue` | Số issue |
| `github_url` | Link issue |
| `github_issue_updated_at` | Thời điểm cập nhật issue |
| `cvat_task_id`, `cvat_job_id` | Tham chiếu trong body |
| `actual_cvat_task_id` | Task thực tế của job do CVAT trả về |
| `relationship_verified` | Có khớp task/job không |
| `status` | Trạng thái kiểm tra |
| `error_type` | Loại lỗi nếu xác minh thất bại |

Không phải mọi phần tử đều có đủ các trường.

| Status | Ý nghĩa |
|---|---|
| `verified` | Job thuộc đúng task được ghi |
| `mismatch` | Job thuộc task khác |
| `unlinked` | Không có dòng tham chiếu theo mẫu |
| `invalid_reference` | Thiếu, trùng hoặc sai định dạng ID |
| `verification_failed` | Không thể xác minh qua API |

Các dòng body để chương trình đọc ID:

```text
CVAT task ID: 2592622
CVAT job ID: 4475446
```

Mỗi loại ID xuất hiện đúng một lần và là số nguyên dương.

## 7. JSON nguồn

### cvat.json

```text
task          object
jobs          array
labels        array
issues        array
comments      array
annotations   array
```

`labels` là danh mục nhãn, ví dụ vehicle.
`annotations` là dữ liệu đã gán như boxes, polygons hoặc tracks.

Mỗi phần tử `annotations` có:

```text
job_id
status
data         # payload nguyên bản khi success
error_type   # khi failed
error        # nếu có
```

Trong `data` có các nhóm như tags, shapes, tracks và trường khác do CVAT trả về.
Cần Save trên CVAT trước khi lấy để nhận thay đổi đã lưu.
Chương trình không tải ảnh.

### github.json

```text
issues     array
labels     array
comments   array
```

Giữ payload nguồn để đối chiếu.
Issues gồm cả mở và đóng, đã loại PR.

## 8. Bản nháp Markdown

`MENTOR_REPORT_DRAFT.md` gồm:

1. Tiến độ batch và thống kê annotations.
2. Điểm chấm.
3. Ca khó kèm link job.
4. Câu hỏi mở.

Có thời điểm lấy dữ liệu, thời điểm tạo nháp, phiên mentor và tham chiếu snapshot.
Đây là bản nháp cần review trước khi nộp.

## 9. Người làm tiếp sử dụng output thế nào?

1. Kiểm tra manifest và phạm vi dữ liệu.
2. Dùng report_data.json làm đầu vào chính.
3. Kiểm tra status/null trước khi tính toán.
4. Đối chiếu raw và links.json nếu cần điều tra.
5. Giữ tham chiếu snapshot khi tạo báo cáo hoặc dashboard.

Phần tiếp tục cần nhóm thống nhất:

- Nguồn điểm chấm và thang điểm QA/QC.
- Định nghĩa frame/batch hoàn thành.
- Phạm vi nhiều task.
- Lịch chạy và deadline phiên mentor.
- Ghi nhận thời gian soạn/nộp để đo trước/sau và số lần nộp sau 12:00.

Hiện chưa triển khai các chỉ tiêu thời gian, lịch tự động, so sánh giữa kỳ
hoặc đồng bộ hai chiều.