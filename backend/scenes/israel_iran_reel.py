from manim import *
import numpy as np
import os

class ReelScene(Scene):
    def construct(self):
        BG      = "#0a0d14"
        GOLD    = "#f5a623"
        RED     = "#e63946"
        CYAN    = "#4cc9f0"
        WHITE   = "#ffffff"
        DIM     = "#7a8599"
        ORANGE  = "#f06623"
        GREEN   = "#06d6a0"
        PURPLE  = "#8338ec"
        DARK    = "#1a1f2e"

        self.camera.background_color = BG
        self.camera.frame_width  = 9
        self.camera.frame_height = 16

        # Load SD images from env (injected by runner)
        def load_img(key, width=9.0, opacity=0.30):
            path = os.environ.get(key, "")
            if path and os.path.exists(path):
                img = ImageMobject(path).set_width(width).set_opacity(opacity)
                return img
            return None

        # ── Shared helpers ───────────────────────────────────────────
        def star_field(n=100, seed=42):
            rng = np.random.default_rng(seed)
            g = VGroup()
            for _ in range(n):
                x = rng.uniform(-4.5, 4.5)
                y = rng.uniform(-8.0, 8.0)
                r = rng.uniform(0.02, 0.05)
                a = rng.uniform(0.2, 0.8)
                g.add(Dot(radius=r, color=WHITE, fill_opacity=a).move_to([x, y, 0]))
            return g

        def pill(text, col, y):
            bg = RoundedRectangle(width=7.8, height=0.75, corner_radius=0.18,
                                  fill_color=DARK, fill_opacity=0.92,
                                  stroke_color=col, stroke_width=1.5).move_to(UP*y)
            tx = Text(text, font_size=21, color=col).move_to(UP*y)
            return VGroup(bg, tx)

        def section_header(title, subtitle, col=GOLD):
            t = Text(title,    font_size=52, color=col,   weight=BOLD).move_to(UP*6.1)
            s = Text(subtitle, font_size=25, color=DIM).move_to(UP*5.05)
            return t, s

        # ═══════════════════════════════════════════════════
        # SCENE 1 — OVERVIEW: The Flashpoint
        # ═══════════════════════════════════════════════════
        stars = star_field(seed=1)
        self.add(stars)

        img1 = load_img("SD_IMG_0", opacity=0.28)
        if img1: self.add(img1)

        tag   = Text("GEOPOLITICS", font_size=30, color=CYAN, weight=BOLD).move_to(UP*6.8)
        title = Text("Israel vs Iran", font_size=62, color=WHITE, weight=BOLD).move_to(UP*5.7)
        sub   = Text("The Middle East's Defining Conflict", font_size=28,
                     color=DIM).move_to(UP*4.75)

        self.play(FadeIn(tag, shift=DOWN*0.3), run_time=0.6)
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub,  shift=UP*0.2), run_time=0.7)

        # Two flag-coloured dots representing the nations
        il_dot = Circle(radius=0.55, fill_color="#0038b8", fill_opacity=1,
                        stroke_color=WHITE, stroke_width=2).move_to(LEFT*2.2 + UP*2.8)
        ir_dot = Circle(radius=0.55, fill_color="#239f40", fill_opacity=1,
                        stroke_color=WHITE, stroke_width=2).move_to(RIGHT*2.2 + UP*2.8)
        il_lbl = Text("Israel", font_size=22, color=WHITE, weight=BOLD).next_to(il_dot, DOWN, buff=0.15)
        ir_lbl = Text("Iran",   font_size=22, color=WHITE, weight=BOLD).next_to(ir_dot, DOWN, buff=0.15)

        vs_txt = Text("VS", font_size=38, color=RED, weight=BOLD).move_to(UP*2.8)

        flash_line = Line(il_dot.get_right(), ir_dot.get_left(),
                          color=RED, stroke_width=3, stroke_opacity=0.8)

        self.play(GrowFromCenter(il_dot), GrowFromCenter(ir_dot), run_time=0.9)
        self.play(FadeIn(il_lbl), FadeIn(ir_lbl), run_time=0.5)
        self.play(Write(vs_txt), Create(flash_line), run_time=0.8)
        self.play(Indicate(vs_txt, scale_factor=1.2, color=RED), run_time=0.7)

        # Key fact pills
        facts = VGroup(
            pill("Proxy wars spanning 4 decades",         CYAN,  0.8),
            pill("Iran nuclear enrichment near 90%",      ORANGE, 0.0),
            pill("First direct strikes: April 2024",       RED,  -0.8),
        )
        self.play(LaggedStart(*[FadeIn(f, shift=UP*0.2) for f in facts],
                               lag_ratio=0.25), run_time=1.2)
        self.wait(0.8)

        # ═══════════════════════════════════════════════════
        # SCENE 2 — HISTORY: Decades of Tension
        # ═══════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(star_field(seed=2))

        img2 = load_img("SD_IMG_1", opacity=0.22)
        if img2: self.add(img2)

        t2, s2 = section_header("Four Decades", "of shadow conflict", ORANGE)
        self.play(Write(t2), run_time=0.9)
        self.play(FadeIn(s2, shift=UP*0.2), run_time=0.6)

        # Timeline vertical line
        tl_line = Line(UP*3.8, DOWN*4.5, color=DIM, stroke_width=2)
        self.play(Create(tl_line), run_time=0.7)

        # Events
        events = [
            (1979, "Iranian Revolution",         "Israel loses its ally",        CYAN,   3.2),
            (1982, "Iran funds Hezbollah",        "Proxy force in Lebanon",       ORANGE, 1.8),
            (2006, "Lebanon War",                 "Hezbollah vs Israel",          RED,    0.4),
            (2018, "Nuclear deal collapsed",      "US sanctions re-imposed",      GOLD,  -1.0),
            (2024, "First direct strikes",        "Iran fires 300+ drones",       RED,   -2.5),
        ]
        for yr, title_e, detail, col, y in events:
            dot  = Dot(radius=0.10, color=col, fill_opacity=1).move_to(UP*y)
            yr_t = Text(str(yr), font_size=20, color=col, weight=BOLD)\
                .next_to(dot, LEFT, buff=0.18)
            ti_t = Text(title_e, font_size=21, color=WHITE, weight=BOLD)\
                .next_to(dot, RIGHT, buff=0.18)
            de_t = Text(detail, font_size=17, color=DIM)\
                .next_to(ti_t, DOWN, buff=0.08).align_to(ti_t, LEFT)
            self.play(
                GrowFromCenter(dot),
                FadeIn(yr_t), FadeIn(ti_t), FadeIn(de_t),
                run_time=0.4
            )
        self.wait(1.2)

        # ═══════════════════════════════════════════════════
        # SCENE 3 — APRIL 2024: The Direct Strike
        # ═══════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(star_field(seed=3))

        img3 = load_img("SD_IMG_2", opacity=0.25)
        if img3: self.add(img3)

        t3, s3 = section_header("April 2024", "Iran attacks Israel directly — a historic first", RED)
        self.play(Write(t3), run_time=0.9)
        self.play(FadeIn(s3, shift=UP*0.2), run_time=0.6)

        # Iran dot (right side of screen, since map orientation)
        iran_pos   = RIGHT*2.5 + UP*1.0
        israel_pos = LEFT*2.0  + UP*2.5

        iran_c   = Circle(radius=0.4, fill_color="#239f40", fill_opacity=1,
                          stroke_width=0).move_to(iran_pos)
        israel_c = Circle(radius=0.4, fill_color="#0038b8", fill_opacity=1,
                          stroke_width=0).move_to(israel_pos)
        iran_lbl   = Text("Iran",   font_size=20, color=WHITE).next_to(iran_c,   DOWN, buff=0.1)
        israel_lbl = Text("Israel", font_size=20, color=WHITE).next_to(israel_c, DOWN, buff=0.1)

        self.play(GrowFromCenter(iran_c), GrowFromCenter(israel_c),
                  FadeIn(iran_lbl), FadeIn(israel_lbl), run_time=0.8)

        # Missile arcs: Iran → Israel
        for i in range(5):
            color = ORANGE if i % 2 == 0 else RED
            arc = ArcBetweenPoints(
                iran_pos + np.array([np.random.uniform(-0.3, 0.3), 0, 0]),
                israel_pos + np.array([np.random.uniform(-0.2, 0.2), 0, 0]),
                angle=np.random.uniform(-1.2, -0.7),
                color=color, stroke_width=2.5, stroke_opacity=0.9
            )
            dot = Dot(radius=0.07, color=color, fill_opacity=1).move_to(iran_pos)
            self.play(
                MoveAlongPath(dot, arc),
                Create(arc),
                run_time=0.5
            )
            self.play(Flash(dot, color=color, num_lines=6, flash_radius=0.2),
                      run_time=0.3)

        # Stats
        stats = VGroup(
            VGroup(
                Text("330+",      font_size=34, color=RED,   weight=BOLD),
                Text("drones & missiles", font_size=19, color=DIM),
            ).arrange(DOWN, buff=0.08),
            VGroup(
                Text("99%",       font_size=34, color=GREEN, weight=BOLD),
                Text("intercepted",      font_size=19, color=DIM),
            ).arrange(DOWN, buff=0.08),
        ).arrange(RIGHT, buff=1.2).move_to(DOWN*2.0)

        self.play(FadeIn(stats, shift=UP*0.3), run_time=0.9)

        allies = Text("Intercepted with help from US, UK, Jordan & Saudi Arabia",
                      font_size=19, color=CYAN).move_to(DOWN*3.4)
        self.play(Write(allies), run_time=0.9)
        self.wait(0.8)

        # ═══════════════════════════════════════════════════
        # SCENE 4 — PROXY NETWORK & REGIONAL IMPACT
        # ═══════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(star_field(seed=4))

        img4 = load_img("SD_IMG_3", opacity=0.22)
        if img4: self.add(img4)

        t4, s4 = section_header("Iran's Proxy Ring", "Surrounding Israel from all sides", PURPLE)
        self.play(Write(t4), run_time=0.9)
        self.play(FadeIn(s4, shift=UP*0.2), run_time=0.6)

        # Central Israel dot
        il_center = Dot(radius=0.22, color="#0038b8", fill_opacity=1).move_to(ORIGIN + UP*0.5)
        il_label  = Text("Israel", font_size=20, color=WHITE, weight=BOLD)\
            .next_to(il_center, DOWN, buff=0.12)
        self.play(GrowFromCenter(il_center), FadeIn(il_label), run_time=0.6)

        proxies = [
            ("Hezbollah",  "Lebanon",   UP*3.2   + LEFT*0.5,  RED),
            ("Hamas",      "Gaza",      LEFT*3.0 + UP*0.2,    ORANGE),
            ("Houthis",    "Yemen",     DOWN*3.0 + RIGHT*0.5, PURPLE),
            ("Militias",   "Iraq/Syria",LEFT*1.5 + UP*2.0,    GOLD),
        ]
        for proxy, country, pos, col in proxies:
            pdot  = Dot(radius=0.16, color=col, fill_opacity=1).move_to(pos)
            pname = Text(proxy,   font_size=19, color=col, weight=BOLD)\
                .next_to(pdot, UP, buff=0.1)
            pctry = Text(country, font_size=16, color=DIM)\
                .next_to(pdot, DOWN, buff=0.08)
            arrow = Arrow(pos, il_center.get_center(), color=col,
                          stroke_width=2, buff=0.2,
                          max_tip_length_to_length_ratio=0.12)
            self.play(GrowFromCenter(pdot), FadeIn(pname), FadeIn(pctry),
                      GrowArrow(arrow), run_time=0.55)

        fact_prx = Text("All funded and armed by Iran", font_size=22,
                        color=ORANGE, weight=BOLD).move_to(DOWN*4.8)
        self.play(FadeIn(fact_prx, shift=UP*0.2), run_time=0.7)
        self.wait(0.8)

        # ═══════════════════════════════════════════════════
        # SCENE 5 — GLOBAL STAKES + CLOSING
        # ═══════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(star_field(n=150, seed=5))

        img5 = load_img("SD_IMG_4", opacity=0.22)
        if img5: self.add(img5)

        t5, s5 = section_header("Global Stakes", "Why the world cannot ignore this", CYAN)
        self.play(Write(t5), run_time=0.9)
        self.play(FadeIn(s5, shift=UP*0.2), run_time=0.6)

        # Strait of Hormuz oil stat
        hormuz_bg = RoundedRectangle(
            width=8.0, height=1.6, corner_radius=0.25,
            fill_color=DARK, fill_opacity=0.9,
            stroke_color=GOLD, stroke_width=1.5
        ).move_to(UP*3.5)
        hormuz_tx1 = Text("Strait of Hormuz", font_size=26, color=GOLD,
                          weight=BOLD).move_to(UP*3.72)
        hormuz_tx2 = Text("20% of the world's oil passes through here",
                          font_size=20, color=DIM).move_to(UP*3.22)
        self.play(FadeIn(hormuz_bg), Write(hormuz_tx1), run_time=0.7)
        self.play(FadeIn(hormuz_tx2), run_time=0.5)

        stakes = [
            ("Oil prices spike with every escalation",    ORANGE),
            ("Nuclear risk if Iran crosses the threshold", RED),
            ("US & Russia both deeply involved",           PURPLE),
            ("Ceasefire or wider war — the world watches", CYAN),
        ]
        for i, (text, col) in enumerate(stakes):
            y = 2.0 - i * 1.0
            dot  = Dot(radius=0.09, color=col, fill_opacity=1).move_to(LEFT*3.8 + UP*y)
            line = Text(text, font_size=21, color=col).move_to(RIGHT*0.2 + UP*y)
            self.play(GrowFromCenter(dot), FadeIn(line, shift=LEFT*0.2), run_time=0.4)

        # Closing statement
        close1 = Text("This conflict belongs", font_size=40, color=WHITE, weight=BOLD)
        close2 = Text("to every nation",       font_size=40, color=WHITE, weight=BOLD)
        close3 = Text("on Earth.",             font_size=46, color=GOLD,  weight=BOLD)
        closing = VGroup(close1, close2, close3).arrange(DOWN, buff=0.3).move_to(DOWN*2.5)
        self.play(
            LaggedStart(*[FadeIn(l, shift=UP*0.2) for l in closing], lag_ratio=0.25),
            run_time=1.5
        )

        # Brand bar
        brand_bg  = RoundedRectangle(
            width=8.2, height=1.7, corner_radius=0.3,
            fill_color="#c8372d", fill_opacity=1, stroke_width=0
        ).move_to(DOWN*4.4)
        brand_txt = Text("ScrollUForward", font_size=40, color=WHITE,
                         weight=BOLD).move_to(DOWN*4.15)
        learn_txt = Text("Learn Something Real Every Day",
                         font_size=21, color="#ffe0de").move_to(DOWN*4.75)

        self.play(FadeIn(brand_bg), run_time=0.6)
        self.play(Write(brand_txt), Write(learn_txt), run_time=1.0)
        self.wait(2.5)
        self.play(FadeOut(*self.mobjects), run_time=1.2)
