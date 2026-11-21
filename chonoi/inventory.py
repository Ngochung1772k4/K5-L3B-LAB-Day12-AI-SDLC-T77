"""File kho v1.2 (Ticket-03): {"items": [{"id","kind","fresh"}, ...]} — kho CÁ THỂ.

Đọc: từ chối kho đếm v1.0/v1.1, sai schema, kind lạ, id trùng/rỗng, fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử, byte-ổn-định; fresh ghi đủ chính xác
(repr float của u/240) để đọc lại giữ đúng nhánh ở ngưỡng 30.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import id_key
from .items import from_dict

KINDS_P1 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")  # 6 nguyên liệu


def validate_item_list(items, name="items", kinds=KINDS_P1):
    """Kiểm mảng cá thể; trả danh sách nội bộ {id, kind, u}."""
    if not isinstance(items, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (kho đếm không còn hợp lệ ở v1.2)")
    seen, out = set(), []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}[{i}] phải có đúng các khóa id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"]:
            raise BadInput(f"{name}[{i}].id phải là chuỗi khác rỗng")
        if it["id"] in seen:
            raise BadInput(f"{name}: id trùng {it['id']}")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"{name}[{i}]: nguyên liệu lạ {it['kind']!r}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not (0 <= f <= 100):
            raise BadInput(f"{name}[{i}].fresh phải là số hữu hạn trong [0, 100]")
        out.append(from_dict(it))
    return out


def read_inventory(path: str, kinds=KINDS_P1) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_item_list(data["items"], "file kho items", kinds)


def write_inventory(path: str, items: list):
    """`items`: danh sách cá thể dạng xuất {id, kind, fresh}."""
    items = sorted(items, key=lambda it: id_key(it["id"]))
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
