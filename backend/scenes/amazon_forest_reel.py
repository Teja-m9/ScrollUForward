from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        # ── Palette ──────────────────────────────────────────────────
        BG      = "#071a0a"
        FOREST  = "#1b4332"
        CANOPY  = "#40916c"
        LEAF    = "#74c69d"
        BRIGHT  = "#b7e4c7"
        GOLD    = "#f5a623"
        ORANGE  = "#f06623"
        RED     = "#e63946"
        WHITE   = "#ffffff"
        DIM     = "#5a8a6a"
        WATER   = "#4cc9f0"
        BROWN   = "#8b5e3c"
        BURNT   = "#5a2e0c"

        self.camera.background_color = BG
        self.camera.frame_width  = 9
        self.camera.frame_height = 16

        # ══════════════════════════════════════════
        # SHARED HELPERS
        # ══════════════════════════════════════════
        def make_tree(x, y, scale=1.0, col=CANOPY, col2=LEAF):
            trunk  = Rectangle(width=0.18*scale, height=0.55*scale,
                               fill_color=BROWN, fill_opacity=1, stroke_width=0)
            c1 = Triangle(fill_color=col,  fill_opacity=1, stroke_width=0).scale(0.55*scale)
            c2 = Triangle(fill_color=col2, fill_opacity=1, stroke_width=0).scale(0.42*scale)
            c1.next_to(trunk, UP, buff=0)
            c2.next_to(trunk, UP, buff=0.22*scale)
            return VGroup(trunk, c1, c2).move_to([x, y, 0])

        def make_treeline(y, n, col=CANOPY, col2=LEAF, seed=1):
            rng  = np.random.default_rng(seed)
            xs   = np.linspace(-4.3, 4.3, n)
            grp  = VGroup()
            for x in xs:
                s = rng.uniform(0.7, 1.2)
                dy = rng.uniform(-0.15, 0.15)
                grp.add(make_tree(x, y + dy, scale=s, col=col, col2=col2))
            return grp

        def make_canopy_circles(n=40, y_min=5.5, y_max=8.5, seed=2):
            rng = np.random.default_rng(seed)
            grp = VGroup()
            cols = [FOREST, CANOPY, LEAF, BRIGHT]
            for _ in range(n):
                x = rng.uniform(-4.6, 4.6)
                y = rng.uniform(y_min, y_max)
                r = rng.uniform(0.6, 1.8)
                c = cols[rng.integers(0, len(cols))]
                a = rng.uniform(0.55, 0.95)
                grp.add(Circle(radius=r, fill_color=c, fill_opacity=a,
                               stroke_width=0).move_to([x, y, 0]))
            return grp

        def make_leaf_particles(n=50, seed=3):
            rng = np.random.default_rng(seed)
            grp = VGroup()
            for _ in range(n):
                x = rng.uniform(-4.4, 4.4)
                y = rng.uniform(-8.0, 8.0)
                r = rng.uniform(0.04, 0.10)
                c = rng.choice([FOREST, CANOPY, LEAF])
                a = rng.uniform(0.12, 0.40)
                grp.add(Dot(radius=r, color=c, fill_opacity=a).move_to([x, y, 0]))
            return grp

        def make_bird(x, y, scale=1.0):
            wl = ArcBetweenPoints(LEFT*0.18*scale + UP*0.09*scale,
                                  ORIGIN, angle=-0.6, color=BRIGHT, stroke_width=2)
            wr = ArcBetweenPoints(ORIGIN,
                                  RIGHT*0.18*scale + UP*0.09*scale, angle=-0.6,
                                  color=BRIGHT, stroke_width=2)
            return VGroup(wl, wr).move_to([x, y, 0])

        def make_butterfly(x, y, col=GOLD):
            wl = Ellipse(width=0.38, height=0.22, fill_color=col,
                         fill_opacity=0.85, stroke_width=0).shift(LEFT*0.18)
            wr = Ellipse(width=0.38, height=0.22, fill_color=col,
                         fill_opacity=0.85, stroke_width=0).shift(RIGHT*0.18)
            body = Dot(radius=0.05, color=BROWN, fill_opacity=1)
            return VGroup(wl, wr, body).move_to([x, y, 0])

        def make_jaguar(x, y):
            body  = Ellipse(width=1.3, height=0.65,
                            fill_color=GOLD, fill_opacity=1, stroke_width=0)
            head  = Circle(radius=0.35, fill_color=GOLD,
                           fill_opacity=1, stroke_width=0).shift(RIGHT*0.82)
            ear_l = Triangle(fill_color=GOLD, fill_opacity=1, stroke_width=0)\
                        .scale(0.12).shift(RIGHT*0.65 + UP*0.38)
            ear_r = Triangle(fill_color=GOLD, fill_opacity=1, stroke_width=0)\
                        .scale(0.12).shift(RIGHT*1.0 + UP*0.38)
            spots = VGroup(*[
                Dot(radius=r, color="#3d1a00", fill_opacity=0.7).shift([sx, sy, 0])
                for sx, sy, r in [
                    (-0.4,  0.12, 0.09), (0.0,  -0.10, 0.08),
                    (0.35,  0.14, 0.09), (-0.1, -0.22, 0.07),
                    (0.70,  0.0,  0.06),
                ]
            ])
            return VGroup(body, head, ear_l, ear_r, spots).move_to([x, y, 0])

        def make_river(y=-3.6):
            pts = [
                [-4.6, y+0.3, 0], [-3.0, y-0.1, 0], [-1.5, y+0.35, 0],
                [0.0,  y-0.2,  0], [1.5,  y+0.3, 0], [3.0, y-0.1, 0],
                [4.6, y+0.2, 0],
            ]
            r = VMobject(color=WATER, stroke_width=9, stroke_opacity=0.85)
            r.set_points_smoothly([np.array(p) for p in pts])
            return r

        def make_co2(x, y):
            c = Text("C", font_size=18, color=ORANGE, weight=BOLD).move_to([x, y, 0])
            o1 = Dot(radius=0.09, color=RED, fill_opacity=1).move_to([x-0.2, y, 0])
            o2 = Dot(radius=0.09, color=RED, fill_opacity=1).move_to([x+0.2, y, 0])
            return VGroup(c, o1, o2)

        def make_o2(x, y):
            o1 = Dot(radius=0.10, color=BRIGHT, fill_opacity=1).move_to([x-0.12, y, 0])
            o2 = Dot(radius=0.10, color=BRIGHT, fill_opacity=1).move_to([x+0.12, y, 0])
            lbl = Text("O2", font_size=14, color=BRIGHT).move_to([x, y-0.22, 0])
            return VGroup(o1, o2, lbl)

        # ══════════════════════════════════════════════════════════════
        # SCENE 1 — HOOK  "Earth's Last Great Lung"
        # ══════════════════════════════════════════════════════════════
        particles = make_leaf_particles()
        self.add(particles)

        canopy = make_canopy_circles(n=35, y_min=5.8, y_max=8.8)
        self.play(
            LaggedStart(*[GrowFromCenter(c) for c in canopy], lag_ratio=0.04),
            run_time=1.6
        )

        trees_bg = make_treeline(-5.8, 13, col=FOREST, col2=CANOPY, seed=10)
        trees_mg = make_treeline(-4.6, 10, col=CANOPY, col2=LEAF,   seed=20)
        trees_fg = make_treeline(-3.5, 7,  col=LEAF,   col2=BRIGHT, seed=30)
        self.play(
            LaggedStart(*[GrowFromPoint(t, t.get_bottom()) for t in trees_bg], lag_ratio=0.05),
            run_time=1.2
        )
        self.play(
            LaggedStart(*[GrowFromPoint(t, t.get_bottom()) for t in trees_mg], lag_ratio=0.06),
            LaggedStart(*[GrowFromPoint(t, t.get_bottom()) for t in trees_fg], lag_ratio=0.07),
            run_time=1.0
        )

        tag    = Text("THE AMAZON", font_size=36, color=LEAF,  weight=BOLD).move_to(UP*6.3)
        title  = Text("Earth's Last",  font_size=62, color=WHITE, weight=BOLD).move_to(UP*5.1)
        title2 = Text("Great Lung",    font_size=62, color=GOLD,  weight=BOLD).move_to(UP*3.95)

        self.play(FadeIn(tag, shift=DOWN*0.3), run_time=0.6)
        self.play(Write(title),  run_time=0.9)
        self.play(Write(title2), run_time=0.9)

        stat_bg = RoundedRectangle(
            width=7.4, height=1.0, corner_radius=0.22,
            fill_color=FOREST, fill_opacity=0.92,
            stroke_color=LEAF, stroke_width=1.5
        ).move_to(UP*2.55)
        stat_tx = Text("5.5 million km²  ·  Larger than the EU",
                       font_size=23, color=BRIGHT).move_to(UP*2.55)
        self.play(FadeIn(stat_bg), Write(stat_tx), run_time=0.9)

        # Firefly dots floating
        fireflies = VGroup(*[
            Dot(radius=0.05, color=GOLD, fill_opacity=0.8)
            .move_to([np.random.uniform(-3.5, 3.5), np.random.uniform(-1.0, 1.5), 0])
            for _ in range(10)
        ])
        self.play(LaggedStart(*[FadeIn(f) for f in fireflies], lag_ratio=0.1),
                  run_time=0.8)
        self.play(LaggedStart(*[f.animate.shift(UP*0.4) for f in fireflies],
                               lag_ratio=0.05), run_time=1.2)
        self.wait(0.5)

        # ══════════════════════════════════════════════════════════════
        # SCENE 2 — BIODIVERSITY
        # ══════════════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(make_leaf_particles(n=35, seed=9))

        t2_title = Text("Biodiversity", font_size=54, color=LEAF, weight=BOLD).move_to(UP*6.2)
        t2_sub   = Text("10% of ALL species on Earth",
                        font_size=27, color=BRIGHT).move_to(UP*5.2)
        self.play(Write(t2_title), run_time=0.9)
        self.play(FadeIn(t2_sub, shift=UP*0.2), run_time=0.6)

        # Animated species bars
        cats = [
            ("Plants",   40000, LEAF),
            ("Birds",     1300, GOLD),
            ("Mammals",    430, ORANGE),
            ("Reptiles",   380, WATER),
            ("Fish",      3000, BRIGHT),
        ]
        max_v = 40000
        bar_w = 5.8
        ys    = [3.6, 2.5, 1.4, 0.3, -0.8]

        for (name, val, col), y in zip(cats, ys):
            lbl = Text(name, font_size=21, color=WHITE).move_to(LEFT*3.4 + UP*y)
            bg  = Rectangle(width=bar_w, height=0.30,
                            fill_color=FOREST, fill_opacity=0.7,
                            stroke_width=0).move_to(RIGHT*0.2 + UP*y)
            fw  = bar_w * val / max_v
            fill = Rectangle(width=fw, height=0.30,
                             fill_color=col, fill_opacity=0.95,
                             stroke_width=0)\
                .align_to(bg, LEFT)
            vl  = Text(f"{val:,}", font_size=18, color=col)\
                .next_to(bg, RIGHT, buff=0.12).shift(UP*y*0+UP*y)
            self.play(FadeIn(lbl), FadeIn(bg), run_time=0.2)
            self.play(GrowFromEdge(fill, LEFT), run_time=0.45)
            self.play(FadeIn(vl), run_time=0.2)

        # Animals
        jaguar = make_jaguar(-1.2, -2.4).scale(0.9)
        birds  = VGroup(*[make_bird(x, -1.8, scale=1.2)
                          for x in [-3.2, -2.2, 2.0, 3.0, 3.8]])
        bflies = VGroup(*[make_butterfly(x, y, col)
                          for x, y, col in [
                              (1.5,-2.1,GOLD),(2.8,-2.6,ORANGE),(-2.5,-2.3,LEAF)]])

        self.play(GrowFromCenter(jaguar), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(b, shift=RIGHT*0.4) for b in birds], lag_ratio=0.1),
            LaggedStart(*[GrowFromCenter(bf) for bf in bflies], lag_ratio=0.15),
            run_time=0.9
        )

        fact = VGroup(
            Text("New species discovered", font_size=24, color=WHITE, weight=BOLD),
            Text("here every single day.", font_size=24, color=DIM),
        ).arrange(DOWN, buff=0.18).move_to(DOWN*4.3)
        self.play(FadeIn(fact, shift=UP*0.3), run_time=0.8)
        self.wait(1.0)

        # ══════════════════════════════════════════════════════════════
        # SCENE 3 — CLIMATE ENGINE
        # ══════════════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(make_leaf_particles(n=30, seed=11))

        t3_title = Text("The Climate Engine", font_size=48,
                        color=WATER, weight=BOLD).move_to(UP*6.2)
        t3_sub   = Text("Regulating life for the whole planet",
                        font_size=24, color=DIM).move_to(UP*5.2)
        self.play(Write(t3_title), run_time=0.9)
        self.play(FadeIn(t3_sub, shift=UP*0.2), run_time=0.6)

        # Big central tree
        big_tree = make_tree(0, 0.5, scale=2.6, col=CANOPY, col2=LEAF)
        self.play(GrowFromPoint(big_tree, big_tree.get_bottom()), run_time=1.2)

        # CO2 molecules drifting down into tree
        co2_mols = VGroup(*[make_co2(-2.5 + i*0.9, 4.5) for i in range(4)])
        co2_lbl  = Text("CO₂", font_size=32, color=ORANGE, weight=BOLD).move_to(LEFT*3.2 + UP*3.8)
        self.play(FadeIn(co2_lbl), LaggedStart(*[FadeIn(m) for m in co2_mols], lag_ratio=0.15),
                  run_time=0.7)
        self.play(
            LaggedStart(*[m.animate.move_to([0, 1.5, 0]).set_opacity(0)
                          for m in co2_mols], lag_ratio=0.1),
            run_time=1.2
        )

        # O2 molecules rising out of tree
        o2_mols = VGroup(*[make_o2(-1.8 + i*1.2, 2.2) for i in range(4)])
        o2_lbl  = Text("O₂", font_size=32, color=BRIGHT, weight=BOLD).move_to(RIGHT*3.2 + UP*3.8)
        self.play(
            LaggedStart(*[FadeIn(m) for m in o2_mols], lag_ratio=0.1),
            run_time=0.6
        )
        self.play(
            FadeIn(o2_lbl),
            LaggedStart(*[m.animate.shift(UP*2.5).set_opacity(0)
                          for m in o2_mols], lag_ratio=0.08),
            run_time=1.1
        )

        # Stats
        stats = VGroup(
            VGroup(
                Text("2 Billion tons", font_size=26, color=ORANGE, weight=BOLD),
                Text("CO₂ absorbed / year", font_size=18, color=DIM),
            ).arrange(DOWN, buff=0.1),
            VGroup(
                Text("20%", font_size=26, color=BRIGHT, weight=BOLD),
                Text("of Earth's oxygen", font_size=18, color=DIM),
            ).arrange(DOWN, buff=0.1),
        ).arrange(RIGHT, buff=0.8).move_to(DOWN*2.2)
        self.play(FadeIn(stats, shift=UP*0.3), run_time=0.8)

        # River + rain
        river = make_river(y=-3.8)
        self.play(Create(river), run_time=0.8)
        rain  = VGroup(*[
            Dot(radius=0.05, color=WATER, fill_opacity=0.8)
            .move_to([np.random.uniform(-4, 4), np.random.uniform(-0.5, 1.5), 0])
            for _ in range(18)
        ])
        self.play(LaggedStart(*[r.animate.shift(DOWN*1.4).set_opacity(0)
                                for r in rain], lag_ratio=0.04), run_time=1.0)

        water_lbl = Text("Moisture → rain for all of South America",
                         font_size=20, color=WATER).move_to(DOWN*5.3)
        self.play(Write(water_lbl), run_time=0.7)
        self.wait(0.8)

        # ══════════════════════════════════════════════════════════════
        # SCENE 4 — DEFORESTATION
        # ══════════════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)

        t4_title = Text("The Crisis", font_size=58, color=RED,
                        weight=BOLD).move_to(UP*6.2)
        t4_sub   = Text("17% already destroyed in 50 years",
                        font_size=25, color=DIM).move_to(UP*5.2)
        self.play(Write(t4_title), run_time=0.9)
        self.play(FadeIn(t4_sub, shift=UP*0.2), run_time=0.6)

        # Living forest block (left side)
        forest_block = Rectangle(
            width=8.2, height=4.6,
            fill_color=CANOPY, fill_opacity=0.88, stroke_width=0
        ).move_to(UP*1.2)

        # Mini trees inside forest block
        mini_trees = VGroup(*[
            make_tree(-3.5 + i*0.9, 1.2 + (i % 2)*0.3,
                      scale=0.55, col=FOREST, col2=CANOPY)
            for i in range(9)
        ])

        self.play(FadeIn(forest_block), run_time=0.5)
        self.play(LaggedStart(*[GrowFromPoint(t, t.get_bottom())
                                for t in mini_trees], lag_ratio=0.06), run_time=0.8)

        # Deforestation encroaches from the right
        burnt_block = Rectangle(
            width=0.05, height=4.6,
            fill_color=BURNT, fill_opacity=0.92, stroke_width=0
        ).align_to(forest_block, RIGHT).shift(LEFT*0.02).move_to(UP*1.2)
        self.add(burnt_block)

        self.play(
            forest_block.animate.stretch_to_fit_width(6.7).align_to(LEFT*4.1, LEFT),
            burnt_block.animate.stretch_to_fit_width(1.55).align_to(RIGHT*4.1, RIGHT),
            run_time=1.4
        )

        # Fire dots in burnt area
        fire_dots = VGroup(*[
            Dot(radius=np.random.uniform(0.07, 0.18),
                color=np.random.choice([RED, ORANGE, GOLD]),
                fill_opacity=0.85)
            .move_to([np.random.uniform(2.0, 4.0),
                      np.random.uniform(-0.5, 2.8), 0])
            for _ in range(22)
        ])
        self.play(LaggedStart(*[GrowFromCenter(d) for d in fire_dots],
                               lag_ratio=0.04), run_time=0.8)
        self.play(
            LaggedStart(*[d.animate.shift(UP*0.3).set_opacity(0.2)
                          for d in fire_dots], lag_ratio=0.04),
            run_time=0.7
        )

        # Stats
        proj = VGroup(
            Text("At current rates:", font_size=24, color=DIM),
            Text("30% gone by 2050", font_size=30, color=RED, weight=BOLD),
        ).arrange(DOWN, buff=0.2).move_to(DOWN*2.8)
        impact = VGroup(
            Text("Species vanish forever.", font_size=22, color=ORANGE),
            Text("Rainfall patterns collapse.", font_size=22, color=ORANGE),
            Text("Carbon floods the atmosphere.", font_size=22, color=ORANGE),
        ).arrange(DOWN, buff=0.15).move_to(DOWN*4.4)

        self.play(FadeIn(proj, shift=UP*0.3), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(l, shift=UP*0.2) for l in impact],
                               lag_ratio=0.2), run_time=0.9)
        self.wait(1.0)

        # ══════════════════════════════════════════════════════════════
        # SCENE 5 — CLOSING + BRANDING
        # ══════════════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)
        self.add(make_leaf_particles(n=40, seed=7))

        # Dense layered forest for closing
        cl_bg = make_treeline(-6.5, 15, col=FOREST,  col2=CANOPY, seed=40)
        cl_mg = make_treeline(-5.2, 11, col=CANOPY,  col2=LEAF,   seed=50)
        cl_fg = make_treeline(-4.1,  8, col=LEAF,    col2=BRIGHT, seed=60)
        cl_cn = make_canopy_circles(n=25, y_min=5.5, y_max=8.8, seed=70)

        self.play(
            LaggedStart(*[GrowFromPoint(t, t.get_bottom()) for t in cl_bg], lag_ratio=0.04),
            LaggedStart(*[GrowFromPoint(t, t.get_bottom()) for t in cl_mg], lag_ratio=0.05),
            run_time=1.2
        )
        self.play(
            LaggedStart(*[GrowFromPoint(t, t.get_bottom()) for t in cl_fg], lag_ratio=0.06),
            LaggedStart(*[GrowFromCenter(c) for c in cl_cn], lag_ratio=0.03),
            run_time=1.0
        )

        # Sun rising
        sun      = Circle(radius=0.55, fill_color=GOLD, fill_opacity=1,
                          stroke_width=0).move_to(UP*0.4)
        sun_rays = VGroup(*[
            Line(sun.get_center(),
                 sun.get_center() + rotate_vector(RIGHT*0.95, i*TAU/10),
                 color=GOLD, stroke_width=2.5, stroke_opacity=0.65)
            for i in range(10)
        ])
        self.play(GrowFromCenter(sun), run_time=0.7)
        self.play(LaggedStart(*[Create(r) for r in sun_rays], lag_ratio=0.04),
                  run_time=0.6)
        self.play(Rotate(sun_rays, angle=TAU/20, rate_func=smooth), run_time=1.0)

        # Closing words
        c1 = Text("The Amazon isn't",     font_size=46, color=WHITE, weight=BOLD)
        c2 = Text("just Brazil's forest.", font_size=46, color=WHITE, weight=BOLD)
        c3 = Text("It belongs to every",  font_size=38, color=DIM)
        c4 = Text("breath you take.",     font_size=50, color=GOLD,  weight=BOLD)
        closing = VGroup(c1, c2, c3, c4).arrange(DOWN, buff=0.3).move_to(UP*3.8)

        self.play(
            LaggedStart(*[FadeIn(l, shift=UP*0.2) for l in closing], lag_ratio=0.22),
            run_time=2.0
        )

        # River at bottom of closing
        close_river = make_river(y=-5.5)
        self.play(Create(close_river), run_time=0.7)

        # Brand bar
        brand_bg  = RoundedRectangle(
            width=8.2, height=1.7, corner_radius=0.3,
            fill_color="#c8372d", fill_opacity=1, stroke_width=0
        ).move_to(DOWN*3.55)
        brand_txt = Text("ScrollUForward", font_size=40, color=WHITE,
                         weight=BOLD).move_to(DOWN*3.3)
        learn_txt = Text("Learn Something Real Every Day",
                         font_size=21, color="#ffe0de").move_to(DOWN*3.9)

        self.play(FadeIn(brand_bg), run_time=0.6)
        self.play(Write(brand_txt), Write(learn_txt), run_time=1.1)
        self.wait(2.5)
        self.play(FadeOut(*self.mobjects), run_time=1.2)
