from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0f0e17"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        RED = "#e53170"
        BLUE = "#00b4d8"
        GREEN = "#2cb67d"
        ORANGE = "#ff8906"
        YELLOW = "#FFD700"
        TEXT_COL = "#fffffe"
        DIM = "#a7a9be"

        # ═══ SCENE 1: Hook ═══
        t1 = Text("Earth has warmed", font_size=40, color=TEXT_COL, weight=BOLD)
        t2 = Text("1.2\u00b0C", font_size=72, color=RED, weight=BOLD)
        t3 = Text("since 1850", font_size=36, color=DIM)
        hook = VGroup(t1, t2, t3).arrange(DOWN, buff=0.4).move_to(UP * 3)

        earth = Circle(radius=1.5, color=BLUE, fill_opacity=0.15, stroke_width=2).move_to(DOWN * 1.5)
        land = VGroup(
            Ellipse(width=1, height=0.6, color=GREEN, fill_opacity=0.3, stroke_width=0).move_to(earth.get_center() + LEFT * 0.3 + UP * 0.4),
            Ellipse(width=0.7, height=0.5, color=GREEN, fill_opacity=0.3, stroke_width=0).move_to(earth.get_center() + RIGHT * 0.4 + DOWN * 0.2),
        )
        heat_waves = VGroup(*[
            Arc(radius=1.8 + i * 0.3, angle=PI / 3, start_angle=PI / 6 + i * 0.2,
                color=RED, stroke_width=2, stroke_opacity=0.5 - i * 0.1).move_to(earth)
            for i in range(4)
        ])

        self.play(Write(t1), run_time=1)
        self.play(Write(t2), run_time=1)
        self.play(Write(t3), run_time=0.8)
        self.play(GrowFromCenter(earth), FadeIn(land), run_time=1.5)
        self.play(
            LaggedStart(*[Create(w) for w in heat_waves], lag_ratio=0.2),
            run_time=2
        )
        self.wait(1.5)

        # ═══ SCENE 2: The Greenhouse Effect ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title2 = Text("The Greenhouse Effect", font_size=42, color=ORANGE, weight=BOLD).move_to(UP * 5.5)

        ground = Line(LEFT * 4, RIGHT * 4, color=GREEN, stroke_width=3).move_to(DOWN * 2)
        ground_label = Text("Earth's Surface", font_size=18, color=GREEN).next_to(ground, DOWN, buff=0.3)

        atmo = DashedLine(LEFT * 4, RIGHT * 4, color=BLUE, stroke_width=2, dash_length=0.2).move_to(UP * 2)
        atmo_label = Text("Atmosphere", font_size=18, color=BLUE).next_to(atmo, UP, buff=0.3)

        # Sun rays coming in
        sun = Circle(radius=0.5, color=YELLOW, fill_opacity=0.5, stroke_width=2).move_to(LEFT * 3 + UP * 4)
        sun_label = Text("\u2600", font_size=36, color=YELLOW).move_to(sun)

        ray_in = Arrow(sun.get_center() + DOWN * 0.5 + RIGHT * 0.5, DOWN * 1, color=YELLOW, stroke_width=2)
        ray_label = Text("Sunlight in", font_size=18, color=YELLOW).next_to(ray_in, RIGHT, buff=0.2)

        # Heat radiating up
        heat_up = Arrow(DOWN * 1.5, UP * 0.5, color=RED, stroke_width=2).move_to(RIGHT * 0.5)
        heat_label = Text("Heat out", font_size=18, color=RED).next_to(heat_up, LEFT, buff=0.2)

        # Trapped heat bouncing back
        trapped = Arrow(UP * 1, DOWN * 0, color=ORANGE, stroke_width=2).move_to(RIGHT * 2)
        trap_label = Text("Trapped!", font_size=20, color=ORANGE, weight=BOLD).next_to(trapped, RIGHT, buff=0.2)

        # CO2 molecules
        co2_mols = VGroup()
        for pos in [LEFT * 1 + UP * 1, RIGHT * 0.5 + UP * 1.5, RIGHT * 2.5 + UP * 0.5, LEFT * 2 + UP * 2]:
            c = Circle(radius=0.12, color=ORANGE, fill_opacity=0.4, stroke_width=1.5)
            o1 = Circle(radius=0.1, color=RED, fill_opacity=0.3, stroke_width=1).move_to(c.get_center() + LEFT * 0.2)
            o2 = Circle(radius=0.1, color=RED, fill_opacity=0.3, stroke_width=1).move_to(c.get_center() + RIGHT * 0.2)
            mol = VGroup(o1, c, o2).move_to(pos)
            co2_mols.add(mol)

        co2_label = Text("CO\u2082 molecules", font_size=20, color=ORANGE).move_to(LEFT * 2 + DOWN * 3.5)

        self.play(Write(title2), run_time=1)
        self.play(Create(ground), Write(ground_label), Create(atmo), Write(atmo_label), run_time=1.5)
        self.play(FadeIn(sun), FadeIn(sun_label), run_time=0.8)
        self.play(GrowArrow(ray_in), Write(ray_label), run_time=1)
        self.play(GrowArrow(heat_up), Write(heat_label), run_time=1)
        self.play(
            LaggedStart(*[GrowFromCenter(m) for m in co2_mols], lag_ratio=0.15),
            Write(co2_label),
            run_time=1.5
        )
        self.play(GrowArrow(trapped), Write(trap_label), run_time=1.5)
        self.play(Indicate(trap_label, color=ORANGE, scale_factor=1.15), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 3: CO2 Rising ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title3 = Text("CO\u2082 Is Skyrocketing", font_size=42, color=RED, weight=BOLD).move_to(UP * 5.5)

        axes = Axes(x_range=[1900, 2030, 20], y_range=[280, 430, 30], x_length=6.5, y_length=5,
            axis_config={"color": DIM, "stroke_width": 1.5, "include_numbers": False}).move_to(UP * 0.5)

        x_labels = VGroup(
            Text("1900", font_size=16, color=DIM).move_to(axes.c2p(1900, 275)),
            Text("1960", font_size=16, color=DIM).move_to(axes.c2p(1960, 275)),
            Text("2024", font_size=16, color=DIM).move_to(axes.c2p(2020, 275)),
        )
        y_label = Text("CO\u2082 (ppm)", font_size=18, color=DIM).next_to(axes.y_axis, LEFT, buff=0.4).rotate(PI / 2)

        # CO2 curve - exponential-ish rise
        co2_curve = axes.plot(
            lambda x: 280 + 0.0003 * (x - 1900) ** 2.2,
            x_range=[1900, 2025], color=RED, stroke_width=3
        )

        safe_line = DashedLine(
            axes.c2p(1900, 350), axes.c2p(2030, 350),
            color=GREEN, stroke_width=2, dash_length=0.15
        )
        safe_label = Text("Safe limit: 350 ppm", font_size=18, color=GREEN).next_to(safe_line, UP, buff=0.15)

        now_dot = Dot(radius=0.15, color=RED).move_to(axes.c2p(2024, 422))
        now_label = Text("422 ppm", font_size=22, color=RED, weight=BOLD).next_to(now_dot, UP, buff=0.3)

        self.play(Write(title3), run_time=1)
        self.play(Create(axes), FadeIn(x_labels), Write(y_label), run_time=1.5)
        self.play(Create(safe_line), Write(safe_label), run_time=1)
        self.play(Create(co2_curve), run_time=3, rate_func=smooth)
        self.play(FadeIn(now_dot, scale=2), Write(now_label), run_time=1.5)
        self.play(Flash(now_dot, color=RED, num_lines=8), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 4: Solutions ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title4 = Text("What Can We Do?", font_size=44, color=GREEN, weight=BOLD).move_to(UP * 5.5)

        solutions = [
            ("\u2600", "Solar & Wind", "Replace fossil fuels", GREEN),
            ("\U0001F333", "Plant Trees", "Natural carbon capture", "#2ECC71"),
            ("\u26A1", "Electrify Transport", "EVs over gasoline", BLUE),
            ("\U0001F3ED", "Clean Industry", "Green steel & cement", ORANGE),
        ]

        cards = VGroup()
        for emoji, name, desc, col in solutions:
            card = RoundedRectangle(width=7, height=1.6, corner_radius=0.2,
                color=col, fill_opacity=0.08, stroke_width=1.5)
            icon = Text(emoji, font_size=32).move_to(card.get_left() + RIGHT * 0.8)
            n = Text(name, font_size=24, color=col, weight=BOLD).move_to(card.get_left() + RIGHT * 2.5 + UP * 0.2)
            d = Text(desc, font_size=18, color=DIM).move_to(card.get_left() + RIGHT * 2.8 + DOWN * 0.25)
            cards.add(VGroup(card, icon, n, d))
        cards.arrange(DOWN, buff=0.35).move_to(UP * 0.5)

        self.play(Write(title4), run_time=1)
        self.play(
            LaggedStart(*[FadeIn(c, shift=RIGHT * 0.5) for c in cards], lag_ratio=0.25),
            run_time=3
        )
        self.wait(2)

        # ═══ SCENE 5: Closing ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        earth_final = Circle(radius=2, color=BLUE, fill_opacity=0.1, stroke_width=3).move_to(UP * 0.5)
        land_final = VGroup(
            Ellipse(width=1.2, height=0.7, color=GREEN, fill_opacity=0.3, stroke_width=0).move_to(earth_final.get_center() + LEFT * 0.3 + UP * 0.5),
            Ellipse(width=0.8, height=0.5, color=GREEN, fill_opacity=0.3, stroke_width=0).move_to(earth_final.get_center() + RIGHT * 0.5 + DOWN * 0.3),
        )

        closing1 = Text("One Planet.", font_size=44, color=TEXT_COL, weight=BOLD)
        closing2 = Text("One Chance.", font_size=44, color=GREEN, weight=BOLD)
        closing = VGroup(closing1, closing2).arrange(DOWN, buff=0.3).move_to(DOWN * 3.5)
        self.play(GrowFromCenter(earth_final), FadeIn(land_final), run_time=2)
        self.play(FadeIn(closing1, shift=UP * 0.3), run_time=1)
        self.play(FadeIn(closing2, shift=UP * 0.3), run_time=1)
        self.play(earth_final.animate.scale(1.05), rate_func=there_and_back, run_time=2)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
