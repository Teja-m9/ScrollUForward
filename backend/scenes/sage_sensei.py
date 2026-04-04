"""
Sage Sensei — Manim Anime Character
=====================================
A wise old teacher with white beard, purple robe, and a glowing staff.
"""
from manim import *


class SageSensei(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        # ── Staff ──
        staff = Line(start=[0.6, -1.8, 0], end=[0.7, 1.1, 0],
                     stroke_color=GOLD, stroke_width=5)
        orb = Circle(radius=0.16, fill_color=TEAL, fill_opacity=1,
                     stroke_color=WHITE, stroke_width=1.5)
        orb.move_to([0.7, 1.28, 0])

        # ── Robe (body) ──
        robe = Triangle(fill_color=PURPLE_B, fill_opacity=1,
                        stroke_color=WHITE, stroke_width=2).scale(1.15)
        robe.shift(DOWN * 0.62)

        # ── Arms ──
        arm_l = Line(start=[-0.22, 0.02, 0], end=[-0.68, -0.52, 0],
                     stroke_color=PURPLE_B, stroke_width=9)
        arm_r = Line(start=[0.22, 0.02, 0], end=[0.68, -0.52, 0],
                     stroke_color=PURPLE_B, stroke_width=9)

        # ── Head ──
        head = Circle(radius=0.44, fill_color=LIGHT_PINK, fill_opacity=1,
                      stroke_color=WHITE, stroke_width=2)
        head.shift(UP * 0.62)

        # ── White hair cap ──
        hair = Arc(radius=0.44, start_angle=0, angle=PI,
                   fill_color=WHITE, fill_opacity=1, stroke_width=0)
        hair.shift(UP * 0.62)

        # ── White beard ──
        beard = Ellipse(width=0.58, height=0.72, fill_color=WHITE,
                        fill_opacity=1, stroke_width=0)
        beard.shift(UP * 0.20)

        # ── Eyes (closed / serene) ──
        for sign in [-1, 1]:
            eye_line = Arc(radius=0.09, start_angle=0, angle=PI,
                           stroke_color=BLACK, stroke_width=2)
            eye_line.move_to([sign * 0.17, 0.64, 0])
            self.add(eye_line)

        # ── Bushy eyebrows ──
        for sign in [-1, 1]:
            brow = Arc(radius=0.13, start_angle=PI * 0.18, angle=PI * 0.64,
                       stroke_color=WHITE, stroke_width=2.5)
            brow.move_to([sign * 0.17, 0.78, 0])
            self.add(brow)

        # ── Smile ──
        smile = Arc(radius=0.11, start_angle=-PI * 0.7, angle=-PI * 0.6,
                    stroke_color=BLACK, stroke_width=2)
        smile.shift(UP * 0.50)

        # ── Assemble (back to front) ──
        self.add(staff, orb, robe, arm_l, arm_r, head, hair, beard, smile)
