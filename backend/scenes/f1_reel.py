from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        BG     = "#0c0c0f"
        RED    = "#e8002d"   # F1 red
        GOLD   = "#f5a623"
        WHITE  = "#ffffff"
        DIM    = "#6a6a7a"
        SILVER = "#c0c0c0"
        CYAN   = "#00d2ff"
        ORANGE = "#ff8700"   # McLaren
        TEAL   = "#00d2be"   # Mercedes
        NAVY   = "#3671c6"   # Red Bull
        SCARLET= "#dc0000"   # Ferrari
        GREEN  = "#00a651"   # Podium

        self.camera.background_color = BG
        self.camera.frame_width  = 9
        self.camera.frame_height = 16

        # ── helpers ───────────────────────────────────────────────────
        def make_f1_car(x, y, col=RED, scale=1.0):
            body    = Polygon(
                [-1.6, -0.18, 0], [1.6, -0.18, 0],
                [1.3,  0.18, 0],  [-1.0, 0.28, 0],
                fill_color=col, fill_opacity=1, stroke_width=0
            ).scale(scale)
            nose    = Polygon(
                [1.3, 0.0, 0], [2.0, -0.06, 0], [1.6, -0.18, 0],
                fill_color=col, fill_opacity=1, stroke_width=0
            ).scale(scale)
            wing_f  = Rectangle(width=1.0*scale, height=0.10*scale,
                                fill_color=SILVER, fill_opacity=1, stroke_width=0)\
                        .move_to(RIGHT*1.75*scale + DOWN*0.22*scale)
            wing_r  = Rectangle(width=0.7*scale, height=0.10*scale,
                                fill_color=SILVER, fill_opacity=1, stroke_width=0)\
                        .move_to(LEFT*1.55*scale + UP*0.12*scale)
            w1      = Circle(radius=0.18*scale, fill_color="#111111",
                             fill_opacity=1, stroke_color=SILVER, stroke_width=1)\
                        .move_to(LEFT*0.9*scale + DOWN*0.25*scale)
            w2      = Circle(radius=0.18*scale, fill_color="#111111",
                             fill_opacity=1, stroke_color=SILVER, stroke_width=1)\
                        .move_to(RIGHT*0.7*scale + DOWN*0.25*scale)
            return VGroup(body, nose, wing_f, wing_r, w1, w2).move_to([x, y, 0])

        def speed_trail(car_group, n=8):
            lines = VGroup()
            x_start = car_group.get_left()[0]
            y_c     = car_group.get_center()[1]
            for i in range(n):
                alpha = 0.6 - i * 0.06
                length= 0.4 + i * 0.25
                l = Line(
                    [x_start - 0.1 - i*0.35, y_c + np.random.uniform(-0.08, 0.08), 0],
                    [x_start - 0.1 - i*0.35 - length, y_c + np.random.uniform(-0.08, 0.08), 0],
                    color=RED, stroke_width=2.5 - i*0.2, stroke_opacity=alpha
                )
                lines.add(l)
            return lines

        def team_bar(driver, team, titles, col, y):
            bg   = RoundedRectangle(width=8.0, height=0.88, corner_radius=0.18,
                                    fill_color="#1a1a25", fill_opacity=1,
                                    stroke_color=col, stroke_width=1.5).move_to(UP*y)
            accent = Rectangle(width=0.18, height=0.88,
                               fill_color=col, fill_opacity=1, stroke_width=0)\
                        .align_to(bg, LEFT).move_to(LEFT*3.92 + UP*y)
            drv  = Text(driver,  font_size=22, color=WHITE, weight=BOLD)\
                    .move_to(LEFT*2.1 + UP*y+0.16)
            tm   = Text(team,    font_size=17, color=col)\
                    .move_to(LEFT*2.2 + UP*y-0.17)
            wdc  = Text(f"{titles}x WDC", font_size=20, color=GOLD, weight=BOLD)\
                    .move_to(RIGHT*2.8 + UP*y)
            return VGroup(bg, accent, drv, tm, wdc)

        # ═══════════════════════════════════════════════════════
        # SCENE 1 — HOOK
        # ═══════════════════════════════════════════════════════
        # Track curve across screen
        track = VMobject(color="#2a2a35", stroke_width=60, stroke_opacity=1)
        track.set_points_smoothly([
            np.array([-4.6, -2.5, 0]),
            np.array([-1.5, -1.5, 0]),
            np.array([0.0,  -2.0, 0]),
            np.array([2.0,  -1.2, 0]),
            np.array([4.6,  -2.0, 0]),
        ])
        track_line = VMobject(color=WHITE, stroke_width=1.5, stroke_opacity=0.25)
        track_line.set_points_smoothly([
            np.array([-4.6, -2.5, 0]),
            np.array([-1.5, -1.5, 0]),
            np.array([0.0,  -2.0, 0]),
            np.array([2.0,  -1.2, 0]),
            np.array([4.6,  -2.0, 0]),
        ])
        self.play(Create(track), Create(track_line), run_time=0.8)

        # Car enters from left
        car = make_f1_car(-6.5, -2.0, col=RED, scale=0.95)
        trail = speed_trail(car)
        self.add(trail)
        self.play(
            car.animate.move_to([0.5, -2.0, 0]),
            run_time=1.2, rate_func=rush_from
        )
        self.play(
            Flash(car.get_center() + RIGHT*1.5, color=RED,
                  num_lines=8, flash_radius=0.5),
            run_time=0.5
        )

        # Title
        tag   = Text("FORMULA ONE", font_size=34, color=RED, weight=BOLD).move_to(UP*6.5)
        title = Text("The Fastest", font_size=60, color=WHITE, weight=BOLD).move_to(UP*5.3)
        title2= Text("Sport on Earth", font_size=54, color=GOLD, weight=BOLD).move_to(UP*4.2)

        self.play(FadeIn(tag, shift=DOWN*0.3), run_time=0.5)
        self.play(Write(title),  run_time=0.8)
        self.play(Write(title2), run_time=0.8)

        # Key stats
        stats = VGroup(
            Text("360 km/h  ·  Top Speed",   font_size=22, color=SILVER),
            Text("6G  ·  Cornering Force",    font_size=22, color=SILVER),
            Text("1000+ hp  ·  Power Output", font_size=22, color=SILVER),
        ).arrange(DOWN, buff=0.32).move_to(UP*1.8)
        for s in stats:
            dot = Dot(radius=0.06, color=RED, fill_opacity=1)\
                    .next_to(s, LEFT, buff=0.15)
            self.play(GrowFromCenter(dot), FadeIn(s, shift=RIGHT*0.2), run_time=0.35)

        # Second car zooms past
        car2 = make_f1_car(-7.0, -2.0, col=NAVY, scale=0.80)
        self.play(car2.animate.move_to([7.0, -2.0, 0]),
                  run_time=0.7, rate_func=rush_from)
        self.wait(0.6)

        # ═══════════════════════════════════════════════════════
        # SCENE 2 — WHAT IS F1
        # ═══════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)

        t2    = Text("The Championship", font_size=50, color=GOLD, weight=BOLD).move_to(UP*6.2)
        t2sub = Text("24 races · 10 teams · 20 drivers", font_size=26,
                     color=DIM).move_to(UP*5.2)
        self.play(Write(t2), run_time=0.9)
        self.play(FadeIn(t2sub, shift=UP*0.2), run_time=0.6)

        # World map dots (race locations)
        race_dots = VGroup(*[
            Dot(radius=0.14, color=RED, fill_opacity=0.9).move_to([x, y, 0])
            for x, y in [
                (-3.5, 2.5),  # Americas
                (-3.0, 1.8),
                (-2.8, 0.8),
                (-0.5, 2.8),  # Europe
                (0.2, 2.5),
                (0.8, 2.2),
                (1.2, 2.7),
                (1.8, 1.8),   # Middle East
                (2.8, 1.5),
                (3.5, -0.5),  # Asia/Pacific
                (3.8, 0.2),
                (3.2, 0.8),
            ]
        ])
        # Connecting pulse lines
        globe_circle = Circle(radius=3.2, color=DIM, stroke_width=1,
                              stroke_opacity=0.25, fill_opacity=0).move_to(UP*1.5)
        self.play(Create(globe_circle), run_time=0.6)
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in race_dots], lag_ratio=0.06),
            run_time=1.2
        )

        # Season calendar strip
        cal = VGroup(
            Text("Bahrain → Saudi Arabia → Australia → Japan → China ...",
                 font_size=17, color=DIM),
            Text("... Las Vegas → Qatar → Abu Dhabi",
                 font_size=17, color=DIM),
        ).arrange(DOWN, buff=0.18).move_to(DOWN*1.8)
        self.play(FadeIn(cal, shift=UP*0.2), run_time=0.7)

        fact_box_bg = RoundedRectangle(
            width=8.0, height=1.1, corner_radius=0.22,
            fill_color="#1a1a25", fill_opacity=0.9,
            stroke_color=RED, stroke_width=1.5
        ).move_to(DOWN*3.2)
        fact_box_tx = Text(
            "Constructors' & Drivers' Championship — two titles per season",
            font_size=20, color=WHITE
        ).move_to(DOWN*3.2)
        self.play(FadeIn(fact_box_bg), Write(fact_box_tx), run_time=0.8)
        self.wait(0.8)

        # ═══════════════════════════════════════════════════════
        # SCENE 3 — THE LEGENDS
        # ═══════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)

        t3    = Text("The Legends", font_size=54, color=GOLD, weight=BOLD).move_to(UP*6.2)
        t3sub = Text("Greatest drivers in F1 history", font_size=26,
                     color=DIM).move_to(UP*5.2)
        self.play(Write(t3), run_time=0.9)
        self.play(FadeIn(t3sub, shift=UP*0.2), run_time=0.6)

        legends = [
            ("Ayrton Senna",      "McLaren",          3, CYAN,   3.8),
            ("Alain Prost",       "McLaren / Ferrari", 4, WHITE,  2.6),
            ("Michael Schumacher","Ferrari",           7, SCARLET,1.4),
            ("Sebastian Vettel",  "Red Bull",          4, NAVY,   0.2),
            ("Fernando Alonso",   "Renault / Alpine",  2, ORANGE,-1.0),
        ]
        for driver, team, titles, col, y in legends:
            bar = team_bar(driver, team, titles, col, y)
            self.play(FadeIn(bar, shift=LEFT*0.3), run_time=0.45)

        legend_note = Text("* Schumacher & Hamilton share the all-time record: 7 titles",
                           font_size=17, color=DIM).move_to(DOWN*2.4)
        self.play(FadeIn(legend_note), run_time=0.7)

        # Mini trophy icons (triangles)
        trophies = VGroup(*[
            Triangle(fill_color=GOLD, fill_opacity=0.9, stroke_width=0)
            .scale(0.18)
            .move_to([-3.5 + i*0.45, -3.3, 0])
            for i in range(7)
        ])
        self.play(LaggedStart(*[GrowFromCenter(t) for t in trophies], lag_ratio=0.08),
                  run_time=0.7)
        self.wait(0.8)

        # ═══════════════════════════════════════════════════════
        # SCENE 4 — MODERN STARS
        # ═══════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)

        t4    = Text("Today's Stars", font_size=54, color=CYAN, weight=BOLD).move_to(UP*6.2)
        t4sub = Text("The current generation rewriting records",
                     font_size=24, color=DIM).move_to(UP*5.2)
        self.play(Write(t4), run_time=0.9)
        self.play(FadeIn(t4sub, shift=UP*0.2), run_time=0.6)

        modern = [
            ("Lewis Hamilton",  "Ferrari",  7, SCARLET, 3.8),
            ("Max Verstappen",  "Red Bull", 4, NAVY,    2.6),
            ("Fernando Alonso", "Aston Martin", 2, "#006f62", 1.4),
            ("Charles Leclerc", "Ferrari",  0, SCARLET, 0.2),
            ("Lando Norris",    "McLaren",  0, ORANGE, -1.0),
            ("Carlos Sainz",    "Williams", 0, CYAN,   -2.2),
        ]
        for driver, team, titles, col, y in modern:
            bar = team_bar(driver, team, titles, col, y)
            self.play(FadeIn(bar, shift=LEFT*0.3), run_time=0.40)

        # Live race — two cars racing
        car_a = make_f1_car(-5.5, -4.2, col=RED,  scale=0.65)
        car_b = make_f1_car(-5.8, -4.9, col=NAVY, scale=0.65)
        self.add(car_a, car_b)
        self.play(
            car_a.animate.move_to([4.5, -4.2, 0]),
            car_b.animate.move_to([3.8, -4.9, 0]),
            run_time=1.4, rate_func=rush_from
        )
        self.wait(0.5)

        # ═══════════════════════════════════════════════════════
        # SCENE 5 — TECHNOLOGY
        # ═══════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.7)

        t5    = Text("The Machine", font_size=54, color=SILVER, weight=BOLD).move_to(UP*6.2)
        t5sub = Text("Engineering at the limits of physics",
                     font_size=24, color=DIM).move_to(UP*5.2)
        self.play(Write(t5), run_time=0.9)
        self.play(FadeIn(t5sub, shift=UP*0.2), run_time=0.6)

        # Large car diagram with labels
        big_car = make_f1_car(0, 1.2, col=RED, scale=1.6)
        self.play(GrowFromCenter(big_car), run_time=1.0)

        # Annotation arrows
        annots = [
            (RIGHT*2.8 + UP*1.6,  RIGHT*1.2 + UP*1.4, "Front Wing — Aero",   SILVER),
            (LEFT*3.0  + UP*1.5,  LEFT*1.4  + UP*1.5, "Rear Wing — DRS",      CYAN),
            (UP*3.0,              UP*1.7,              "Hybrid V6 — 1000 hp",  GOLD),
            (LEFT*2.5  + UP*0.4,  LEFT*0.5  + UP*0.9, "Halo — Driver Safety", WHITE),
        ]
        for end, start, label, col in annots:
            arr = Arrow(start, end, color=col, stroke_width=2, buff=0.05,
                        max_tip_length_to_length_ratio=0.15)
            lbl = Text(label, font_size=18, color=col).move_to(
                end + (end - start) * 0.35
            )
            self.play(GrowArrow(arr), FadeIn(lbl), run_time=0.5)

        # Weight/power strip
        spec_bg = RoundedRectangle(
            width=8.2, height=1.6, corner_radius=0.22,
            fill_color="#1a1a25", fill_opacity=0.9,
            stroke_color=RED, stroke_width=1.5
        ).move_to(DOWN*3.2)
        spec_tx = VGroup(
            Text("798 kg  ·  total car weight",  font_size=21, color=WHITE),
            Text("1000+ hp  ·  rebuilt every race", font_size=21, color=GOLD),
        ).arrange(DOWN, buff=0.18).move_to(DOWN*3.2)
        self.play(FadeIn(spec_bg), FadeIn(spec_tx), run_time=0.8)
        self.wait(1.0)

        # ═══════════════════════════════════════════════════════
        # END CARD — PURE BLACK SCREEN
        # ═══════════════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=1.0)
        self.camera.background_color = "#000000"
        self.wait(0.2)

        logo_txt  = Text("ScrollUForward", font_size=52, color=WHITE,
                         weight=BOLD).move_to(UP*0.6)
        tagline   = Text("Learn Something Real Every Day",
                         font_size=26, color="#bbbbbb").move_to(DOWN*0.4)
        rule      = Line(LEFT*2.5, RIGHT*2.5, color="#444444",
                         stroke_width=1).move_to(DOWN*0.0)

        self.play(FadeIn(logo_txt, shift=UP*0.3), run_time=0.9)
        self.play(FadeIn(rule), FadeIn(tagline, shift=UP*0.2), run_time=0.7)
        self.wait(3.0)
        self.play(FadeOut(logo_txt, tagline, rule), run_time=0.8)
