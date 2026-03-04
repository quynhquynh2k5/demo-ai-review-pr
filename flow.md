# PR-Agent Flow

## Luồng chung

```
python3 -m pr_agent.cli --pr_url="$MR_URL" <command>
```

```
cli.py:run()
  → PRAgent().handle_request(pr_url, ["describe"])
    → command2class["describe"](pr_url).run()
```

Mapping lệnh → class tại `pr_agent/agent/pr_agent.py`:

| Lệnh | Class |
|------|-------|
| `describe` | `PRDescription` |
| `review` | `PRReviewer` |
| `improve` | `PRCodeSuggestions` |

---

## 1. `describe` — Tự động mô tả PR

**Class**: `PRDescription` tại `pr_agent/tools/pr_description.py`

**Luồng**:
1. Lấy thông tin PR từ git provider (title, branch, description, commit messages)
2. Trích xuất ticket liên quan (nếu có)
3. **Gọi AI** qua `retry_with_fallback_models(self._prepare_prediction)` — lấy diff → gửi prompt + diff cho LLM
4. AI trả về: **title mới, type (Bug fix/Enhancement/...), summary, walkthrough các file thay đổi**
5. Publish kết quả:
   - Cập nhật **title** và **body** của PR/MR
   - Gán **labels** (nếu bật)
   - Thêm **file changes walkthrough** (bảng mô tả từng file)

---

## 2. `review` — Review code tự động

**Class**: `PRReviewer` tại `pr_agent/tools/pr_reviewer.py`

**Luồng**:
1. Lấy diff files từ PR
2. Trích xuất ticket liên quan
3. **Lấy PR diff** qua `get_pr_diff()` — lấy patch của tất cả file thay đổi, thêm line numbers
4. **Gọi AI** qua `retry_with_fallback_models(self._prepare_prediction)` — gửi diff + prompt cho LLM
5. AI phân tích và trả về:
   - **Estimated effort** to review (1-5)
   - **Security concerns**
   - **Relevant tests** có hay không
   - **Recommended focus areas** (vấn đề logic, performance, style...)
6. Publish **comment review** lên PR/MR (persistent comment)

---

## 3. `improve` — Đề xuất cải tiến code

**Class**: `PRCodeSuggestions` tại `pr_agent/tools/pr_code_suggestions.py`

**Luồng**:
1. Lấy diff files từ PR
2. **Gọi AI** qua `retry_with_fallback_models(self._prepare_prediction_extended)` — chế độ extended, có thể gọi nhiều lần AI cho PR lớn
3. AI trả về danh sách **code suggestions**, mỗi suggestion gồm:
   - File + dòng code cụ thể
   - Code cũ → code mới (dạng diff)
   - Category (General / Possible issue)
   - Impact level (Low/Medium/High)
   - Lý do đề xuất
4. Publish bảng **"PR Code Suggestions"** lên PR/MR comment

---

## Điểm chung cả 3 lệnh

```
Git Provider (vnpt_scm)          AI Handler (ic_coding_assistant)
        │                                    │
        ▼                                    ▼
   get_diff_files()              gọi LLM API qua ic_code__base_url
   get_pr_description()          với ic_code__key
   get_commit_messages()              │
        │                              ▼
        └──── diff + context ───► Prompt (Jinja2 template) ───► AI response
                                                                    │
                                                                    ▼
                                                          publish_comment()
                                                          (ghi comment lên MR)
```

- Tất cả đều dùng **VNPT SCM provider** (`config__git_provider="vnpt_scm"`) để đọc/ghi lên GitLab
- Tất cả gọi **IC Coding Assistant** LLM thông qua `ic_code__base_url` + `ic_code__key`
- Kết quả được **publish trực tiếp** dưới dạng comment trên Merge Request
