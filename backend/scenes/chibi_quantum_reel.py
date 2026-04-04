from manim import *
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from chibi_character import ChibiCharacter

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

        # ── Create our physics chibi (energetic fighter style) ──
        chibi = ChibiCharacter(style="energetic", color="#E74C3C", accent="#FFD700")
        chibi.scale(0.9).move_to(RIGHT * 3 + DOWN * 5.5)

        # ═══ SCENE 1: Character intro + Hook ═══
        # Character slides in from the right
        chibi_start = chibi.copy().shift(RIGHT * 3)
        self.add(chibi_start)
        self.play(chibi_start.animate.move_to(chibi.get_center()), run_time=1, rate_func=smooth)
        self.remove(chibi_start)
        self.add(chibi)

        # Character waves hello
        chibi.wave(self, duration=1.2)

        # Speech bubble
        intro_bg = RoundedRectangle(width=5, height=0.8, corner_radius=0.2,
            color=WHITE, fill_opacity=0.9, stroke_color="#E74C3C", stroke_width=2)
        intro_text = Text("Let's learn something epic!", font_size=22, color=BLACK, weight=BOLD)
        intro_text.move_to(intro_bg)
        intro_bubble = VGroup(intro_bg, intro_text).next_to(chibi, UP, buff=0.2)
        tail = Triangle(color=WHITE, fill_opacity=0.9, stroke_color="#E74C3C", stroke_width=2)
        tail.scale(0.1).rotate(PI).next_to(intro_bg, DOWN, buff=-0.02)
        intro_bubble.add(tail)

        self.play(FadeIn(intro_bubble, scale=0.5), run_time=0.6)

        # Hook text appears
        q1 = Text("A coin is heads", font_size=38, color=TEXT_COL, weight=BOLD)
        q2 = Text("or tails.", font_size=38, color=TEXT_COL, weight=BOLD)
        q3 = Text("But what if it's", font_size=34, color=DIM)
        q4 = Text("both at once?", font_size=48, color=PURPLE, weight=BOLD)
        hook = VGroup(q1, q2, q3, q4).arrange(DOWN, buff=0.35).move_to(UP * 3)

        self.play(Write(q1), Write(q2), run_time=1.5)
        self.play(FadeOut(intro_bubble), run_time=0.3)
        self.play(Write(q3), run_time=0.8)
        self.play(Write(q4), run_time=1)

        # Character bounces with excitement
        chibi.bounce(self, times=2, height=0.15, duration=0.8)

        # Coin animation
        coin = Circle(radius=1.0, color=ORANGE, fill_opacity=0.15, stroke_width=3).move_to(DOWN * 1)
        heads = Text("H", font_size=48, color=ORANGE, weight=BOLD).move_to(coin.get_center() + LEFT * 0.25)
        slash = Text("/", font_size=48, color=DIM).move_to(coin)
        tails = Text("T", font_size=48, color=CYAN, weight=BOLD).move_to(coin.get_center() + RIGHT * 0.25)
        coin_group = VGroup(coin, heads, slash, tails)

        self.play(GrowFromCenter(coin), FadeIn(heads), FadeIn(slash), FadeIn(tails), run_time=1.5)

        # Character points at coin
        chibi.point_at(self, coin.get_center(), duration=0.6)

        # Spin coin
        self.play(
            Rotate(coin_group, angle=2 * PI, about_point=coin.get_center()),
            run_time=2, rate_func=smooth
        )

        # Character nods
        chibi.nod(self, times=2, duration=0.6)
        self.wait(0.5)

        # ═══ SCENE 2: Superposition ═══
        # Keep chibi, fade everything else
        self.play(FadeOut(hook), FadeOut(coin_group), run_time=0.6)

        # Reset arm
        arm = chibi.arm_right
        shoulder = arm[0].get_start()
        self.play(Rotate(arm, angle=-0.5, about_point=shoulder), run_time=0.3)

        title2 = Text("Superposition", font_size=48, color=PURPLE, weight=BOLD).move_to(UP * 5.5)
        self.play(Write(title2), run_time=1)

        # Classical bit vs Qubit
        bit_box = RoundedRectangle(width=2.5, height=2, corner_radius=0.2,
            color=DIM, fill_opacity=0.05, stroke_width=2).move_to(LEFT * 2 + UP * 1.5)
        bit_label = Text("Classical Bit", font_size=20, color=DIM, weight=BOLD).next_to(bit_box, UP, buff=0.2)
        bit_0 = Text("0 or 1", font_size=36, color=ORANGE, weight=BOLD).move_to(bit_box)

        qubit_box = RoundedRectangle(width=2.5, height=2, corner_radius=0.2,
            color=PURPLE, fill_opacity=0.08, stroke_width=2).move_to(RIGHT * 0.5 + UP * 1.5)
        qubit_label = Text("Qubit", font_size=20, color=PURPLE, weight=BOLD).next_to(qubit_box, UP, buff=0.2)
        q_content = VGroup(
            Text("0", font_size=36, color=ORANGE, weight=BOLD),
            Text(" & ", font_size=24, color=PURPLE),
            Text("1", font_size=36, color=CYAN, weight=BOLD),
        ).arrange(RIGHT, buff=0.1).move_to(qubit_box)

        self.play(FadeIn(bit_box), Write(bit_label), FadeIn(bit_0), run_time=1.5)

        # Character points at classical bit
        chibi.point_at(self, bit_box.get_center(), duration=0.5)
        chibi.nod(self, times=1, duration=0.4)

        self.play(
            FadeIn(qubit_box), Write(qubit_label), FadeIn(q_content),
            run_time=1.5
        )

        # Character gets excited about qubit
        chibi.bounce(self, times=2, height=0.12, duration=0.6)
        chibi.excited_eyes(self, duration=0.6)

        # Bloch sphere
        bloch = Circle(radius=0.8, color=PURPLE, stroke_width=1.5, fill_opacity=0.05).move_to(DOWN * 1.5)
        bloch_arrow = Arrow(bloch.get_center(), bloch.get_center() + np.array([0.4, 0.55, 0]),
            color=PURPLE, stroke_width=2)
        zero_l = Text("|0\u27E9", font_size=18, color=ORANGE).move_to(bloch.get_top() + UP * 0.25)
        one_l = Text("|1\u27E9", font_size=18, color=CYAN).move_to(bloch.get_bottom() + DOWN * 0.25)

        self.play(Create(bloch), GrowArrow(bloch_arrow), Write(zero_l), Write(one_l), run_time=1.5)

        # Character thinks while arrow rotates
        self.play(
            Rotate(bloch_arrow, angle=PI / 2, about_point=bloch.get_center()),
            run_time=1.5, rate_func=smooth
        )
        chibi.think(self, duration=1.0)
        self.wait(0.5)

        # ═══ SCENE 3: Entanglement ═══
        self.play(FadeOut(title2, bit_box, bit_label, bit_0, qubit_box, qubit_label,
                          q_content, bloch, bloch_arrow, zero_l, one_l), run_time=0.6)

        title3 = Text("Entanglement", font_size=48, color=PINK, weight=BOLD).move_to(UP * 5.5)
        desc = Text("Spooky action at a distance", font_size=22, color=DIM).move_to(UP * 4.5)

        p1 = Circle(radius=0.7, color=PURPLE, fill_opacity=0.2, stroke_width=3).move_to(LEFT * 2 + UP * 1.5)
        p1_label = Text("A", font_size=28, color=PURPLE, weight=BOLD).move_to(p1)
        p1_spin = Arrow(p1.get_center(), p1.get_center() + UP * 0.45, color=PURPLE, stroke_width=3)

        p2 = Circle(radius=0.7, color=PINK, fill_opacity=0.2, stroke_width=3).move_to(RIGHT * 1 + UP * 1.5)
        p2_label = Text("B", font_size=28, color=PINK, weight=BOLD).move_to(p2)
        p2_spin = Arrow(p2.get_center(), p2.get_center() + DOWN * 0.45, color=PINK, stroke_width=3)

        link = DashedLine(p1.get_right(), p2.get_left(), color=CYAN, stroke_width=2, dash_length=0.12)
        link_label = Text("Entangled!", font_size=22, color=CYAN, weight=BOLD).move_to(UP * 0.3)

        self.play(Write(title3), Write(desc), run_time=1.5)
        self.play(
            GrowFromCenter(p1), FadeIn(p1_label), GrowArrow(p1_spin),
            GrowFromCenter(p2), FadeIn(p2_label), GrowArrow(p2_spin),
            run_time=2
        )

        # Character points at particles
        chibi.point_at(self, link.get_center(), duration=0.5)

        self.play(Create(link), Write(link_label), run_time=1.2)

        # Spins flip simultaneously — character bounces
        self.play(
            Rotate(p1_spin, angle=PI, about_point=p1.get_center()),
            Rotate(p2_spin, angle=PI, about_point=p2.get_center()),
            Flash(p1, color=PURPLE, num_lines=6),
            Flash(p2, color=PINK, num_lines=6),
            run_time=1.5
        )
        chibi.bounce(self, times=3, height=0.1, duration=0.9)

        # Distance text
        dist_text = Text("Even light-years apart!", font_size=22, color=DIM).move_to(DOWN * 1.5)
        self.play(Write(dist_text), run_time=1)
        chibi.excited_eyes(self, duration=0.6)
        self.wait(0.5)

        # ═══ SCENE 4: Quantum Computing ═══
        self.play(FadeOut(title3, desc, p1, p1_label, p1_spin, p2, p2_label, p2_spin,
                          link, link_label, dist_text), run_time=0.6)

        title4 = Text("Quantum Computing", font_size=42, color=CYAN, weight=BOLD).move_to(UP * 5.5)

        classical = VGroup(
            Text("Classical", font_size=22, color=DIM, weight=BOLD),
            Text("One path at a time", font_size=18, color=DIM),
        ).arrange(DOWN, buff=0.15).move_to(LEFT * 2 + UP * 3)

        quantum = VGroup(
            Text("Quantum", font_size=22, color=CYAN, weight=BOLD),
            Text("ALL paths at once!", font_size=18, color=CYAN),
        ).arrange(DOWN, buff=0.15).move_to(RIGHT * 0.5 + UP * 3)

        # Maze lines
        maze_c = VGroup(*[
            Line(LEFT * 3.5, LEFT * 1.2, color=DIM, stroke_width=1.5).move_to(UP * (1.5 - i * 0.7))
            for i in range(4)
        ])
        dot_c = Dot(radius=0.1, color=ORANGE).move_to(maze_c[0].get_left())

        maze_q = VGroup(*[
            Line(RIGHT * -0.2, RIGHT * 2, color=CYAN, stroke_width=1.5, stroke_opacity=0.6).move_to(UP * (1.5 - i * 0.7))
            for i in range(4)
        ])
        dots_q = VGroup(*[Dot(radius=0.08, color=CYAN, fill_opacity=0.6).move_to(l.get_left()) for l in maze_q])

        self.play(Write(title4), run_time=1)
        self.play(FadeIn(classical), FadeIn(quantum), run_time=0.8)
        self.play(
            LaggedStart(*[Create(l) for l in maze_c], lag_ratio=0.15),
            LaggedStart(*[Create(l) for l in maze_q], lag_ratio=0.15),
            run_time=1.2
        )
        self.play(FadeIn(dot_c), FadeIn(dots_q), run_time=0.5)

        # Classical: one at a time (character watches)
        for i, line in enumerate(maze_c):
            if i > 0:
                self.play(dot_c.animate.move_to(line.get_left()), run_time=0.15)
            self.play(dot_c.animate.move_to(line.get_right()), run_time=0.3)

        # Character shakes head at slow classical
        chibi.nod(self, times=1, duration=0.4)

        # Quantum: all at once
        self.play(
            *[d.animate.move_to(maze_q[i].get_right()) for i, d in enumerate(dots_q)],
            run_time=0.8, rate_func=smooth
        )
        self.play(*[Flash(d, color=CYAN, num_lines=4, flash_radius=0.3) for d in dots_q], run_time=0.8)

        # Character goes wild
        chibi.bounce(self, times=3, height=0.15, duration=0.9)
        self.wait(0.5)

        # ═══ SCENE 5: Closing — character takes center stage ═══
        self.play(FadeOut(title4, classical, quantum, maze_c, maze_q, dot_c, dots_q), run_time=0.6)

        # Move character to center-bottom
        self.play(chibi.animate.move_to(DOWN * 3.5).scale(1.3), run_time=1)

        final = Text("Quantum", font_size=56, color=PURPLE, weight=BOLD).move_to(UP * 2)
        final2 = Text("is the Future", font_size=44, color=TEXT_COL, weight=BOLD).move_to(UP * 0.8)
        glow = Circle(radius=2.5, color=PURPLE, fill_opacity=0.04, stroke_width=1).move_to(UP * 1.4)

        self.play(GrowFromCenter(glow), run_time=0.8)
        self.play(Write(final), run_time=1.5)
        self.play(Write(final2), run_time=1)

        # Character's final speech bubble
        final_bubble_bg = RoundedRectangle(width=5, height=0.7, corner_radius=0.2,
            color=WHITE, fill_opacity=0.9, stroke_color="#E74C3C", stroke_width=2)
        final_bubble_text = Text("Learn more on ScrollUForward!", font_size=20, color=BLACK, weight=BOLD)
        final_bubble_text.move_to(final_bubble_bg)
        final_bubble = VGroup(final_bubble_bg, final_bubble_text).next_to(chibi, UP, buff=0.15)
        ftail = Triangle(color=WHITE, fill_opacity=0.9, stroke_color="#E74C3C", stroke_width=2)
        ftail.scale(0.1).rotate(PI).next_to(final_bubble_bg, DOWN, buff=-0.02)
        final_bubble.add(ftail)

        self.play(FadeIn(final_bubble, scale=0.5), run_time=0.6)
        chibi.wave(self, duration=1.2)

        self.play(glow.animate.scale(1.1), rate_func=there_and_back, run_time=1.5)
        self.wait(1)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
