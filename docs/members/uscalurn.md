# uscalurn — Phase 1

**Vai trò:** D — QA Lead / AI Harness.

Tôi dùng Codex đọc PRD-0/Test Contract v1.0, hoàn thiện [67 test methods](../../tests/test_gather_rules.py), gồm [39 test Quán](../../tests/test_quan_rules.py). Sáu regression kiểm validator của C; tôi không triển khai validator.

Chạy mới: 99 methods, 48 PASS/51 FAIL, không ERROR/SKIP. [Proof](../proof/phase-1/d-uscalurn-run-81321f1b/summary.json) ghi revision nền 6a7f66a35e5816996fe51010ea5b20ac9098fe5c và hash working tree; chưa có commit riêng. [Smoke](../proof/phase-1/d-uscalurn-run-81321f1b/integration.md) và [determinism](../proof/phase-1/d-uscalurn-determinism-df2e0816/determinism.md) PASS trong fixture đã chạy.

Tôi tạo hai skill, [verification](../verification/phase-1.md), triage. Kiểm chứng AI bằng unittest, exit code, snapshot/event, so byte; không sửa assertion cho xanh.

Vướng mắc: A/B còn TODO oxy, hái/bắt, khách, nấu/phục vụ. Tôi phát hiện default khách và player.vel thiếu trong snapshot Quán. Không thực hiện review/merge.

Bài học: contract-first testing phát hiện thiếu hành vi sớm; regression bảo vệ liên kết dữ liệu. Determinism PASS không chứng minh gameplay đúng. Cần chuyển owner fixture, seed, tick, expected/actual rồi chạy lại.

Token, chi phí, thời gian AI: Không đo được.
