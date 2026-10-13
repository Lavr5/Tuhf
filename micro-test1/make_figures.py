"""Рисует графики к задачам банка и вставляет их в index.html.

Каждый график стоит в index.html между маркерами <!--FIG:id--> и <!--/FIG:id-->.
Запуск: python3 make_figures.py  (перезаписывает содержимое между маркерами).
Цвета берутся из CSS-токенов страницы (классы .c-*, .a-* в <style>).
"""
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "index.html"


def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def rich(s):
    """'p_{w}' -> p с нижним индексом w, 'q^{m}' -> верхний индекс."""
    out, i, shift = [], 0, 0
    pending_reset = 0
    while i < len(s):
        if s[i] in "_^" and i + 1 < len(s) and s[i + 1] == "{":
            j = s.index("}", i)
            inner = s[i + 2:j]
            d = 3.5 if s[i] == "_" else -5
            dy = d - shift
            out.append(f'<tspan dy="{fmt(dy)}" font-size="9">{inner}</tspan>')
            shift = d
            i = j + 1
        else:
            j = i
            while j < len(s) and not (s[j] in "_^" and j + 1 < len(s) and s[j + 1] == "{"):
                j += 1
            chunk = s[i:j]
            if shift:
                out.append(f'<tspan dy="{fmt(-shift)}">{chunk}</tspan>')
                shift = 0
            else:
                out.append(chunk)
            i = j
    return "".join(out)


class Plot:
    def __init__(self, fid, xmax, ymax, xmin=0, ymin=0, w=360, h=250, xl="q", yl="p",
                 ml=40, mr=26, mt=20, mb=30):
        self.fid, self.x0, self.x1, self.y0, self.y1 = fid, xmin, xmax, ymin, ymax
        self.w, self.h, self.ml, self.mr, self.mt, self.mb = w, h, ml, mr, mt, mb
        self.xl, self.yl = xl, yl
        self.back, self.mid, self.front = [], [], []

    # coordinates
    def sx(self, x):
        return self.ml + (x - self.x0) / (self.x1 - self.x0) * (self.w - self.ml - self.mr)

    def sy(self, y):
        return self.h - self.mb - (y - self.y0) / (self.y1 - self.y0) * (self.h - self.mt - self.mb)

    def pts(self, xy):
        return " ".join(f"{fmt(self.sx(x))},{fmt(self.sy(y))}" for x, y in xy)

    @staticmethod
    def sample(f, a, b, n=160):
        return [(a + (b - a) * k / n, f(a + (b - a) * k / n)) for k in range(n + 1)]

    # marks
    def curve(self, f, a, b, cls, n=160):
        self.mid.append(f'<polyline class="{cls}" points="{self.pts(self.sample(f, a, b, n))}"/>')

    def line(self, xy, cls):
        self.mid.append(f'<polyline class="{cls}" points="{self.pts(xy)}"/>')

    def steps(self, segs, cls):
        """segs: [(x_from, x_to, y), ...] — ступенчатая функция с вертикальными переходами."""
        xy = []
        for a, b, y in segs:
            xy += [(a, y), (b, y)]
        self.line(xy, cls)

    def poly(self, xy, cls):
        self.back.append(f'<polygon class="{cls}" points="{self.pts(xy)}"/>')

    def between(self, top, bot, a, b, cls, n=120):
        up = self.sample(top, a, b, n)
        lo = self.sample(bot, a, b, n)[::-1]
        self.poly(up + lo, cls)

    def rect(self, a, b, y_lo, y_hi, cls):
        self.poly([(a, y_lo), (b, y_lo), (b, y_hi), (a, y_hi)], cls)

    def band(self, a, b, cls="a-hi"):
        self.poly([(a, self.y0), (b, self.y0), (b, self.y1), (a, self.y1)], cls)

    def guide(self, x, y, to_x=True, to_y=True):
        if to_x:
            self.back.append(f'<line class="guide" x1="{fmt(self.sx(x))}" y1="{fmt(self.sy(y))}" x2="{fmt(self.sx(x))}" y2="{fmt(self.sy(self.y0))}"/>')
        if to_y:
            self.back.append(f'<line class="guide" x1="{fmt(self.sx(x))}" y1="{fmt(self.sy(y))}" x2="{fmt(self.sx(self.x0))}" y2="{fmt(self.sy(y))}"/>')

    def point(self, x, y, hollow=False):
        cls = "pt-open" if hollow else "pt"
        self.front.append(f'<circle class="{cls}" cx="{fmt(self.sx(x))}" cy="{fmt(self.sy(y))}" r="4"/>')

    def text(self, x, y, s, anchor="start", dx=0, dy=0, cls="t"):
        self.front.append(
            f'<text class="{cls}" x="{fmt(self.sx(x) + dx)}" y="{fmt(self.sy(y) + dy)}" text-anchor="{anchor}">{rich(s)}</text>')

    def leader(self, x1, y1, x2, y2):
        self.front.append(f'<line class="leader" x1="{fmt(self.sx(x1))}" y1="{fmt(self.sy(y1))}" x2="{fmt(self.sx(x2))}" y2="{fmt(self.sy(y2))}"/>')

    def xt(self, x, label=None):
        X, Y = self.sx(x), self.sy(self.y0)
        self.front.append(f'<line class="ax" x1="{fmt(X)}" y1="{fmt(Y)}" x2="{fmt(X)}" y2="{fmt(Y + 4)}"/>')
        self.front.append(f'<text class="tk" x="{fmt(X)}" y="{fmt(Y + 16)}" text-anchor="middle">{rich(label if label is not None else fmt(x).replace(".", ","))}</text>')

    def yt(self, y, label=None):
        X, Y = self.sx(self.x0), self.sy(y)
        self.front.append(f'<line class="ax" x1="{fmt(X - 4)}" y1="{fmt(Y)}" x2="{fmt(X)}" y2="{fmt(Y)}"/>')
        self.front.append(f'<text class="tk" x="{fmt(X - 7)}" y="{fmt(Y + 4)}" text-anchor="end">{rich(label if label is not None else fmt(y).replace(".", ","))}</text>')

    def svg(self, aria):
        X0, Y0 = self.sx(self.x0), self.sy(self.y0)
        X1, Y1 = self.w - self.mr + 12, self.mt - 10
        cid = f"clip-{self.fid}"
        axes = [
            f'<line class="ax" x1="{fmt(X0)}" y1="{fmt(Y0)}" x2="{fmt(X1)}" y2="{fmt(Y0)}"/>',
            f'<polygon class="ax-head" points="{fmt(X1 + 6)},{fmt(Y0)} {fmt(X1)},{fmt(Y0 - 3.5)} {fmt(X1)},{fmt(Y0 + 3.5)}"/>',
            f'<line class="ax" x1="{fmt(X0)}" y1="{fmt(Y0)}" x2="{fmt(X0)}" y2="{fmt(Y1)}"/>',
            f'<polygon class="ax-head" points="{fmt(X0)},{fmt(Y1 - 6)} {fmt(X0 - 3.5)},{fmt(Y1)} {fmt(X0 + 3.5)},{fmt(Y1)}"/>',
            f'<text class="axl" x="{fmt(X1 + 4)}" y="{fmt(Y0 + 17)}" text-anchor="end">{rich(self.xl)}</text>',
            f'<text class="axl" x="{fmt(X0 + 8)}" y="{fmt(Y1 - 1)}">{rich(self.yl)}</text>',
        ]
        clip = (f'<clipPath id="{cid}"><rect x="{fmt(X0)}" y="{fmt(self.sy(self.y1))}" '
                f'width="{fmt(self.sx(self.x1) - X0)}" height="{fmt(Y0 - self.sy(self.y1))}"/></clipPath>')
        body = (f'<defs>{clip}</defs><g clip-path="url(#{cid})">' + "".join(self.back) + "".join(self.mid)
                + "</g>" + "".join(axes) + "".join(self.front))
        return (f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{aria}" '
                f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


def figure(svgs, caption):
    inner = "".join(svgs)
    if len(svgs) > 1:
        inner = f'<div class="panels">{inner}</div>'
    return f'<figure class="fig">{inner}<figcaption>{caption}</figcaption></figure>'


FIGS = {}


def fig(fid):
    def deco(fn):
        FIGS[fid] = fn
        return fn
    return deco


# ---------------- Part A ----------------

@fig("A1a")
def _():
    p = Plot("A1a", 2.7, 15)
    p.curve(lambda q: 4 / (3 * q) + 2 * q * q / 3, 0.09, 2.7, "c-ac")
    p.curve(lambda q: 2 * q * q, 0, 1, "c-mc thin")
    p.curve(lambda q: 2 * q * q, 1, 2.7, "c-mc bold")
    p.front.append(f'<polyline class="c-mc bold" points="{p.pts([(0, 0), (0, 2)])}"/>')
    p.line([(0, 2), (1, 2)], "c-jump")
    p.guide(1, 2, to_y=False)
    p.point(0, 2); p.point(1, 2)
    p.xt(1, "q_{s}=1"); p.yt(2, "p_{s}=2"); p.yt(8); p.xt(2)
    p.text(2.42, 13.2, "MC", "end"); p.text(2.65, 5.6, "AC", "end")
    p.text(1.75, 9.8, "s(p)", "start"); p.text(0.18, 0.7, "q = 0", "start", cls="tm")
    return figure([p.svg("Предложение фирмы: ноль ниже цены 2, дальше кривая MC")],
                  "Жирная линия — предложение. При \\(p\\lt2\\) фирма выпускает 0 (отрезок на оси p), при \\(p=2\\) скачок к \\(q_s=1\\) в минимуме AC, выше идёт по \\(MC=2q^2\\). На тесте отметь \\(p_s\\), \\(q_s\\) и скачок.")


@fig("A1b")
def _():
    p = Plot("A1b", 8.6, 17.5)
    qs = (-1 + math.sqrt(33)) / 2
    p.poly([(0, 16), (2, 12), (0, 12)], "a-cs")
    p.between(lambda q: 12, lambda q: 2 * q * q, 0, 2, "a-ps")
    p.between(lambda q: 16 - 2 * q, lambda q: 2 * q * q, 2, qs, "a-dwl")
    p.curve(lambda q: 16 - 2 * q, 0, 8, "c-d")
    p.curve(lambda q: 16 - 4 * q, 0, 4, "c-mr")
    p.curve(lambda q: 2 * q * q, 0, 2.95, "c-mc")
    p.guide(2, 12); p.guide(2, 8, to_x=False)
    p.point(2, 12); p.point(2, 8); p.point(qs, 16 - 2 * qs, hollow=True)
    p.xt(2, "q^{m}=2"); p.xt(4); p.xt(8)
    p.yt(8); p.yt(12, "p^{m}=12"); p.yt(16)
    p.text(6.6, 4.4, "D"); p.text(3.75, 2.2, "MR"); p.text(3.05, 16.2, "MC")
    p.text(0.15, 12.5, "CS", cls="tl"); p.text(0.75, 10.2, "PS", cls="tl")
    p.text(3.6, 11.6, "DWL", cls="tl"); p.leader(3.55, 11.9, 2.2, 11.4)
    return figure([p.svg("Монополия: MR пересекает MC при q=2, цена 12 по спросу")],
                  "Точка \\(MR=MC\\) даёт \\(q^m=2\\), цену снимаем с кривой спроса: \\(p^m=12\\). Синий треугольник — CS, зелёная область между ценой и MC — PS, красный клин до \\(q^*\\approx2{,}37\\) — DWL.")


@fig("A2")
def _():
    p = Plot("A2", 72, 1.3)
    p.between(lambda q: 2 / math.sqrt(max(q, 1e-4)), lambda q: 0.5, 0.02, 16, "a-cs", n=300)
    p.rect(0, 16, 0.25, 0.5, "a-ps")
    p.between(lambda q: 2 / math.sqrt(q), lambda q: 0.25, 16, 64, "a-dwl")
    p.curve(lambda q: 2 / math.sqrt(q), 2.2, 72, "c-d")
    p.curve(lambda q: 1 / math.sqrt(q), 0.55, 72, "c-mr")
    p.line([(0, 0.25), (72, 0.25)], "c-mc")
    p.guide(16, 0.5); p.guide(64, 0.25, to_y=False)
    p.point(16, 0.5); p.point(16, 0.25); p.point(64, 0.25, hollow=True)
    p.xt(16); p.xt(64, "q^{*}=64")
    p.yt(0.25, "1/4"); p.yt(0.5, "1/2"); p.yt(1)
    p.text(30, 0.43, "D"); p.text(40, 0.08, "MR", cls="t"); p.text(70, 0.28, "MC", "end")
    p.text(5, 0.62, "CS", cls="tl"); p.text(5, 0.33, "PS", cls="tl"); p.text(30, 0.29, "DWL", cls="tl")
    return figure([p.svg("Монополия при D=4/p²: q=16, p=1/2, эффективный объём 64")],
                  "Спрос \\(p=2/\\sqrt q\\), \\(MR=1/\\sqrt q\\) идёт вдвое ниже. \\(MR=MC=\\frac14\\) при \\(q^m=16\\), цена \\(\\frac12\\). CS уходит вверх без ограничения по высоте, но его площадь конечна (= 8). DWL — область между спросом и MC от 16 до 64.")


@fig("A3a")
def _():
    p = Plot("A3a", 21, 13.5)
    p.curve(lambda q: 12 - q, 0, 12, "c-ind")
    p.curve(lambda q: 8 - q, 0, 8, "c-ind")
    p.curve(lambda q: 12 - q, 0, 4, "c-d bold")
    p.curve(lambda q: 10 - q / 2, 4, 20, "c-d bold")
    p.guide(4, 8)
    p.point(4, 8)
    p.xt(4); p.xt(8); p.xt(12); p.xt(20)
    p.yt(8); p.yt(10); p.yt(12)
    p.text(11.6, 1.6, "D_{1}", cls="tm"); p.text(6.8, 2.2, "D_{2}", cls="tm")
    p.text(15, 3.6, "D = D_{1}+D_{2}"); p.text(4, 8, "излом", dx=7, dy=-7, cls="tm")
    return figure([p.svg("Рыночный спрос с изломом в q=4, p=8")],
                  "Складываем количества при одной цене. Выше \\(p=8\\) покупает только первый (рыночный спрос совпадает с \\(D_1\\)), ниже — оба, и кривая становится положе. На тесте подпиши точки пересечения с осями (12 и 20) и излом (4; 8).")


@fig("A3b")
def _():
    p = Plot("A3b", 21, 13.5)
    p.rect(0, 8, 2, 6, "a-ps")
    p.curve(lambda q: 12 - q, 0, 4, "c-d")
    p.curve(lambda q: 10 - q / 2, 4, 20, "c-d")
    p.curve(lambda q: 12 - 2 * q, 0, 4, "c-mr")
    p.line([(4, 4), (4, 6)], "c-jump")
    p.curve(lambda q: 10 - q, 4, 10, "c-mr")
    p.line([(0, 2), (21, 2)], "c-mc")
    p.guide(8, 6); p.guide(8, 2, to_y=False)
    p.point(8, 6); p.point(8, 2); p.point(4, 8, hollow=True)
    p.xt(4); p.xt(8); p.xt(10); p.xt(20)
    p.yt(2); p.yt(6); p.yt(8); p.yt(12)
    p.text(16, 2.9, "D"); p.text(9.8, 0.5, "MR"); p.text(20.5, 2.5, "MC = 2", "end")
    p.text(0.5, 2.7, "π = 32", cls="tl"); p.text(4, 8, "π = 24", dx=7, dy=-6, cls="tm")
    return figure([p.svg("Единая цена: MR правого куска пересекает MC при q=8, цена 6")],
                  "У ломаного спроса MR рвётся в точке излома (скачок с 4 до 6 при \\(q=4\\)). MC = 2 пересекает правый кусок MR при \\(q=8\\), цена с кривой спроса 6, прибыль — зелёный прямоугольник 32. Кандидат на изломе (полый кружок) даёт только 24.")


@fig("A3c")
def _():
    a = Plot("A3c1", 13, 13, w=280, h=230)
    a.poly([(0, 12), (10, 2), (0, 2)], "a-cs")
    a.curve(lambda q: 12 - q, 0, 12, "c-d")
    a.line([(0, 2), (13, 2)], "c-mc")
    a.guide(10, 2, to_y=False); a.point(10, 2)
    a.xt(10); a.yt(2); a.yt(12)
    a.text(2.2, 4.2, "F_{1}=50", cls="tl"); a.text(12.3, 3.2, "D_{1}", "end"); a.text(12.8, 1.0, "MC", "end")
    b = Plot("A3c2", 13, 13, w=280, h=230)
    b.poly([(0, 8), (6, 2), (0, 2)], "a-cs")
    b.curve(lambda q: 8 - q, 0, 8, "c-d")
    b.line([(0, 2), (13, 2)], "c-mc")
    b.guide(6, 2, to_y=False); b.point(6, 2)
    b.xt(6); b.yt(2); b.yt(8)
    b.text(1.2, 3.4, "F_{2}=18", cls="tl"); b.text(8.2, 1.0, "D_{2}"); b.text(12.8, 1.0, "MC", "end")
    return figure([a.svg("Потребитель 1: q=10 при цене 2, взнос 50"), b.svg("Потребитель 2: q=6 при цене 2, взнос 18")],
                  "1-я степень: каждому цена за единицу \\(=MC=2\\), а взнос \\(F_i\\) равен его треугольнику CS. Слева потребитель 1, справа потребитель 2.")


@fig("A4a")
def _():
    p = Plot("A4a", 37, 11)
    p.curve(lambda q: 10 - q / 2, 0, 20, "c-ind")
    p.curve(lambda q: 8 - q / 2, 0, 16, "c-ind")
    p.curve(lambda q: 10 - q / 2, 0, 4, "c-d bold")
    p.curve(lambda q: 9 - q / 4, 4, 36, "c-d bold")
    p.guide(4, 8); p.point(4, 8)
    p.xt(4); p.xt(16); p.xt(20); p.xt(36); p.yt(8); p.yt(10)
    p.text(17.2, 0.45, "D_{1}", "end", cls="tm"); p.text(12.5, 0.6, "D_{2}", "end", cls="tm")
    p.text(25, 3.6, "D = D_{1}+D_{2}")
    return figure([p.svg("Рыночный спрос задачи A.4 с изломом в q=4, p=8")],
                  "До цены 8 покупает только первый, ниже — оба. Излом в (4; 8), пересечения с осями 10 и 36.")


@fig("A4b")
def _():
    p = Plot("A4b", 21, 11)
    p.poly([(0, 10), (10, 5), (0, 5)], "a-cs")
    p.curve(lambda q: 10 - q / 2, 0, 20, "c-d")
    p.curve(lambda q: 8 - q / 2, 0, 16, "c-ind")
    p.line([(0, 5), (21, 5)], "c-mc")
    p.guide(10, 5, to_y=False); p.point(10, 5)
    p.xt(10); p.xt(16); p.xt(20); p.yt(5); p.yt(8); p.yt(10)
    p.text(0.4, 5.45, "F = 25", cls="tl")
    p.text(18.5, 1.6, "D_{1}"); p.text(13, 0.8, "D_{2}", "end", cls="tm"); p.text(20.7, 5.5, "MC = 5", "end")
    return figure([p.svg("Тариф только для первого: p=5, взнос 25")],
                  "Обслуживаем только первого: цена за единицу \\(=MC=5\\), взнос забирает весь его излишек (синий треугольник, 25). Второму при таком взносе покупать невыгодно: его CS при \\(p=5\\) всего 9.")


@fig("A4c")
def _():
    p = Plot("A4c", 21, 11)
    p.poly([(0, 8), (4, 6), (0, 6)], "a-cs")
    p.curve(lambda q: 10 - q / 2, 0, 20, "c-d")
    p.curve(lambda q: 8 - q / 2, 0, 16, "c-d")
    p.line([(0, 6), (21, 6)], "c-pw")
    p.line([(0, 5), (21, 5)], "c-mc")
    p.guide(4, 6, to_y=False); p.guide(8, 6, to_y=False)
    p.point(4, 6); p.point(8, 6)
    p.xt(4, "q_{2}=4"); p.xt(8, "q_{1}=8"); p.yt(5); p.yt(6); p.yt(8); p.yt(10)
    p.text(6.5, 8.4, "F = CS_{2} = 4", cls="tl"); p.leader(6.4, 8.6, 1.2, 6.6)
    p.text(18.5, 1.6, "D_{1}"); p.text(14.6, 1.6, "D_{2}", "end"); p.text(20.7, 6.4, "p = 6", "end"); p.text(20.7, 4.1, "MC = 5", "end")
    return figure([p.svg("Тариф для обоих: p=6, взнос равен излишку второго, 4")],
                  "Обслуживаем обоих: цена за единицу 6, взнос равен излишку слабого (синий треугольник, 4). Первый платит тот же взнос и сохраняет часть излишка. Прибыль \\(1\\cdot12+2\\cdot4=20\\lt25\\).")


@fig("A5a")
def _():
    p = Plot("A5a", 13, 9)
    p.curve(lambda q: 8 - q, 0, 8, "c-ind")
    p.curve(lambda q: 4 - q, 0, 4, "c-ind")
    p.curve(lambda q: 8 - q, 0, 4, "c-d bold")
    p.curve(lambda q: 6 - q / 2, 4, 12, "c-d bold")
    p.guide(4, 4); p.point(4, 4)
    p.xt(4); p.xt(8); p.xt(12); p.yt(4); p.yt(6); p.yt(8)
    p.text(6.3, 0.5, "D_{1}", "end", cls="tm"); p.text(2.6, 0.5, "D_{2}", "end", cls="tm")
    p.text(8.4, 2.6, "D = D_{1}+D_{2}")
    return figure([p.svg("Рыночный спрос задачи A.5 с изломом в q=4, p=4")],
                  "Излом в (4; 4): выше цены 4 покупает только первый. Пересечения с осями 8 и 12.")


@fig("A5b")
def _():
    p = Plot("A5b", 13, 9)
    p.rect(0, 3, 2, 5, "a-ps")
    p.curve(lambda q: 8 - q, 0, 4, "c-d")
    p.curve(lambda q: 6 - q / 2, 4, 12, "c-d")
    p.curve(lambda q: 8 - 2 * q, 0, 4, "c-mr")
    p.line([(4, 0), (4, 2)], "c-jump")
    p.curve(lambda q: 6 - q, 4, 6, "c-mr")
    p.line([(0, 2), (13, 2)], "c-mc")
    p.guide(3, 5); p.guide(3, 2, to_y=False)
    p.point(3, 5); p.point(3, 2); p.point(4, 4, hollow=True)
    p.xt(3); p.xt(4); p.xt(6); p.xt(12); p.yt(2); p.yt(4); p.yt(5); p.yt(8)
    p.text(10, 1.6, "D"); p.text(5.6, 0.9, "MR", "start"); p.text(12.8, 2.35, "MC = 2", "end")
    p.text(0.6, 3.2, "π = 9", cls="tl"); p.text(4, 4, "π = 8", dx=7, dy=-6, cls="tm")
    return figure([p.svg("Единая цена в A.5: q=3, p=5, второй не обслуживается")],
                  "Левый кусок MR пересекает MC при \\(q=3\\), цена 5, прибыль 9. Правый кусок MR касается MC ровно в изломе (\\(q=4\\), \\(p=4\\), прибыль 8). Выбираем \\(p=5\\): второй потребитель не покупает.")


@fig("A5c")
def _():
    a = Plot("A5c1", 9, 9, w=280, h=230)
    a.rect(0, 3, 2, 5, "a-ps")
    a.curve(lambda q: 8 - q, 0, 8, "c-d"); a.curve(lambda q: 8 - 2 * q, 0, 4, "c-mr")
    a.line([(0, 2), (9, 2)], "c-mc")
    a.guide(3, 5); a.guide(3, 2, to_y=False); a.point(3, 5); a.point(3, 2)
    a.xt(3); a.xt(8); a.yt(2); a.yt(5); a.yt(8)
    a.text(7.1, 1.6, "D_{1}"); a.text(3.9, 0.5, "MR_{1}"); a.text(8.8, 2.4, "MC", "end")
    b = Plot("A5c2", 9, 9, w=280, h=230)
    b.rect(0, 1, 2, 3, "a-ps")
    b.curve(lambda q: 4 - q, 0, 4, "c-d"); b.curve(lambda q: 4 - 2 * q, 0, 2, "c-mr")
    b.line([(0, 2), (9, 2)], "c-mc")
    b.guide(1, 3); b.guide(1, 2, to_y=False); b.point(1, 3); b.point(1, 2)
    b.xt(1); b.xt(4); b.yt(2); b.yt(3); b.yt(4)
    b.text(3.4, 1.1, "D_{2}"); b.text(1.5, 0.3, "MR_{2}"); b.text(8.8, 2.4, "MC", "end")
    return figure([a.svg("Рынок 1: q=3, p=5"), b.svg("Рынок 2: q=1, p=3")],
                  "3-я степень: на каждом рынке своё \\(MR_i=MC\\). Рынок 1 (слева): \\(q_1=3\\), \\(p_1=5\\). Рынок 2 (справа): \\(q_2=1\\), \\(p_2=3\\). Прибыль 9 + 1 = 10.")


@fig("A6")
def _():
    p = Plot("A6", 25, 13.5, h=300)
    p.curve(lambda q: 12 - q / 2, 0, 24, "c-d")
    p.curve(lambda q: 12 - q, 0, 12, "c-mr")
    p.curve(lambda q: q + 4, 0, 9.4, "c-mc")
    p.line([(0, 10), (25, 10)], "c-pw")
    p.guide(2, 11); p.guide(6, 10, to_y=False); p.guide(4, 8)
    p.point(2, 11); p.point(2, 10); p.point(6, 10); p.point(4, 8, hollow=True)
    p.xt(2, "q_{d}"); p.xt(4); p.xt(6, "Q"); p.xt(24)
    p.yt(4); p.yt(8); p.yt(10); p.yt(11); p.yt(12)
    p.text(20, 2.8, "D"); p.text(12.4, 0.5, "MR"); p.text(9.6, 12.4, "MC"); p.text(24.6, 10.4, "p_{w} = 10", "end")
    return figure([p.svg("Монополист с мировым рынком: дома 2 по цене 11, всего 6, экспорт 4")],
                  "Мировая цена — горизонталь \\(p_w=10\\). Дома продаём, пока \\(MR\\ge p_w\\): \\(q_d=2\\), цена по спросу 11. Производим, пока \\(MC\\le p_w\\): \\(Q=6\\). Разница 4 уходит на экспорт. Полый кружок — пересечение MR и MC без мирового рынка (уровень 8): при \\(p_w\\le8\\) экспорта нет. При \\(p_w\\ge12\\) (точка, где MR касается оси p) всё уходит за рубеж.")


@fig("A7")
def _():
    p = Plot("A7", 9.6, 19.5)
    p.curve(lambda q: 18 - 2 * q, 0, 9, "c-d")
    p.curve(lambda q: 18 - 4 * q, 0, 4.5, "c-mr")
    p.curve(lambda q: 2 * q, 0, 9.5, "c-mc")
    p.line([(0, 10), (9.6, 10)], "c-pw")
    p.guide(2, 14); p.guide(5, 10, to_y=False); p.guide(3, 6)
    p.point(2, 14); p.point(2, 10); p.point(5, 10); p.point(3, 6, hollow=True)
    p.xt(2, "q_{d}=2"); p.xt(3); p.xt(5, "Q=5"); p.xt(9)
    p.yt(6); p.yt(10); p.yt(14); p.yt(18)
    p.text(7.7, 5.6, "D"); p.text(4.55, 1.2, "MR"); p.text(8.6, 18.6, "MC", "end"); p.text(9.5, 10.6, "p_{w} = 10", "end")
    return figure([p.svg("A.7: при мировой цене 10 дома 2 по цене 14, всего 5")],
                  "Пороги видны прямо на графике: MR пересекает MC на уровне 6 (полый кружок), значит при \\(p_w\\le6\\) всё продаётся дома. MR начинается с 18 на оси p, значит при \\(p_w\\ge18\\) всё уходит за рубеж. Для (c) горизонталь \\(p_w=10\\): \\(q_d=2\\), \\(Q=5\\), \\(q_d/Q=40\\%\\).")


@fig("A8")
def _():
    p = Plot("A8", 16, 16)
    p.curve(lambda q: 10 - q, 0, 10, "c-ind"); p.curve(lambda q: 15 - q, 0, 15, "c-ind")
    p.curve(lambda q: 10 - 2 * q, 0, 5, "c-mr"); p.curve(lambda q: 15 - 2 * q, 0, 7.5, "c-mr")
    p.line([(0, 4), (16, 4)], "c-mc")
    p.guide(3, 4, to_y=False); p.guide(5.5, 4, to_y=False)
    p.point(3, 4); p.point(5.5, 4); p.point(5, 0, hollow=True); p.point(7.5, 0, hollow=True)
    p.xt(3, "q_{1}"); p.xt(5.5, "q_{2}"); p.xt(7.5); p.xt(10); p.xt(15); p.yt(4, "MC"); p.yt(10); p.yt(15)
    p.text(4.25, 4, "2,5", "middle", dy=14, cls="tl")
    p.text(9.4, 1.3, "D_{1}", cls="tm"); p.text(14.4, 1.3, "D_{2}", cls="tm")
    p.text(1.7, 8.2, "MR_{1}"); p.text(5.3, 6.5, "MR_{2}")
    return figure([p.svg("Две прямые MR сдвинуты по горизонтали на 2,5")],
                  "\\(MR_1\\) и \\(MR_2\\) параллельны и сдвинуты на 2,5 по горизонтали, поэтому при любом уровне MC \\(q_2-q_1=2{,}5\\). Самый большой выпуск при \\(MC=0\\): полые кружки на оси q, 5 + 7,5 = 12,5.")


@fig("A9")
def _():
    p = Plot("A9", 19, 13)
    p.between(lambda q: 12 - 2 * q / 3, lambda q: 3, 0, 9, "a-cs")
    p.between(lambda q: 3, lambda q: q / 3, 0, 9, "a-ps")
    p.between(lambda q: 12 - 2 * q / 3, lambda q: q / 3, 9, 12, "a-dwl")
    p.curve(lambda q: 12 - 2 * q / 3, 0, 18, "c-d")
    p.curve(lambda q: q / 3, 0, 19, "c-mc")
    p.curve(lambda q: 2 * q / 3, 0, 19, "c-mbc")
    p.guide(9, 6); p.guide(9, 3, to_x=False); p.guide(12, 4)
    p.point(9, 6); p.point(9, 3); p.point(12, 4, hollow=True)
    p.xt(9, "q^{m}=9"); p.xt(12, "q^{*}"); p.xt(18); p.yt(3, "p^{m}=3"); p.yt(4); p.yt(6); p.yt(12)
    p.text(16.4, 1.9, "MV"); p.text(18.6, 6.9, "S", "end"); p.text(18.6, 12.1, "MBC", "end")
    p.text(2.2, 6.4, "прибыль 54", cls="tl"); p.text(4.4, 2.1, "PS", cls="tl")
    p.text(14.4, 9.4, "DWL", cls="tl"); p.leader(14.2, 9.2, 10.4, 4.9)
    return figure([p.svg("Монопсония: MV=MBC при q=9, цена 3 по кривой предложения")],
                  "Монопсония покупает, пока \\(MV\\ge MBC\\): \\(q^m=9\\). Платит цену с кривой предложения S: \\(p^m=3\\), а не 6. Синяя область — прибыль монопсонии, зелёная — PS поставщиков, красный треугольник до \\(q^*=12\\) — DWL.")


@fig("A10")
def _():
    p = Plot("A10", 7, 14)
    p.curve(lambda q: 13 - 2 * q, 0, 6.5, "c-d")
    p.curve(lambda q: 1 + q / 2, 0, 7, "c-mc")
    p.curve(lambda q: 1 + q, 0, 7, "c-mbc")
    p.line([(0, 3), (7, 3)], "c-pw")
    p.guide(2, 3, to_y=False); p.guide(2, 2, to_x=False); p.guide(5, 3, to_y=False); p.guide(4, 5)
    p.point(2, 3); p.point(2, 2); p.point(5, 3); p.point(4, 5, hollow=True)
    p.xt(2, "q_{d}"); p.xt(4); p.xt(5, "Q"); p.yt(1); p.yt(2); p.yt(3); p.yt(5); p.yt(13)
    p.text(1.0, 9.6, "MV", "end"); p.text(6.9, 4.9, "S", "end"); p.text(6.9, 8.4, "MBC", "end")
    p.text(6.9, 3.4, "p_{w} = 3", "end")
    return figure([p.svg("Монопсония с мировым рынком: дома 2 по цене 2, всего 5, импорт 3")],
                  "Покупаем дома, пока \\(MBC\\le p_w\\): \\(q_d=2\\), платим по кривой S цену 2. Всего покупаем, пока \\(MV\\ge p_w\\): \\(Q=5\\), импорт 3. Без мирового рынка \\(MV=MBC\\) на уровне 5 (полый кружок): при \\(p_w\\ge5\\) всё покупается дома. MBC начинается с 1 на оси p: при \\(p_w\\le1\\) всё покупается за рубежом.")


# ---------------- Part B ----------------

@fig("B1")
def _():
    p = Plot("B1", 63, 12.5, h=250)
    p.rect(0, 10, 10, 11, "a-cs")
    p.rect(0, 30, 6, 10, "a-ps")
    p.rect(30, 40, 8, 9, "a-dwl")
    p.steps([(0, 10, 11), (10, 30, 10), (30, 40, 9), (40, 60, 7)], "c-d")
    p.steps([(0, 30, 6), (30, 60, 8)], "c-mc")
    p.guide(30, 10, to_y=False); p.guide(40, 9, to_y=False)
    p.point(30, 10)
    p.xt(10); p.xt(30, "q^{m}=30"); p.xt(40, "q^{*}=40"); p.xt(60)
    p.yt(6); p.yt(7); p.yt(8); p.yt(9); p.yt(10); p.yt(11)
    p.text(52, 7.3, "ω (спрос)"); p.text(52, 8.3, "MC")
    p.text(13, 7.6, "прибыль 120", cls="tl"); p.text(1.5, 10.25, "CS", cls="tl")
    p.text(44, 10.8, "DWL = 10", cls="tl"); p.leader(43.6, 10.6, 36, 8.7)
    return figure([p.svg("Ступенчатый спрос и MC: цена 10, продано 30, эффективно 40")],
                  "Синяя ступенька — готовность платить, отсортированная по убыванию. Красная — MC (6 до 30-й машины, потом 8). Эффективно продавать, пока синяя выше красной: \\(q^*=40\\). Монополия ставит цену 10 и продаёт 30; потерянные 10 машин с ценностью 9 при MC 8 дают DWL.")


@fig("B2")
def _():
    p = Plot("B2", 6.7, 13)
    p.rect(0, 1, 10, 12, "a-cs")
    p.rect(0, 2, 5, 10, "a-ps")
    p.poly([(2, 5), (3, 5), (3, 8), (2, 8)], "a-dwl")
    p.poly([(3, 3), (4, 3), (4, 6), (3, 6)], "a-dwl")
    p.poly([(4, 3), (5, 3), (5, 4), (4, 4)], "a-dwl")
    p.steps([(0, 1, 12), (1, 2, 10), (2, 3, 8), (3, 4, 6), (4, 5, 4), (5, 6, 2)], "c-d")
    p.steps([(0, 3, 5), (3, 6, 3)], "c-mc")
    p.guide(2, 10); p.guide(5, 4, to_y=False)
    p.point(2, 10)
    for k in range(1, 7):
        p.xt(k)
    p.yt(3); p.yt(5); p.yt(10); p.yt(12)
    p.text(5.15, 1.0, "ω"); p.text(6.6, 3.4, "MC", "end")
    p.text(1.0, 7.2, "прибыль 10", "middle", cls="tl"); p.text(0.5, 10.6, "CS", "middle", cls="tl")
    p.text(3.4, 9.5, "DWL = 7", cls="tl"); p.leader(3.35, 9.2, 2.6, 7.4)
    return figure([p.svg("Шесть покупателей и падающие MC: эффективно 5, монополия продаёт 2")],
                  "MC падает с 5 до 3 после третьей единицы, поэтому эффективный объём ищем по всей таблице: \\(q^*=5\\) (5-й покупатель с 4 ещё выше MC 3). При единой цене 10 продаются 2 единицы, красные столбики — потерянный излишек 3 + 3 + 1 = 7 = 19 − 12.")


@fig("B3")
def _():
    p = Plot("B3", 73, 11.5, xl="q", yl="w")
    p.rect(0, 40, 6, 10, "a-cs")
    p.rect(0, 20, 5, 6, "a-ps")
    p.rect(40, 50, 7, 8, "a-dwl")
    p.steps([(0, 40, 10), (40, 70, 8)], "c-d")
    p.steps([(0, 20, 5), (20, 40, 6), (40, 50, 7), (50, 70, 9)], "c-mc")
    p.guide(40, 6, to_y=False); p.guide(50, 7, to_y=False)
    p.point(40, 6)
    p.xt(20); p.xt(40, "q^{m}=40"); p.xt(50, "q^{*}"); p.xt(70)
    p.yt(5); p.yt(6); p.yt(7); p.yt(8); p.yt(9); p.yt(10)
    p.text(70, 8.3, "MR", "end"); p.text(70, 9.3, "c (работники)", "end")
    p.text(13, 7.8, "прибыль 160", cls="tl"); p.text(2, 4.3, "излишек 20", cls="tm")
    p.text(52, 6.0, "DWL = 10", cls="tl"); p.leader(51.8, 6.3, 46, 7.4)
    return figure([p.svg("Найм работников: зарплата 6, нанято 40, эффективно 50")],
                  "Красные ступеньки — минимальные зарплаты работников по возрастанию, синие — предельная выручка с машины (10, затем 8). Эффективно нанимать, пока выручка выше \\(c\\): 50. Единая зарплата 6 нанимает 40, зелёный прямоугольник — излишек работников типа 1, красный — DWL.")


@fig("B4")
def _():
    p = Plot("B4", 8, 12.5, xl="x", yl="π")
    p.band(0.5, 3.5)
    p.line([(0, 7), (2, 7), (4, 11), (8, 11)], "c-d")
    p.line([(0, 6), (2, 10), (7, 10), (8, 11)], "c-pw")
    p.point(0.5, 7, hollow=True); p.point(3.5, 10, hollow=True)
    p.xt(0.5); p.xt(2); p.xt(3.5); p.xt(4); p.xt(7); p.xt(8); p.yt(6); p.yt(7); p.yt(10); p.yt(11)
    p.text(5.6, 11.4, "π_{S} раздельно"); p.text(4.6, 9.2, "π_{B} набор")
    p.text(2, 1.4, "набор лучше", "middle", cls="tm")
    return figure([p.svg("Прибыль от x: набор лучше при x от 0,5 до 3,5")],
                  "Синяя ломаная — раздельная продажа, зелёная — набор. Изломы там, где меняется лучшая цена (\\(x=2\\), \\(x=4\\), \\(x=7\\)). Набор строго лучше там, где зелёная выше синей: \\(x\\in(0{,}5;\\,3{,}5)\\), закрашенная полоса.")


@fig("B5")
def _():
    p = Plot("B5", 100, 1250, ymin=700, xl="x", yl="π", ml=44)
    p.band(80, 100)
    p.line([(0, 1000), (50, 800), (60, 800), (100, 1200)], "c-d")
    p.line([(0, 1000), (250 / 3, 1000), (100, 1200)], "c-pw")
    p.point(80, 1000, hollow=True); p.point(250 / 3, 1000)
    p.xt(50); p.xt(60); p.xt(80); p.xt(100); p.yt(800); p.yt(1000); p.yt(1200)
    p.text(30, 780, "π_{S} раздельно", "middle"); p.text(40, 1030, "π_{B} набор", "middle")
    p.text(90, 730, "раздельно лучше", "middle", cls="tm")
    return figure([p.svg("Прибыль от x: раздельная продажа лучше при x от 80 до 100")],
                  "Раздельная прибыль сначала падает (A дорого продавать некому), держится на 800, потом растёт по \\(200+10x\\). Набор даёт 1000, пока выгодно продавать всем, и \\(12x\\) после 83,3. Синяя выше зелёной только на \\((80;\\,100)\\). При \\(x=100\\) прибыли равны.")


@fig("B6")
def _():
    p = Plot("B6", 1, 14, xl="x", yl="π")
    p.band(0.4, 0.5)
    p.line([(0, 6), (6 / 13, 6), (1, 13)], "c-d")
    p.line([(0, 4), (1, 9)], "c-pw")
    p.point(0.4, 6, hollow=True); p.point(0.5, 6.5, hollow=True)
    p.xt(0.4); p.xt(0.5); p.xt(1); p.yt(4); p.yt(6); p.yt(9); p.yt(13)
    p.text(0.7, 11.6, "только Fancy", "end"); p.text(0.98, 6.4, "обе версии", "end")
    p.text(0.45, 1.4, "обе лучше", "middle", cls="tm")
    return figure([p.svg("Прибыль от x: обе версии выгоднее при x от 0,4 до 0,5")],
                  "Только Fancy: 6 (продаём всем) или \\(13x\\) (только типу I), излом в \\(x=6/13\\). Обе версии: прямая \\(4+5x\\). Она выше синей ломаной только на \\((0{,}4;\\,0{,}5)\\).")


@fig("B7")
def _():
    p = Plot("B7", 3, 11.5, ymin=6, xl="y", yl="π")
    p.band(0, 0.5)
    p.line([(0, 8), (1, 8), (3, 10)], "c-d")
    p.line([(0, 7.5), (3, 10.5)], "c-pw")
    p.point(0.5, 8, hollow=True)
    p.xt(0.5); p.xt(1); p.xt(2); p.xt(3); p.yt(7.5); p.yt(8); p.yt(10)
    p.text(2.95, 8.8, "только Top", "end"); p.text(1.6, 9.5, "Top + Xlam", "end")
    p.text(0.03, 6.35, "Top лучше", cls="tm")
    return figure([p.svg("Прибыль от y: только Top лучше при y меньше 0,5")],
                  "Только Top: 8 (продаём обоим по 5), с \\(y=1\\) выгоднее продавать только первому: \\(7+y\\). Две версии: \\(7{,}5+y\\), всегда на 0,5 выше правого куска. Только Top лучше при \\(y\\in[0;\\,0{,}5)\\).")


@fig("B8")
def _():
    p = Plot("B8", 4, 6, xl="α", yl="q")
    p.line([(0, 5), (4, 5)], "c-d")
    p.line([(0, 0), (4, 4)], "c-ind")
    p.line([(0, 0), (2.5, 0), (4, 3)], "c-pw")
    p.guide(3, 1); p.point(3, 1); p.point(3, 5); p.point(2.5, 0, hollow=True)
    p.xt(2.5); p.xt(3); p.xt(4); p.yt(1); p.yt(3); p.yt(5)
    p.text(0.2, 5.25, "q_{G}=5 (без искажений)"); p.text(1.6, 2.1, "эффективно q_{T}=α", cls="tm")
    p.text(3.35, 1.0, "q_{T}=2α−5")
    return figure([p.svg("Мощности от α: у Газа всегда 5, у Тормоза 2α−5 после 2,5")],
                  "Мощность машины Газа не зависит от α. Машина Тормоза занижена относительно эффективной (пунктир) и при \\(\\alpha\\le2{,}5\\) не выпускается вовсе. Две разные машины при \\(\\alpha\\in(2{,}5;\\,4)\\); при \\(\\alpha=3\\) получаем \\(q_T=1\\).")


@fig("B9")
def _():
    p = Plot("B9", 8, 9, xmin=3, xl="α", yl="q")
    p.line([(3, 3), (8, 8)], "c-d")
    p.line([(3, 3), (8, 3)], "c-ind")
    p.line([(3, 3), (6, 0), (8, 0)], "c-pw")
    p.guide(4, 4); p.guide(4, 2, to_x=False); p.point(4, 4); p.point(4, 2); p.point(6, 0, hollow=True)
    p.xt(4); p.xt(6); p.xt(8); p.yt(2); p.yt(3); p.yt(4); p.yt(8)
    p.text(6.4, 7.0, "q_{T}=α", "end"); p.text(7.9, 3.3, "эффективно q_{J}=3", "end", cls="tm")
    p.text(5.3, 1.6, "q_{J}=6−α")
    return figure([p.svg("Площади от α: у Тома α, у Джерри 6−α до α=6")],
                  "Дом Тома эффективный (\\(q_T=\\alpha\\)). Дом Джерри занижен и исчезает при \\(\\alpha\\ge6\\). Два разных дома при \\(\\alpha\\in(3;\\,6)\\); при \\(\\alpha=4\\): \\(q_T=4\\), \\(q_J=2\\).")


@fig("B10")
def _():
    p = Plot("B10", 1, 6, xl="x", yl="q")
    p.line([(0, 5), (1, 5)], "c-d")
    p.line([(0, 3), (1, 3)], "c-ind")
    p.curve(lambda x: (3 - 5 * x) / (1 - x), 0, 0.6, "c-pw")
    p.line([(0.6, 0), (1, 0)], "c-pw")
    p.guide(0.5, 1); p.point(0.5, 1); p.point(0.6, 0, hollow=True)
    p.xt(0.5); p.xt(0.6); p.xt(1); p.yt(1); p.yt(3); p.yt(5)
    p.text(0.02, 5.25, "q_{G}=5"); p.text(0.98, 3.25, "эффективно q_{T}=3", "end", cls="tm")
    p.text(0.62, 1.8, "q_{T}=(3−5x)/(1−x)")
    return figure([p.svg("Мощность машины Тормоза падает с ростом доли Газов и обнуляется при x=0,6")],
                  "Чем больше доля сильного типа x, тем дороже информационная рента, и тем сильнее фирма занижает \\(q_T\\). При \\(x\\ge0{,}6\\) машину Тормоза не выпускают. При \\(x=0{,}5\\) получаем \\(q_T=1\\).")


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
