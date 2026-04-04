from manim import *
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sage_sensei import SageSensei

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0d0d1a"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # SAFE ZONE: y -3 to 5.5

        BLUE = "#00b4d8"
        PURPLE = "#7f5af0"
        GREEN = "#2cb67d"
        ORANGE = "#ff8906"
        PINK = "#e53170"
        CYAN = "#00d4ff"
        W = "#fffffe"
        DIM = "#72757e"

        # ── Build Sage Sensei ──
        sensei = SageSensei().scale(0.7)
        orb = sensei.submobjects[1]  # the glowing orb on staff

        def sensei_float(dur=0.8):
            self.play(sensei.animate.shift(UP * 0.2), run_time=dur / 2, rate_func=there_and_back)

        def orb_pulse(dur=0.5):
            self.play(orb.animate.set_fill(YELLOW, opacity=1), run_time=dur / 2)
            self.play(orb.animate.set_fill(TEAL, opacity=1), run_time=dur / 2)

        def sensei_bob(dur=0.6):
            self.play(sensei.animate.shift(UP * 0.15), run_time=dur / 3, rate_func=rush_from)
            self.play(sensei.animate.shift(DOWN * 0.15), run_time=dur / 3, rate_func=rush_into)

        def speak(text, dur=2.0):
            bg = RoundedRectangle(width=5.5, height=0.85, corner_radius=0.2,
                color=WHITE, fill_opacity=0.95, stroke_color=PURPLE_B, stroke_width=2)
            txt = Text(text, font_size=24, color=BLACK, weight=BOLD)
            if txt.width > 5.0: txt.scale_to_fit_width(5.0)
            txt.move_to(bg)
            tail = Triangle(color=WHITE, fill_opacity=0.95, stroke_color=PURPLE_B,
                            stroke_width=2).scale(0.08).rotate(PI)
            tail.next_to(bg, DOWN, buff=-0.02)
            bubble = VGroup(bg, txt, tail).next_to(sensei, UP, buff=0.15)
            self.play(FadeIn(bubble, scale=0.6), run_time=0.35)
            self.wait(dur - 0.7)
            self.play(FadeOut(bubble), run_time=0.35)

        def react(symbol, color=GOLD, dur=0.6):
            r = Text(symbol, font_size=44, color=color, weight=BOLD)
            r.next_to(sensei, UP, buff=0.1)
            self.play(FadeIn(r, scale=2), run_time=dur / 2)
            self.play(FadeOut(r, shift=UP * 0.3), run_time=dur / 2)

        # ══════════════════════════════════════════
        # SCENE 1: Sensei enters + Hook
        # ══════════════════════════════════════════
        sensei.move_to(LEFT * 2 + DOWN * 1.5)
        self.play(GrowFromCenter(sensei), run_time=1)
        orb_pulse(dur=0.6)
        sensei_float(dur=0.8)

        speak("Welcome, young student!", dur=1.8)

        h1 = Text("Your Brain:", font_size=52, color=W, weight=BOLD).move_to(RIGHT * 1 + UP * 4)
        h2 = Text("86 Billion", font_size=68, color=ORANGE, weight=BOLD).move_to(RIGHT * 1 + UP * 2.5)
        h3 = Text("Neurons", font_size=52, color=W, weight=BOLD).move_to(RIGHT * 1 + UP * 1.3)

        self.play(Write(h1), run_time=0.8)
        self.play(Write(h2), run_time=1)
        react("!!", ORANGE)
        self.play(Write(h3), run_time=0.8)

        speak("Can machines learn like you?", dur=2.2)
        self.wait(1.5)

        # ══════════════════════════════════════════
        # SCENE 2: Biological Neuron
        # ══════════════════════════════════════════
        self.play(FadeOut(h1, h2, h3), run_time=0.4)
        self.play(sensei.animate.move_to(LEFT * 3 + DOWN * 1), run_time=0.5)

        title = Text("The Neuron", font_size=56, color=CYAN, weight=BOLD).move_to(UP * 5)
        self.play(Write(title), run_time=0.8)

        # BIG neuron
        cell = Circle(radius=1.2, color=GREEN, fill_opacity=0.1, stroke_width=3).move_to(RIGHT * 0.5 + UP * 1.5)
        cell_txt = Text("Cell Body", font_size=30, color=GREEN, weight=BOLD).move_to(cell)

        # Dendrites
        dendrites = VGroup()
        for angle in [PI * 0.65, PI * 0.8, PI * 0.95, PI * 1.1, PI * 1.25]:
            s = cell.get_center() + 1.2 * np.array([np.cos(angle), np.sin(angle), 0])
            e = cell.get_center() + 2.2 * np.array([np.cos(angle), np.sin(angle), 0])
            dendrites.add(Line(e, s, color=BLUE, stroke_width=3))
            dendrites.add(Dot(radius=0.08, color=BLUE).move_to(e))
        inp_label = Text("Inputs", font_size=26, color=BLUE, weight=BOLD).move_to(LEFT * 2.5 + UP * 3.2)

        # Axon
        axon = Arrow(cell.get_right(), cell.get_right() + RIGHT * 2.2, color=ORANGE,
                     stroke_width=5, max_tip_length_to_length_ratio=0.12)
        out_label = Text("Output", font_size=26, color=ORANGE, weight=BOLD).next_to(axon, DOWN, buff=0.15)

        speak("Observe the neuron!", dur=1.8)
        orb_pulse()

        self.play(GrowFromCenter(cell), Write(cell_txt), run_time=1.5)
        self.wait(0.5)
        self.play(LaggedStart(*[Create(d) for d in dendrites], lag_ratio=0.06), Write(inp_label), run_time=1.5)

        # Signals flow in — orb glows each time
        for i in range(0, len(dendrites), 2):
            sig = Dot(radius=0.12, color=CYAN).move_to(dendrites[i + 1].get_center())
            self.play(sig.animate.move_to(cell.get_center()), run_time=0.25)
            self.remove(sig)
        orb_pulse(dur=0.4)

        self.play(Flash(cell, color=GREEN, num_lines=8, flash_radius=1.5), run_time=0.5)
        self.play(GrowArrow(axon), Write(out_label), run_time=0.8)

        sig_out = Dot(radius=0.14, color=ORANGE).move_to(cell.get_right())
        self.play(sig_out.animate.move_to(axon.get_end()), run_time=0.5)
        self.play(Flash(axon.get_end(), color=ORANGE, num_lines=6), FadeOut(sig_out), run_time=0.5)
        react("\u26A1", ORANGE)
        self.wait(1.5)

        # ══════════════════════════════════════════
        # SCENE 3: Artificial Neuron
        # ══════════════════════════════════════════
        self.play(FadeOut(title, cell, cell_txt, dendrites, inp_label, axon, out_label), run_time=0.4)
        self.play(sensei.animate.move_to(RIGHT * 3 + DOWN * 1), run_time=0.5)

        title3 = Text("Artificial Neuron", font_size=56, color=PURPLE, weight=BOLD).move_to(UP * 5)
        self.play(Write(title3), run_time=0.8)

        neuron = Circle(radius=1.0, color=PURPLE, fill_opacity=0.1, stroke_width=3).move_to(LEFT * 0.5 + UP * 1.5)
        sigma = Text("\u03A3 \u2192 f", font_size=40, color=PURPLE, weight=BOLD).move_to(neuron)

        inp_data = [("x\u2081", 0.9), ("x\u2082", 0), ("x\u2083", -0.9)]
        arrows = VGroup()
        labels = VGroup()
        for txt, y in inp_data:
            s = LEFT * 3.5 + UP * (1.5 + y)
            e = neuron.get_left() + UP * y * 0.5
            a = Arrow(s, e, color=CYAN, stroke_width=3, max_tip_length_to_length_ratio=0.12)
            l = Text(txt, font_size=28, color=W).next_to(s, LEFT, buff=0.1)
            arrows.add(a)
            labels.add(l)

        out = Arrow(neuron.get_right(), neuron.get_right() + RIGHT * 2, color=ORANGE,
                    stroke_width=5, max_tip_length_to_length_ratio=0.12)
        y_label = Text("y", font_size=34, color=ORANGE, weight=BOLD).next_to(out, RIGHT, buff=0.1)

        speak("Now in code!", dur=1.8)

        self.play(GrowFromCenter(neuron), Write(sigma), run_time=1)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.15),
            LaggedStart(*[FadeIn(l) for l in labels], lag_ratio=0.15),
            run_time=1.2
        )

        for a in arrows:
            d = Dot(radius=0.1, color=CYAN).move_to(a.get_start())
            self.play(d.animate.move_to(neuron.get_center()), run_time=0.2)
            self.remove(d)
        orb_pulse(dur=0.3)

        self.play(Flash(neuron, color=PURPLE, num_lines=8), run_time=0.4)
        self.play(GrowArrow(out), Write(y_label), run_time=0.8)

        formula = Text("y = f( w\u2081x\u2081 + w\u2082x\u2082 + w\u2083x\u2083 + b )",
                        font_size=28, color=W).move_to(DOWN * 0.8)
        self.play(Write(formula), run_time=1.5)
        self.wait(1)
        sensei_bob()
        self.wait(1.5)

        # ══════════════════════════════════════════
        # SCENE 4: Deep Network
        # ══════════════════════════════════════════
        self.play(FadeOut(title3, neuron, sigma, arrows, labels, out, y_label, formula), run_time=0.4)
        self.play(sensei.animate.move_to(DOWN * 2.2).scale(0.85), run_time=0.5)

        title4 = Text("Deep Network", font_size=56, color=W, weight=BOLD).move_to(UP * 5)
        self.play(Write(title4), run_time=0.8)

        speak("Stack them into layers!", dur=2)

        layers = [3, 5, 5, 3]
        cols = [GREEN, PURPLE, PURPLE, ORANGE]
        xp = [-2.8, -0.9, 0.9, 2.8]

        all_n = []
        all_d = VGroup()
        for li, (cnt, x, c) in enumerate(zip(layers, xp, cols)):
            layer = []
            for ni in range(cnt):
                y = (ni - (cnt - 1) / 2) * 1.0
                dot = Circle(radius=0.28, color=c, fill_opacity=0.2, stroke_width=2.5)
                dot.move_to(np.array([x, y + 2, 0]))
                layer.append(dot)
                all_d.add(dot)
            all_n.append(layer)

        conns = VGroup()
        for li in range(len(layers) - 1):
            for n1 in all_n[li]:
                for n2 in all_n[li + 1]:
                    conns.add(Line(n1.get_center(), n2.get_center(),
                                   color=DIM, stroke_width=0.7, stroke_opacity=0.25))

        self.play(LaggedStart(*[Create(c) for c in conns], lag_ratio=0.003), run_time=1.5)
        for layer in all_n:
            self.play(LaggedStart(*[GrowFromCenter(n) for n in layer], lag_ratio=0.08), run_time=0.5)

        # "DEEP" brace
        br = Brace(VGroup(all_d[3], all_d[12]), DOWN, color=CYAN).shift(DOWN * 0.3)
        br_txt = Text("DEEP = hidden layers", font_size=26, color=CYAN, weight=BOLD).next_to(br, DOWN, buff=0.1)
        self.play(Create(br), Write(br_txt), run_time=0.8)
        orb_pulse()

        # Signal flow x2
        for _ in range(2):
            sigs = VGroup(*[Dot(radius=0.1, color=ORANGE).move_to(n.get_center()) for n in all_n[0]])
            self.play(FadeIn(sigs, scale=0.5), run_time=0.2)
            for li in range(len(layers) - 1):
                ns = VGroup(*[Dot(radius=0.1, color=ORANGE).move_to(n.get_center()) for n in all_n[li + 1]])
                self.play(FadeOut(sigs), FadeIn(ns), run_time=0.3)
                sigs = ns
            self.play(*[Flash(n.get_center(), color=ORANGE, num_lines=4, flash_radius=0.3)
                        for n in all_n[-1]], FadeOut(sigs), run_time=0.4)

        react("\U0001F525", ORANGE)
        self.wait(2)

        # ══════════════════════════════════════════
        # SCENE 5: Training — loss goes down
        # ══════════════════════════════════════════
        self.play(FadeOut(title4, all_d, conns, br, br_txt), run_time=0.4)
        self.play(sensei.animate.move_to(LEFT * 3 + DOWN * 1.5), run_time=0.4)

        title5 = Text("Training", font_size=56, color=GREEN, weight=BOLD).move_to(UP * 5)
        self.play(Write(title5), run_time=0.8)

        speak("It learns from mistakes!", dur=2)

        axes = Axes(x_range=[0, 8, 1], y_range=[0, 5, 1], x_length=6, y_length=4.5,
                    axis_config={"color": DIM, "stroke_width": 1.5}).move_to(RIGHT * 0.5 + UP * 1)
        x_lab = Text("Epochs", font_size=24, color=DIM).next_to(axes.x_axis, DOWN, buff=0.2)
        y_lab = Text("Error", font_size=24, color=DIM).next_to(axes.y_axis, LEFT, buff=0.2)

        loss = axes.plot(lambda x: 4 * np.exp(-0.6 * x) + 0.2, x_range=[0, 8],
                         color=PINK, stroke_width=4)
        tracer = Dot(radius=0.14, color=ORANGE).move_to(axes.c2p(0, 4.2))

        bad = Text("High Error", font_size=26, color=PINK, weight=BOLD).move_to(axes.c2p(1.5, 4.8))
        good = Text("Learned!", font_size=26, color=GREEN, weight=BOLD).move_to(axes.c2p(6, 1.2))

        self.play(Create(axes), Write(x_lab), Write(y_lab), run_time=1)
        self.play(FadeIn(bad), run_time=0.4)
        self.play(Create(loss), MoveAlongPath(tracer, loss), run_time=3.5, rate_func=smooth)
        self.play(FadeIn(good, scale=1.3), Flash(tracer, color=GREEN, num_lines=8), run_time=0.8)

        orb_pulse()
        react("\u2714", GREEN)
        self.wait(1.5)

        # ══════════════════════════════════════════
        # SCENE 6: Applications
        # ══════════════════════════════════════════
        self.play(FadeOut(title5, axes, x_lab, y_lab, loss, tracer, bad, good), run_time=0.4)
        self.play(sensei.animate.move_to(RIGHT * 3 + DOWN * 1.5), run_time=0.4)

        title6 = Text("Superpowers", font_size=56, color=ORANGE, weight=BOLD).move_to(UP * 5)
        self.play(Write(title6), run_time=0.8)

        apps = [
            ("\U0001F441", "See — Image Recognition", BLUE),
            ("\U0001F4AC", "Read — Understand Language", GREEN),
            ("\U0001F697", "Drive — Self-Driving Cars", ORANGE),
            ("\U0001F3A8", "Create — Generate Art", PURPLE),
            ("\U0001F3E5", "Diagnose — Detect Disease", PINK),
        ]

        cards = VGroup()
        for emoji, txt, col in apps:
            card = RoundedRectangle(width=6.5, height=1.0, corner_radius=0.15,
                                     color=col, fill_opacity=0.06, stroke_width=2)
            ic = Text(emoji, font_size=30).move_to(card.get_left() + RIGHT * 0.5)
            tx = Text(txt, font_size=24, color=W, weight=BOLD).move_to(card.get_center() + RIGHT * 0.3)
            cards.add(VGroup(card, ic, tx))
        cards.arrange(DOWN, buff=0.2).move_to(LEFT * 0.3 + UP * 1.5)

        for i, card in enumerate(cards):
            self.play(FadeIn(card, shift=RIGHT * 0.5), run_time=0.45)
            if i == 0: orb_pulse(dur=0.3)
            if i == 2: react("!", ORANGE, dur=0.4)

        sensei_bob()
        self.wait(1.5)

        # ══════════════════════════════════════════
        # SCENE 7: Closing — Sensei center stage
        # ══════════════════════════════════════════
        self.play(FadeOut(title6, cards), run_time=0.4)
        self.play(sensei.animate.move_to(DOWN * 0.5).scale(1.15), run_time=0.8)

        c1 = Text("Deep Learning", font_size=64, color=PURPLE, weight=BOLD).move_to(UP * 4.5)
        c2 = Text("is Rewriting", font_size=48, color=W, weight=BOLD).move_to(UP * 3.2)
        c3 = Text("the Future", font_size=48, color=CYAN, weight=BOLD).move_to(UP * 2.2)

        glow = Circle(radius=3.5, color=PURPLE, fill_opacity=0.03, stroke_width=1).move_to(UP * 1)

        self.play(GrowFromCenter(glow), run_time=0.5)
        self.play(Write(c1), run_time=1)
        self.play(Write(c2), run_time=0.8)
        self.play(Write(c3), run_time=0.8)

        speak("Learn on ScrollUForward!", dur=2.5)
        sensei_float(dur=1)
        orb_pulse(dur=0.6)

        self.play(glow.animate.scale(1.1), rate_func=there_and_back, run_time=2)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
