from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0a0a12"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        ORANGE = "#ff6b35"
        PURPLE = "#7f5af0"
        CYAN = "#00d4ff"
        TEXT_COL = "#fffffe"
        DIM = "#a7a9be"

        # ═══ SCENE 1: Hook ═══
        t1 = Text("A region of space where", font_size=36, color=TEXT_COL, weight=BOLD)
        t2 = Text("nothing can escape", font_size=44, color=ORANGE, weight=BOLD)
        t3 = Text("Not even light.", font_size=36, color=DIM)
        hook = VGroup(t1, t2, t3).arrange(DOWN, buff=0.4).move_to(UP * 3)

        hole = Circle(radius=1.5, color=BLACK, fill_opacity=1, stroke_width=0).move_to(DOWN * 1.5)
        glow_ring = Annulus(inner_radius=1.5, outer_radius=2.2, color=ORANGE,
            fill_opacity=0.3, stroke_width=2).move_to(hole)
        outer_glow = Annulus(inner_radius=2.2, outer_radius=3.0, color=ORANGE,
            fill_opacity=0.08, stroke_width=0).move_to(hole)

        # Stars being pulled in
        stars = VGroup(*[
            Dot(radius=0.04, color=TEXT_COL).move_to(hole.get_center() + np.array([
                np.random.uniform(-3.5, 3.5), np.random.uniform(-3, 3), 0
            ])) for _ in range(25)
        ])

        self.play(Write(t1), run_time=1)
        self.play(Write(t2), run_time=1)
        self.play(Write(t3), run_time=0.8)
        self.play(
            GrowFromCenter(hole), FadeIn(glow_ring), FadeIn(outer_glow),
            FadeIn(stars),
            run_time=2
        )
        # Stars fall inward
        self.play(
            *[s.animate.move_to(hole.get_center() + np.array([
                np.random.uniform(-0.3, 0.3), np.random.uniform(-0.3, 0.3), 0
            ])) for s in stars],
            run_time=3, rate_func=rush_into
        )
        self.wait(1)

        # ═══ SCENE 2: How They Form ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title2 = Text("How They Form", font_size=46, color=TEXT_COL, weight=BOLD).move_to(UP * 5.5)

        # Massive star
        big_star = Circle(radius=2, color="#FFD700", fill_opacity=0.3, stroke_width=3).move_to(UP * 1)
        star_label = Text("Massive Star", font_size=26, color="#FFD700", weight=BOLD).move_to(big_star)
        mass_text = Text("20-50x Sun mass", font_size=20, color=DIM).next_to(big_star, DOWN, buff=0.5)

        self.play(Write(title2), run_time=1)
        self.play(GrowFromCenter(big_star), Write(star_label), FadeIn(mass_text), run_time=2)
        # Collapse animation
        self.play(
            big_star.animate.scale(0.15).set_fill(opacity=1).set_color(ORANGE),
            star_label.animate.scale(0.3).set_opacity(0),
            mass_text.animate.set_opacity(0),
            run_time=2.5, rate_func=rush_into
        )

        # Shockwave
        shock = Circle(radius=0.3, color=ORANGE, stroke_width=4, fill_opacity=0).move_to(big_star)
        collapse_label = Text("Supernova!", font_size=36, color=ORANGE, weight=BOLD).move_to(DOWN * 2)
        self.play(
            shock.animate.scale(15).set_stroke(opacity=0),
            FadeIn(collapse_label, scale=1.5),
            run_time=2
        )

        bh_label = Text("Black Hole", font_size=32, color=PURPLE, weight=BOLD).move_to(DOWN * 2)
        self.play(FadeOut(collapse_label), FadeIn(bh_label), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 3: Anatomy ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title3 = Text("Anatomy of a Black Hole", font_size=40, color=TEXT_COL, weight=BOLD).move_to(UP * 5.5)

        singularity = Dot(radius=0.12, color=WHITE).move_to(UP * 0.5)
        s_label = Text("Singularity", font_size=20, color=TEXT_COL).next_to(singularity, DOWN, buff=0.3)

        event_horizon = Circle(radius=1.5, color=ORANGE, stroke_width=2.5,
            fill_opacity=0).move_to(singularity)
        eh_label = Text("Event Horizon", font_size=20, color=ORANGE).move_to(event_horizon.get_right() + RIGHT * 0.3 + UP * 0.8)
        eh_arrow = Arrow(eh_label.get_left(), event_horizon.point_at_angle(0.3),
            color=ORANGE, stroke_width=1.5, max_tip_length_to_length_ratio=0.2)

        accretion = Annulus(inner_radius=1.8, outer_radius=2.8, color=CYAN,
            fill_opacity=0.12, stroke_width=1.5).move_to(singularity)
        acc_label = Text("Accretion Disk", font_size=20, color=CYAN).move_to(accretion.get_top() + UP * 0.4)

        photon_sphere = DashedVMobject(
            Circle(radius=2, color=PURPLE, stroke_width=1.5).move_to(singularity),
            num_dashes=20
        )
        ph_label = Text("Photon Sphere", font_size=18, color=PURPLE).move_to(LEFT * 2.5 + DOWN * 2)
        ph_arrow = Arrow(ph_label.get_right(), photon_sphere.get_center() + LEFT * 1.5 + DOWN * 0.5,
            color=PURPLE, stroke_width=1.5, max_tip_length_to_length_ratio=0.2)

        self.play(Write(title3), run_time=1)
        self.play(FadeIn(singularity, scale=2), Write(s_label), run_time=1)
        self.play(Create(event_horizon), Write(eh_label), GrowArrow(eh_arrow), run_time=1.5)
        self.play(FadeIn(accretion), Write(acc_label), run_time=1.5)
        self.play(Create(photon_sphere), Write(ph_label), GrowArrow(ph_arrow), run_time=1.5)
        self.wait(2)

        # ═══ SCENE 4: Spacetime Warping ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title4 = Text("Warping Spacetime", font_size=44, color=PURPLE, weight=BOLD).move_to(UP * 5.5)

        grid = NumberPlane(
            x_range=[-4, 4, 0.5], y_range=[-3, 3, 0.5],
            x_length=7, y_length=5,
            background_line_style={"stroke_color": CYAN, "stroke_width": 0.8, "stroke_opacity": 0.4},
            axis_config={"stroke_width": 0},
        ).move_to(UP * 0.5)

        self.play(Write(title4), run_time=1)
        self.play(Create(grid), run_time=2)
        # Warp the grid
        grid.prepare_for_nonlinear_transform()
        self.play(
            grid.animate.apply_function(
                lambda p: p + np.array([
                    0.8 * p[0] / (p[0]**2 + p[1]**2 + 0.8),
                    0.8 * p[1] / (p[0]**2 + p[1]**2 + 0.8),
                    0
                ])
            ),
            run_time=3, rate_func=smooth
        )

        bh_dot = Dot(radius=0.2, color=ORANGE).move_to(grid.get_center())
        bh_text = Text("Black Hole", font_size=24, color=ORANGE, weight=BOLD).next_to(bh_dot, DOWN, buff=0.5)
        self.play(FadeIn(bh_dot, scale=2), Write(bh_text), run_time=1)
        self.wait(2)

        # ═══ SCENE 5: Famous Black Holes ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title5 = Text("Famous Black Holes", font_size=42, color=TEXT_COL, weight=BOLD).move_to(UP * 5.5)

        bhs = [
            ("Sagittarius A*", "Center of Milky Way", "4M solar masses", ORANGE),
            ("M87*", "First ever photographed", "6.5B solar masses", PURPLE),
            ("Cygnus X-1", "First confirmed BH", "21 solar masses", CYAN),
        ]

        cards = VGroup()
        for name, desc, mass, col in bhs:
            card = RoundedRectangle(width=7, height=2.2, corner_radius=0.2,
                color=col, fill_opacity=0.08, stroke_width=1.5)
            dot = Circle(radius=0.35, color=col, fill_opacity=0.3, stroke_width=2).move_to(card.get_left() + RIGHT * 1)
            core = Dot(radius=0.08, color=col).move_to(dot)
            n = Text(name, font_size=26, color=col, weight=BOLD).move_to(card.get_left() + RIGHT * 2.8 + UP * 0.35)
            d = Text(desc, font_size=18, color=DIM).move_to(card.get_left() + RIGHT * 2.8 + DOWN * 0.1)
            m = Text(mass, font_size=18, color=TEXT_COL).move_to(card.get_left() + RIGHT * 2.8 + DOWN * 0.5)
            cards.add(VGroup(card, dot, core, n, d, m))

        cards.arrange(DOWN, buff=0.4).move_to(UP * 0.5)

        self.play(Write(title5), run_time=1)
        self.play(LaggedStart(*[FadeIn(c, shift=LEFT * 0.5) for c in cards], lag_ratio=0.3), run_time=3)
        self.wait(2)

        # ═══ SCENE 6: Closing ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        final_hole = Circle(radius=1.8, color=BLACK, fill_opacity=1, stroke_width=0).move_to(UP * 0.5)
        final_glow = Annulus(inner_radius=1.8, outer_radius=2.8, color=ORANGE,
            fill_opacity=0.25, stroke_width=2).move_to(final_hole)
        outer = Annulus(inner_radius=2.8, outer_radius=3.8, color=ORANGE,
            fill_opacity=0.06, stroke_width=0).move_to(final_hole)

        closing = Text("The Universe's\nDarkest Secret", font_size=44, color=TEXT_COL,
            weight=BOLD, line_spacing=1.3).move_to(DOWN * 4)
        self.play(GrowFromCenter(final_hole), FadeIn(final_glow), FadeIn(outer), run_time=2.5)
        self.play(FadeIn(closing, shift=UP * 0.3), run_time=1.5)
        self.play(final_glow.animate.scale(1.1), rate_func=there_and_back, run_time=2)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
