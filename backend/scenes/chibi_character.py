"""
Reusable animated chibi character for Manim educational reels.
Original designs — no copyrighted characters.
Each domain gets a unique look (hair, color, accessories).
"""
from manim import *
import numpy as np


class ChibiCharacter(VGroup):
    """A cute chibi character built from Manim primitives that can gesture, point, react."""

    def __init__(self, style="energetic", color="#E74C3C", accent="#FFD700", **kwargs):
        super().__init__(**kwargs)
        self.char_color = color
        self.accent_color = accent
        self.style = style

        # ── Body parts ──
        # Head
        self.head = Circle(radius=0.45, color=WHITE, fill_opacity=1, stroke_color=color, stroke_width=2)

        # Eyes
        self.eye_left = Dot(radius=0.07, color=BLACK).move_to(self.head.get_center() + LEFT * 0.15 + UP * 0.05)
        self.eye_right = Dot(radius=0.07, color=BLACK).move_to(self.head.get_center() + RIGHT * 0.15 + UP * 0.05)
        # Eye shine
        self.shine_l = Dot(radius=0.025, color=WHITE).move_to(self.eye_left.get_center() + UP * 0.02 + RIGHT * 0.02)
        self.shine_r = Dot(radius=0.025, color=WHITE).move_to(self.eye_right.get_center() + UP * 0.02 + RIGHT * 0.02)

        # Mouth (happy arc)
        self.mouth = Arc(radius=0.12, angle=-PI * 0.7, start_angle=-PI * 0.15,
                         color=BLACK, stroke_width=2).move_to(self.head.get_center() + DOWN * 0.15)

        # Blush marks
        self.blush_l = Ellipse(width=0.15, height=0.08, color="#FFB6C1", fill_opacity=0.5,
                               stroke_width=0).move_to(self.head.get_center() + LEFT * 0.28 + DOWN * 0.08)
        self.blush_r = Ellipse(width=0.15, height=0.08, color="#FFB6C1", fill_opacity=0.5,
                               stroke_width=0).move_to(self.head.get_center() + RIGHT * 0.28 + DOWN * 0.08)

        # Hair (spiky triangles on top)
        hair_points = self._make_hair(style)
        self.hair = Polygon(*hair_points, color=accent, fill_opacity=1,
                            stroke_color=color, stroke_width=1.5)

        # Body (rounded rectangle)
        self.body = RoundedRectangle(width=0.6, height=0.7, corner_radius=0.15,
                                     color=color, fill_opacity=0.9, stroke_width=2)
        self.body.next_to(self.head, DOWN, buff=0.02)

        # Belt/detail line
        self.belt = Line(self.body.get_left() + UP * 0.05, self.body.get_right() + UP * 0.05,
                         color=accent, stroke_width=2)

        # Arms (lines that can rotate)
        self.arm_left = self._make_arm(LEFT)
        self.arm_right = self._make_arm(RIGHT)

        # Legs
        self.leg_left = RoundedRectangle(width=0.18, height=0.35, corner_radius=0.08,
                                          color=color, fill_opacity=0.8, stroke_width=1.5)
        self.leg_left.next_to(self.body, DOWN, buff=0.02).shift(LEFT * 0.12)
        self.leg_right = RoundedRectangle(width=0.18, height=0.35, corner_radius=0.08,
                                           color=color, fill_opacity=0.8, stroke_width=1.5)
        self.leg_right.next_to(self.body, DOWN, buff=0.02).shift(RIGHT * 0.12)

        # Feet
        self.foot_left = Ellipse(width=0.22, height=0.1, color=accent, fill_opacity=0.9,
                                  stroke_width=1).next_to(self.leg_left, DOWN, buff=0.01)
        self.foot_right = Ellipse(width=0.22, height=0.1, color=accent, fill_opacity=0.9,
                                   stroke_width=1).next_to(self.leg_right, DOWN, buff=0.01)

        # Assemble (order matters for layering)
        self.add(
            self.leg_left, self.leg_right, self.foot_left, self.foot_right,
            self.body, self.belt,
            self.arm_left, self.arm_right,
            self.head,
            self.hair,
            self.eye_left, self.eye_right, self.shine_l, self.shine_r,
            self.mouth, self.blush_l, self.blush_r,
        )

    def _make_hair(self, style):
        """Generate spiky hair points based on style."""
        cx, cy = 0, 0.45
        if style == "energetic":
            # Wild spiky hair (like a battle-ready character)
            return [
                np.array([cx - 0.5, cy - 0.1, 0]),
                np.array([cx - 0.4, cy + 0.35, 0]),
                np.array([cx - 0.2, cy + 0.15, 0]),
                np.array([cx - 0.1, cy + 0.5, 0]),
                np.array([cx + 0.05, cy + 0.25, 0]),
                np.array([cx + 0.15, cy + 0.55, 0]),
                np.array([cx + 0.3, cy + 0.2, 0]),
                np.array([cx + 0.4, cy + 0.4, 0]),
                np.array([cx + 0.5, cy - 0.1, 0]),
            ]
        elif style == "cool":
            # Sleek swept hair
            return [
                np.array([cx - 0.45, cy - 0.15, 0]),
                np.array([cx - 0.35, cy + 0.3, 0]),
                np.array([cx - 0.1, cy + 0.2, 0]),
                np.array([cx + 0.0, cy + 0.4, 0]),
                np.array([cx + 0.2, cy + 0.25, 0]),
                np.array([cx + 0.35, cy + 0.15, 0]),
                np.array([cx + 0.5, cy + 0.3, 0]),
                np.array([cx + 0.55, cy - 0.1, 0]),
            ]
        elif style == "genius":
            # Pineapple ponytail style
            return [
                np.array([cx - 0.4, cy - 0.1, 0]),
                np.array([cx - 0.2, cy + 0.2, 0]),
                np.array([cx - 0.05, cy + 0.15, 0]),
                np.array([cx + 0.1, cy + 0.5, 0]),
                np.array([cx + 0.25, cy + 0.65, 0]),
                np.array([cx + 0.35, cy + 0.45, 0]),
                np.array([cx + 0.3, cy + 0.2, 0]),
                np.array([cx + 0.4, cy - 0.1, 0]),
            ]
        elif style == "cute":
            # Round fluffy hair
            return [
                np.array([cx - 0.5, cy - 0.1, 0]),
                np.array([cx - 0.45, cy + 0.2, 0]),
                np.array([cx - 0.3, cy + 0.35, 0]),
                np.array([cx - 0.1, cy + 0.4, 0]),
                np.array([cx + 0.1, cy + 0.4, 0]),
                np.array([cx + 0.3, cy + 0.35, 0]),
                np.array([cx + 0.45, cy + 0.2, 0]),
                np.array([cx + 0.5, cy - 0.1, 0]),
            ]
        else:  # scholar
            return [
                np.array([cx - 0.45, cy - 0.1, 0]),
                np.array([cx - 0.4, cy + 0.25, 0]),
                np.array([cx - 0.15, cy + 0.3, 0]),
                np.array([cx + 0.0, cy + 0.35, 0]),
                np.array([cx + 0.15, cy + 0.3, 0]),
                np.array([cx + 0.4, cy + 0.25, 0]),
                np.array([cx + 0.45, cy - 0.1, 0]),
            ]

    def _make_arm(self, side):
        """Create an arm as a group of shapes."""
        direction = -1 if side[0] < 0 else 1
        shoulder = self.head.get_center() + DOWN * 0.55 + side * 0.3
        hand_pos = shoulder + DOWN * 0.35 + side * 0.15

        arm_line = Line(shoulder, hand_pos, color=WHITE, stroke_width=4)
        hand = Circle(radius=0.08, color=WHITE, fill_opacity=1,
                      stroke_color=self.char_color, stroke_width=1.5).move_to(hand_pos)
        return VGroup(arm_line, hand)

    # ── ANIMATION METHODS ──

    def wave(self, scene, duration=1.5):
        """Wave the right arm up and down."""
        arm = self.arm_right
        scene.play(
            Rotate(arm, angle=PI / 3, about_point=arm[0].get_start()),
            run_time=duration / 3
        )
        scene.play(
            Rotate(arm, angle=-PI / 6, about_point=arm[0].get_start()),
            run_time=duration / 6
        )
        scene.play(
            Rotate(arm, angle=PI / 6, about_point=arm[0].get_start()),
            run_time=duration / 6
        )
        scene.play(
            Rotate(arm, angle=-PI / 3, about_point=arm[0].get_start()),
            run_time=duration / 3
        )

    def point_at(self, scene, target_pos, duration=1.0):
        """Point the right arm toward a target position."""
        arm = self.arm_right
        shoulder = arm[0].get_start()
        direction = target_pos - shoulder
        angle = np.arctan2(direction[1], direction[0])
        current_angle = np.arctan2(
            arm[0].get_end()[1] - shoulder[1],
            arm[0].get_end()[0] - shoulder[0]
        )
        delta = angle - current_angle
        scene.play(
            Rotate(arm, angle=delta, about_point=shoulder),
            run_time=duration
        )

    def bounce(self, scene, times=2, height=0.2, duration=1.0):
        """Bounce up and down excitedly."""
        dt = duration / (times * 2)
        for _ in range(times):
            scene.play(self.animate.shift(UP * height), run_time=dt, rate_func=rush_from)
            scene.play(self.animate.shift(DOWN * height), run_time=dt, rate_func=rush_into)

    def nod(self, scene, times=2, duration=0.8):
        """Nod the head."""
        dt = duration / (times * 2)
        head_group = VGroup(self.head, self.hair, self.eye_left, self.eye_right,
                            self.shine_l, self.shine_r, self.mouth, self.blush_l, self.blush_r)
        for _ in range(times):
            scene.play(head_group.animate.shift(DOWN * 0.06), run_time=dt)
            scene.play(head_group.animate.shift(UP * 0.06), run_time=dt)

    def think(self, scene, duration=1.5):
        """Thinking pose — tilt head, show thought bubble."""
        head_group = VGroup(self.head, self.hair, self.eye_left, self.eye_right,
                            self.shine_l, self.shine_r, self.mouth, self.blush_l, self.blush_r)
        # Tilt head
        scene.play(Rotate(head_group, angle=PI / 12, about_point=self.head.get_bottom()), run_time=duration / 3)
        scene.wait(duration / 3)
        scene.play(Rotate(head_group, angle=-PI / 12, about_point=self.head.get_bottom()), run_time=duration / 3)

    def speak_bubble(self, scene, text, duration=2.0):
        """Show a speech bubble next to the character."""
        bubble_bg = RoundedRectangle(width=3.5, height=0.8, corner_radius=0.2,
                                      color=WHITE, fill_opacity=0.9, stroke_color=self.char_color, stroke_width=2)
        bubble_text = Text(text, font_size=20, color=BLACK, weight=BOLD)
        if bubble_text.width > 3.2:
            bubble_text.scale_to_fit_width(3.2)
        bubble_text.move_to(bubble_bg)

        # Position above head
        bubble = VGroup(bubble_bg, bubble_text)
        bubble.next_to(self, UP, buff=0.15)

        # Tail triangle pointing down
        tail = Triangle(color=WHITE, fill_opacity=0.9, stroke_color=self.char_color, stroke_width=2)
        tail.scale(0.12).rotate(PI).next_to(bubble_bg, DOWN, buff=-0.03)
        bubble.add(tail)

        scene.play(FadeIn(bubble, scale=0.5), run_time=0.5)
        scene.wait(duration - 1)
        scene.play(FadeOut(bubble), run_time=0.5)
        return bubble

    def excited_eyes(self, scene, duration=0.8):
        """Make eyes sparkle (scale up then back)."""
        eyes = VGroup(self.eye_left, self.eye_right)
        scene.play(eyes.animate.scale(1.4), run_time=duration / 2)
        scene.play(eyes.animate.scale(1 / 1.4), run_time=duration / 2)


# ── Pre-built character styles per domain ──

def get_physics_character():
    """Energetic fighter-style character for physics."""
    return ChibiCharacter(style="energetic", color="#E74C3C", accent="#FFD700")

def get_math_character():
    """Genius strategist character for math."""
    return ChibiCharacter(style="genius", color="#F39C12", accent="#2C3E50")

def get_biology_character():
    """Cute doctor character for biology."""
    return ChibiCharacter(style="cute", color="#27AE60", accent="#F5B7B1")

def get_tech_character():
    """Cool precise character for tech/AI."""
    return ChibiCharacter(style="cool", color="#1976D2", accent="#212121")

def get_space_character():
    """Scholar inventor character for space/science."""
    return ChibiCharacter(style="scholar", color="#1ABC9C", accent="#8E44AD")

def get_nature_character():
    """Navigator character for nature/geography."""
    return ChibiCharacter(style="cute", color="#2ECC71", accent="#E67E22")

CHARACTER_FACTORY = {
    "physics": get_physics_character,
    "mathematics": get_math_character,
    "biology": get_biology_character,
    "technology": get_tech_character,
    "ai": get_tech_character,
    "space": get_space_character,
    "nature": get_nature_character,
    "chemistry": lambda: ChibiCharacter(style="cool", color="#16A085", accent="#F39C12"),
    "history": lambda: ChibiCharacter(style="scholar", color="#D4A843", accent="#ECF0F1"),
}

def get_character(domain: str) -> ChibiCharacter:
    factory = CHARACTER_FACTORY.get(domain, get_physics_character)
    return factory()
