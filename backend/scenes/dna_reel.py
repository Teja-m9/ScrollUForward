from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0f0e17"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        BLUE = "#00b4d8"
        RED = "#e53170"
        GREEN = "#2cb67d"
        PURPLE = "#7f5af0"
        ORANGE = "#ff8906"
        TEXT_COL = "#fffffe"
        DIM = "#a7a9be"

        # ═══ SCENE 1: Hook ═══
        q1 = Text("Inside every cell", font_size=40, color=TEXT_COL, weight=BOLD)
        q2 = Text("of your body lives a", font_size=36, color=DIM)
        q3 = Text("3 billion letter code", font_size=46, color=BLUE, weight=BOLD)
        hook = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4).move_to(UP * 3)

        cell = Circle(radius=1.8, color=GREEN, fill_opacity=0.08, stroke_width=2).move_to(DOWN * 1.5)
        nucleus = Circle(radius=0.7, color=PURPLE, fill_opacity=0.15, stroke_width=2).move_to(cell)
        nuc_label = Text("Nucleus", font_size=18, color=PURPLE).next_to(nucleus, DOWN, buff=0.3)

        organelles = VGroup(*[
            Circle(radius=0.15, color=GREEN, fill_opacity=0.2, stroke_width=1).move_to(
                cell.get_center() + np.array([1.2 * np.cos(a), 1.2 * np.sin(a), 0])
            ) for a in np.linspace(0, 2 * PI, 8, endpoint=False)
        ])

        self.play(Write(q1), run_time=1)
        self.play(Write(q2), run_time=0.8)
        self.play(Write(q3), run_time=1)
        self.play(
            GrowFromCenter(cell), GrowFromCenter(nucleus), Write(nuc_label),
            LaggedStart(*[FadeIn(o, scale=0.3) for o in organelles], lag_ratio=0.1),
            run_time=2
        )
        self.play(Indicate(nucleus, color=PURPLE, scale_factor=1.2), run_time=1.5)
        self.wait(1)

        # ═══ SCENE 2: The Double Helix ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title2 = Text("The Double Helix", font_size=46, color=BLUE, weight=BOLD).move_to(UP * 5.5)

        # Build DNA helix from circles and lines
        helix_group = VGroup()
        n_rungs = 12
        for i in range(n_rungs):
            t = i / (n_rungs - 1)
            y = 4 - 8 * t  # top to bottom
            x_offset = 1.2 * np.sin(t * 4 * PI)

            left_dot = Circle(radius=0.18, color=BLUE, fill_opacity=0.4, stroke_width=2)
            left_dot.move_to(np.array([-x_offset, y, 0]))
            right_dot = Circle(radius=0.18, color=RED, fill_opacity=0.4, stroke_width=2)
            right_dot.move_to(np.array([x_offset, y, 0]))

            # Base pair bond
            bond = Line(left_dot.get_center(), right_dot.get_center(),
                color=DIM, stroke_width=1.5, stroke_opacity=0.5)

            helix_group.add(bond, left_dot, right_dot)

        helix_group.move_to(UP * 0.5)

        # Backbone lines
        left_backbone = VGroup()
        right_backbone = VGroup()
        for i in range(n_rungs - 1):
            l1 = helix_group[i * 3 + 1]  # left dot
            l2 = helix_group[(i + 1) * 3 + 1]  # next left dot
            r1 = helix_group[i * 3 + 2]
            r2 = helix_group[(i + 1) * 3 + 2]
            left_backbone.add(Line(l1.get_center(), l2.get_center(), color=BLUE, stroke_width=1.5, stroke_opacity=0.5))
            right_backbone.add(Line(r1.get_center(), r2.get_center(), color=RED, stroke_width=1.5, stroke_opacity=0.5))

        labels_group = VGroup(
            Text("Sugar-phosphate", font_size=18, color=BLUE).move_to(LEFT * 2.5 + DOWN * 4.5),
            Text("backbone", font_size=18, color=BLUE).move_to(LEFT * 2.5 + DOWN * 4.9),
            Text("Base pairs", font_size=18, color=DIM).move_to(RIGHT * 2.5 + DOWN * 4.7),
        )

        self.play(Write(title2), run_time=1)
        self.play(
            LaggedStart(*[Create(helix_group[i]) for i in range(len(helix_group))], lag_ratio=0.04),
            run_time=3
        )
        self.play(
            LaggedStart(*[Create(l) for l in left_backbone], lag_ratio=0.08),
            LaggedStart(*[Create(r) for r in right_backbone], lag_ratio=0.08),
            run_time=1.5
        )
        self.play(FadeIn(labels_group), run_time=1.5)
        self.wait(1.5)

        # ═══ SCENE 3: Base Pairs ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title3 = Text("The 4 Letters of Life", font_size=44, color=TEXT_COL, weight=BOLD).move_to(UP * 5.5)

        bases = [
            ("A", "Adenine", BLUE, "T", "Thymine", RED),
            ("G", "Guanine", GREEN, "C", "Cytosine", ORANGE),
        ]

        pairs_group = VGroup()
        for i, (l1, n1, c1, l2, n2, c2) in enumerate(bases):
            y = 1.5 - i * 3.5

            left_c = Circle(radius=0.6, color=c1, fill_opacity=0.2, stroke_width=2.5)
            left_l = Text(l1, font_size=40, color=c1, weight=BOLD)
            left_n = Text(n1, font_size=18, color=c1).next_to(left_c, DOWN, buff=0.25)
            left_g = VGroup(left_c, left_l, left_n).move_to(LEFT * 2 + UP * y)

            right_c = Circle(radius=0.6, color=c2, fill_opacity=0.2, stroke_width=2.5)
            right_l = Text(l2, font_size=40, color=c2, weight=BOLD)
            right_n = Text(n2, font_size=18, color=c2).next_to(right_c, DOWN, buff=0.25)
            right_g = VGroup(right_c, right_l, right_n).move_to(RIGHT * 2 + UP * y)

            bond1 = DashedLine(left_c.get_right(), right_c.get_left(), color=DIM, stroke_width=2)
            bond_label = Text("H bonds", font_size=16, color=DIM).move_to(UP * y + UP * 0.9)

            pairs_group.add(VGroup(left_g, right_g, bond1, bond_label))

        self.play(Write(title3), run_time=1)
        for pair in pairs_group:
            self.play(
                GrowFromCenter(pair[0]), GrowFromCenter(pair[1]),
                Create(pair[2]), FadeIn(pair[3]),
                run_time=1.5
            )
        self.wait(1.5)

        # ═══ SCENE 4: CRISPR ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title4 = Text("CRISPR: Editing DNA", font_size=42, color=GREEN, weight=BOLD).move_to(UP * 5.5)

        # DNA strand as horizontal bar
        dna_bar = VGroup()
        for i in range(10):
            base = RoundedRectangle(width=0.6, height=1.2, corner_radius=0.1,
                color=BLUE if i != 5 else RED, fill_opacity=0.2 if i != 5 else 0.4,
                stroke_width=2).move_to(LEFT * 2.7 + RIGHT * i * 0.6 + UP * 1)
            letter = Text(["A", "T", "G", "C", "A", "X", "G", "T", "C", "A"][i],
                font_size=20, color=BLUE if i != 5 else RED, weight=BOLD).move_to(base)
            dna_bar.add(VGroup(base, letter))

        error_label = Text("\u2190 Error", font_size=22, color=RED, weight=BOLD)
        error_label.next_to(dna_bar[5], UP, buff=0.3)

        # Scissors
        scissors = Text("\u2702", font_size=44, color=GREEN).move_to(dna_bar[5].get_center() + UP * 2)

        cut_label = Text("CRISPR cuts here", font_size=22, color=GREEN).next_to(scissors, UP, buff=0.2)

        # Fixed base
        fixed_base = RoundedRectangle(width=0.6, height=1.2, corner_radius=0.1,
            color=GREEN, fill_opacity=0.3, stroke_width=2).move_to(dna_bar[5][0].get_center() + DOWN * 3)
        fixed_letter = Text("T", font_size=20, color=GREEN, weight=BOLD).move_to(fixed_base)
        fix_label = Text("Corrected!", font_size=24, color=GREEN, weight=BOLD).move_to(DOWN * 3)

        self.play(Write(title4), run_time=1)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.3) for b in dna_bar], lag_ratio=0.08), run_time=2)
        self.play(Write(error_label), run_time=0.8)
        self.play(FadeIn(scissors, shift=DOWN * 0.5), Write(cut_label), run_time=1)
        # Cut animation
        self.play(scissors.animate.move_to(dna_bar[5].get_center()), run_time=1)
        self.play(
            Flash(dna_bar[5], color=RED, num_lines=6),
            dna_bar[5].animate.shift(DOWN * 2).set_opacity(0.2),
            FadeOut(error_label), FadeOut(scissors), FadeOut(cut_label),
            run_time=1.5
        )
        self.play(
            FadeIn(fixed_base, shift=UP * 1), FadeIn(fixed_letter, shift=UP * 1),
            run_time=1
        )
        self.play(
            VGroup(fixed_base, fixed_letter).animate.move_to(dna_bar[5][0].get_center()),
            run_time=1.5
        )
        self.play(Write(fix_label), run_time=0.8)
        self.wait(1.5)

        # ═══ SCENE 5: Closing ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        final_helix = VGroup()
        for i in range(8):
            t = i / 7
            y = 2 - 4 * t
            x = 1.0 * np.sin(t * 3 * PI)
            ld = Circle(radius=0.2, color=BLUE, fill_opacity=0.4, stroke_width=2).move_to(np.array([-x, y, 0]))
            rd = Circle(radius=0.2, color=RED, fill_opacity=0.4, stroke_width=2).move_to(np.array([x, y, 0]))
            bond = Line(ld.get_center(), rd.get_center(), color=DIM, stroke_width=1)
            final_helix.add(bond, ld, rd)
        final_helix.move_to(UP * 1)

        closing1 = Text("Your DNA Makes", font_size=42, color=TEXT_COL, weight=BOLD)
        closing2 = Text("You, You", font_size=50, color=BLUE, weight=BOLD)
        closing = VGroup(closing1, closing2).arrange(DOWN, buff=0.3).move_to(DOWN * 3.5)
        self.play(
            LaggedStart(*[GrowFromCenter(final_helix[i]) for i in range(len(final_helix))], lag_ratio=0.06),
            run_time=2.5
        )
        self.play(FadeIn(closing1, shift=UP * 0.3), FadeIn(closing2, shift=UP * 0.3), run_time=1.5)
        self.wait(2)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
