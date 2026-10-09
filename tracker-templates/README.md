# annotation-qa-tracker: bộ thiết lập repo

Đây là bộ file chuẩn bị cho repo `DuyWebdev/annotation-qa-tracker`.
Copy thư mục `.github` trong đây vào gốc repo tracker và commit lên default branch.
Chưa tự đăng các file này lên GitHub; chúng đang nằm trong project pipeline local.

Tạo hai label trong tracker: `ca-kho` và `mentor-question` trước khi dùng templates.
Mẫu ca khó yêu cầu task/job ID; câu hỏi chung có thể không có tham chiếu CVAT.
Issue có cả hai label xuất hiện trong cả hai mục báo cáo.

Định dạng pipeline đọc:

```text
CVAT task ID: 2592622
CVAT job ID: 4475446
```

Mỗi loại ID chỉ có một dòng, ID là số nguyên dương. GitHub Issue Forms thêm
heading nhưng giữ nội dung các dòng này. Pipeline xác minh job thuộc task qua CVAT.
Frame hiện chỉ là thông tin mô tả, chưa được xác minh tự động.

Issue thử dùng prefix `[API test]` hoặc label `api-test` để loại khỏi báo cáo.
Không coi việc đóng issue là pass/reject hay tự xem mọi issue là defect.
Repo public: nội dung issue công khai; không đưa token hoặc dữ liệu không được
nhóm cho phép công khai vào issue.
