from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d0d1a"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        YELLOW  = "#FFD700"
        PINK    = "#FF69B4"
        CYAN    = "#00CED1"
        PURPLE  = "#9B59B6"
        GREEN   = "#2CB67D"
        WHITE   = "#FFFFFE"
        DIM     = "#a7a9be"
        RED     = "#E53170"
        ORANGE  = "#E67E22"

        # ═══ SCENE 1: Hook ═══
        hook1 = Text("Why does music", font_size=56, color=WHITE, weight=BOLD)
        hook2 = Text("make you happy?", font_size=56, color=YELLOW, weight=BOLD)
        hook = VGroup(hook1, hook2).arrange(DOWN, buff=0.4).move_to(UP * 4.5)

        note_positions = [
            np.array([-3.2,  1.5, 0]),
            np.array([ 3.2,  1.0, 0]),
            np.array([-1.8, -0.5, 0]),
            np.array([ 2.5, -1.8, 0]),
            np.array([ 0.0,  0.3, 0]),
        ]
        note_colors = [YELLOW, PINK, CYAN, GREEN, PURPLE]
        notes = VGroup(*[
            Text("\u266a", font_size=72, color=c).move_to(p)
            for p, c in zip(note_positions, note_colors)
        ])

        self.play(Write(hook1), run_time=1)
        self.play(Write(hook2), run_time=1)
        self.play(
            LaggedStart(*[FadeIn(n, scale=0.3) for n in notes], lag_ratio=0.15),
            run_time=2
        )
        self.play(
            LaggedStart(*[n.animate.shift(UP * 0.5) for n in notes], lag_ratio=0.1),
            run_time=1.5
        )
        self.wait(1.5)

        # ═══ SCENE 2: Major Keys ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title2 = Text("Major Keys = Happiness", font_size=46, color=YELLOW, weight=BOLD).move_to(UP * 5.8)

        key_group = VGroup()
        white_w, white_h = 0.9, 3.8
        for i in range(7):
            key = Rectangle(width=white_w, height=white_h,
                            fill_color=WHITE, fill_opacity=0.95,
                            stroke_color=DIM, stroke_width=1.5)
            key.move_to(LEFT * 2.7 + RIGHT * i * (white_w + 0.05) + UP * 0.5)
            key_group.add(key)

        black_offsets = [0, 1, 3, 4, 5]
        for i in black_offsets:
            bkey = Rectangle(width=0.55, height=2.4,
                             fill_color="#1a1a2e", fill_opacity=1,
                             stroke_color=DIM, stroke_width=1)
            bkey.move_to(LEFT * 2.7 + RIGHT * (i * (white_w + 0.05) + 0.47) + UP * 1.7)
            key_group.add(bkey)

        chord_label = Text("C Major Chord", font_size=30, color=YELLOW).move_to(UP * 4.5)
        highlight_keys = VGroup()
        for i in [0, 2, 4]:
            glow = Rectangle(width=white_w, height=white_h,
                             fill_color=YELLOW, fill_opacity=0.45, stroke_width=0)
            glow.move_to(key_group[i].get_center())
            highlight_keys.add(glow)

        note_labels = VGroup(
            Text("C", font_size=26, color="#0d0d1a", weight=BOLD).move_to(key_group[0].get_bottom() + UP * 0.4),
            Text("E", font_size=26, color="#0d0d1a", weight=BOLD).move_to(key_group[2].get_bottom() + UP * 0.4),
            Text("G", font_size=26, color="#0d0d1a", weight=BOLD).move_to(key_group[4].get_bottom() + UP * 0.4),
        )

        happy_label = Text("Sounds bright & joyful!", font_size=32, color=GREEN, weight=BOLD).move_to(DOWN * 2.8)

        self.play(Write(title2), run_time=1)
        self.play(LaggedStart(*[GrowFromCenter(k) for k in key_group[:7]], lag_ratio=0.08), run_time=2)
        self.play(LaggedStart(*[FadeIn(k) for k in key_group[7:]], lag_ratio=0.08), run_time=1)
        self.play(Write(chord_label), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(h) for h in highlight_keys], lag_ratio=0.2),
            LaggedStart(*[Write(l) for l in note_labels], lag_ratio=0.2),
            run_time=1.5
        )
        self.play(Indicate(highlight_keys, scale_factor=1.05, color=YELLOW), run_time=1)
        self.play(Write(happy_label), run_time=0.8)
        self.wait(1.5)

        # ═══ SCENE 3: BPM / Tempo ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title3 = Text("The Power of BPM", font_size=48, color=CYAN, weight=BOLD).move_to(UP * 5.8)

        heart = Text("\u2665", font_size=100, color=RED).move_to(UP * 2.5)
        bpm_val = Text("120 BPM", font_size=64, color=CYAN, weight=BOLD).move_to(UP * 0.3)
        bpm_label = Text("Beats Per Minute", font_size=30, color=DIM).move_to(DOWN * 0.8)

        bars = VGroup(*[
            Rectangle(width=0.38, height=1.0 + 0.9 * abs(np.sin(i * 0.8)),
                      fill_color=CYAN, fill_opacity=0.85, stroke_width=0)
            .move_to(LEFT * 3.3 + RIGHT * i * 0.55 + DOWN * 2.6)
            for i in range(13)
        ])

        tempo_desc = VGroup(
            Text("Slow 60 BPM = Calm / Sad", font_size=26, color=DIM),
            Text("Fast 120 BPM = Happy!", font_size=28, color=YELLOW, weight=BOLD),
        ).arrange(DOWN, buff=0.5).move_to(DOWN * 4.4)

        self.play(Write(title3), run_time=1)
        self.play(GrowFromCenter(heart), run_time=1)
        for _ in range(2):
            self.play(heart.animate.scale(1.18), run_time=0.25)
            self.play(heart.animate.scale(1 / 1.18), run_time=0.25)
        self.play(FadeIn(bpm_val, shift=UP * 0.3), Write(bpm_label), run_time=1)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.06),
            run_time=2
        )
        self.play(FadeIn(tempo_desc), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 4: Dopamine & Brain ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title4 = Text("Dopamine Rush", font_size=52, color=PURPLE, weight=BOLD).move_to(UP * 5.8)

        brain_left  = Ellipse(width=3.0, height=2.5, color=PURPLE,
                              fill_opacity=0.12, stroke_width=2.5).move_to(LEFT * 0.8 + UP * 1.5)
        brain_right = Ellipse(width=3.0, height=2.5, color=PURPLE,
                              fill_opacity=0.12, stroke_width=2.5).move_to(RIGHT * 0.8 + UP * 1.5)
        brain_label = Text("Brain", font_size=28, color=PURPLE, weight=BOLD).move_to(UP * 1.5)

        dopa_positions = [
            np.array([-2.8,  3.5, 0]),
            np.array([ 2.8,  3.2, 0]),
            np.array([-1.2,  4.0, 0]),
            np.array([ 1.5,  3.8, 0]),
            np.array([ 0.0,  4.5, 0]),
        ]
        dopamines = VGroup(*[
            VGroup(
                Circle(radius=0.30, color=YELLOW, fill_opacity=0.9, stroke_width=0).move_to(p),
                Text("D", font_size=22, color="#0d0d1a", weight=BOLD).move_to(p),
            ) for p in dopa_positions
        ])

        reward_label = Text("REWARD SIGNAL!", font_size=34, color=YELLOW, weight=BOLD).move_to(DOWN * 0.5)
        stats = VGroup(
            Text("Happy music = same reward as food", font_size=24, color=WHITE),
            Text("Dopamine spikes at the chorus", font_size=22, color=DIM),
        ).arrange(DOWN, buff=0.4).move_to(DOWN * 3.0)

        self.play(Write(title4), run_time=1)
        self.play(
            GrowFromCenter(brain_left),
            GrowFromCenter(brain_right),
            Write(brain_label),
            run_time=1.5
        )
        self.play(
            LaggedStart(*[GrowFromCenter(dg) for dg in dopamines], lag_ratio=0.15),
            run_time=2
        )
        self.play(
            LaggedStart(*[dg.animate.shift(UP * 0.7) for dg in dopamines], lag_ratio=0.1),
            run_time=1
        )
        self.play(Write(reward_label), run_time=0.8)
        self.play(Indicate(reward_label, color=YELLOW, scale_factor=1.1), run_time=0.8)
        self.play(FadeIn(stats), run_time=1.2)
        self.wait(1.5)

        # ═══ SCENE 5: Closing + ScrollUForward Branding ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        close1 = Text("Music is science", font_size=52, color=WHITE, weight=BOLD)
        close2 = Text("you can feel.", font_size=52, color=YELLOW, weight=BOLD)
        closing = VGroup(close1, close2).arrange(DOWN, buff=0.4).move_to(UP * 3.8)

        icons = VGroup(
            Text("\u266a", font_size=56, color=CYAN),
            Text("\u2665", font_size=56, color=RED),
            Text("\u25cb", font_size=56, color=PURPLE),
            Text("\u2605", font_size=56, color=YELLOW),
        ).arrange(RIGHT, buff=1.0).move_to(UP * 0.5)

        # ScrollUForward branding
        brand_bg = RoundedRectangle(
            width=8.0, height=1.6, corner_radius=0.3,
            fill_color="#c8372d", fill_opacity=1, stroke_width=0
        ).move_to(DOWN * 2.5)
        brand_text = Text("ScrollUForward", font_size=38, color=WHITE, weight=BOLD).move_to(DOWN * 2.3)
        learn_text = Text("Learn Something Real Every Day", font_size=22, color="#ffe0de").move_to(DOWN * 2.9)

        self.play(FadeIn(close1, shift=UP * 0.3), FadeIn(close2, shift=UP * 0.3), run_time=1.5)
        self.play(
            LaggedStart(*[FadeIn(ic, scale=0.4) for ic in icons], lag_ratio=0.2),
            run_time=1.5
        )
        self.play(FadeIn(brand_bg), run_time=0.6)
        self.play(Write(brand_text), Write(learn_text), run_time=1.2)
        self.play(Indicate(brand_bg, scale_factor=1.02, color="#c8372d"), run_time=0.8)
        self.wait(2.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
