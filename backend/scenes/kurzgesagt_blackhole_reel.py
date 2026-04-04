from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        # ── Kurzgesagt palette ──
        BG       = "#0a0e1f"
        GOLD     = "#f5a623"
        ORANGE   = "#f06623"
        CYAN     = "#00d4ff"
        RED      = "#e63946"
        PURPLE   = "#8338ec"
        WHITE    = "#ffffff"
        DIM      = "#7a8599"
        GREEN    = "#06d6a0"

        self.camera.background_color = BG
        self.camera.frame_width  = 9
        self.camera.frame_height = 16

        # ── helper: star field ──
        def make_stars(n=120, seed=42):
            rng = np.random.default_rng(seed)
            stars = VGroup()
            for _ in range(n):
                x = rng.uniform(-4.4, 4.4)
                y = rng.uniform(-7.8, 7.8)
                r = rng.uniform(0.02, 0.06)
                alpha = rng.uniform(0.3, 1.0)
                s = Dot(radius=r, color=WHITE, fill_opacity=alpha).move_to([x, y, 0])
                stars.add(s)
            return stars

        # ═══ SCENE 1 — HOOK ═══════════════════════════════════════
        stars = make_stars()
        self.add(stars)

        hook_q = Text("What happens if you", font_size=52, color=WHITE, weight=BOLD)
        hook_a = Text("fall into a", font_size=52, color=WHITE, weight=BOLD)
        hook_b = Text("Black Hole?", font_size=64, color=GOLD, weight=BOLD)
        hook   = VGroup(hook_q, hook_a, hook_b).arrange(DOWN, buff=0.35).move_to(UP * 3.8)

        # A simple flat Kurzgesagt-style astronaut: circle head + rectangle body
        head   = Circle(radius=0.45, color=CYAN, fill_opacity=1, stroke_width=0).move_to(DOWN * 0.5)
        visor  = Ellipse(width=0.5, height=0.32, color="#1a1a3e", fill_opacity=1, stroke_width=0).move_to(head.get_center() + RIGHT*0.05)
        body   = RoundedRectangle(width=0.75, height=0.9, corner_radius=0.12,
                                  color=WHITE, fill_opacity=1, stroke_width=0).move_to(DOWN * 1.5)
        arm_l  = RoundedRectangle(width=0.22, height=0.6, corner_radius=0.08,
                                  color=WHITE, fill_opacity=1, stroke_width=0).move_to(DOWN * 1.5 + LEFT * 0.55)
        arm_r  = RoundedRectangle(width=0.22, height=0.6, corner_radius=0.08,
                                  color=WHITE, fill_opacity=1, stroke_width=0).move_to(DOWN * 1.5 + RIGHT * 0.55)
        astronaut = VGroup(body, arm_l, arm_r, head, visor).move_to(DOWN * 1.2)

        # Black hole hint — glowing circle at bottom
        bh_glow = Circle(radius=1.8, color=PURPLE, fill_opacity=0.08, stroke_width=0).move_to(DOWN * 5.5)
        bh_ring = Circle(radius=1.8, color=PURPLE, fill_opacity=0, stroke_width=3).move_to(DOWN * 5.5)

        self.play(FadeIn(stars, run_time=0.5))
        self.play(Write(hook_q), run_time=0.9)
        self.play(Write(hook_a), run_time=0.7)
        self.play(Write(hook_b), run_time=0.9)
        self.play(
            GrowFromCenter(astronaut),
            FadeIn(bh_glow), Create(bh_ring),
            run_time=1.5
        )
        self.play(
            astronaut.animate.shift(DOWN * 0.8).scale(0.85),
            bh_ring.animate.scale(1.08),
            rate_func=there_and_back_with_pause,
            run_time=2,
        )
        self.wait(1)

        # ═══ SCENE 2 — EVENT HORIZON ══════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)
        stars2 = make_stars(seed=7)
        self.add(stars2)

        t2_title = Text("The Event Horizon", font_size=54, color=GOLD, weight=BOLD).move_to(UP * 5.8)
        t2_sub   = Text("The point of no return", font_size=30, color=DIM).move_to(UP * 4.8)

        # Concentric rings representing pull zones
        rings = VGroup(*[
            Circle(radius=r, color=c, fill_opacity=0, stroke_width=w, stroke_opacity=a)
            .move_to(UP * 0.5)
            for r, c, w, a in [
                (2.8, DIM,    1.5, 0.3),
                (2.2, PURPLE, 2.0, 0.5),
                (1.6, ORANGE, 2.5, 0.7),
                (1.0, RED,    3.0, 0.85),
                (0.5, WHITE,  3.5, 1.0),
            ]
        ])
        bh_core = Circle(radius=0.5, color="#000000", fill_opacity=1, stroke_width=0).move_to(UP * 0.5)
        bh_label = Text("Singularity", font_size=22, color=DIM).next_to(bh_core, DOWN, buff=0.25)

        horizon_ring = rings[3]
        horizon_label = Text("Event Horizon", font_size=24, color=RED).move_to(LEFT * 2.5 + UP * 0.5)
        horizon_arrow = Arrow(
            start=horizon_label.get_right() + RIGHT * 0.1,
            end=rings[3].get_left() + LEFT * 0.05,
            color=RED, buff=0.05, stroke_width=2, max_tip_length_to_length_ratio=0.15
        )

        fact = VGroup(
            Text("Light itself cannot escape", font_size=28, color=WHITE, weight=BOLD),
            Text("once it crosses this boundary.", font_size=26, color=DIM),
        ).arrange(DOWN, buff=0.25).move_to(DOWN * 3.5)

        self.play(Write(t2_title), run_time=1)
        self.play(Write(t2_sub), run_time=0.7)
        self.play(
            LaggedStart(*[Create(r) for r in rings], lag_ratio=0.2),
            FadeIn(bh_core),
            run_time=2.5
        )
        self.play(Write(bh_label), run_time=0.6)
        self.play(Write(horizon_label), GrowArrow(horizon_arrow), run_time=1)
        self.play(
            Indicate(rings[3], scale_factor=1.06, color=RED),
            run_time=1
        )
        self.play(FadeIn(fact, shift=UP * 0.3), run_time=1.2)
        self.wait(1.5)

        # ═══ SCENE 3 — SPAGHETTIFICATION ══════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)
        stars3 = make_stars(seed=99)
        self.add(stars3)

        t3_title = Text("Spaghettification", font_size=52, color=ORANGE, weight=BOLD).move_to(UP * 5.8)
        t3_sub   = Text("Tidal forces rip everything apart", font_size=28, color=DIM).move_to(UP * 4.8)

        # Astronaut being stretched — build from stacked ellipses
        n_slices = 8
        base_w, base_h = 0.7, 0.25
        normal_slices = VGroup(*[
            Ellipse(width=base_w, height=base_h,
                    color=CYAN, fill_opacity=0.9, stroke_width=0)
            .move_to(UP * (1.5 - i * 0.32))
            for i in range(n_slices)
        ])

        stretched_slices = VGroup(*[
            Ellipse(width=base_w * (0.55 + i * 0.07),
                    height=base_h * 0.5,
                    color=CYAN, fill_opacity=0.85, stroke_width=0)
            .move_to(UP * (3.2 - i * 0.72))
            for i in range(n_slices)
        ])

        # Gravity arrows pointing down
        grav_arrows = VGroup(*[
            Arrow(start=UP * (1.8 - i * 0.5) + RIGHT * 2.0,
                  end=UP * (1.3 - i * 0.5) + RIGHT * 2.0,
                  color=PURPLE, buff=0, stroke_width=2.5,
                  max_tip_length_to_length_ratio=0.25)
            for i in range(4)
        ])
        grav_label = Text("Gravity", font_size=22, color=PURPLE).next_to(grav_arrows, UP, buff=0.15)

        fact3 = VGroup(
            Text("Gravity is stronger at your feet", font_size=26, color=WHITE, weight=BOLD),
            Text("than at your head — you stretch.", font_size=24, color=DIM),
        ).arrange(DOWN, buff=0.25).move_to(DOWN * 4.0)

        self.play(Write(t3_title), run_time=1)
        self.play(Write(t3_sub), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(s) for s in normal_slices], lag_ratio=0.05), run_time=1.5)
        self.play(
            LaggedStart(*[
                Transform(normal_slices[i], stretched_slices[i])
                for i in range(n_slices)
            ], lag_ratio=0.1),
            LaggedStart(*[GrowArrow(a) for a in grav_arrows], lag_ratio=0.1),
            Write(grav_label),
            run_time=2.5,
        )
        self.play(FadeIn(fact3, shift=UP * 0.3), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 4 — SINGULARITY ════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)
        stars4 = make_stars(seed=13)
        self.add(stars4)

        t4_title = Text("The Singularity", font_size=54, color=PURPLE, weight=BOLD).move_to(UP * 5.8)
        t4_sub   = Text("Where physics breaks down", font_size=28, color=DIM).move_to(UP * 4.8)

        # Collapsing rings → point
        collapse_rings = VGroup(*[
            Circle(radius=r, color=c, fill_opacity=0, stroke_width=2.5, stroke_opacity=0.8)
            .move_to(UP * 0.5)
            for r, c in [
                (2.5, DIM),
                (1.8, CYAN),
                (1.2, ORANGE),
                (0.7, RED),
                (0.3, WHITE),
            ]
        ])
        sing_dot = Dot(radius=0.12, color=WHITE, fill_opacity=1).move_to(UP * 0.5)

        label_density = Text("Infinite Density", font_size=30, color=WHITE, weight=BOLD).move_to(DOWN * 1.5)
        label_volume  = Text("Zero Volume", font_size=26, color=DIM).move_to(DOWN * 2.2)

        facts4 = VGroup(
            Text("All known laws of physics", font_size=26, color=WHITE, weight=BOLD),
            Text("cease to exist here.", font_size=26, color=DIM),
            Text("We genuinely don't know", font_size=24, color=GOLD),
            Text("what happens next.", font_size=24, color=GOLD),
        ).arrange(DOWN, buff=0.28).move_to(DOWN * 4.0)

        self.play(Write(t4_title), run_time=1)
        self.play(Write(t4_sub), run_time=0.7)
        self.play(
            LaggedStart(*[Create(r) for r in collapse_rings], lag_ratio=0.15),
            run_time=2
        )
        self.play(
            LaggedStart(*[
                r.animate.scale(0.05).set_opacity(0)
                for r in collapse_rings
            ], lag_ratio=0.1),
            GrowFromCenter(sing_dot),
            run_time=2,
        )
        self.play(
            Flash(sing_dot, color=WHITE, num_lines=12, flash_radius=0.4),
            run_time=1
        )
        self.play(Write(label_density), Write(label_volume), run_time=1)
        self.play(FadeIn(facts4, shift=UP * 0.3), run_time=1.2)
        self.wait(1.5)

        # ═══ SCENE 5 — CLOSING + BRANDING ════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)
        stars5 = make_stars(n=200, seed=55)
        self.add(stars5)

        close1 = Text("Black holes are not", font_size=50, color=WHITE, weight=BOLD)
        close2 = Text("cosmic vacuum cleaners.", font_size=50, color=WHITE, weight=BOLD)
        close3 = Text("They are windows into", font_size=44, color=DIM)
        close4 = Text("the unknown.", font_size=54, color=GOLD, weight=BOLD)
        closing = VGroup(close1, close2, close3, close4).arrange(DOWN, buff=0.35).move_to(UP * 3.2)

        # Mini black hole illustration
        mini_bh = Circle(radius=0.6, color="#000000", fill_opacity=1, stroke_width=0).move_to(DOWN * 1.2)
        mini_ring = Circle(radius=0.6, color=ORANGE, fill_opacity=0, stroke_width=3).move_to(DOWN * 1.2)
        mini_glow = Circle(radius=0.9, color=PURPLE, fill_opacity=0.1, stroke_width=0).move_to(DOWN * 1.2)

        # ScrollUForward brand bar
        brand_bg = RoundedRectangle(
            width=8.2, height=1.7, corner_radius=0.3,
            fill_color="#c8372d", fill_opacity=1, stroke_width=0
        ).move_to(DOWN * 3.5)
        brand_txt  = Text("ScrollUForward", font_size=40, color=WHITE, weight=BOLD).move_to(DOWN * 3.3)
        learn_txt  = Text("Learn Something Real Every Day", font_size=22, color="#ffe0de").move_to(DOWN * 3.9)

        self.play(
            LaggedStart(*[FadeIn(l, shift=UP * 0.2) for l in closing], lag_ratio=0.25),
            run_time=2.5
        )
        self.play(
            GrowFromCenter(mini_glow),
            GrowFromCenter(mini_bh),
            Create(mini_ring),
            run_time=1.5
        )
        self.play(Rotate(mini_ring, angle=TAU * 0.3, rate_func=smooth), run_time=1.2)
        self.play(FadeIn(brand_bg), run_time=0.6)
        self.play(Write(brand_txt), Write(learn_txt), run_time=1.2)
        self.wait(2.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
