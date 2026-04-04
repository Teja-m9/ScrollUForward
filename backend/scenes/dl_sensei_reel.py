from manim import *
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sensei_char import build_sensei, sensei_wave, sensei_react, sensei_speak

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0a0a12"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # SAFE ZONE: y from -3.5 to 5.5

        BLUE = "#00b4d8"
        PURPLE = "#7f5af0"
        GREEN = "#2cb67d"
        ORANGE = "#ff8906"
        PINK = "#e53170"
        CYAN = "#00d4ff"
        W = "#fffffe"
        DIM = "#72757e"

        # ── Build character ──
        sensei, parts = build_sensei(scale=1.1)
        sensei.move_to(RIGHT * 8)  # off-screen

        # ══════════════════════════════════════════
        # SCENE 1: Character slides in, introduces topic
        # ══════════════════════════════════════════
        sensei.move_to(RIGHT * 2.5 + DOWN * 2)
        sensei_off = sensei.copy().shift(RIGHT * 6)
        self.add(sensei_off)
        self.play(sensei_off.animate.move_to(sensei.get_center()), run_time=1, rate_func=smooth)
        self.remove(sensei_off)
        self.add(sensei)

        # Wave hello
        sensei_wave(self, sensei, dur=0.8)

        # Speech bubble
        sensei_speak(self, sensei, "Let me teach you Deep Learning!", dur=2)

        # Big hook text
        h1 = Text("Your brain:", font_size=48, color=W, weight=BOLD).move_to(LEFT * 1 + UP * 4)
        h2 = Text("86 Billion", font_size=64, color=ORANGE, weight=BOLD).move_to(LEFT * 1 + UP * 2.8)
        h3 = Text("Neurons", font_size=48, color=W, weight=BOLD).move_to(LEFT * 1 + UP * 1.8)

        self.play(Write(h1), run_time=0.8)
        self.play(Write(h2), run_time=1)
        sensei_react(self, sensei, "!!", ORANGE, dur=0.6)
        self.play(Write(h3), run_time=0.8)

        self.wait(0.5)

        # ══════════════════════════════════════════
        # SCENE 2: Biological neuron — character explains
        # ══════════════════════════════════════════
        self.play(FadeOut(h1, h2, h3), run_time=0.5)

        # Move character to bottom-left
        self.play(sensei.animate.move_to(LEFT * 2.8 + DOWN * 2.5).scale(0.8), run_time=0.6)

        title = Text("The Neuron", font_size=52, color=CYAN, weight=BOLD).move_to(UP * 4.5)
        self.play(Write(title), run_time=0.8)

        # BIG biological neuron diagram
        cell = Circle(radius=1.0, color=GREEN, fill_opacity=0.12, stroke_width=3).move_to(UP * 1.5)
        cell_label = Text("Cell Body", font_size=28, color=GREEN, weight=BOLD).move_to(cell)

        # Dendrites (left)
        dendrites = VGroup()
        d_label = Text("Inputs", font_size=24, color=BLUE).move_to(LEFT * 3.2 + UP * 2.2)
        for i, angle in enumerate([PI * 0.7, PI * 0.85, PI * 1.0, PI * 1.15]):
            start = cell.get_center() + 1.0 * np.array([np.cos(angle), np.sin(angle), 0])
            end = cell.get_center() + 2.0 * np.array([np.cos(angle), np.sin(angle), 0])
            d = Line(end, start, color=BLUE, stroke_width=3)
            dot = Dot(radius=0.08, color=BLUE).move_to(end)
            dendrites.add(d, dot)

        # Axon (right)
        axon = Arrow(cell.get_right(), cell.get_right() + RIGHT * 2, color=ORANGE,
                     stroke_width=4, max_tip_length_to_length_ratio=0.15)
        axon_label = Text("Output", font_size=24, color=ORANGE).next_to(axon, DOWN, buff=0.15)

        sensei_speak(self, sensei, "This is how YOUR neurons work!", dur=1.5)

        self.play(GrowFromCenter(cell), Write(cell_label), run_time=1)
        self.play(
            LaggedStart(*[Create(d) for d in dendrites], lag_ratio=0.1),
            Write(d_label),
            run_time=1.2
        )

        # Signals flow in
        for i in range(0, len(dendrites), 2):
            sig = Dot(radius=0.1, color=CYAN).move_to(dendrites[i + 1].get_center())
            self.play(sig.animate.move_to(cell.get_center()), run_time=0.3)
            self.remove(sig)

        self.play(Flash(cell, color=GREEN, num_lines=8, flash_radius=1.2), run_time=0.5)
        self.play(GrowArrow(axon), Write(axon_label), run_time=1)

        # Signal out
        sig_out = Dot(radius=0.12, color=ORANGE).move_to(cell.get_center())
        self.play(sig_out.animate.move_to(axon.get_end()), run_time=0.6)
        self.play(Flash(axon.get_end(), color=ORANGE, num_lines=6), FadeOut(sig_out), run_time=0.5)

        sensei_react(self, sensei, "\u26A1", ORANGE, dur=0.5)
        self.wait(0.3)

        # ══════════════════════════════════════════
        # SCENE 3: Artificial neuron
        # ══════════════════════════════════════════
        self.play(FadeOut(title, cell, cell_label, dendrites, d_label, axon, axon_label), run_time=0.5)

        title3 = Text("Artificial Neuron", font_size=52, color=PURPLE, weight=BOLD).move_to(UP * 4.5)
        self.play(Write(title3), run_time=0.8)

        # BIG artificial neuron
        neuron = Circle(radius=0.9, color=PURPLE, fill_opacity=0.12, stroke_width=3).move_to(UP * 1)
        sigma = Text("\u03A3 \u2192 f", font_size=36, color=PURPLE, weight=BOLD).move_to(neuron)

        # Input arrows with weights
        inp_data = [("x\u2081", 0.8), ("x\u2082", 0), ("x\u2083", -0.8)]
        inp_arrows = VGroup()
        inp_labels = VGroup()
        w_labels = VGroup()
        for label, y_off in inp_data:
            start = LEFT * 3 + UP * (1 + y_off)
            end = neuron.get_left() + UP * y_off * 0.5
            arr = Arrow(start, end, color=CYAN, stroke_width=3, max_tip_length_to_length_ratio=0.15)
            lbl = Text(label, font_size=26, color=W).next_to(start, LEFT, buff=0.15)
            w = Text("w", font_size=18, color=CYAN).move_to(arr.get_center() + UP * 0.2)
            inp_arrows.add(arr)
            inp_labels.add(lbl)
            w_labels.add(w)

        # Output
        out_arr = Arrow(neuron.get_right(), neuron.get_right() + RIGHT * 2,
                        color=ORANGE, stroke_width=4, max_tip_length_to_length_ratio=0.15)
        out_lbl = Text("y", font_size=30, color=ORANGE, weight=BOLD).next_to(out_arr, RIGHT, buff=0.15)

        sensei_speak(self, sensei, "Now let's build one in code!", dur=1.5)

        self.play(GrowFromCenter(neuron), Write(sigma), run_time=1)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in inp_arrows], lag_ratio=0.15),
            LaggedStart(*[FadeIn(l) for l in inp_labels], lag_ratio=0.15),
            LaggedStart(*[FadeIn(w) for w in w_labels], lag_ratio=0.15),
            run_time=1.5
        )

        # Data flows in
        for arr in inp_arrows:
            d = Dot(radius=0.08, color=CYAN).move_to(arr.get_start())
            self.play(d.animate.move_to(neuron.get_center()), run_time=0.25)
            self.remove(d)

        self.play(Flash(neuron, color=PURPLE, num_lines=8), run_time=0.4)
        self.play(GrowArrow(out_arr), Write(out_lbl), run_time=0.8)

        # Formula
        formula = Text("y = f( w\u2081x\u2081 + w\u2082x\u2082 + w\u2083x\u2083 + b )",
                        font_size=26, color=W).move_to(DOWN * 1.5)
        self.play(Write(formula), run_time=1.2)
        sensei_react(self, sensei, "\u2714", GREEN, dur=0.5)
        self.wait(0.3)

        # ══════════════════════════════════════════
        # SCENE 4: Deep Neural Network — character builds it
        # ══════════════════════════════════════════
        self.play(FadeOut(title3, neuron, sigma, inp_arrows, inp_labels, w_labels,
                          out_arr, out_lbl, formula), run_time=0.5)

        # Move character to bottom-right
        self.play(sensei.animate.move_to(RIGHT * 2.8 + DOWN * 2.5), run_time=0.5)

        title4 = Text("Deep Network", font_size=52, color=W, weight=BOLD).move_to(UP * 4.5)
        self.play(Write(title4), run_time=0.8)

        sensei_speak(self, sensei, "Stack neurons into layers!", dur=1.5)

        # Build network — BIG
        layers = [3, 5, 5, 3]
        layer_cols = [GREEN, PURPLE, PURPLE, ORANGE]
        layer_names = ["Input", "Hidden", "Hidden", "Output"]
        x_pos = [-2.5, -0.8, 0.8, 2.5]

        all_neurons = []
        all_dots = VGroup()
        for li, (count, xp, col) in enumerate(zip(layers, x_pos, layer_cols)):
            layer = []
            for ni in range(count):
                y = (ni - (count - 1) / 2) * 1.0
                dot = Circle(radius=0.25, color=col, fill_opacity=0.2, stroke_width=2.5)
                dot.move_to(np.array([xp, y + 1.5, 0]))
                layer.append(dot)
                all_dots.add(dot)
            all_neurons.append(layer)

        connections = VGroup()
        for li in range(len(layers) - 1):
            for n1 in all_neurons[li]:
                for n2 in all_neurons[li + 1]:
                    l = Line(n1.get_center(), n2.get_center(),
                             color=DIM, stroke_width=0.7, stroke_opacity=0.3)
                    connections.add(l)

        # Layer by layer appearance
        self.play(LaggedStart(*[Create(c) for c in connections], lag_ratio=0.005), run_time=1.5)
        for li, layer in enumerate(all_neurons):
            self.play(
                LaggedStart(*[GrowFromCenter(n) for n in layer], lag_ratio=0.1),
                run_time=0.6
            )

        # "DEEP" highlight
        bracket = Brace(VGroup(all_dots[3], all_dots[12]), direction=DOWN, color=CYAN).shift(DOWN * 0.5)
        deep_label = Text("DEEP = many hidden layers", font_size=24, color=CYAN, weight=BOLD)
        deep_label.next_to(bracket, DOWN, buff=0.15)
        self.play(Create(bracket), Write(deep_label), run_time=1)

        # Signal flow
        for _ in range(2):
            sigs = VGroup(*[Dot(radius=0.1, color=ORANGE).move_to(n.get_center()) for n in all_neurons[0]])
            self.play(FadeIn(sigs, scale=0.5), run_time=0.2)
            for li in range(len(layers) - 1):
                targets = [n.get_center() for n in all_neurons[li + 1]]
                new_sigs = VGroup(*[Dot(radius=0.1, color=ORANGE).move_to(t) for t in targets])
                self.play(FadeOut(sigs), FadeIn(new_sigs), run_time=0.35)
                sigs = new_sigs
            self.play(*[Flash(n.get_center(), color=ORANGE, num_lines=4, flash_radius=0.3)
                        for n in all_neurons[-1]], FadeOut(sigs), run_time=0.4)

        sensei_react(self, sensei, "\U0001F525", ORANGE, dur=0.5)
        self.wait(0.3)

        # ══════════════════════════════════════════
        # SCENE 5: Training — error goes down
        # ══════════════════════════════════════════
        self.play(FadeOut(title4, all_dots, connections, bracket, deep_label), run_time=0.5)

        # Move character to center-bottom
        self.play(sensei.animate.move_to(DOWN * 2.5), run_time=0.4)

        title5 = Text("Training Loop", font_size=52, color=GREEN, weight=BOLD).move_to(UP * 4.5)
        self.play(Write(title5), run_time=0.8)

        sensei_speak(self, sensei, "It learns by making mistakes!", dur=1.5)

        # Loss curve — BIG
        axes = Axes(x_range=[0, 8, 1], y_range=[0, 5, 1], x_length=7, y_length=4,
                    axis_config={"color": DIM, "stroke_width": 1.5}).move_to(UP * 1)
        x_lab = Text("Training Time", font_size=22, color=DIM).next_to(axes.x_axis, DOWN, buff=0.2)
        y_lab = Text("Error", font_size=22, color=DIM).next_to(axes.y_axis, LEFT, buff=0.2)

        loss = axes.plot(lambda x: 4 * np.exp(-0.6 * x) + 0.2, x_range=[0, 8],
                         color=PINK, stroke_width=4)
        tracer = Dot(radius=0.14, color=ORANGE).move_to(axes.c2p(0, 4.2))

        # Labels at start and end
        bad = Text("High Error", font_size=24, color=PINK, weight=BOLD).move_to(axes.c2p(1, 4.5))
        good = Text("Low Error!", font_size=24, color=GREEN, weight=BOLD).move_to(axes.c2p(6.5, 1))

        self.play(Create(axes), Write(x_lab), Write(y_lab), run_time=1.2)
        self.play(FadeIn(bad), run_time=0.5)
        self.play(
            Create(loss), MoveAlongPath(tracer, loss),
            run_time=3.5, rate_func=smooth
        )
        self.play(FadeIn(good, scale=1.3), Flash(tracer, color=GREEN, num_lines=8), run_time=0.8)

        sensei_react(self, sensei, "\u2714\u2714", GREEN, dur=0.5)
        self.wait(0.3)

        # ══════════════════════════════════════════
        # SCENE 6: What it can do
        # ══════════════════════════════════════════
        self.play(FadeOut(title5, axes, x_lab, y_lab, loss, tracer, bad, good), run_time=0.5)

        # Move character to bottom-left
        self.play(sensei.animate.move_to(LEFT * 2.8 + DOWN * 2.5), run_time=0.4)

        title6 = Text("Superpowers", font_size=52, color=ORANGE, weight=BOLD).move_to(UP * 4.5)
        self.play(Write(title6), run_time=0.8)

        apps = [
            ("\U0001F441", "See — Image Recognition", BLUE),
            ("\U0001F4AC", "Read — Understand Language", GREEN),
            ("\U0001F697", "Drive — Self-Driving Cars", ORANGE),
            ("\U0001F3A8", "Create — Generate Art", PURPLE),
            ("\U0001F3E5", "Diagnose — Detect Disease", PINK),
        ]

        cards = VGroup()
        for emoji, text, col in apps:
            card = RoundedRectangle(width=7.5, height=1.0, corner_radius=0.15,
                                     color=col, fill_opacity=0.08, stroke_width=2)
            icon = Text(emoji, font_size=32).move_to(card.get_left() + RIGHT * 0.6)
            txt = Text(text, font_size=24, color=W, weight=BOLD).move_to(card.get_center() + RIGHT * 0.3)
            cards.add(VGroup(card, icon, txt))

        cards.arrange(DOWN, buff=0.2).move_to(UP * 1.5)

        for i, card in enumerate(cards):
            self.play(FadeIn(card, shift=RIGHT * 0.5), run_time=0.5)
            if i == 0:
                sensei_react(self, sensei, "!!", BLUE, dur=0.4)
            elif i == 2:
                sensei_react(self, sensei, "\U0001F525", ORANGE, dur=0.4)

        self.wait(0.5)

        # ══════════════════════════════════════════
        # SCENE 7: Closing — character center stage
        # ══════════════════════════════════════════
        self.play(FadeOut(title6, cards), run_time=0.5)

        # Character moves to center
        self.play(sensei.animate.move_to(DOWN * 1).scale(1.3), run_time=0.8)

        closing1 = Text("Deep Learning", font_size=60, color=PURPLE, weight=BOLD).move_to(UP * 4)
        closing2 = Text("is Rewriting", font_size=48, color=W, weight=BOLD).move_to(UP * 2.8)
        closing3 = Text("the Future", font_size=48, color=CYAN, weight=BOLD).move_to(UP * 1.8)

        glow = Circle(radius=3.5, color=PURPLE, fill_opacity=0.03, stroke_width=1).move_to(UP * 1)

        self.play(GrowFromCenter(glow), run_time=0.6)
        self.play(Write(closing1), run_time=1.2)
        self.play(Write(closing2), run_time=0.8)
        self.play(Write(closing3), run_time=0.8)

        sensei_speak(self, sensei, "Learn more on ScrollUForward!", dur=2)
        sensei_wave(self, sensei, dur=0.8)

        self.play(glow.animate.scale(1.1), rate_func=there_and_back, run_time=1.5)
        self.wait(0.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
