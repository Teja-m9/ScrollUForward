from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0a0a12"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        PURPLE = "#7f5af0"
        CYAN = "#00d4ff"
        PINK = "#e53170"
        ORANGE = "#ff8906"
        TEXT_COL = "#fffffe"
        DIM = "#a7a9be"

        # ═══ SCENE 1: Hook — The Coin ═══
        q1 = Text("A coin is heads", font_size=38, color=TEXT_COL, weight=BOLD)
        q2 = Text("or tails.", font_size=38, color=TEXT_COL, weight=BOLD)
        q3 = Text("But what if it could be", font_size=34, color=DIM)
        q4 = Text("both at once?", font_size=48, color=PURPLE, weight=BOLD)
        hook = VGroup(q1, q2, q3, q4).arrange(DOWN, buff=0.35).move_to(UP * 3)

        coin = Circle(radius=1.2, color=ORANGE, fill_opacity=0.15, stroke_width=3).move_to(DOWN * 1.5)
        heads = Text("H", font_size=56, color=ORANGE, weight=BOLD).move_to(coin.get_center() + LEFT * 0.3)
        tails = Text("T", font_size=56, color=CYAN, weight=BOLD).move_to(coin.get_center() + RIGHT * 0.3)
        slash = Text("/", font_size=56, color=DIM).move_to(coin)
        coin_group = VGroup(coin, heads, slash, tails)

        self.play(Write(q1), Write(q2), run_time=1.5)
        self.play(Write(q3), run_time=0.8)
        self.play(Write(q4), run_time=1)
        self.play(GrowFromCenter(coin), FadeIn(heads), FadeIn(slash), FadeIn(tails), run_time=1.5)
        # Spinning effect
        self.play(
            Rotate(coin_group, angle=2 * PI, about_point=coin.get_center()),
            run_time=2, rate_func=smooth
        )
        self.wait(1)

        # ═══ SCENE 2: Superposition ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title2 = Text("Superposition", font_size=48, color=PURPLE, weight=BOLD).move_to(UP * 5.5)

        # Classical bit
        bit_box = RoundedRectangle(width=2.5, height=2.5, corner_radius=0.2,
            color=DIM, fill_opacity=0.05, stroke_width=2).move_to(LEFT * 2 + UP * 1.5)
        bit_label = Text("Classical Bit", font_size=22, color=DIM, weight=BOLD).next_to(bit_box, UP, buff=0.3)
        bit_0 = Text("0", font_size=52, color=ORANGE, weight=BOLD).move_to(bit_box)
        or_text = Text("or", font_size=22, color=DIM).move_to(bit_box.get_center() + RIGHT * 0.6)
        bit_1 = Text("1", font_size=52, color=CYAN, weight=BOLD).move_to(bit_box.get_center() + RIGHT * 1.2)
        # Only show one at a time
        bit_content = VGroup(bit_0)

        # Qubit
        qubit_box = RoundedRectangle(width=2.5, height=2.5, corner_radius=0.2,
            color=PURPLE, fill_opacity=0.08, stroke_width=2).move_to(RIGHT * 2 + UP * 1.5)
        qubit_label = Text("Qubit", font_size=22, color=PURPLE, weight=BOLD).next_to(qubit_box, UP, buff=0.3)
        qubit_0 = Text("0", font_size=44, color=ORANGE, weight=BOLD).move_to(qubit_box.get_center() + LEFT * 0.5 + UP * 0.2)
        qubit_and = Text("&", font_size=28, color=PURPLE).move_to(qubit_box)
        qubit_1 = Text("1", font_size=44, color=CYAN, weight=BOLD).move_to(qubit_box.get_center() + RIGHT * 0.5 + DOWN * 0.2)

        # Bloch sphere hint
        bloch = Circle(radius=1, color=PURPLE, stroke_width=1.5, fill_opacity=0.05).move_to(DOWN * 2.5)
        bloch_arrow = Arrow(
            bloch.get_center(),
            bloch.get_center() + np.array([0.5, 0.7, 0]),
            color=PURPLE, stroke_width=2
        )
        state_label = Text("|state\u27E9", font_size=22, color=PURPLE).next_to(bloch_arrow.get_end(), RIGHT, buff=0.2)
        zero_label = Text("|0\u27E9", font_size=20, color=ORANGE).move_to(bloch.get_top() + UP * 0.3)
        one_label = Text("|1\u27E9", font_size=20, color=CYAN).move_to(bloch.get_bottom() + DOWN * 0.3)

        self.play(Write(title2), run_time=1)
        self.play(
            FadeIn(bit_box), Write(bit_label), FadeIn(bit_0),
            run_time=1.5
        )
        # Toggle bit
        self.play(Transform(bit_0, Text("1", font_size=52, color=CYAN, weight=BOLD).move_to(bit_box)), run_time=0.5)
        self.play(Transform(bit_0, Text("0", font_size=52, color=ORANGE, weight=BOLD).move_to(bit_box)), run_time=0.5)
        self.play(
            FadeIn(qubit_box), Write(qubit_label),
            FadeIn(qubit_0), FadeIn(qubit_and), FadeIn(qubit_1),
            run_time=1.5
        )
        self.play(
            Create(bloch), GrowArrow(bloch_arrow),
            Write(state_label), Write(zero_label), Write(one_label),
            run_time=2
        )
        # Rotate the state arrow
        self.play(
            Rotate(bloch_arrow, angle=PI / 2, about_point=bloch.get_center()),
            run_time=2, rate_func=smooth
        )
        self.wait(1)

        # ═══ SCENE 3: Entanglement ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title3 = Text("Entanglement", font_size=48, color=PINK, weight=BOLD).move_to(UP * 5.5)
        desc = Text("Spooky action at a distance", font_size=24, color=DIM).move_to(UP * 4.5)

        p1 = Circle(radius=0.8, color=PURPLE, fill_opacity=0.2, stroke_width=3).move_to(LEFT * 2.5 + UP * 1)
        p1_label = Text("Particle A", font_size=22, color=PURPLE, weight=BOLD).next_to(p1, UP, buff=0.3)
        p1_spin = Arrow(p1.get_center(), p1.get_center() + UP * 0.5, color=PURPLE, stroke_width=3)

        p2 = Circle(radius=0.8, color=PINK, fill_opacity=0.2, stroke_width=3).move_to(RIGHT * 2.5 + UP * 1)
        p2_label = Text("Particle B", font_size=22, color=PINK, weight=BOLD).next_to(p2, UP, buff=0.3)
        p2_spin = Arrow(p2.get_center(), p2.get_center() + DOWN * 0.5, color=PINK, stroke_width=3)

        # Wavy connection
        link = DashedLine(p1.get_right(), p2.get_left(), color=CYAN, stroke_width=2, dash_length=0.15)
        link_label = Text("Entangled!", font_size=24, color=CYAN, weight=BOLD).move_to(UP * 1 + DOWN * 1.2)

        distance = Text("Even light-years apart", font_size=24, color=DIM).move_to(DOWN * 2.5)
        galaxies = VGroup(
            Text("\u2605", font_size=28, color=PURPLE).move_to(LEFT * 3 + DOWN * 3.5),
            Text("\u2605", font_size=28, color=PINK).move_to(RIGHT * 3 + DOWN * 3.5),
        )
        dist_arrow = Arrow(LEFT * 2.5 + DOWN * 3.5, RIGHT * 2.5 + DOWN * 3.5, color=DIM, stroke_width=1.5)

        self.play(Write(title3), Write(desc), run_time=1.5)
        self.play(
            GrowFromCenter(p1), Write(p1_label), GrowArrow(p1_spin),
            GrowFromCenter(p2), Write(p2_label), GrowArrow(p2_spin),
            run_time=2
        )
        self.play(Create(link), Write(link_label), run_time=1.5)
        # Flip spin simultaneously
        self.play(
            Rotate(p1_spin, angle=PI, about_point=p1.get_center()),
            Rotate(p2_spin, angle=PI, about_point=p2.get_center()),
            Flash(p1, color=PURPLE, num_lines=6),
            Flash(p2, color=PINK, num_lines=6),
            run_time=1.5
        )
        self.play(Write(distance), FadeIn(galaxies), GrowArrow(dist_arrow), run_time=1.5)
        self.wait(1.5)

        # ═══ SCENE 4: Quantum Computing ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title4 = Text("Quantum Computing", font_size=42, color=CYAN, weight=BOLD).move_to(UP * 5.5)

        classical = VGroup(
            Text("Classical", font_size=24, color=DIM, weight=BOLD),
            Text("Try paths one", font_size=20, color=DIM),
            Text("by one", font_size=20, color=DIM),
        ).arrange(DOWN, buff=0.2).move_to(LEFT * 2 + UP * 2.5)

        quantum = VGroup(
            Text("Quantum", font_size=24, color=CYAN, weight=BOLD),
            Text("Try ALL paths", font_size=20, color=CYAN),
            Text("at once", font_size=20, color=CYAN),
        ).arrange(DOWN, buff=0.2).move_to(RIGHT * 2 + UP * 2.5)

        # Maze metaphor
        maze_lines_c = VGroup()
        for i in range(5):
            y = -0.5 - i * 0.8
            line = Line(LEFT * 3.5, LEFT * 1, color=DIM, stroke_width=1.5).move_to(UP * y + LEFT * 0.5)
            maze_lines_c.add(line)
        dot_c = Dot(radius=0.12, color=ORANGE).move_to(maze_lines_c[0].get_left())

        maze_lines_q = VGroup()
        for i in range(5):
            y = -0.5 - i * 0.8
            line = Line(RIGHT * 1, RIGHT * 3.5, color=CYAN, stroke_width=1.5, stroke_opacity=0.6).move_to(UP * y + RIGHT * 0.5)
            maze_lines_q.add(line)
        dots_q = VGroup(*[
            Dot(radius=0.1, color=CYAN, fill_opacity=0.6).move_to(line.get_left())
            for line in maze_lines_q
        ])

        self.play(Write(title4), run_time=1)
        self.play(FadeIn(classical), FadeIn(quantum), run_time=1)
        self.play(
            LaggedStart(*[Create(l) for l in maze_lines_c], lag_ratio=0.15),
            LaggedStart(*[Create(l) for l in maze_lines_q], lag_ratio=0.15),
            run_time=1.5
        )
        self.play(FadeIn(dot_c), FadeIn(dots_q), run_time=1)

        # Classical: one at a time
        for i, line in enumerate(maze_lines_c):
            if i > 0:
                self.play(dot_c.animate.move_to(line.get_left()), run_time=0.2)
            self.play(dot_c.animate.move_to(line.get_right()), run_time=0.4)

        # Quantum: all at once (already there)
        self.play(
            *[d.animate.move_to(maze_lines_q[i].get_right()) for i, d in enumerate(dots_q)],
            run_time=1, rate_func=smooth
        )
        self.play(*[Flash(d, color=CYAN, num_lines=4, flash_radius=0.3) for d in dots_q], run_time=1)
        self.wait(1)

        # ═══ SCENE 5: Closing ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        final = Text("Quantum", font_size=60, color=PURPLE, weight=BOLD).move_to(UP * 1.5)
        final2 = Text("is the Future", font_size=48, color=TEXT_COL, weight=BOLD).move_to(UP * 0)
        glow = Circle(radius=3, color=PURPLE, fill_opacity=0.04, stroke_width=1).move_to(UP * 0.75)

        tagline = Text("The weird science that will", font_size=26, color=DIM).move_to(DOWN * 2.5)
        tagline2 = Text("change everything", font_size=32, color=CYAN, weight=BOLD).move_to(DOWN * 3.2)
        self.play(GrowFromCenter(glow), run_time=1)
        self.play(Write(final), run_time=1.5)
        self.play(Write(final2), run_time=1)
        self.play(FadeIn(tagline), FadeIn(tagline2, shift=UP * 0.3), run_time=1.5)
        self.play(glow.animate.scale(1.1), rate_func=there_and_back, run_time=2)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
