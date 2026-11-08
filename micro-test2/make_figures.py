"""Графики к тесту 2. Вставляет SVG в index.html между <!--FIG:id--> и <!--/FIG:id-->.
Использует Plot из ../micro-test1/make_figures.py. Запуск: python3 make_figures.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "micro-test1"))
from make_figures import Plot, figure, fmt, rich  # noqa: E402

PAGE = HERE / "index.html"
FIGS = {}


def fig(fid):
    def deco(fn):
        FIGS[fid] = fn
        return fn
    return deco


@fig("A6")
def _():
    p = Plot("t2A6", 8.6, 8.6, xl="s_{J}", yl="s_{T}")
    p.line([(0, 1), (7, 8), (8, 8)], "c-d")
    p.line([(0.5, 0), (4.5, 8)], "c-mc")
    p.guide(2, 3); p.point(2, 3)
    p.xt(0.5, "0,5"); p.xt(2); p.xt(4.5, "4,5"); p.xt(7); p.yt(1); p.yt(3); p.yt(8)
    p.text(5.6, 5.3, "BR_{T}: s_{T}=1+s_{J}"); p.text(4.4, 7.4, "BR_{J}", "end")
    p.text(2, 3, "NE (2; 3)", dx=8, dy=14, cls="tm")
    return figure([p.svg("Лучшие ответы Тома и Джерри пересекаются в точке sJ=2, sT=3")],
                  "Синяя — лучший ответ Тома (\\(s_T=1+s_J\\), упирается в 8), красная — лучший ответ Джерри (\\(s_J=\\frac{1+s_T}2\\), от 0,5 до 4,5). Пересечение — равновесие.")


@fig("A7")
def _():
    W, H = 360, 230
    nodes = {"r": (180, 30), "x": (80, 110), "y": (220, 110)}
    leaves = [("x", 40, "8, 10", "A"), ("x", 120, "2, 0", "B"), ("y", 180, "12, 0", "A"), ("y", 260, "6, 10", "B")]
    el = []
    for k, (lx, txt) in {"x": (80, "x"), "y": (220, "y")}.items():
        x0, y0 = nodes["r"]; el.append(f'<line class="ax" x1="{x0}" y1="{y0}" x2="{lx}" y2="110"/>')
        el.append(f'<text class="t" x="{(x0 + lx) / 2 + (-10 if k == "x" else 6)}" y="{(y0 + 110) / 2}" text-anchor="{"end" if k == "x" else "start"}">{txt}</text>')
    el.append('<line class="ax" x1="180" y1="30" x2="320" y2="110"/>')
    el.append('<text class="t" x="258" y="64">z</text>')
    el.append('<text class="t" x="320" y="130" text-anchor="middle">8, 5</text>')
    for parent, lx, pay, act in leaves:
        x0, y0 = nodes[parent]
        el.append(f'<line class="ax" x1="{x0}" y1="{y0}" x2="{lx}" y2="185"/>')
        el.append(f'<text class="tm" x="{(x0 + lx) / 2 + (-8 if lx < x0 else 8)}" y="{(y0 + 185) / 2 + 4}" text-anchor="{"end" if lx < x0 else "start"}">{act}</text>')
        el.append(f'<text class="t" x="{lx}" y="205" text-anchor="middle">{pay}</text>')
    for k, (x, y) in nodes.items():
        el.append(f'<circle class="pt" cx="{x}" cy="{y}" r="5"/>')
    el.append('<text class="tm" x="192" y="26">игрок 1</text>')
    el.append('<text class="tm" x="68" y="106" text-anchor="end">игрок 2</text>')
    el.append('<text class="tm" x="232" y="106">игрок 2</text>')
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Дерево игры: игрок 1 выбирает x, y или z, после x и y ходит игрок 2" '
           f'xmlns="http://www.w3.org/2000/svg">' + "".join(el) + "</svg>")
    return figure([svg], "Корень — игрок 1. После x и после y у игрока 2 два разных узла (он видит выбор), z сразу заканчивает игру. На листьях выигрыши (игрок 1, игрок 2).")


@fig("B1")
def _():
    p = Plot("t2B1", 21, 21, xl="q_{1}", yl="q_{2}")
    p.line([(0, 20), (10, 0)], "c-d")
    p.line([(0, 8), (16, 0)], "c-mc")
    p.guide(8, 4); p.point(8, 4)
    p.xt(8); p.xt(10); p.xt(16); p.yt(4); p.yt(8); p.yt(20)
    p.text(4.2, 13, "BR_{1}"); p.text(13, 2.2, "BR_{2}")
    p.text(8, 4, "NE (8; 4)", dx=8, dy=-8, cls="tm")
    return figure([p.svg("Лучшие ответы Курно: BR1 от 20 на оси q2 до 10 на оси q1, BR2 от 8 до 16, пересечение (8; 4)")],
                  "\\(q_1\\) по горизонтали, \\(q_2\\) по вертикали. \\(BR_1\\) пересекает оси в точках \\(q_2=20\\) и \\(q_1=10\\) (монопольный объём фирмы 1), \\(BR_2\\) — в точках \\(q_2=8\\) и \\(q_1=16\\). Пересечение — равновесие (8; 4).")


@fig("B5")
def _():
    p = Plot("t2B5", 10.8, 10.8, xl="q_{1}", yl="q_{2}")
    p.line([(0, 10), (2.5, 0)], "c-d")
    p.line([(0, 2.5), (10, 0)], "c-mc")
    p.guide(2, 2); p.point(2, 2)
    p.xt(2.5, "2,5"); p.xt(10); p.yt(2.5, "2,5"); p.yt(10)
    p.text(1.6, 7.4, "BR_{1}"); p.text(7.5, 1.3, "BR_{2}")
    p.text(2, 2, "NE (2; 2)", dx=10, dy=-10, cls="tm")
    return figure([p.svg("Лучшие ответы: BR1 от 10 на оси q2 до 2,5 на оси q1, BR2 симметрично, пересечение (2; 2)")],
                  "\\(BR_1\\): \\(q_1=\\frac{10-q_2}4\\), пересечения с осями 2,5 (по \\(q_1\\)) и 10 (по \\(q_2\\)). \\(BR_2\\) симметрична. Пересечение — (2; 2).")


@fig("B6")
def _():
    p = Plot("t2B6", 9, 9, xl="p_{1}", yl="p_{2}")
    p.line([(4.5, 0), (6.75, 9)], "c-d")
    p.line([(0, 4.5), (9, 6.75)], "c-mc")
    p.guide(6, 6); p.point(6, 6)
    p.xt(4.5, "4,5"); p.xt(6); p.yt(4.5, "4,5"); p.yt(6)
    p.text(6.5, 8.4, "BR_{1}", "end"); p.text(8.8, 7.1, "BR_{2}", "end")
    p.text(6, 6, "NE (6; 6)", dx=10, dy=14, cls="tm")
    return figure([p.svg("Лучшие ответы по ценам растут: BR1 от 4,5 на оси p1, BR2 от 4,5 на оси p2, пересечение (6; 6)")],
                  "В ценовой конкуренции лучшие ответы растут: соперник дороже — и мне можно дороже. \\(BR_1\\) начинается с 4,5 на оси \\(p_1\\), \\(BR_2\\) — с 4,5 на оси \\(p_2\\). Пересечение (6; 6).")


@fig("B7")
def _():
    p = Plot("t2B7", 13, 40, xl="q_{1}", yl="π_{1}")
    p.curve(lambda q: (17 - q) / 2 * q, 0, 7, "c-d")
    p.curve(lambda q: (12 - q) * q, 7, 12, "c-mc")
    p.guide(7, 35); p.point(7, 35)
    p.xt(6); p.xt(7); p.xt(12); p.yt(35)
    p.text(2.2, 22, "фирма 2 производит"); p.text(8.4, 30, "фирма 2 = 0")
    return figure([p.svg("Прибыль лидера от q1 при c=5: растёт до 7, потом падает, максимум 35 при q1=7")],
                  "Слева от 7 фирма 2 производит, и прибыль лидера растёт. Справа фирма 2 молчит, лидер — монополист, но после 6 прибыль уже падает. Максимум в точке стыка \\(q_1=7\\).")


@fig("B8")
def _():
    p = Plot("t2B8", 13, 40, xl="q_{1}", yl="π_{1}")
    p.curve(lambda q: (12 - q) / 2 * q, 0, 8, "c-d")
    p.curve(lambda q: (12 - q) * q, 8, 12, "c-mc")
    p.line([(8, 16), (8, 32)], "c-jump")
    p.guide(6, 18); p.guide(8, 32); p.point(6, 18); p.point(8, 32)
    p.point(8, 16, hollow=True)
    p.xt(6); p.xt(8); p.xt(12); p.yt(18); p.yt(32)
    p.text(1, 10, "пустить фирму 2"); p.text(8.4, 34, "не пустить")
    return figure([p.svg("Прибыль лидера при F=4: 18 если пустить, 32 при q1=8 если не пустить")],
                  "До \\(q_1=8\\) фирма 2 входит и прибыль лидера не выше 18 (при \\(q_1=6\\)). С \\(q_1=8\\) вход невыгоден, прибыль скачком растёт до 32. Лидер выбирает 8.")


@fig("B9")
def _():
    W, H = 360, 110
    x0, x1, y = 30, 330, 60
    xh = x0 + (x1 - x0) * 3 / 8
    el = [
        f'<rect class="a-cs-r" x="{x0}" y="{y - 12}" width="{xh - x0}" height="24"/>',
        f'<rect class="a-ps-r" x="{xh}" y="{y - 12}" width="{x1 - xh}" height="24"/>',
        f'<line class="ax" x1="{x0}" y1="{y}" x2="{x1}" y2="{y}"/>',
        f'<circle class="pt" cx="{x0}" cy="{y}" r="5"/>', f'<circle class="pt" cx="{x1}" cy="{y}" r="5"/>',
        f'<line class="c-jump-l" x1="{xh}" y1="{y - 22}" x2="{xh}" y2="{y + 22}"/>',
        f'<text class="t" x="{x0}" y="{y - 20}" text-anchor="middle">фирма 1</text>',
        f'<text class="t" x="{x1}" y="{y - 20}" text-anchor="middle">фирма 2</text>',
        f'<text class="tm" x="{xh}" y="{y + 38}" text-anchor="middle">{rich("x̂ = 3/8")}</text>',
        f'<text class="tk" x="{x0}" y="{y + 38}" text-anchor="middle">0</text>',
        f'<text class="tk" x="{x1}" y="{y + 38}" text-anchor="middle">1</text>',
        f'<text class="tl" x="{(x0 + xh) / 2}" y="{y + 4}" text-anchor="middle">к фирме 1</text>',
        f'<text class="tl" x="{(xh + x1) / 2}" y="{y + 4}" text-anchor="middle">к фирме 2</text>',
    ]
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Улица от 0 до 1, безразличный покупатель в точке 3/8" '
           f'xmlns="http://www.w3.org/2000/svg">' + "".join(el) + "</svg>")
    return figure([svg], "Покупатели левее \\(\\hat x\\) идут к фирме 1, правее — к фирме 2. В равновесии B.9 \\(\\hat x=3/8\\): лидер дороже и получает меньшую часть улицы.")


def main():
    html = PAGE.read_text(encoding="utf-8")
    for fid, fn in FIGS.items():
        pat = re.compile(rf"<!--FIG:{fid}-->.*?<!--/FIG:{fid}-->", re.S)
        if not pat.search(html):
            raise SystemExit(f"marker for {fid} not found")
        html = pat.sub(lambda m: f"<!--FIG:{fid}-->{fn()}<!--/FIG:{fid}-->", html)
    PAGE.write_text(html, encoding="utf-8")
    print(f"inserted {len(FIGS)} figures")


if __name__ == "__main__":
    main()
