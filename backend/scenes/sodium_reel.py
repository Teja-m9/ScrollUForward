from manim import *
import numpy as np

class ReelScene(Scene):
    def construct(self):
        # ── Camera: vertical 9:16 ──
        self.camera.background_color = "#0f0e17"
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # ── Color palette ──
        NA_COLOR = "#ff8906"      # warm orange for sodium
        CL_COLOR = "#2cb67d"      # green for chlorine
        LI_COLOR = "#e53170"      # pink for lithium
        ACCENT = "#7f5af0"        # purple accent
        TEXT_COL = "#fffffe"
        DIM_TEXT = "#a7a9be"
        BG_DARK = "#0f0e17"
        CARD_BG = "#1a1a2e"

        # ════════════════════════════════════════════
        # SCENE 1: Hook — "What if the world runs out of lithium?"
        # ════════════════════════════════════════════
        title1 = Text("What if the world", font_size=44, color=TEXT_COL, weight=BOLD)
        title2 = Text("runs out of", font_size=44, color=TEXT_COL, weight=BOLD)
        title3 = Text("Lithium?", font_size=56, color=LI_COLOR, weight=BOLD)
        title_group = VGroup(title1, title2, title3).arrange(DOWN, buff=0.4).move_to(UP * 2)

        # Lithium atom
        li_atom = Circle(radius=1.0, color=LI_COLOR, fill_opacity=0.15, stroke_width=3)
        li_label = Text("Li", font_size=52, color=LI_COLOR, weight=BOLD)
        li_num = Text("3", font_size=24, color=DIM_TEXT)
        li_num.next_to(li_label, UP + RIGHT, buff=0.05)
        li_group = VGroup(li_atom, li_label, li_num).move_to(DOWN * 2.5)

        # Electrons orbiting
        e1 = Dot(radius=0.1, color=ACCENT).move_to(li_atom.point_at_angle(0))
        e2 = Dot(radius=0.1, color=ACCENT).move_to(li_atom.point_at_angle(PI * 2 / 3))
        orbit = Circle(radius=1.0, color=ACCENT, stroke_width=1, stroke_opacity=0.3)
        orbit.move_to(li_group.get_center())

        self.play(Write(title1), run_time=1)
        self.play(Write(title2), run_time=0.8)
        self.play(Write(title3), run_time=1)
        self.play(
            GrowFromCenter(li_atom),
            FadeIn(li_label, scale=0.5),
            FadeIn(li_num, scale=0.5),
            Create(orbit),
            FadeIn(e1), FadeIn(e2),
            run_time=2
        )
        # Animate electron orbit
        self.play(
            Rotate(e1, angle=PI, about_point=li_group.get_center()),
            Rotate(e2, angle=PI, about_point=li_group.get_center()),
            run_time=2, rate_func=smooth
        )
        self.wait(1.5)

        # ════════════════════════════════════════════
        # SCENE 2: Sodium Introduction — "Meet Sodium"
        # ════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        na_title = Text("Meet Sodium", font_size=50, color=NA_COLOR, weight=BOLD)
        na_title.move_to(UP * 5.5)

        # Sodium atom — bigger than lithium (atomic number 11)
        na_atom = Circle(radius=1.4, color=NA_COLOR, fill_opacity=0.12, stroke_width=3)
        na_symbol = Text("Na", font_size=64, color=NA_COLOR, weight=BOLD)
        na_number = Text("11", font_size=26, color=DIM_TEXT)
        na_number.next_to(na_symbol, UP + RIGHT, buff=0.05)
        na_group = VGroup(na_atom, na_symbol, na_number).move_to(UP * 1.5)

        # Electron shells (2, 8, 1)
        shell1 = Circle(radius=0.5, color=ACCENT, stroke_width=1, stroke_opacity=0.4)
        shell2 = Circle(radius=1.0, color=ACCENT, stroke_width=1, stroke_opacity=0.3)
        shell3 = Circle(radius=1.4, color=ACCENT, stroke_width=1, stroke_opacity=0.2)
        shells = VGroup(shell1, shell2, shell3).move_to(na_group.get_center())

        # Place electrons on shells
        inner_electrons = VGroup(*[
            Dot(radius=0.06, color=ACCENT).move_to(
                na_group.get_center() + 0.5 * np.array([np.cos(a), np.sin(a), 0])
            ) for a in [0, PI]
        ])
        mid_electrons = VGroup(*[
            Dot(radius=0.06, color=ACCENT).move_to(
                na_group.get_center() + 1.0 * np.array([np.cos(a), np.sin(a), 0])
            ) for a in np.linspace(0, 2 * PI, 8, endpoint=False)
        ])
        outer_electron = Dot(radius=0.1, color=NA_COLOR, fill_opacity=1).move_to(
            na_group.get_center() + 1.4 * np.array([1, 0, 0])
        )
        outer_label = Text("1 valence e\u207b", font_size=22, color=NA_COLOR)
        outer_label.next_to(outer_electron, RIGHT, buff=0.2)

        # Properties card
        props = VGroup(
            Text("6th most abundant element", font_size=24, color=DIM_TEXT),
            Text("Found in table salt (NaCl)", font_size=24, color=DIM_TEXT),
            Text("10,000x cheaper than lithium", font_size=24, color=NA_COLOR),
        ).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to(DOWN * 3)

        self.play(Write(na_title), run_time=1)
        self.play(
            GrowFromCenter(na_atom),
            FadeIn(na_symbol, scale=0.5),
            FadeIn(na_number),
            run_time=1.5
        )
        self.play(
            LaggedStart(
                Create(shell1), Create(shell2), Create(shell3),
                lag_ratio=0.3
            ),
            LaggedStart(
                *[FadeIn(e, scale=0.3) for e in inner_electrons],
                *[FadeIn(e, scale=0.3) for e in mid_electrons],
                lag_ratio=0.05
            ),
            run_time=2
        )
        self.play(
            FadeIn(outer_electron, scale=2),
            Write(outer_label),
            run_time=1.5
        )
        self.play(
            LaggedStart(*[FadeIn(p, shift=LEFT * 0.5) for p in props], lag_ratio=0.3),
            run_time=2
        )
        self.play(Indicate(props[2], color=NA_COLOR, scale_factor=1.1), run_time=1)
        self.wait(1.5)

        # ════════════════════════════════════════════
        # SCENE 3: NaCl — How salt forms
        # ════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        salt_title = Text("How Salt Forms", font_size=46, color=TEXT_COL, weight=BOLD)
        salt_title.move_to(UP * 5.5)

        # Sodium atom (left)
        na_circle = Circle(radius=0.9, color=NA_COLOR, fill_opacity=0.15, stroke_width=3)
        na_text = Text("Na", font_size=40, color=NA_COLOR, weight=BOLD)
        na_side = VGroup(na_circle, na_text).move_to(LEFT * 2.5 + UP * 1.5)

        # Chlorine atom (right)
        cl_circle = Circle(radius=1.1, color=CL_COLOR, fill_opacity=0.15, stroke_width=3)
        cl_text = Text("Cl", font_size=40, color=CL_COLOR, weight=BOLD)
        cl_side = VGroup(cl_circle, cl_text).move_to(RIGHT * 2.5 + UP * 1.5)

        # Electron to transfer
        transfer_e = Dot(radius=0.12, color=NA_COLOR).move_to(na_side.get_right() + RIGHT * 0.1)

        # Arrow showing electron transfer
        transfer_arrow = CurvedArrow(
            na_side.get_right() + UP * 0.5,
            cl_side.get_left() + UP * 0.5,
            color=ACCENT, angle=-TAU / 4
        )
        e_label = Text("e\u207b", font_size=28, color=ACCENT)
        e_label.next_to(transfer_arrow, UP, buff=0.15)

        self.play(Write(salt_title), run_time=1)
        self.play(
            GrowFromCenter(na_circle), FadeIn(na_text),
            GrowFromCenter(cl_circle), FadeIn(cl_text),
            FadeIn(transfer_e),
            run_time=2
        )
        self.play(
            Create(transfer_arrow), Write(e_label),
            run_time=1.5
        )
        # Electron moves to chlorine
        self.play(
            transfer_e.animate.move_to(cl_side.get_left() + LEFT * 0.1),
            run_time=1.5, rate_func=smooth
        )

        # Transform to ions
        na_ion_label = Text("Na\u207a", font_size=38, color=NA_COLOR, weight=BOLD)
        cl_ion_label = Text("Cl\u207b", font_size=38, color=CL_COLOR, weight=BOLD)
        na_ion_label.move_to(na_text)
        cl_ion_label.move_to(cl_text)

        self.play(
            Transform(na_text, na_ion_label),
            Transform(cl_text, cl_ion_label),
            FadeOut(transfer_e), FadeOut(transfer_arrow), FadeOut(e_label),
            na_circle.animate.set_stroke(color=NA_COLOR, width=4),
            cl_circle.animate.set_stroke(color=CL_COLOR, width=4),
            run_time=1.5
        )

        # Ionic bond — attract
        plus = Text("+", font_size=44, color=DIM_TEXT).move_to(UP * 1.5)
        arrow_bond = Arrow(LEFT * 0.8, RIGHT * 0.8, color=ACCENT, stroke_width=3).move_to(DOWN * 0.5)
        bond_label = Text("Ionic Bond", font_size=28, color=ACCENT)
        bond_label.next_to(arrow_bond, DOWN, buff=0.2)

        # NaCl result
        result = Text("NaCl", font_size=52, color=TEXT_COL, weight=BOLD)
        result_sub = Text("Table Salt", font_size=30, color=DIM_TEXT)
        result_group = VGroup(result, result_sub).arrange(DOWN, buff=0.3).move_to(DOWN * 3.5)

        self.play(
            na_side.animate.shift(RIGHT * 1),
            cl_side.animate.shift(LEFT * 1),
            FadeIn(plus),
            run_time=1.5
        )
        self.play(Create(arrow_bond), Write(bond_label), run_time=1)
        self.play(FadeIn(result_group, shift=UP * 0.5), run_time=1.5)
        self.wait(1.5)

        # ════════════════════════════════════════════
        # SCENE 4: Battery — Sodium-Ion Battery
        # ════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        batt_title = Text("Sodium-Ion Battery", font_size=44, color=NA_COLOR, weight=BOLD)
        batt_title.move_to(UP * 5.5)

        # Battery cell outline
        cell = RoundedRectangle(
            width=7, height=6, corner_radius=0.3,
            color=DIM_TEXT, stroke_width=2, fill_opacity=0.05
        ).move_to(UP * 0.5)

        # Cathode (left)
        cathode = Rectangle(width=1.2, height=4.5, color=LI_COLOR, fill_opacity=0.2, stroke_width=2)
        cathode.move_to(LEFT * 2.5 + UP * 0.5)
        cathode_label = Text("Cathode", font_size=22, color=LI_COLOR)
        cathode_label.next_to(cathode, DOWN, buff=0.25)

        # Anode (right)
        anode = Rectangle(width=1.2, height=4.5, color=CL_COLOR, fill_opacity=0.2, stroke_width=2)
        anode.move_to(RIGHT * 2.5 + UP * 0.5)
        anode_label = Text("Anode", font_size=22, color=CL_COLOR)
        anode_label.next_to(anode, DOWN, buff=0.25)

        # Electrolyte (middle)
        electrolyte = Rectangle(width=3.5, height=4.5, color=ACCENT, fill_opacity=0.05, stroke_width=1)
        electrolyte.move_to(UP * 0.5)
        elec_label = Text("Electrolyte", font_size=20, color=ACCENT)
        elec_label.move_to(UP * 3.2)

        # Separator line
        sep = DashedLine(UP * 2.75 + UP * 0.5, DOWN * 2.75 + UP * 0.5, color=DIM_TEXT, stroke_width=1)

        # Na+ ions flowing
        ions = VGroup()
        ion_positions = [
            LEFT * 1.0 + UP * 1.5,
            LEFT * 0.3 + UP * 0.5,
            RIGHT * 0.5 + DOWN * 0.2,
            LEFT * 0.8 + DOWN * 1.0,
            RIGHT * 0.2 + UP * 2.0,
            RIGHT * 1.0 + UP * 0.8,
        ]
        for pos in ion_positions:
            ion_circle = Circle(radius=0.22, color=NA_COLOR, fill_opacity=0.3, stroke_width=2)
            ion_text = Text("Na\u207a", font_size=14, color=NA_COLOR)
            ion = VGroup(ion_circle, ion_text).move_to(pos + UP * 0.5)
            ions.add(ion)

        # Flow arrows
        flow1 = Arrow(LEFT * 1.5, RIGHT * 1.5, color=NA_COLOR, stroke_width=2, max_tip_length_to_length_ratio=0.15)
        flow1.move_to(DOWN * 2 + UP * 0.5)
        flow_label = Text("Na\u207a flow \u2192", font_size=20, color=NA_COLOR)
        flow_label.next_to(flow1, DOWN, buff=0.15)

        self.play(Write(batt_title), run_time=1)
        self.play(Create(cell), run_time=1)
        self.play(
            FadeIn(cathode), Write(cathode_label),
            FadeIn(anode), Write(anode_label),
            Create(sep),
            FadeIn(electrolyte), Write(elec_label),
            run_time=2
        )
        self.play(
            LaggedStart(*[GrowFromCenter(ion) for ion in ions], lag_ratio=0.12),
            run_time=2
        )
        self.play(GrowArrow(flow1), Write(flow_label), run_time=1.5)

        # Animate ions moving right (charging)
        self.play(
            *[ion.animate.shift(RIGHT * 1.5) for ion in ions],
            run_time=2.5, rate_func=smooth
        )
        self.wait(1.5)

        # ════════════════════════════════════════════
        # SCENE 5: Li vs Na Comparison
        # ════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        vs_title = Text("Lithium vs Sodium", font_size=44, color=TEXT_COL, weight=BOLD)
        vs_title.move_to(UP * 5.5)

        # Comparison cards
        def make_card(symbol, color, stats, x_pos):
            card_bg = RoundedRectangle(
                width=3.3, height=7, corner_radius=0.3,
                color=color, fill_opacity=0.08, stroke_width=2
            )
            sym = Text(symbol, font_size=56, color=color, weight=BOLD)
            sym.move_to(card_bg.get_top() + DOWN * 1)

            stat_items = VGroup()
            for label, value in stats:
                l = Text(label, font_size=18, color=DIM_TEXT)
                v = Text(value, font_size=22, color=color, weight=BOLD)
                row = VGroup(l, v).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
                stat_items.add(row)
            stat_items.arrange(DOWN, buff=0.45, aligned_edge=LEFT)
            stat_items.next_to(sym, DOWN, buff=0.6)

            group = VGroup(card_bg, sym, stat_items).move_to(x_pos)
            return group

        li_card = make_card("Li", LI_COLOR, [
            ("Abundance", "0.002%"),
            ("Cost", "$15/kg"),
            ("Energy", "260 Wh/kg"),
            ("Cycles", "1000+"),
            ("Safety", "Fire risk"),
        ], LEFT * 2 + DOWN * 0.5)

        na_card = make_card("Na", NA_COLOR, [
            ("Abundance", "2.6%"),
            ("Cost", "$0.15/kg"),
            ("Energy", "160 Wh/kg"),
            ("Cycles", "3000+"),
            ("Safety", "Very stable"),
        ], RIGHT * 2 + DOWN * 0.5)

        vs_text = Text("VS", font_size=36, color=ACCENT, weight=BOLD).move_to(DOWN * 0.5)

        self.play(Write(vs_title), run_time=1)
        self.play(
            FadeIn(li_card, shift=RIGHT * 0.5),
            FadeIn(na_card, shift=LEFT * 0.5),
            FadeIn(vs_text, scale=1.5),
            run_time=2
        )
        # Highlight sodium advantages
        self.play(
            Indicate(na_card[2][1], color=NA_COLOR, scale_factor=1.15),  # cost
            run_time=1.5
        )
        self.play(
            Indicate(na_card[2][3], color=NA_COLOR, scale_factor=1.15),  # cycles
            run_time=1.5
        )
        self.play(
            Indicate(na_card[2][4], color=NA_COLOR, scale_factor=1.15),  # safety
            run_time=1.5
        )
        self.wait(1)

        # ════════════════════════════════════════════
        # SCENE 6: Crystal Lattice — NaCl structure
        # ════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        lattice_title = Text("Salt Crystal Lattice", font_size=44, color=TEXT_COL, weight=BOLD)
        lattice_title.move_to(UP * 5.5)

        # Build a 4x4 alternating grid of Na+ and Cl-
        lattice = VGroup()
        spacing = 1.1
        for row in range(4):
            for col in range(4):
                is_na = (row + col) % 2 == 0
                color = NA_COLOR if is_na else CL_COLOR
                radius = 0.3 if is_na else 0.38
                atom = Circle(radius=radius, color=color, fill_opacity=0.3, stroke_width=2)
                label = Text(
                    "Na\u207a" if is_na else "Cl\u207b",
                    font_size=14, color=color
                )
                atom_group = VGroup(atom, label)
                x = (col - 1.5) * spacing
                y = (row - 1.5) * spacing
                atom_group.move_to(np.array([x, y, 0]))
                lattice.add(atom_group)

        lattice.move_to(UP * 0.5)

        # Bonds connecting adjacent atoms
        bonds = VGroup()
        for row in range(4):
            for col in range(4):
                idx = row * 4 + col
                if col < 3:
                    right_idx = row * 4 + (col + 1)
                    bond = Line(
                        lattice[idx].get_center(), lattice[right_idx].get_center(),
                        color=DIM_TEXT, stroke_width=1, stroke_opacity=0.5
                    )
                    bonds.add(bond)
                if row < 3:
                    down_idx = (row + 1) * 4 + col
                    bond = Line(
                        lattice[idx].get_center(), lattice[down_idx].get_center(),
                        color=DIM_TEXT, stroke_width=1, stroke_opacity=0.5
                    )
                    bonds.add(bond)

        legend = VGroup(
            VGroup(
                Circle(radius=0.15, color=NA_COLOR, fill_opacity=0.4),
                Text("Na\u207a", font_size=22, color=NA_COLOR)
            ).arrange(RIGHT, buff=0.2),
            VGroup(
                Circle(radius=0.18, color=CL_COLOR, fill_opacity=0.4),
                Text("Cl\u207b", font_size=22, color=CL_COLOR)
            ).arrange(RIGHT, buff=0.2),
        ).arrange(RIGHT, buff=1.2).move_to(DOWN * 4)

        self.play(Write(lattice_title), run_time=1)
        self.play(
            LaggedStart(*[Create(b) for b in bonds], lag_ratio=0.02),
            run_time=1.5
        )
        self.play(
            LaggedStart(*[GrowFromCenter(a) for a in lattice], lag_ratio=0.04),
            run_time=3
        )
        self.play(
            FadeIn(legend),
            run_time=1.5
        )
        # Highlight one sodium and its 4 neighbors (2D cross)
        center_idx = 5  # row=1, col=1
        highlight = SurroundingRectangle(lattice[center_idx], color=NA_COLOR, buff=0.15, stroke_width=3)
        self.play(Create(highlight), run_time=1)
        self.wait(2)

        # ════════════════════════════════════════════
        # SCENE 7: Closing — "The Future is Sodium"
        # ════════════════════════════════════════════
        self.play(FadeOut(*self.mobjects), run_time=0.8)

        # Big sodium symbol
        final_circle = Circle(radius=2, color=NA_COLOR, fill_opacity=0.1, stroke_width=4)
        final_na = Text("Na", font_size=96, color=NA_COLOR, weight=BOLD)
        final_glow = Circle(radius=2.3, color=NA_COLOR, fill_opacity=0.05, stroke_width=1)
        atom_final = VGroup(final_glow, final_circle, final_na).move_to(UP * 1)

        closing1 = Text("The Future", font_size=48, color=TEXT_COL, weight=BOLD)
        closing2 = Text("is Sodium", font_size=48, color=NA_COLOR, weight=BOLD)
        closing = VGroup(closing1, closing2).arrange(DOWN, buff=0.3).move_to(DOWN * 3)

        self.play(
            GrowFromCenter(final_circle),
            FadeIn(final_na, scale=0.5),
            FadeIn(final_glow),
            run_time=2.5
        )
        self.play(
            FadeIn(closing1, shift=UP * 0.3),
            FadeIn(closing2, shift=UP * 0.3),
            run_time=2
        )
        # Gentle pulse
        self.play(
            final_circle.animate.scale(1.1).set_stroke(opacity=0.6),
            final_glow.animate.scale(1.15),
            run_time=1.5, rate_func=there_and_back
        )
        self.wait(2)
        self.play(FadeOut(*self.mobjects), run_time=1.5)
