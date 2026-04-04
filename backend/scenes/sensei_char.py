"""
Animated Sensei character for educational reels.
Spiky-haired, orange outfit, headband — original Manim-drawn character.
Moves, points, reacts, explains.
"""
from manim import *
import numpy as np


def build_sensei(scale=1.0):
    """Build the full character as a VGroup. Returns (full_group, parts_dict)."""
    parts = {}

    # ── HEAD (big round) ──
    head = Circle(radius=0.55 * scale, color="#FFD5A0", fill_opacity=1,
                  stroke_color="#E8A050", stroke_width=2 * scale)
    parts["head"] = head

    # ── EYES (big anime eyes) ──
    eye_l_white = Ellipse(width=0.22 * scale, height=0.26 * scale, color=WHITE,
                          fill_opacity=1, stroke_width=1.5 * scale).move_to(
                          head.get_center() + LEFT * 0.18 * scale + UP * 0.05 * scale)
    eye_l_pupil = Dot(radius=0.07 * scale, color="#1976D2").move_to(eye_l_white.get_center())
    eye_l_shine = Dot(radius=0.025 * scale, color=WHITE).move_to(
                  eye_l_pupil.get_center() + UP * 0.02 * scale + RIGHT * 0.02 * scale)

    eye_r_white = Ellipse(width=0.22 * scale, height=0.26 * scale, color=WHITE,
                          fill_opacity=1, stroke_width=1.5 * scale).move_to(
                          head.get_center() + RIGHT * 0.18 * scale + UP * 0.05 * scale)
    eye_r_pupil = Dot(radius=0.07 * scale, color="#1976D2").move_to(eye_r_white.get_center())
    eye_r_shine = Dot(radius=0.025 * scale, color=WHITE).move_to(
                  eye_r_pupil.get_center() + UP * 0.02 * scale + RIGHT * 0.02 * scale)

    eyes = VGroup(eye_l_white, eye_l_pupil, eye_l_shine, eye_r_white, eye_r_pupil, eye_r_shine)
    parts["eyes"] = eyes

    # ── MOUTH (happy grin) ──
    mouth = Arc(radius=0.15 * scale, angle=-PI * 0.6, start_angle=-PI * 0.2,
                color="#333", stroke_width=2.5 * scale).move_to(head.get_center() + DOWN * 0.2 * scale)
    parts["mouth"] = mouth

    # ── HEADBAND ──
    band = RoundedRectangle(width=1.1 * scale, height=0.18 * scale, corner_radius=0.05 * scale,
                            color="#2962FF", fill_opacity=0.9, stroke_width=1.5 * scale)
    band.move_to(head.get_center() + UP * 0.32 * scale)
    band_plate = RoundedRectangle(width=0.25 * scale, height=0.14 * scale, corner_radius=0.03 * scale,
                                  color="#90CAF9", fill_opacity=1, stroke_color="#2962FF",
                                  stroke_width=1.5 * scale).move_to(band)
    headband = VGroup(band, band_plate)
    parts["headband"] = headband

    # ── HAIR (spiky yellow) ──
    s = scale
    hair_spikes = Polygon(
        np.array([-0.6 * s, 0.2 * s, 0]),
        np.array([-0.55 * s, 0.7 * s, 0]),
        np.array([-0.35 * s, 0.45 * s, 0]),
        np.array([-0.2 * s, 0.85 * s, 0]),
        np.array([-0.05 * s, 0.5 * s, 0]),
        np.array([0.1 * s, 0.9 * s, 0]),
        np.array([0.2 * s, 0.55 * s, 0]),
        np.array([0.35 * s, 0.8 * s, 0]),
        np.array([0.5 * s, 0.45 * s, 0]),
        np.array([0.6 * s, 0.7 * s, 0]),
        np.array([0.65 * s, 0.2 * s, 0]),
        color="#FFD700", fill_opacity=1, stroke_color="#E6B800", stroke_width=1.5 * s
    )
    hair_spikes.move_to(head.get_center() + UP * 0.35 * s)
    parts["hair"] = hair_spikes

    # ── BODY (orange jacket) ──
    body = RoundedRectangle(width=0.8 * s, height=0.9 * s, corner_radius=0.15 * s,
                            color="#FF6D00", fill_opacity=0.95, stroke_color="#E65100",
                            stroke_width=2 * s)
    body.next_to(head, DOWN, buff=0.03 * s)
    # Jacket zip line
    zip_line = Line(body.get_top(), body.get_bottom(), color="#FFB300", stroke_width=2 * s)
    parts["body"] = VGroup(body, zip_line)

    # ── ARMS ──
    shoulder_l = body.get_left() + UP * 0.25 * s
    shoulder_r = body.get_right() + UP * 0.25 * s

    arm_l_upper = Line(shoulder_l, shoulder_l + DOWN * 0.3 * s + LEFT * 0.2 * s,
                       color="#FF6D00", stroke_width=5 * s)
    arm_l_lower = Line(arm_l_upper.get_end(), arm_l_upper.get_end() + DOWN * 0.25 * s + LEFT * 0.1 * s,
                       color="#FF6D00", stroke_width=4.5 * s)
    hand_l = Circle(radius=0.08 * s, color="#FFD5A0", fill_opacity=1,
                    stroke_width=1.5 * s).move_to(arm_l_lower.get_end())

    arm_r_upper = Line(shoulder_r, shoulder_r + DOWN * 0.3 * s + RIGHT * 0.2 * s,
                       color="#FF6D00", stroke_width=5 * s)
    arm_r_lower = Line(arm_r_upper.get_end(), arm_r_upper.get_end() + DOWN * 0.25 * s + RIGHT * 0.1 * s,
                       color="#FF6D00", stroke_width=4.5 * s)
    hand_r = Circle(radius=0.08 * s, color="#FFD5A0", fill_opacity=1,
                    stroke_width=1.5 * s).move_to(arm_r_lower.get_end())

    left_arm = VGroup(arm_l_upper, arm_l_lower, hand_l)
    right_arm = VGroup(arm_r_upper, arm_r_lower, hand_r)
    parts["left_arm"] = left_arm
    parts["right_arm"] = right_arm

    # ── LEGS ──
    leg_l = RoundedRectangle(width=0.2 * s, height=0.4 * s, corner_radius=0.08 * s,
                             color="#1565C0", fill_opacity=0.9, stroke_width=1.5 * s)
    leg_l.next_to(body, DOWN, buff=0.02 * s).shift(LEFT * 0.15 * s)
    shoe_l = Ellipse(width=0.26 * s, height=0.1 * s, color="#212121", fill_opacity=0.9,
                     stroke_width=1 * s).next_to(leg_l, DOWN, buff=0.01 * s)

    leg_r = RoundedRectangle(width=0.2 * s, height=0.4 * s, corner_radius=0.08 * s,
                             color="#1565C0", fill_opacity=0.9, stroke_width=1.5 * s)
    leg_r.next_to(body, DOWN, buff=0.02 * s).shift(RIGHT * 0.15 * s)
    shoe_r = Ellipse(width=0.26 * s, height=0.1 * s, color="#212121", fill_opacity=0.9,
                     stroke_width=1 * s).next_to(leg_r, DOWN, buff=0.01 * s)

    legs = VGroup(leg_l, shoe_l, leg_r, shoe_r)
    parts["legs"] = legs

    # ── Assemble ──
    full = VGroup(
        legs, parts["body"], left_arm, right_arm,
        head, hair_spikes, headband, eyes, mouth
    )
    return full, parts


def sensei_point_right(scene, char, parts, target, dur=0.8):
    """Animate right arm pointing at target."""
    arm = parts["right_arm"]
    hand = arm[2]
    shoulder = arm[0].get_start()
    direction = (target - shoulder)
    direction = direction / np.linalg.norm(direction) * 0.6

    new_upper = Line(shoulder, shoulder + direction * 0.55,
                     color="#FF6D00", stroke_width=arm[0].get_stroke_width())
    new_lower = Line(new_upper.get_end(), new_upper.get_end() + direction * 0.4,
                     color="#FF6D00", stroke_width=arm[1].get_stroke_width())
    new_hand = hand.copy().move_to(new_lower.get_end())

    scene.play(
        Transform(arm[0], new_upper),
        Transform(arm[1], new_lower),
        arm[2].animate.move_to(new_lower.get_end()),
        run_time=dur
    )


def sensei_wave(scene, char, dur=1.0):
    """Bounce the whole character and tilt slightly."""
    scene.play(
        char.animate.shift(UP * 0.15).rotate(0.05, about_point=char.get_bottom()),
        run_time=dur / 4, rate_func=rush_from
    )
    scene.play(
        char.animate.shift(DOWN * 0.15).rotate(-0.05, about_point=char.get_bottom()),
        run_time=dur / 4, rate_func=rush_into
    )
    scene.play(
        char.animate.shift(UP * 0.1).rotate(0.03, about_point=char.get_bottom()),
        run_time=dur / 4, rate_func=rush_from
    )
    scene.play(
        char.animate.shift(DOWN * 0.1).rotate(-0.03, about_point=char.get_bottom()),
        run_time=dur / 4, rate_func=rush_into
    )


def sensei_react(scene, char, text="!", color="#FFD700", dur=0.8):
    """Show a reaction symbol above the character's head."""
    react = Text(text, font_size=40, color=color, weight=BOLD)
    react.next_to(char, UP, buff=0.15)
    scene.play(FadeIn(react, scale=2), run_time=dur / 2)
    scene.play(FadeOut(react, shift=UP * 0.3), run_time=dur / 2)


def sensei_speak(scene, char, text, dur=2.5):
    """Show a speech bubble."""
    bg = RoundedRectangle(width=4.5, height=0.9, corner_radius=0.2,
                          color=WHITE, fill_opacity=0.95, stroke_color="#FF6D00", stroke_width=2)
    txt = Text(text, font_size=22, color="#1a1a1a", weight=BOLD)
    if txt.width > 4.0:
        txt.scale_to_fit_width(4.0)
    txt.move_to(bg)
    tail = Triangle(color=WHITE, fill_opacity=0.95, stroke_color="#FF6D00", stroke_width=2)
    tail.scale(0.08).rotate(PI).next_to(bg, DOWN, buff=-0.02)
    bubble = VGroup(bg, txt, tail).next_to(char, UP, buff=0.1)

    scene.play(FadeIn(bubble, scale=0.6), run_time=0.4)
    scene.wait(dur - 0.8)
    scene.play(FadeOut(bubble), run_time=0.4)
