# -*- coding: utf-8 -*-
"""Draw review-book figures as SVG and render them to PNG with headless Edge.

Reference implementation from DASE7501 (robot kinematics/dynamics figures).
The SVG helper functions (txt/line/arrow/dim/arc/rect/circle/axhead/...), the
Edge headless render loop and the PIL verification harness are generic: copy
this file, replace the FIGURES list with your own drawing functions, and run.

Figures are hand-written SVG (bilingual EN/ZH labels), rendered 1:1 by Edge
(--headless=new --screenshot) and verified with PIL pixel checks:
  - output size matches the SVG canvas
  - corners are white (background)
  - ink coverage is sane (not blank)
  - expected axis colors (red/blue/green) are present when used
Usage: python make_figures.py
Output: figures/*.svg + figures/*.png
Embed in Markdown as ![caption](figures/name.png); build_interactive_review.py
inlines them as base64 data URIs.
"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'figures')

DARK = '#1d2637'; GRAY = '#5f6d88'; RED = '#d64550'; GREEN = '#178a56'; BLUE = '#3f6dff'
LIGHT = '#f4f7ff'; LINE = '#d9e1f0'

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def txt(x, y, s, size=15, weight='normal', fill=DARK, anchor='middle', italic=False):
    fw = ' font-weight="%s"' % weight if weight != 'normal' else ''
    fs = ' font-style="italic"' if italic else ''
    return ('<text x="%g" y="%g" font-size="%g"%s%s fill="%s" text-anchor="%s">%s</text>'
            % (x, y, size, fw, fs, fill, anchor, esc(s)))

def line(x1, y1, x2, y2, color=DARK, w=2.5, marker='ad', dash=None, mstart=None):
    a = ' marker-end="url(#%s)"' % marker if marker else ''
    b = ' marker-start="url(#%s)"' % mstart if mstart else ''
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return ('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"%s%s%s/>'
            % (x1, y1, x2, y2, color, w, a, b, d))

def arrow(x1, y1, x2, y2, color=DARK, w=2.5, marker='ad', dash=None):
    return line(x1, y1, x2, y2, color, w, marker, dash)

def dim(x1, y1, x2, y2, color=GRAY, w=1.6, tick=7):
    """Dimension line with arrowhead triangles at both ends."""
    import math
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    hw = tick * 0.62
    def tri(x, y, sx, sy):
        return ('<polygon points="%g,%g %g,%g %g,%g" fill="%s"/>'
                % (x + sx * tick, y + sy * tick,
                   x + px * hw + sx * 0, y + py * hw + sy * 0,
                   x - px * hw + sx * 0, y - py * hw + sy * 0, color))
    return (line(x1, y1, x2, y2, color, w) + tri(x1, y1, ux, uy) + tri(x2, y2, -ux, -uy))

def arc(cx, cy, r, a1, a2, color=GRAY, w=1.8, dash='5,4'):
    """Arc from angle a1 to a2 (degrees, screen coords, y down), clockwise."""
    import math
    a1r, a2r = math.radians(a1), math.radians(a2)
    x1, y1 = cx + r * math.cos(a1r), cy + r * math.sin(a1r)
    x2, y2 = cx + r * math.cos(a2r), cy + r * math.sin(a2r)
    sweep = 1 if (a2 - a1) % 360 <= 180 else 0
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return ('<path d="M%g,%g A%g,%g 0 0 %d %g,%g" fill="none" stroke="%s" stroke-width="%g"%s/>'
            % (x1, y1, r, r, sweep, x2, y2, color, w, d))

def rect(x, y, w, h, fill=LIGHT, stroke=BLUE, sw=2, rx=12):
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"/>'
            % (x, y, w, h, rx, fill, stroke, sw))

def circle(cx, cy, r, fill=DARK, stroke='none', sw=0):
    s = ' stroke="%s" stroke-width="%g"' % (stroke, sw) if stroke != 'none' else ''
    return '<circle cx="%g" cy="%g" r="%g" fill="%s"%s/>' % (cx, cy, r, fill, s)

def zsym(x, y, label, r=13):
    """Z axis out of the page: ring with centre dot + label."""
    return (circle(x, y, r, 'none', BLUE, 2.6) + circle(x, y, 2.6, BLUE)
            + txt(x + r + 8, y + 4, label, 16, 'bold', BLUE, 'start'))

def axhead(x, y, ang, color, label, lx, ly, ln=75, w=3):
    """Axis arrow: from (x,y) direction ang (deg, screen, y down), length ln."""
    import math
    a = math.radians(ang)
    x2, y2 = x + ln * math.cos(a), y + ln * math.sin(a)
    return (line(x, y, x2, y2, color, w, 'a' + color[1:])
            + txt(lx, ly, label, 15, 'bold', color, 'start'))

def hatch(x, y, w, h, gap=9, color='#8a93a8', wd=1.4):
    out = []
    n = int(w / gap) + 1
    for k in range(n):
        out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"/>'
                   % (x + k * gap, y + h, x + k * gap + h, y, color, wd))
    return ''.join(out)

def defs(colors):
    out = ['<defs>']
    for name, c in colors:
        out.append('<marker id="a%s" markerWidth="9" markerHeight="9" refX="7" refY="3.5" '
                   'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L7,3.5 L0,7 z" fill="%s"/></marker>'
                   % (name, c))
    out.append('</defs>')
    return ''.join(out)

def svg(w, h, body, colors=(('d', DARK), ('d64550', RED), ('178a56', GREEN), ('3f6dff', BLUE))):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'font-family="Segoe UI, Microsoft YaHei, sans-serif">'
            '<rect width="%d" height="%d" fill="#ffffff"/>%s%s</svg>' % (w, h, w, h, w, h, defs(colors), body))

def title(x, w, s, y=42, size=19):
    return txt(x + w / 2.0, y, s, size, 'bold', DARK)

def note(x, y, s, w=860, size=13, fill=GRAY):
    return txt(x + w / 2.0, y, s, size, 'normal', fill)

# ============================================================ F1 fk_ik_map
def fk_ik_map():
    b = []
    b.append(title(0, 860, '正运动学 vs 逆运动学 (Forward vs Inverse Kinematics)'))
    b.append(rect(30, 90, 300, 140))
    b.append(txt(180, 135, 'Joint Space', 20, 'bold', BLUE))
    b.append(txt(180, 162, '关节空间', 16))
    b.append(txt(180, 192, 'q = (q₁, q₂, …, qₙ)', 15, 'normal', GRAY, italic=True))
    b.append(rect(530, 90, 300, 140))
    b.append(txt(680, 135, 'Task Space', 20, 'bold', GREEN))
    b.append(txt(680, 162, '任务空间', 16))
    b.append(txt(680, 192, '(x, y, z, φ) 位姿', 15, 'normal', GRAY, italic=True))
    b.append(arrow(330, 140, 524, 140, DARK, 3))
    b.append(txt(427, 126, 'Forward Kinematics 正运动学', 15, 'bold'))
    b.append(txt(427, 166, '已知关节角 → 求位姿 (given q → find pose)', 12.5, 'normal', GRAY))
    b.append(arrow(524, 215, 330, 215, DARK, 3))
    b.append(txt(427, 252, 'Inverse Kinematics 逆运动学', 15, 'bold'))
    b.append(txt(427, 278, '已知位姿 → 求关节角 (given pose → find q)', 12.5, 'normal', GRAY))
    return svg(860, 300, ''.join(b))

# ============================================================ F2 dh_frames_planar2
def dh_frames_planar2():
    import math
    b = []
    b.append(title(0, 960, 'D-H 坐标系:两连杆平面机械臂 (D-H frames on a 2-link planar arm)', 17))
    O0 = (150, 500)
    O1 = (291, 359)
    O2 = (247, 195)
    b.append(rect(110, 500, 80, 35, '#eceff5', '#8a93a8', 1.5, 4))
    b.append(hatch(110, 500, 80, 35))
    # links
    b.append(line(O0[0], O0[1], O1[0], O1[1], '#5a6478', 7))
    b.append(line(O1[0], O1[1], O2[0], O2[1], '#5a6478', 7))
    # end-effector triangle at tip of link2
    tip = (237, 156)
    b.append('<polygon points="%g,%g %g,%g %g,%g" fill="%s"/>'
             % (tip[0], tip[1], tip[0] - 6, tip[1] + 16, tip[0] + 10, tip[1] + 12, DARK))
    # axes frame 0
    b.append(axhead(O0[0], O0[1], 0, RED, 'X₀', O0[0] + 82, O0[1] + 16))
    b.append(axhead(O0[0], O0[1], -90, GREEN, 'Y₀', O0[0] - 24, O0[1] - 80))
    # axes frame 1 (link1 dir = 45 deg up-right -> screen angle -45;
    # right-handed: Y at screen angle X-90 = -135)
    b.append(axhead(O1[0], O1[1], -45, RED, 'X₁', O1[0] + 58, O1[1] - 62))
    b.append(axhead(O1[0], O1[1], -135, GREEN, 'Y₁', O1[0] - 115, O1[1] + 65))
    # axes frame 2 (link2 dir: angle -75 deg in screen (105 deg math);
    # right-handed: Y at screen angle X-90 = -165)
    b.append(axhead(O2[0], O2[1], -75, RED, 'X₂', O2[0] - 60, O2[1] - 84))
    b.append(axhead(O2[0], O2[1], -165, GREEN, 'Y₂', O2[0] - 63, O2[1] - 25))
    # Z out-of-page symbols
    b.append(zsym(O0[0], O0[1] - 26, 'Z₀'))
    b.append(zsym(O1[0], O1[1] - 26, 'Z₁'))
    b.append(zsym(O2[0], O2[1] - 26, 'Z₂'))
    # joints
    b.append(circle(O0[0], O0[1], 7, DARK))
    b.append(circle(O1[0], O1[1], 7, DARK))
    b.append(circle(O2[0], O2[1], 7, DARK))
    # joint angle arcs (screen coords: theta1 from 0 to -45 deg)
    b.append(arc(O0[0], O0[1], 58, 0, -45))
    b.append(txt(O0[0] + 74, O0[1] - 40, 'θ₁', 17, 'bold', BLUE))
    b.append(arc(O1[0], O1[1], 52, -45, -75))
    b.append(txt(O1[0] + 52, O1[1] - 66, 'θ₂', 17, 'bold', BLUE))
    # dimension a1 along link1, offset to upper-left side
    import math as _m
    a1s = (150 + 0.12 * 141.4 - 21.2, 500 - 0.12 * 141.4 - 21.2)
    a1e = (150 + 0.92 * 141.4 - 21.2, 500 - 0.92 * 141.4 - 21.2)
    b.append(dim(a1s[0], a1s[1], a1e[0], a1e[1]))
    b.append(txt(196, 438, 'a₁ = l₁', 15, 'bold', GRAY))
    # dimension a2 along link2, offset to right side
    a2s = (291 - 0.12 * 44 + 27, 359 - 0.12 * 164.2 - 7.2)
    a2e = (247 - 0.85 * 44 + 27, 195 - 0.85 * 164.2 - 7.2)
    b.append(dim(a2s[0], a2s[1], a2e[0], a2e[1]))
    b.append(txt(300, 200, 'a₂ = l₂', 15, 'bold', GRAY))
    # legend
    b.append(rect(30, 70, 400, 74, '#ffffff', LINE, 1.5, 10))
    b.append(txt(52, 96, 'X 轴:红色', 13.5, 'bold', RED, 'start'))
    b.append(txt(52, 118, 'Y 轴:绿色', 13.5, 'bold', GREEN, 'start'))
    b.append(txt(180, 96, 'Z 轴:蓝色 ⊙(垂直纸面向外)', 13.5, 'bold', BLUE, 'start'))
    b.append(txt(180, 118, '原点在关节中心 · 右手系 X × Y = Z', 13.5, 'normal', GRAY, 'start'))
    # note
    b.append(rect(560, 600, 370, 84, '#fff8ec', '#d9a53f', 1.5, 10))
    b.append(txt(745, 626, '本例:Z₀ ∥ Z₁ ∥ Z₂ → α₁ = α₂ = 0、d₁ = d₂ = 0', 13, 'bold', '#8a6a1f'))
    b.append(txt(745, 650, 'a₁ = l₁、a₂ = l₂(沿 X 轴的距离)', 13, 'normal', '#8a6a1f'))
    b.append(txt(745, 672, 'θ₁、θ₂ 为关节变量(绕 Z 轴的转角)', 13, 'normal', '#8a6a1f'))
    return svg(960, 700, ''.join(b))

# ============================================================ F3 dh_params_4
def dh_params_4():
    b = []
    b.append(title(0, 880, '四个 D-H 参数 (The four D-H parameters)', 20))
    # Z_{i-1} vertical at x=200
    b.append(line(200, 90, 200, 490, BLUE, 3.2, 'a3f6dff'))
    b.append(txt(184, 76, 'Z_{i−1}', 16, 'bold', BLUE, 'start'))
    # O_{i-1}, O_i
    b.append(circle(200, 230, 6, DARK))
    b.append(circle(600, 370, 6, DARK))
    b.append(txt(200, 208, 'O_{i−1}', 14, 'normal', GRAY))
    # X_{i-1} oblique (out-of-page hint), down-left
    b.append(line(200, 230, 156, 306, RED, 3, 'ad64550'))
    b.append(txt(128, 322, 'X_{i−1}', 15, 'bold', RED))
    # X_i horizontal right
    b.append(line(600, 370, 718, 370, RED, 3, 'ad64550'))
    b.append(txt(726, 364, 'X_i', 15, 'bold', RED))
    # theta_i arc from X_{i-1} dir to X_i dir
    b.append(arc(200, 230, 46, 120, 10))
    b.append(txt(192, 196, 'θ_i', 17, 'bold', BLUE))
    # d_i dimension along Z_{i-1}
    b.append(dim(140, 230, 140, 370))
    b.append(txt(122, 305, 'd_i', 16, 'bold', GRAY))
    b.append(txt(112, 345, '沿 Z_{i−1}', 12, 'normal', GRAY))
    # a_i dimension between the axes at height of O_i, offset below X_i
    b.append(dim(200, 406, 600, 406))
    b.append(txt(400, 428, 'a_i', 16, 'bold', GRAY))
    b.append(txt(400, 448, '沿 X_i(公垂线 common normal)', 12, 'normal', GRAY))
    # alpha_i: dashed reference vertical through O_i, Z_i tilted 20 deg
    b.append(line(600, 370, 600, 495, '#b8bfcf', 1.8, dash='6,5'))
    b.append(line(600 - 84 * 0.342, 370 - 84 * 0.94, 600 + 92 * 0.342, 370 + 92 * 0.94, BLUE, 3.2, 'a3f6dff'))
    b.append(txt(646, 296, 'Z_i', 16, 'bold', BLUE))
    b.append(arc(600, 370, 44, 90, 70))
    b.append(txt(652, 408, 'α_i', 17, 'bold', BLUE))
    b.append(txt(652, 430, '绕 X_i', 12, 'normal', GRAY))
    # note
    b.append(rect(30, 486, 520, 62, '#fff8ec', '#d9a53f', 1.5, 10))
    b.append(txt(290, 510, 'θ_i:绕 Z_{i−1},从 X_{i−1} 转到 X_i(关节角/关节变量)', 12.5, 'normal', '#8a6a1f'))
    b.append(txt(290, 532, 'd_i:沿 Z_{i−1},X_{i−1} 到 X_i 的距离(关节偏移)', 12.5, 'normal', '#8a6a1f'))
    return svg(880, 560, ''.join(b))

# ============================================================ F4 ik_two_solutions
def ik_two_solutions():
    b = []
    b.append(title(0, 760, 'IK 解不唯一:同一末端位姿对应多组关节角', 17))
    O = (140, 340); P = (470, 210)
    e_up = (330, 338); e_dn = (280, 212)
    # dashed elbow-down config
    b.append(line(O[0], O[1], e_dn[0], e_dn[1], '#9aa4b8', 3.5, dash='8,6'))
    b.append(line(e_dn[0], e_dn[1], P[0], P[1], '#9aa4b8', 3.5, dash='8,6'))
    b.append(circle(e_dn[0], e_dn[1], 7, '#9aa4b8'))
    # solid elbow-up config
    b.append(line(O[0], O[1], e_up[0], e_up[1], DARK, 4))
    b.append(line(e_up[0], e_up[1], P[0], P[1], DARK, 4))
    b.append(circle(e_up[0], e_up[1], 7, DARK))
    # base
    b.append(rect(105, 340, 70, 34, '#eceff5', '#8a93a8', 1.5, 4))
    b.append(hatch(105, 340, 70, 34))
    b.append(circle(O[0], O[1], 7, DARK))
    # target P with cross
    b.append(circle(P[0], P[1], 6, RED))
    b.append(line(P[0] - 12, P[1], P[0] + 12, P[1], RED, 2))
    b.append(line(P[0], P[1] - 12, P[0], P[1] + 12, RED, 2))
    b.append(txt(500, 196, 'same pose P 同一位姿', 13.5, 'bold', RED, 'start'))
    b.append(txt(300, 322, 'elbow up 肘上', 14, 'bold'))
    b.append(txt(262, 232, 'elbow down 肘下', 14, 'bold'))
    b.append(txt(340, 385, '两组关节角 (θ₁, θ₂) → 同一个 (x, y)', 13, 'normal', GRAY))
    return svg(760, 420, ''.join(b))

# ============================================================ F5 jacobian_map
def jacobian_map():
    b = []
    b.append(title(0, 860, '雅可比:关节速度 → 任务速度 (Jacobian: joint → task velocities)', 17))
    b.append(rect(20, 90, 250, 120))
    b.append(txt(145, 128, 'Joint velocities', 17, 'bold', BLUE))
    b.append(txt(145, 152, '关节速度', 14.5))
    b.append(txt(145, 178, 'q̇ (n×1)', 15, 'normal', GRAY, italic=True))
    b.append(rect(350, 90, 160, 120))
    b.append(txt(430, 130, 'J(q)', 22, 'bold', DARK))
    b.append(txt(430, 158, '雅可比矩阵', 14.5))
    b.append(txt(430, 182, '(6×n)', 14, 'normal', GRAY, italic=True))
    b.append(rect(600, 90, 240, 120))
    b.append(txt(720, 124, 'Task velocities', 17, 'bold', GREEN))
    b.append(txt(720, 148, '任务速度', 14.5))
    b.append(txt(720, 172, 'Ẏ = (ẋ, ẏ, ż, ωₓ, ω_y, ω_z)ᵀ', 13.5, 'normal', GRAY, italic=True))
    b.append(arrow(270, 150, 344, 150, DARK, 3))
    b.append(arrow(510, 150, 594, 150, DARK, 3))
    b.append(note(0, 250, 'J = ∂f(q)/∂q — 随构型变化 (a function of q),不是常数矩阵 (not constant)',
                  860, 13.5))
    return svg(860, 300, ''.join(b))

# ============================================================ F6 planar2_arm
def planar2_arm():
    b = []
    b.append(title(0, 640, '两连杆平面机械臂 (2-link planar arm)', 19))
    O = (110, 400); O1 = (219, 270); P = (144, 140)
    b.append(rect(70, 400, 80, 35, '#eceff5', '#8a93a8', 1.5, 4))
    b.append(hatch(70, 400, 80, 35))
    b.append(line(O[0], O[1], O1[0], O1[1], '#5a6478', 6.5))
    b.append(line(O1[0], O1[1], P[0], P[1], '#5a6478', 6.5))
    b.append(circle(O[0], O[1], 7, DARK)); b.append(circle(O1[0], O1[1], 7, DARK))
    b.append('<polygon points="%g,%g %g,%g %g,%g" fill="%s"/>'
             % (P[0], P[1], P[0] - 5, P[1] + 14, P[0] + 9, P[1] + 11, DARK))
    b.append(arc(110, 400, 46, 0, -50))
    b.append(txt(178, 380, 'θ₁', 17, 'bold', BLUE))
    b.append(arc(219, 270, 40, -50, -120))
    b.append(txt(236, 212, 'θ₂', 17, 'bold', BLUE))
    b.append(txt(148, 322, 'l₁', 16, 'bold', GRAY))
    b.append(txt(198, 192, 'l₂', 16, 'bold', GRAY))
    b.append(txt(158, 116, 'P (x, y)', 14, 'bold', RED))
    b.append(txt(320, 452, '两关节均为绕 Z 轴(垂直纸面)的转动关节 revolute joints about Z', 13, 'normal', GRAY))
    return svg(640, 480, ''.join(b))

# ============================================================ F7 lagrange_spring
def lagrange_spring():
    b = []
    b.append(title(0, 760, '单自由度系统 (1-DOF system):质量-弹簧 mass–spring', 17))
    b.append(rect(40, 70, 32, 180, '#eceff5', '#8a93a8', 1.5, 3))
    b.append(hatch(40, 70, 32, 180, gap=14))
    pts = [(72, 160), (92, 132), (115, 188), (138, 132), (161, 188), (184, 132), (207, 160), (232, 160)]
    b.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.5"/>'
             % (' '.join('%g,%g' % p for p in pts), DARK))
    b.append(txt(150, 118, 'k(弹簧刚度)', 13.5, 'normal', GRAY))
    b.append(rect(232, 116, 88, 88, '#dbe4ff', BLUE, 2, 8))
    b.append(txt(276, 166, 'm', 19, 'bold'))
    b.append(arrow(320, 160, 408, 160, DARK, 3))
    b.append(txt(416, 152, 'F', 17, 'bold'))
    b.append(line(40, 272, 700, 272, '#b8bfcf', 1.6, dash='7,5'))
    b.append(arrow(72, 268, 268, 268, GRAY, 2.2))
    b.append(txt(170, 292, 'x(位移 displacement)', 13.5, 'normal', GRAY))
    b.append(txt(580, 92, 'K = ½ m ẋ² (动能)', 15, 'bold', DARK))
    b.append(txt(580, 116, 'P = ½ k x² (势能)', 15, 'bold', DARK))
    b.append(txt(580, 140, 'L = K − P (拉格朗日量)', 15, 'bold', DARK))
    b.append(txt(580, 172, 'd/dt(∂L/∂ẋ) − ∂L/∂x = F', 15, 'bold', BLUE))
    b.append(txt(580, 196, '⇒ m ẍ + k x = F (力-加速度关系)', 15, 'bold', GREEN))
    return svg(760, 320, ''.join(b))

# ============================================================ F8 pid_block
def pid_block():
    b = []
    b.append(title(0, 980, 'PID 反馈控制 (PID feedback control)', 19))
    # reference
    b.append(line(60, 120, 124, 148, DARK, 2.5, 'ad'))
    b.append(txt(64, 108, 'q_d 期望位置', 13.5, 'bold', BLUE, 'start'))
    # sum node
    b.append(circle(140, 150, 16, '#ffffff', DARK, 2.5))
    b.append(txt(140, 144, '+', 17, 'bold'))
    b.append(txt(140, 168, '−', 17, 'bold'))
    # error
    b.append(arrow(156, 150, 244, 150, DARK, 2.5))
    b.append(txt(200, 136, 'e', 15, 'bold', RED))
    b.append(txt(200, 174, 'e = q_d − q(跟踪误差)', 12, 'normal', GRAY))
    # PID box
    b.append(rect(250, 112, 180, 76))
    b.append(txt(340, 140, 'PID Controller', 15.5, 'bold'))
    b.append(txt(340, 160, 'PID 控制器', 13.5, 'normal', GRAY))
    b.append(txt(340, 178, 'τ = k_P e + k_I ∫e dt + k_D ė', 12.5, 'normal', DARK))
    # tau
    b.append(arrow(430, 150, 514, 150, DARK, 2.5))
    b.append(txt(472, 136, 'τ 力矩', 14, 'bold'))
    # robot
    b.append(rect(520, 112, 180, 76, '#eafaf2', GREEN, 2))
    b.append(txt(610, 140, 'Robot Arms + Motors', 15, 'bold', GREEN))
    b.append(txt(610, 160, '机器人/电机', 13.5, 'normal', GRAY))
    b.append(txt(610, 178, '受控对象 plant', 12.5, 'normal', GRAY))
    # output
    b.append(arrow(700, 150, 792, 150, DARK, 2.5))
    b.append(txt(800, 132, 'q 实际位置', 13.5, 'bold', DARK, 'start'))
    # feedback
    b.append(line(756, 150, 756, 330, DARK, 2.2))
    b.append(arrow(756, 330, 156, 330, DARK, 2.2, 'ad'))
    b.append(arrow(140, 314, 140, 166, DARK, 2.2, 'ad'))
    b.append(rect(410, 300, 150, 60, '#fdf3f6', RED, 1.8, 10))
    b.append(txt(485, 324, 'Sensors 传感器', 13.5, 'bold', RED))
    b.append(txt(485, 346, '编码器/测速计', 12, 'normal', GRAY))
    b.append(txt(490, 388, 'P:当前误差 · I:累计误差(消除稳态误差) · D:误差变化率(阻尼、抑制超调)',
                13, 'normal', GRAY))
    return svg(980, 420, ''.join(b))

# ============================================================ F9 feedforward_block
def feedforward_block():
    b = []
    b.append(title(0, 980, '前馈控制 (Feedforward Control)', 19))
    b.append(txt(120, 96, 'q_d(t)', 16, 'bold', BLUE))
    b.append(txt(120, 118, '期望轨迹', 13, 'normal', GRAY))
    b.append(arrow(150, 120, 244, 120, DARK, 2.5))
    b.append(rect(250, 82, 180, 76))
    b.append(txt(340, 110, 'Feedforward', 15.5, 'bold'))
    b.append(txt(340, 130, 'Controller', 15.5, 'bold'))
    b.append(txt(340, 150, '前馈控制器(逆动力学)', 12, 'normal', GRAY))
    b.append(arrow(430, 120, 514, 120, DARK, 2.5))
    b.append(txt(472, 106, 'τ 力矩', 14, 'bold'))
    b.append(rect(520, 82, 180, 76, '#eafaf2', GREEN, 2))
    b.append(txt(610, 110, 'Robot Arms', 15, 'bold', GREEN))
    b.append(txt(610, 130, '+ Motors', 15, 'bold', GREEN))
    b.append(txt(610, 150, '机器人/电机', 12, 'normal', GRAY))
    b.append(arrow(700, 120, 792, 120, DARK, 2.5))
    b.append(txt(800, 104, 'q 实际位置', 13.5, 'bold', DARK, 'start'))
    b.append(note(0, 222, '开环 (open loop):无传感器反馈;模型参数有不确定性,且无法处理扰动(磨损、摩擦)',
                  980, 13.5))
    return svg(980, 260, ''.join(b))

# ============================================================ F10 computed_torque
def computed_torque():
    b = []
    b.append(title(0, 980, '计算力矩控制 (Computed Torque Control)', 19))
    b.append(txt(110, 86, 'q_d, q̇_d, q̈_d', 14.5, 'bold', BLUE))
    b.append(txt(110, 106, '期望轨迹+速度+加速度', 11.5, 'normal', GRAY))
    b.append(arrow(180, 105, 224, 105, DARK, 2.5))
    b.append(rect(230, 70, 270, 76))
    b.append(txt(365, 96, 'Linear Controller 线性控制器', 15, 'bold'))
    b.append(txt(365, 118, 'u = q̈_d + K_v(q̇_d − q̇) + K_p(q_d − q)', 12.5, 'normal', DARK))
    b.append(arrow(500, 105, 554, 105, DARK, 2.5))
    b.append(txt(527, 92, 'u', 15, 'bold'))
    b.append(rect(560, 60, 320, 96))
    b.append(txt(720, 86, 'Nonlinear Feedback 非线性反馈', 15, 'bold'))
    b.append(txt(720, 108, '(Computed Torque 计算力矩)', 13, 'normal', GRAY))
    b.append(txt(720, 130, 'τ = M̂(q) u + V̂(q,q̇) + Ĝ(q)', 13.5, 'normal', DARK))
    b.append(txt(720, 148, '基于机器人动力学模型抵消非线性', 11.5, 'normal', GRAY))
    b.append(arrow(720, 156, 720, 214, DARK, 2.5))
    b.append(txt(706, 192, 'τ 力矩', 14, 'bold'))
    b.append(rect(610, 220, 220, 76, '#eafaf2', GREEN, 2))
    b.append(txt(720, 248, 'Robot 机器人', 15, 'bold', GREEN))
    b.append(txt(720, 270, '输出:q, q̇', 13, 'normal', GRAY))
    # feedback q, qdot into linear controller
    b.append(line(610, 260, 140, 260, DARK, 2.2))
    b.append(arrow(140, 244, 140, 146, DARK, 2.2, 'ad'))
    b.append(txt(360, 280, 'q, q̇(反馈 feedback)', 13, 'bold', GRAY))
    b.append(note(0, 372, '模型精确时 (M̂=M, V̂=V, Ĝ=G):q̈ = u — 闭环表现为双积分环节 (double integrator)',
                  980, 13.5))
    return svg(980, 400, ''.join(b))

# ============================================================ F11 task_space_ctrl
def task_space_ctrl():
    b = []
    b.append(title(0, 1000, '任务空间控制 (Task Space Control)', 19))
    # reference
    b.append(rect(20, 82, 160, 76, '#ffffff', LINE, 2, 12))
    b.append(txt(100, 108, 'Task trajectory', 14.5, 'bold', BLUE))
    b.append(txt(100, 128, '任务轨迹', 13, 'normal', GRAY))
    b.append(txt(100, 148, 'Y_d, Ẏ_d, Ÿ_d', 13, 'normal', DARK))
    b.append(line(180, 120, 182, 120, DARK, 2.5))
    # sum node (refs minus feedback)
    b.append(circle(194, 120, 10, '#ffffff', DARK, 2))
    b.append(txt(194, 125, '−', 15, 'bold'))
    b.append(arrow(204, 120, 240, 120, DARK, 2.5))
    # linear controller
    b.append(rect(250, 85, 310, 70))
    b.append(txt(405, 110, 'Linear Controller 线性控制器', 14.5, 'bold'))
    b.append(txt(405, 132, 'U = Ÿ_d + K_v(Ẏ_d − Ẏ) + K_p(Y_d − Y)', 12.5, 'normal', DARK))
    b.append(arrow(560, 120, 604, 120, DARK, 2.5))
    b.append(txt(582, 106, 'U', 15, 'bold'))
    # nonlinear feedback
    b.append(rect(610, 85, 300, 70))
    b.append(txt(760, 110, 'Nonlinear Feedback 非线性反馈', 14.5, 'bold'))
    b.append(txt(760, 132, 'τ:q̈ = J⁻¹(U − J̇ q̇)(逆动力学)', 12.5, 'normal', DARK))
    b.append(arrow(760, 155, 760, 219, DARK, 2.5))
    b.append(txt(746, 194, 'τ 力矩', 14, 'bold'))
    # robot dynamics
    b.append(rect(250, 225, 180, 80, '#eafaf2', GREEN, 2))
    b.append(txt(340, 254, 'Robot Dynamics', 14.5, 'bold', GREEN))
    b.append(txt(340, 276, '机器人动力学', 13, 'normal', GRAY))
    b.append(txt(340, 294, 'q, q̇', 13, 'normal', DARK))
    # forward kinematics
    b.append(arrow(430, 265, 474, 265, DARK, 2.5))
    b.append(txt(452, 250, 'q, q̇', 13, 'bold', GRAY))
    b.append(rect(480, 225, 180, 80, '#eef2ff', BLUE, 2))
    b.append(txt(570, 254, 'Forward Kinematics', 14.5, 'bold', BLUE))
    b.append(txt(570, 276, '正运动学 Y = f(q)', 13, 'normal', GRAY))
    b.append(txt(570, 294, 'Y, Ẏ', 13, 'normal', DARK))
    # output
    b.append(arrow(660, 265, 744, 265, DARK, 2.5))
    b.append(txt(756, 256, 'Y, Ẏ 实际任务', 13, 'bold', DARK, 'start'))
    b.append(txt(756, 274, '位姿/速度', 13, 'bold', DARK, 'start'))
    # feedback
    b.append(line(570, 305, 570, 384, DARK, 2.2))
    b.append(arrow(570, 384, 200, 384, DARK, 2.2, 'ad'))
    b.append(arrow(194, 394, 194, 132, DARK, 2.2, 'ad'))
    b.append(txt(360, 402, 'Y, Ẏ(反馈 feedback)', 13, 'bold', GRAY))
    # note
    b.append(note(0, 432, '闭环:Ÿ_d − Ÿ + K_v(Ẏ_d − Ẏ) + K_p(Y_d − Y) = 0 → s² + K_v s + K_p = 0(K_p = ωₙ², K_v = 2ξωₙ)',
                  1000, 12.5))
    return svg(1000, 460, ''.join(b))

FIGURES = [
    ('fk_ik_map.png', fk_ik_map, 860, 300, {}),
    ('dh_frames_planar2.png', dh_frames_planar2, 960, 700, {'red': 60, 'blue': 60, 'green': 60}),
    ('dh_params_4.png', dh_params_4, 880, 560, {'red': 40, 'blue': 60}),
    ('ik_two_solutions.png', ik_two_solutions, 760, 420, {'red': 30}),
    ('jacobian_map.png', jacobian_map, 860, 300, {'blue': 20, 'green': 20}),
    ('planar2_arm.png', planar2_arm, 640, 480, {'red': 8, 'blue': 15}),
    ('lagrange_spring.png', lagrange_spring, 760, 320, {'blue': 20, 'green': 20}),
    ('pid_block.png', pid_block, 980, 420, {'red': 40, 'green': 40, 'blue': 20}),
    ('feedforward_block.png', feedforward_block, 980, 260, {'blue': 20, 'green': 40}),
    ('computed_torque.png', computed_torque, 980, 400, {'blue': 20, 'green': 40}),
    ('task_space_ctrl.png', task_space_ctrl, 1000, 460, {'red': 20, 'blue': 40, 'green': 40}),
]

def find_edge():
    for c in (os.path.join(os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
                           'Microsoft', 'Edge', 'Application', 'msedge.exe'),
              os.path.join(os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                           'Microsoft', 'Edge', 'Application', 'msedge.exe')):
        if os.path.isfile(c):
            return c
    return None

def render(edge, tmp):
    from PIL import Image
    os.makedirs(FIG, exist_ok=True)
    profile = os.path.join(tmp, 'profile')
    results = []
    for name, fn, w, h, wants in FIGURES:
        svg_path = os.path.join(FIG, name[:-4] + '.svg')
        png_path = os.path.join(FIG, name)
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(fn())
        url = 'file:///' + svg_path.replace('\\', '/').replace(' ', '%20')
        subprocess.run([edge, '--headless=new', '--disable-gpu',
                        '--user-data-dir=' + profile,
                        '--screenshot=' + png_path,
                        '--window-size=%d,%d' % (w, h),
                        '--hide-scrollbars', '--force-device-scale-factor=1',
                        '--default-background-color=FFFFFFFF', url],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        im = Image.open(png_path).convert('RGB')
        ok, msgs = True, []
        if im.size != (w, h):
            ok = False; msgs.append('size %s != (%d,%d)' % (im.size, w, h))
        px = im.load()
        if px[3, 3] != (255, 255, 255) or px[w - 4, h - 4] != (255, 255, 255):
            ok = False; msgs.append('background not white')
        counts = {'red': 0, 'blue': 0, 'green': 0, 'ink': 0}
        for y in range(0, h, 3):
            for x in range(0, w, 3):
                r, g, bl = px[x, y]
                if (r, g, bl) == (255, 255, 255):
                    continue
                counts['ink'] += 1
                if r > 150 and g < 110 and bl < 110:
                    counts['red'] += 1
                elif bl > 150 and r < 110 and g > 90 and g < 170:
                    counts['blue'] += 1
                elif g > 110 and r < 110 and bl < 130:
                    counts['green'] += 1
        frac = counts['ink'] * 9.0 / (w * h)
        if frac < 0.01 or frac > 0.75:
            ok = False; msgs.append('ink fraction %.3f' % frac)
        for col, need in wants.items():
            if counts[col] < need:
                ok = False; msgs.append('%s pixels %d < %d' % (col, counts[col], need))
        results.append((name, ok, msgs, counts['ink']))
        print('%-24s %s ink=%d %s' % (name, 'OK ' if ok else 'FAIL', counts['ink'],
                                      ('; '.join(msgs) if msgs else '')))
    return all(r[1] for r in results)

def main():
    edge = find_edge()
    if not edge:
        print('no Edge found'); sys.exit(2)
    tmp = tempfile.mkdtemp()
    try:
        good = render(edge, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if good else 1)

if __name__ == '__main__':
    main()
