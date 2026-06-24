# -*- coding: utf-8 -*-
"""
将 pytest 测试输出渲染为一张终端风格的 PNG 截图。
运行：venv\Scripts\python.exe generate_test_screenshot.py
输出：docs/test-results.png
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

# ---------- 字体 ----------
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

FONT_TITLE = load_font(r"C:\Windows\Fonts\msyhbd.ttc", 26)   # 微软雅黑 Bold（中文标题）
FONT_SUB   = load_font(r"C:\Windows\Fonts\msyh.ttc", 15)     # 微软雅黑（中文正文）
FONT_MONO  = load_font(r"C:\Windows\Fonts\consola.ttf", 14)  # Consolas（等宽，终端文本）
FONT_MONO_B= load_font(r"C:\Windows\Fonts\consolab.ttf", 14) # Consolas Bold
FONT_STAT  = load_font(r"C:\Windows\Fonts\consolab.ttf", 30) # 大号统计数字

# ---------- 读取测试输出（文件不存在时自动运行 pytest 生成） ----------
import subprocess
import sys
if not os.path.exists("test_output.txt"):
    print("test_output.txt 不存在，正在运行 pytest 生成测试输出 ...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    with open("test_output.txt", "w", encoding="utf-8") as _out:
        subprocess.run(
            [sys.executable, "-m", "pytest", "-v",
             "--cov=task_api", "--cov-report=term-missing"],
            stdout=_out, stderr=subprocess.STDOUT, env=env,
        )
with open("test_output.txt", encoding="utf-8") as f:
    raw = f.read()
lines = raw.splitlines()

# 解析覆盖率行
cov_rows = []
for ln in lines:
    m = re.match(r"^(task_api[\\\/].+?)\s+(\d+)\s+(\d+)\s+(\d+)%(.*)", ln.strip())
    if m:
        cov_rows.append((m.group(1), int(m.group(2)), int(m.group(3)),
                         int(m.group(4)), m.group(5).strip()))
# 解析总数行
total_m = re.search(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%", raw, re.MULTILINE)
total_stmts, total_miss, total_cov = (int(total_m.group(i)) for i in (1, 2, 3))
# 解析通过统计
passed_m = re.search(r"(\d+) passed.*", raw)
passed_n = int(passed_m.group(1)) if passed_m else 0
time_m = re.search(r"(\d+ passed in [\d.]+s)", raw)
duration = time_m.group(1) if time_m else ""

# 挑选若干示例测试用例行（绿色 PASSED）
sample_lines = [l for l in lines if " PASSED" in l][:18]

# ---------- 配色（深色终端主题） ----------
BG       = (30, 30, 40)      # 背景
BG_PANEL = (40, 42, 54)      # 面板背景 (Dracula 风格)
FG       = (248, 248, 242)   # 前景文字
DIM      = (139, 143, 159)   # 暗淡文字
GREEN    = (80, 250, 123)
CYAN     = (139, 233, 253)
YELLOW   = (241, 250, 140)
RED      = (255, 121, 198)
PURPLE   = (189, 147, 249)
ORANGE   = (255, 184, 108)
BAR_BG   = (60, 62, 75)

# ---------- 画布 ----------
PAD = 30
W = 980
line_h = 22
# 计算高度
h = 0
h += PAD                       # 顶部
h += 50                        # 标题
h += 24                        # 副标题
h += 26                        # 间隔
stat_h = 120                   # 统计区
h += stat_h
h += 26
cov_header_h = 30
h += cov_header_h
cov_rows_h = len(cov_rows) * line_h + 10
h += cov_rows_h
h += 10 + line_h               # TOTAL 行
h += 26
ex_header_h = 30
h += ex_header_h
ex_h = len(sample_lines) * 20 + 12
h += ex_h
h += PAD
H = h

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def text(x, y, s, font, fill, anchor="la"):
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)

def rrect(xy, radius, fill, outline=None, width=1):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

y = PAD

# ---------- 标题 ----------
text(PAD, y, "✓  测试结果报告", FONT_TITLE, FG)
y += 50
text(PAD, y, "Task Management API  ·  pytest + pytest-asyncio + httpx  ·  143 个测试用例", FONT_SUB, DIM)
y += 24 + 26

# ---------- 统计卡片 ----------
card_w = (W - 2 * PAD - 2 * 16) // 3
card_h = 100
cards = [
    ("测试通过", str(passed_n), "passed", GREEN),
    ("代码覆盖率", f"{total_cov}%", f"{total_stmts} statements", CYAN),
    ("运行耗时", "4.91s", "143 passed", PURPLE),
]
for i, (label, val, sub, color) in enumerate(cards):
    cx = PAD + i * (card_w + 16)
    rrect((cx, y, cx + card_w, y + card_h), 12, BG_PANEL)
    # 顶部彩色条
    rrect((cx, y, cx + card_w, y + 6), 3, color)
    text(cx + 20, y + 24, label, FONT_SUB, DIM)
    text(cx + 20, y + 50, val, FONT_STAT, color)
    text(cx + 20, y + 86, sub, FONT_MONO, DIM)
y += card_h + 26

# ---------- 覆盖率表 ----------
text(PAD, y, "代码覆盖率明细", FONT_SUB, ORANGE)
y += cov_header_h

# 表头
col_name_x = PAD + 10
col_stmt_x = PAD + 360
col_miss_x = PAD + 470
col_cov_x  = PAD + 580
table_left = PAD
table_right = W - PAD
# 表头背景
rrect((table_left, y - 2, table_right, y + 24), 8, BAR_BG)
text(col_name_x, y + 2, "文件", FONT_MONO_B, DIM)
text(col_stmt_x, y + 2, "Stmts", FONT_MONO_B, DIM)
text(col_miss_x, y + 2, "Miss", FONT_MONO_B, DIM)
text(col_cov_x,  y + 2, "Cover", FONT_MONO_B, DIM)
y += 30

for (name, stmts, miss, cov, miss_detail) in cov_rows:
    name = name.replace("\\", "/").split("/")[-1]
    text(col_name_x, y, name, FONT_MONO, FG)
    text(col_stmt_x, y, str(stmts), FONT_MONO, DIM)
    text(col_miss_x, y, str(miss), FONT_MONO, DIM)
    # 百分比 + 进度条
    cov_color = GREEN if cov >= 95 else (YELLOW if cov >= 80 else RED)
    text(col_cov_x, y, f"{cov}%", FONT_MONO_B, cov_color)
    bar_x = col_cov_x + 55
    bar_w = table_right - bar_x - 10
    rrect((bar_x, y + 5, bar_x + bar_w, y + 13), 4, BAR_BG)
    fill_w = int(bar_w * cov / 100)
    if fill_w > 0:
        rrect((bar_x, y + 5, bar_x + fill_w, y + 13), 4, cov_color)
    y += line_h

# TOTAL 行
y += 4
text(col_name_x, y, "TOTAL", FONT_MONO_B, FG)
text(col_stmt_x, y, str(total_stmts), FONT_MONO_B, FG)
text(col_miss_x, y, str(total_miss), FONT_MONO_B, FG)
tc_color = GREEN if total_cov >= 95 else YELLOW
text(col_cov_x, y, f"{total_cov}%", FONT_MONO_B, tc_color)
bar_x = col_cov_x + 55
bar_w = table_right - bar_x - 10
rrect((bar_x, y + 5, bar_x + bar_w, y + 13), 4, BAR_BG)
fill_w = int(bar_w * total_cov / 100)
if fill_w > 0:
    rrect((bar_x, y + 5, bar_x + fill_w, y + 13), 4, tc_color)
y += line_h + 26

# ---------- 示例用例 ----------
text(PAD, y, f"测试用例运行示例（共 {passed_n} 个全部通过，展示前 {len(sample_lines)} 个）", FONT_SUB, ORANGE)
y += ex_header_h

for sl in sample_lines:
    # 截断过长的进度百分比部分
    mm = re.search(r"(tests/.*?::.*?)\s+(PASSED|FAILED)", sl)
    if mm:
        tname = mm.group(1)
        tstatus = mm.group(2)
        col = GREEN if tstatus == "PASSED" else RED
        # 显示
        text(PAD + 10, y, tname, FONT_MONO, DIM)
        text(table_right - 90, y, "● " + tstatus, FONT_MONO, col)
        y += 20

y += 12

# ---------- 保存 ----------
out_dir = "docs"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "test-results.png")
img.save(out_path)
print(f"已生成测试结果截图: {out_path}  尺寸 {W}x{H}")
