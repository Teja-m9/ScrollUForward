from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0a0a12"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # ── Safe zone: y from -3 to 5.5 (avoids app header + bottom UI) ──
        # Title zone: y 4.5 to 5.5
        # Content zone: y -3 to 4
        # NEVER place content below y = -3

        BLUE = "#00b4d8"
        PURPLE = "#7f5af0"
        GREEN = "#2cb67d"
        ORANGE = "#ff8906"
        PINK = "#e53170"
        CYAN = "#00d4ff"
        TEXT_COL = "#fffffe"
        DIM = "#72757e"

        # ── Glowing pointer that guides the viewer ──
        pointer = Dot(radius=0.12, color=ORANGE, fill_opacity=0.9)
        pointer_glow = Dot(radius=0.25, color=ORANGE, fill_opacity=0.2)
        guide = VGroup(pointer_glow, pointer).move_to(LEFT * 10)  # off screen

        def draw_line(start, end, color=BLUE, width=2.5, dur=1.0):
            """Pointer draws a line from start to end."""
            line = Line(start, end, color=color, stroke_width=width)
            self.play(
                guide.animate.move_to(start), run_time=0.3
            )
            self.play(
                Create(line),
                guide.animate.move_to(end),
                run_time=dur, rate_func=smooth
            )
            return line

        def point_to(pos, dur=0.4):
            self.play(guide.animate.move_to(pos), run_time=dur)

        def pulse(mobject, color=ORANGE, dur=0.6):
            self.play(
                mobject.animate.set_stroke(color=color, width=4),
                Flash(mobject.get_center(), color=color, num_lines=6, flash_radius=0.5),
                run_time=dur
            )

        self.add(guide)

        # ══════════════════════════════════════════════
        # SCENE 1: HOOK — "Your brain has 86 billion neurons"
        # ══════════════════════════════════════════════
        hook1 = Text("Your brain has", font_size=40, color=TEXT_COL, weight=BOLD)
        hook2 = Text("86 billion", font_size=60, color=ORANGE, weight=BOLD)
        hook3 = Text("neurons", font_size=40, color=TEXT_COL, weight=BOLD)
        hook = VGroup(hook1, hook2, hook3).arrange(DOWN, buff=0.35).move_to(UP * 3.5)

        # Brain outline - simple connected dots
        brain_dots = VGroup()
        brain_lines = VGroup()
        positions = [
            np.array([-1.5, 0.5, 0]), np.array([-0.8, 1.2, 0]), np.array([0, 0.8, 0]),
            np.array([0.8, 1.2, 0]), np.array([1.5, 0.5, 0]), np.array([1.0, -0.3, 0]),
            np.array([0, -0.5, 0]), np.array([-1.0, -0.3, 0]),
            np.array([-0.3, 0.3, 0]), np.array([0.5, 0.0, 0]),
        ]
        for p in positions:
            d = Dot(radius=0.08, color=PURPLE, fill_opacity=0.7).move_to(p + DOWN * 0.5)
            brain_dots.add(d)
        # Connect nearby dots
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dist = np.linalg.norm(np.array(positions[i]) - np.array(positions[j]))
                if dist < 1.5:
                    l = Line(positions[i] + DOWN * 0.5, positions[j] + DOWN * 0.5,
                             color=PURPLE, stroke_width=1, stroke_opacity=0.4)
                    brain_lines.add(l)

        self.play(Write(hook1), run_time=0.8)
        self.play(Write(hook2), run_time=1)
        self.play(Write(hook3), run_time=0.8)
        self.play(
            LaggedStart(*[Create(l) for l in brain_lines], lag_ratio=0.03),
            run_time=1
        )
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in brain_dots], lag_ratio=0.05),
            run_time=1.5
        )

        # Pointer traces through the brain network
        point_to(brain_dots[0].get_center())
        for i in [2, 4, 9, 7]:
            point_to(brain_dots[i].get_center(), dur=0.3)

        # Electrical pulse through network
        signal = Dot(radius=0.1, color=ORANGE).move_to(brain_dots[0].get_center())
        self.play(FadeIn(signal, scale=0.5), run_time=0.2)
        for i in [8, 2, 9, 4]:
            self.play(signal.animate.move_to(brain_dots[i].get_center()), run_time=0.25)
        self.play(FadeOut(signal), Flash(brain_dots[4].get_center(), color=ORANGE, num_lines=6), run_time=0.5)

        q = Text("What if machines could do this?", font_size=28, color=CYAN).move_to(DOWN * 2)
        self.play(FadeIn(q, shift=UP * 0.3), run_time=1)
        self.wait(1)

        # ══════════════════════════════════════════════
        # SCENE 2: BIOLOGICAL → ARTIFICIAL NEURON
        # ══════════════════════════════════════════════
        self.play(FadeOut(hook, brain_dots, brain_lines, q, guide), run_time=0.6)
        guide.move_to(LEFT * 10)
        self.add(guide)

        title2 = Text("From Biology to Code", font_size=40, color=TEXT_COL, weight=BOLD).move_to(UP * 5)

        # Biological neuron (left side)
        bio_label = Text("Biological", font_size=22, color=GREEN, weight=BOLD).move_to(LEFT * 2.2 + UP * 3.2)
        bio_body = Circle(radius=0.5, color=GREEN, fill_opacity=0.15, stroke_width=2).move_to(LEFT * 2.2 + UP * 1.5)
        bio_nucleus = Text("Cell", font_size=16, color=GREEN).move_to(bio_body)

        # Dendrites (inputs)
        dendrites = VGroup()
        for angle in [PI * 0.7, PI * 0.9, PI * 1.1]:
            start = bio_body.get_center() + 0.5 * np.array([np.cos(angle), np.sin(angle), 0])
            end = bio_body.get_center() + 1.2 * np.array([np.cos(angle), np.sin(angle), 0])
            dendrites.add(Line(end, start, color=GREEN, stroke_width=2, stroke_opacity=0.7))

        # Axon (output)
        axon_start = bio_body.get_right()
        axon_end = axon_start + RIGHT * 1.2
        axon = Line(axon_start, axon_end, color=GREEN, stroke_width=2.5)
        axon_label = Text("Axon", font_size=14, color=DIM).next_to(axon, DOWN, buff=0.1)

        # Arrow in the middle
        transform_arrow = Arrow(LEFT * 0.3 + UP * 1.5, RIGHT * 0.3 + UP * 1.5,
                                 color=ORANGE, stroke_width=3)
        transform_text = Text("Inspire", font_size=18, color=ORANGE).next_to(transform_arrow, UP, buff=0.15)

        # Artificial neuron (right side)
        art_label = Text("Artificial", font_size=22, color=BLUE, weight=BOLD).move_to(RIGHT * 2.2 + UP * 3.2)
        art_body = Circle(radius=0.5, color=BLUE, fill_opacity=0.15, stroke_width=2).move_to(RIGHT * 2.2 + UP * 1.5)
        sigma = Text("\u03A3", font_size=28, color=BLUE, weight=BOLD).move_to(art_body)

        # Input arrows
        inputs = VGroup()
        input_labels = VGroup()
        for i, y_off in enumerate([0.4, 0, -0.4]):
            start = RIGHT * 0.8 + UP * (1.5 + y_off)
            end = art_body.get_left() + UP * y_off * 0.5
            arr = Arrow(start, end, color=CYAN, stroke_width=1.5, max_tip_length_to_length_ratio=0.2)
            inputs.add(arr)
            w = Text(f"w{i+1}", font_size=14, color=CYAN).next_to(arr, UP, buff=0.05)
            input_labels.add(w)

        # Output
        art_out = Arrow(art_body.get_right(), art_body.get_right() + RIGHT * 0.8,
                        color=BLUE, stroke_width=2.5)
        out_label = Text("Output", font_size=14, color=DIM).next_to(art_out, DOWN, buff=0.1)

        self.play(Write(title2), run_time=1)

        # Build biological side with pointer
        point_to(bio_label.get_center())
        self.play(Write(bio_label), run_time=0.5)
        self.play(GrowFromCenter(bio_body), FadeIn(bio_nucleus), run_time=1)
        self.play(LaggedStart(*[Create(d) for d in dendrites], lag_ratio=0.2), run_time=0.8)
        self.play(Create(axon), Write(axon_label), run_time=0.8)

        # Transform arrow
        self.play(GrowArrow(transform_arrow), Write(transform_text), run_time=0.8)

        # Build artificial side
        point_to(art_label.get_center())
        self.play(Write(art_label), run_time=0.5)
        self.play(GrowFromCenter(art_body), FadeIn(sigma), run_time=1)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in inputs], lag_ratio=0.15),
            LaggedStart(*[FadeIn(l) for l in input_labels], lag_ratio=0.15),
            run_time=1
        )
        self.play(GrowArrow(art_out), Write(out_label), run_time=0.8)

        # Formula below
        formula = Text("output = activation( w\u2081x\u2081 + w\u2082x\u2082 + b )",
                        font_size=20, color=TEXT_COL).move_to(DOWN * 0.8)
        point_to(formula.get_center())
        self.play(Write(formula), run_time=1.5)

        # Highlight weights with pointer
        for inp in inputs:
            pulse(inp, color=CYAN, dur=0.3)
        self.wait(1)

        # ══════════════════════════════════════════════
        # SCENE 3: NEURAL NETWORK — Pointer BUILDS it
        # ══════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        guide.move_to(LEFT * 10)
        self.add(guide)

        title3 = Text("Deep Neural Network", font_size=40, color=TEXT_COL, weight=BOLD).move_to(UP * 5)

        layers_config = [3, 5, 6, 5, 3]
        layer_names = ["Input", "Hidden 1", "Hidden 2", "Hidden 3", "Output"]
        layer_colors = [GREEN, PURPLE, PURPLE, PURPLE, ORANGE]
        x_positions = [-3, -1.5, 0, 1.5, 3]

        all_neurons = []
        all_dots = VGroup()

        for li, (count, xp, col) in enumerate(zip(layers_config, x_positions, layer_colors)):
            layer = []
            for ni in range(count):
                y = (ni - (count - 1) / 2) * 0.8
                dot = Circle(radius=0.2, color=col, fill_opacity=0.15, stroke_width=2)
                dot.move_to(np.array([xp, y + 1.0, 0]))
                layer.append(dot)
                all_dots.add(dot)
            all_neurons.append(layer)

        # Connections
        connections = VGroup()
        for li in range(len(layers_config) - 1):
            for n1 in all_neurons[li]:
                for n2 in all_neurons[li + 1]:
                    line = Line(n1.get_center(), n2.get_center(),
                                color=DIM, stroke_width=0.6, stroke_opacity=0.3)
                    connections.add(line)

        # Layer labels
        labels = VGroup()
        for i, (name, xp, col) in enumerate(zip(layer_names, x_positions, layer_colors)):
            l = Text(name, font_size=14, color=col).move_to(np.array([xp, -2.2, 0]))
            labels.add(l)

        self.play(Write(title3), run_time=1)

        # Pointer draws connections first (faint)
        point_to(np.array([-3, 2, 0]))
        self.play(
            LaggedStart(*[Create(c) for c in connections], lag_ratio=0.005),
            guide.animate.move_to(np.array([3, 2, 0])),
            run_time=2
        )

        # Then neurons appear layer by layer with pointer
        for li, layer in enumerate(all_neurons):
            point_to(np.array([x_positions[li], 2, 0]), dur=0.3)
            self.play(
                LaggedStart(*[GrowFromCenter(n) for n in layer], lag_ratio=0.08),
                run_time=0.8
            )

        self.play(FadeIn(labels), run_time=0.8)

        # "Deep" label pointing to hidden layers
        deep_bracket = Brace(
            VGroup(*[all_neurons[i][0] for i in [1, 2, 3]]),
            direction=DOWN, color=CYAN
        ).shift(DOWN * 1.2)
        deep_text = Text("This is why it's called DEEP", font_size=18, color=CYAN, weight=BOLD)
        deep_text.next_to(deep_bracket, DOWN, buff=0.2)

        point_to(deep_bracket.get_center())
        self.play(Create(deep_bracket), Write(deep_text), run_time=1.2)

        # Signal flow animation
        for round_num in range(2):
            signal_dots = VGroup(*[
                Dot(radius=0.08, color=ORANGE, fill_opacity=0.9).move_to(n.get_center())
                for n in all_neurons[0]
            ])
            self.play(FadeIn(signal_dots, scale=0.5), run_time=0.3)
            for li in range(len(layers_config) - 1):
                targets = [n.get_center() for n in all_neurons[li + 1]]
                new_dots = VGroup(*[Dot(radius=0.08, color=ORANGE).move_to(t) for t in targets])
                self.play(
                    FadeOut(signal_dots),
                    FadeIn(new_dots, scale=0.5),
                    run_time=0.4
                )
                signal_dots = new_dots
            # Flash output
            self.play(
                *[Flash(n.get_center(), color=ORANGE, num_lines=4, flash_radius=0.3)
                  for n in all_neurons[-1]],
                FadeOut(signal_dots),
                run_time=0.5
            )
        self.wait(0.5)

        # ══════════════════════════════════════════════
        # SCENE 4: TRAINING — Loss goes down
        # ══════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        guide.move_to(LEFT * 10)
        self.add(guide)

        title4 = Text("How It Learns", font_size=40, color=TEXT_COL, weight=BOLD).move_to(UP * 5)

        # Training loop diagram
        step_data = [
            ("1. Forward Pass", "Data flows through network", GREEN),
            ("2. Calculate Error", "Compare output vs truth", PINK),
            ("3. Backpropagate", "Send error signal back", ORANGE),
            ("4. Update Weights", "Adjust to reduce error", BLUE),
        ]

        steps = VGroup()
        for i, (title, desc, col) in enumerate(step_data):
            box = RoundedRectangle(width=6, height=1, corner_radius=0.15,
                                    color=col, fill_opacity=0.08, stroke_width=2)
            t = Text(title, font_size=20, color=col, weight=BOLD).move_to(box.get_left() + RIGHT * 1.8)
            d = Text(desc, font_size=15, color=DIM).move_to(box.get_right() + LEFT * 1.5)
            steps.add(VGroup(box, t, d))

        steps.arrange(DOWN, buff=0.3).move_to(UP * 2)

        # Curved arrow showing loop
        loop_arrow = CurvedArrow(
            steps[-1].get_right() + RIGHT * 0.3,
            steps[0].get_right() + RIGHT * 0.3,
            color=CYAN, angle=-PI / 2
        )
        loop_label = Text("Repeat\n1000s of\ntimes", font_size=14, color=CYAN).next_to(loop_arrow, RIGHT, buff=0.15)

        self.play(Write(title4), run_time=1)

        # Pointer guides each step
        for step in steps:
            point_to(step.get_left())
            self.play(FadeIn(step, shift=RIGHT * 0.5), run_time=0.8)

        point_to(loop_arrow.get_center())
        self.play(Create(loop_arrow), Write(loop_label), run_time=1)

        # Loss curve below
        axes = Axes(x_range=[0, 8, 1], y_range=[0, 4, 1], x_length=5.5, y_length=2.5,
                    axis_config={"color": DIM, "stroke_width": 1.5}).move_to(DOWN * 1.5)
        x_lab = Text("Epochs", font_size=16, color=DIM).next_to(axes.x_axis, DOWN, buff=0.2)
        y_lab = Text("Error", font_size=16, color=DIM).next_to(axes.y_axis, LEFT, buff=0.2)

        loss_curve = axes.plot(lambda x: 3.5 * np.exp(-0.5 * x) + 0.2,
                               x_range=[0, 8], color=PINK, stroke_width=3)

        tracer = Dot(radius=0.1, color=ORANGE).move_to(axes.c2p(0, 3.7))

        point_to(axes.get_center())
        self.play(Create(axes), Write(x_lab), Write(y_lab), run_time=1)
        self.play(
            Create(loss_curve),
            MoveAlongPath(tracer, loss_curve),
            run_time=3, rate_func=smooth
        )

        done = Text("Error \u2192 0", font_size=20, color=GREEN, weight=BOLD).next_to(tracer, RIGHT, buff=0.2)
        self.play(Write(done), Flash(tracer, color=GREEN, num_lines=6), run_time=0.8)
        self.wait(0.5)

        # ══════════════════════════════════════════════
        # SCENE 5: WHAT DEEP LEARNING CAN DO
        # ══════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        guide.move_to(LEFT * 10)
        self.add(guide)

        title5 = Text("What It Can Do", font_size=40, color=TEXT_COL, weight=BOLD).move_to(UP * 5)

        apps = [
            ("See", "Image Recognition", "\U0001F441", BLUE),
            ("Read", "Language Understanding", "\U0001F4AC", GREEN),
            ("Drive", "Self-Driving Cars", "\U0001F697", ORANGE),
            ("Create", "Generate Art & Music", "\U0001F3A8", PURPLE),
            ("Diagnose", "Medical Imaging", "\U0001F3E5", PINK),
        ]

        cards = VGroup()
        for verb, desc, emoji, col in apps:
            card = RoundedRectangle(width=7, height=1.1, corner_radius=0.15,
                                     color=col, fill_opacity=0.06, stroke_width=1.5)
            icon = Text(emoji, font_size=28).move_to(card.get_left() + RIGHT * 0.7)
            v = Text(verb, font_size=24, color=col, weight=BOLD).move_to(card.get_left() + RIGHT * 1.8)
            d = Text(desc, font_size=16, color=DIM).move_to(card.get_left() + RIGHT * 3.8)
            cards.add(VGroup(card, icon, v, d))

        cards.arrange(DOWN, buff=0.25).move_to(UP * 1)

        self.play(Write(title5), run_time=1)

        for i, card in enumerate(cards):
            point_to(card.get_left(), dur=0.2)
            self.play(FadeIn(card, shift=RIGHT * 0.5), run_time=0.6)
            self.play(Indicate(card[2], color=apps[i][3], scale_factor=1.1), run_time=0.3)

        self.wait(1)

        # ══════════════════════════════════════════════
        # SCENE 6: CLOSING
        # ══════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.6)

        # Final network as art
        final_dots = VGroup()
        final_lines = VGroup()
        for i in range(30):
            pos = np.array([np.random.uniform(-3, 3), np.random.uniform(-1, 3.5), 0])
            d = Dot(radius=0.06, color=PURPLE, fill_opacity=0.5)
            d.move_to(pos)
            final_dots.add(d)

        for i in range(len(final_dots)):
            for j in range(i + 1, len(final_dots)):
                if np.linalg.norm(final_dots[i].get_center() - final_dots[j].get_center()) < 1.8:
                    l = Line(final_dots[i].get_center(), final_dots[j].get_center(),
                             color=PURPLE, stroke_width=0.5, stroke_opacity=0.2)
                    final_lines.add(l)

        closing1 = Text("Deep Learning", font_size=56, color=PURPLE, weight=BOLD).move_to(UP * 1.5)
        closing2 = Text("is Rewriting the Future", font_size=32, color=TEXT_COL, weight=BOLD).move_to(UP * 0)
        glow = Circle(radius=3, color=PURPLE, fill_opacity=0.03, stroke_width=1).move_to(UP * 0.75)

        self.play(
            LaggedStart(*[Create(l) for l in final_lines], lag_ratio=0.01),
            run_time=1
        )
        self.play(
            LaggedStart(*[FadeIn(d, scale=0.3) for d in final_dots], lag_ratio=0.02),
            run_time=1
        )
        self.play(GrowFromCenter(glow), run_time=0.8)
        self.play(Write(closing1), run_time=1.5)
        self.play(Write(closing2), run_time=1)

        cta = Text("Learn more on ScrollUForward", font_size=22, color=CYAN).move_to(DOWN * 2)
        self.play(FadeIn(cta, shift=UP * 0.3), run_time=1)

        self.play(glow.animate.scale(1.1), rate_func=there_and_back, run_time=2)
        self.wait(1)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
