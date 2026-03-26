from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0f0e17"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        PRIMARY = "#7f5af0"
        ACCENT = "#2cb67d"
        WARM = "#ff8906"
        TEXT_COL = "#fffffe"
        DIM = "#a7a9be"

        # ═══ SCENE 1: Hook ═══
        q1 = Text("How does your phone", font_size=42, color=TEXT_COL, weight=BOLD)
        q2 = Text("know your face?", font_size=48, color=PRIMARY, weight=BOLD)
        hook = VGroup(q1, q2).arrange(DOWN, buff=0.4).move_to(UP * 3)

        phone = RoundedRectangle(width=2.5, height=4, corner_radius=0.3,
            color=DIM, stroke_width=2, fill_opacity=0.05).move_to(DOWN * 1)
        screen = RoundedRectangle(width=2.1, height=3.2, corner_radius=0.15,
            color=PRIMARY, fill_opacity=0.1, stroke_width=1).move_to(phone)
        face = Circle(radius=0.6, color=ACCENT, fill_opacity=0.2, stroke_width=2).move_to(phone.get_center() + UP * 0.3)
        eye_l = Dot(radius=0.08, color=ACCENT).move_to(face.get_center() + LEFT * 0.2 + UP * 0.1)
        eye_r = Dot(radius=0.08, color=ACCENT).move_to(face.get_center() + RIGHT * 0.2 + UP * 0.1)
        mouth = Arc(radius=0.2, angle=-PI, color=ACCENT, stroke_width=2).move_to(face.get_center() + DOWN * 0.15)
        face_group = VGroup(face, eye_l, eye_r, mouth)

        scan_line = Line(LEFT * 1.05, RIGHT * 1.05, color=PRIMARY, stroke_width=3).move_to(phone.get_top() + DOWN * 0.5)

        self.play(Write(q1), run_time=1)
        self.play(Write(q2), run_time=1)
        self.play(FadeIn(phone), FadeIn(screen), GrowFromCenter(face_group), run_time=1.5)
        self.play(scan_line.animate.move_to(phone.get_bottom() + UP * 0.5), run_time=2, rate_func=smooth)
        self.play(face.animate.set_stroke(color=ACCENT, width=4), Flash(face, color=ACCENT, num_lines=8), run_time=1)
        self.wait(1)

        # ═══ SCENE 2: What is ML ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title2 = Text("Machine Learning", font_size=48, color=PRIMARY, weight=BOLD).move_to(UP * 5.5)
        eq = Text("Data + Patterns = Predictions", font_size=30, color=WARM, weight=BOLD).move_to(UP * 3.8)

        data_box = RoundedRectangle(width=2, height=1.5, corner_radius=0.2,
            color=ACCENT, fill_opacity=0.15, stroke_width=2).move_to(LEFT * 2.5 + UP * 1)
        data_label = Text("Data", font_size=28, color=ACCENT, weight=BOLD).move_to(data_box)
        data_dots = VGroup(*[
            Dot(radius=0.06, color=ACCENT).move_to(data_box.get_center() + np.array([
                np.random.uniform(-0.6, 0.6), np.random.uniform(-0.4, 0.4), 0
            ])) for _ in range(12)
        ])

        arrow1 = Arrow(LEFT * 1.2 + UP * 1, LEFT * 0.2 + UP * 1, color=DIM, stroke_width=2)

        brain = Circle(radius=1, color=PRIMARY, fill_opacity=0.1, stroke_width=2).move_to(UP * 1)
        brain_label = Text("ML\nModel", font_size=22, color=PRIMARY, weight=BOLD).move_to(brain)
        neurons = VGroup(*[
            Dot(radius=0.08, color=PRIMARY).move_to(brain.get_center() + 0.6 * np.array([
                np.cos(a), np.sin(a), 0
            ])) for a in np.linspace(0, 2 * PI, 6, endpoint=False)
        ])

        arrow2 = Arrow(RIGHT * 0.2 + UP * 1, RIGHT * 1.2 + UP * 1, color=DIM, stroke_width=2)

        pred_box = RoundedRectangle(width=2, height=1.5, corner_radius=0.2,
            color=WARM, fill_opacity=0.15, stroke_width=2).move_to(RIGHT * 2.5 + UP * 1)
        pred_label = Text("Predict", font_size=28, color=WARM, weight=BOLD).move_to(pred_box)
        check = Text("\u2713", font_size=40, color=ACCENT).move_to(pred_box.get_center() + DOWN * 0.1)

        self.play(Write(title2), run_time=1)
        self.play(FadeIn(eq, shift=DOWN * 0.3), run_time=1)
        self.play(FadeIn(data_box), Write(data_label), LaggedStart(*[FadeIn(d, scale=0.3) for d in data_dots], lag_ratio=0.05), run_time=1.5)
        self.play(GrowArrow(arrow1), run_time=0.8)
        self.play(GrowFromCenter(brain), Write(brain_label), LaggedStart(*[FadeIn(n, scale=0.5) for n in neurons], lag_ratio=0.1), run_time=1.5)
        self.play(GrowArrow(arrow2), run_time=0.8)
        self.play(FadeIn(pred_box), Write(pred_label), run_time=1)
        self.play(FadeIn(check, scale=1.5), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 3: How it learns ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title3 = Text("How It Learns", font_size=46, color=TEXT_COL, weight=BOLD).move_to(UP * 5.5)

        axes = Axes(x_range=[0, 6, 1], y_range=[0, 5, 1], x_length=5.5, y_length=4,
            axis_config={"color": DIM, "stroke_width": 1.5}).move_to(UP * 1)
        x_lab = Text("Experience", font_size=20, color=DIM).next_to(axes.x_axis, DOWN, buff=0.3)
        y_lab = Text("Accuracy", font_size=20, color=DIM).next_to(axes.y_axis, LEFT, buff=0.3).rotate(PI / 2)

        curve = axes.plot(lambda x: 4.5 * (1 - np.exp(-0.7 * x)), x_range=[0, 6], color=ACCENT, stroke_width=3)
        tracer = Dot(radius=0.12, color=WARM).move_to(axes.c2p(0, 0))

        bad_label = Text("Bad", font_size=22, color="#e53170").move_to(axes.c2p(0.5, 0.5) + DOWN * 0.4)
        good_label = Text("Great!", font_size=22, color=ACCENT).move_to(axes.c2p(5.5, 4.2) + UP * 0.4)

        self.play(Write(title3), run_time=1)
        self.play(Create(axes), Write(x_lab), Write(y_lab), run_time=2)
        self.play(FadeIn(bad_label), run_time=0.5)
        self.play(Create(curve), MoveAlongPath(tracer, curve), run_time=3, rate_func=smooth)
        self.play(FadeIn(good_label, scale=1.3), run_time=1)
        self.play(Flash(tracer, color=ACCENT, num_lines=6), run_time=1)
        self.wait(1.5)

        # ═══ SCENE 4: Real world examples ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title4 = Text("ML Is Everywhere", font_size=44, color=PRIMARY, weight=BOLD).move_to(UP * 5.5)

        examples = [
            ("\U0001F3A5", "Netflix", "Recommends shows", PRIMARY),
            ("\U0001F3B5", "Spotify", "Predicts your taste", ACCENT),
            ("\U0001F697", "Tesla", "Self-driving cars", WARM),
            ("\U0001F4F1", "Siri", "Understands speech", "#e53170"),
        ]

        cards = VGroup()
        for i, (emoji, name, desc, col) in enumerate(examples):
            card = RoundedRectangle(width=7, height=1.6, corner_radius=0.2,
                color=col, fill_opacity=0.08, stroke_width=1.5)
            icon = Text(emoji, font_size=36).move_to(card.get_left() + RIGHT * 0.8)
            n = Text(name, font_size=26, color=col, weight=BOLD).move_to(card.get_left() + RIGHT * 2.2 + UP * 0.2)
            d = Text(desc, font_size=20, color=DIM).move_to(card.get_left() + RIGHT * 2.8 + DOWN * 0.25)
            cards.add(VGroup(card, icon, n, d))

        cards.arrange(DOWN, buff=0.35).move_to(UP * 0.5)

        self.play(Write(title4), run_time=1)
        self.play(
            LaggedStart(*[FadeIn(c, shift=RIGHT * 0.5) for c in cards], lag_ratio=0.25),
            run_time=3
        )
        for i, card in enumerate(cards):
            self.play(Indicate(card[0], color=examples[i][3], scale_factor=1.03), run_time=0.6)
        self.wait(1)

        # ═══ SCENE 5: Neural Network ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        title5 = Text("Inside a Neural Network", font_size=40, color=TEXT_COL, weight=BOLD).move_to(UP * 5.5)

        layers = [3, 5, 5, 3]
        all_neurons = []
        all_dots = VGroup()
        x_positions = [-2.5, -0.8, 0.8, 2.5]

        for li, (count, xp) in enumerate(zip(layers, x_positions)):
            layer = []
            for ni in range(count):
                y = (ni - (count - 1) / 2) * 1.2
                color = [ACCENT, PRIMARY, PRIMARY, WARM][li]
                dot = Circle(radius=0.25, color=color, fill_opacity=0.2, stroke_width=2)
                dot.move_to(np.array([xp, y + 0.5, 0]))
                layer.append(dot)
                all_dots.add(dot)
            all_neurons.append(layer)

        connections = VGroup()
        for li in range(len(layers) - 1):
            for n1 in all_neurons[li]:
                for n2 in all_neurons[li + 1]:
                    line = Line(n1.get_center(), n2.get_center(),
                        color=DIM, stroke_width=0.8, stroke_opacity=0.4)
                    connections.add(line)

        labels = VGroup(
            Text("Input", font_size=20, color=ACCENT).move_to(DOWN * 3.5 + LEFT * 2.5),
            Text("Hidden", font_size=20, color=PRIMARY).move_to(DOWN * 3.5),
            Text("Output", font_size=20, color=WARM).move_to(DOWN * 3.5 + RIGHT * 2.5),
        )

        self.play(Write(title5), run_time=1)
        self.play(LaggedStart(*[Create(c) for c in connections], lag_ratio=0.01), run_time=1.5)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in all_dots], lag_ratio=0.05), run_time=2)
        self.play(FadeIn(labels), run_time=1)

        signal_dots = VGroup(*[
            Dot(radius=0.1, color=WARM, fill_opacity=0.9).move_to(all_neurons[0][i].get_center())
            for i in range(3)
        ])
        self.play(FadeIn(signal_dots, scale=0.5), run_time=0.5)
        for li in range(len(layers) - 1):
            targets = [all_neurons[li + 1][j].get_center() for j in range(layers[li + 1])]
            new_dots = VGroup(*[Dot(radius=0.1, color=WARM, fill_opacity=0.9).move_to(t) for t in targets])
            self.play(FadeOut(signal_dots), FadeIn(new_dots, scale=0.5), run_time=0.8)
            signal_dots = new_dots
        self.play(Flash(signal_dots[1], color=WARM, num_lines=8), run_time=1)
        self.wait(1)

        # ═══ SCENE 6: Closing ═══
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        final = Text("Machine\nLearning", font_size=64, color=PRIMARY, weight=BOLD,
            line_spacing=1.3).move_to(UP * 1)
        glow = Circle(radius=3, color=PRIMARY, fill_opacity=0.04, stroke_width=1).move_to(final)
        tagline = Text("Teaching machines to think", font_size=30, color=ACCENT, weight=BOLD).move_to(DOWN * 2.5)
        self.play(GrowFromCenter(glow), run_time=1)
        self.play(Write(final), run_time=2)
        self.play(FadeIn(tagline, shift=UP * 0.3), run_time=1.5)
        self.play(glow.animate.scale(1.1), rate_func=there_and_back, run_time=2)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
