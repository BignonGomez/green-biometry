import sys, os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
font_path, out = sys.argv[1], sys.argv[2]
f = instancer.instantiateVariableFont(TTFont(font_path), {"wght": 700})
gs = f.getGlyphSet(); cmap = f.getBestCmap(); hm = f['hmtx']
# Palette « Eau claire » (ADR-11) : bleu de l'eau + bleu clair
GREEN, GOLD, WHITE = "#0E6BA8", "#7CC6EE", "#FFFFFF"
SIZE = 212; k = SIZE/1000

def text_path(txt, x0, base):
    pen = SVGPathPen(gs); x = x0; o_center = None
    for c in txt:
        g = cmap[ord(c)]
        tp = TransformPen(pen, (k, 0, 0, -k, x, base))
        gs[g].draw(tp)
        if c == 'o' and o_center is None:
            adv = hm[g][0]; o_center = (x + adv*k/2, base - 538*k/2)
        x += hm[g][0]*k
    return pen.getCommands(), o_center

green_d, _ = text_path("Green", 620, 408)
bio_d, oc = text_path("Biometry", 620, 590)

LEAF = ("M398 190C300 250 175 330 152 445C135 540 215 600 350 645"
        "C255 590 200 530 205 450C212 360 300 280 388 232"
        "C440 290 482 340 488 380L501 386C498 330 455 250 398 190Z")
SPROUT = ("M352 636C320 560 330 470 385 425C425 393 465 388 498 384"
          "C492 450 455 520 400 570C380 590 362 610 352 636Z")
VEIN = "M447 444C402 488 362 538 340 600"
TICKS = [(330,325),(367,298),(403,325),(440,298),(475,325),(510,298),(545,325)]

def mark(main, gold, uid):
    ticks = "".join(f'<path d="M264 {y}H{x}"/>' for y, x in TICKS)
    return (f'<defs><mask id="vein-{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="2000" height="1000">'
            f'<rect x="0" y="0" width="2000" height="1000" fill="#fff"/>'
            f'<path d="{VEIN}" fill="none" stroke="#000" stroke-width="9" stroke-linecap="round"/></mask></defs>'
            f'<g fill="{main}"><path d="{LEAF}"/><path d="{SPROUT}" mask="url(#vein-{uid})"/></g>'
            f'<g fill="{gold}"><rect x="256" y="322" width="16" height="231" rx="4"/></g>'
            f'<g fill="none" stroke="{gold}" stroke-width="13" stroke-linecap="round">{ticks}</g>')

def horizontal(main, gold, uid, title):
    cx, cy = oc
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="130 170 1550 500" role="img" aria-labelledby="t-{uid}">'
            f'<title id="t-{uid}">{title}</title>{mark(main, gold, uid)}'
            f'<rect x="543" y="243" width="12" height="364" rx="6" fill="{gold}"/>'
            f'<path fill="{main}" d="{green_d}"/><path fill="{main}" d="{bio_d}"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="24" fill="{gold}"/></svg>\n')

def symbol(main, gold, uid, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="120 170 410 495" role="img" aria-labelledby="t-{uid}">'
            f'<title id="t-{uid}">{title}</title>{mark(main, gold, uid)}</svg>\n')

def favicon():
    # symbole blanc + bleu clair sur carre bleu arrondi, lisible en 32 px
    inner = mark(WHITE, GOLD, "fav")
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Green Biometry">'
            f'<rect width="512" height="512" rx="96" fill="{GREEN}"/>'
            f'<g transform="translate(256 256) scale(0.98) translate(-325 -418)">{inner}</g></svg>\n')

os.makedirs(out, exist_ok=True)
files = {
 "logo-horizontal.svg": horizontal(GREEN, GOLD, "h", "Green Biometry"),
 "logo-horizontal-blanc.svg": horizontal(WHITE, GOLD, "hb", "Green Biometry"),
 "logo-horizontal-mono.svg": horizontal(GREEN, GREEN, "hm", "Green Biometry"),
 "symbole.svg": symbol(GREEN, GOLD, "s", "Green Biometry"),
 "symbole-blanc.svg": symbol(WHITE, GOLD, "sb", "Green Biometry"),
 "favicon.svg": favicon(),
}
for n, c in files.items():
    open(os.path.join(out, n), "w", encoding="utf-8").write(c)
    print(n, len(c), "octets")
