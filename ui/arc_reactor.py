import tkinter as tk
import math
import time
import random

class ArcReactor(tk.Canvas):
    """
    STARK INDUSTRIES MARK VII PALLADIUM ARC REACTOR
    High-tech multi-layered vector animated reactor with:
    - Counter-rotating telemetry & degree rings
    - Outer azimuth markers and technical tick indicators
    - High-energy solenoid coils with gradient glow
    - 360-degree radar luminescence sweep line
    - Pulsing triangular core & plasma bloom
    - Dynamic reactive colors for STANDBY, LISTENING, SPEAKING, PROCESSING, MUTED
    """
    def __init__(self, parent, size=250, bg="#080c16", **kwargs):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size / 2
        self.cy = size / 2
        
        self.angle_inner = 0.0
        self.angle_outer = 0.0
        self.angle_sweep = 0.0
        self.pulse = 0.0
        self.state = "STANDBY" # STANDBY, LISTENING, SPEAKING, PROCESSING, MUTED
        
        self.running = True
        self._animate()

    def set_state(self, new_state):
        self.state = new_state

    def _animate(self):
        if not self.running:
            return

        self.delete("all")
        
        # State-driven dynamics
        if self.state == "SPEAKING":
            speed_inner = 0.05
            speed_outer = -0.035
            sweep_speed = 0.08
            pulse_speed = 0.14
            core_glow = "#00ffff"
            core_bloom = "#38bdf8"
            ring_glow = "#0284c7"
            accent_glow = "#e0f2fe"
        elif self.state == "LISTENING":
            speed_inner = 0.04
            speed_outer = -0.025
            sweep_speed = 0.06
            pulse_speed = 0.10
            core_glow = "#10b981"
            core_bloom = "#34d399"
            ring_glow = "#059669"
            accent_glow = "#d1fae5"
        elif self.state == "PROCESSING":
            speed_inner = 0.08
            speed_outer = -0.06
            sweep_speed = 0.12
            pulse_speed = 0.18
            core_glow = "#f59e0b"
            core_bloom = "#fbbf24"
            ring_glow = "#d97706"
            accent_glow = "#fef3c7"
        elif self.state == "MUTED":
            speed_inner = 0.008
            speed_outer = -0.005
            sweep_speed = 0.02
            pulse_speed = 0.03
            core_glow = "#ef4444"
            core_bloom = "#f87171"
            ring_glow = "#991b1b"
            accent_glow = "#fee2e2"
        else: # STANDBY
            speed_inner = 0.018
            speed_outer = -0.012
            sweep_speed = 0.035
            pulse_speed = 0.045
            core_glow = "#00e5ff"
            core_bloom = "#0284c7"
            ring_glow = "#0369a1"
            accent_glow = "#bae6fd"

        self.angle_inner += speed_inner
        self.angle_outer += speed_outer
        self.angle_sweep += sweep_speed
        self.pulse += pulse_speed

        pulse_offset = math.sin(self.pulse) * 3.5

        # --- 1. Outer Diagnostic Boundary Ring ---
        r_outer = (self.size / 2) - 8
        self.create_oval(
            self.cx - r_outer, self.cy - r_outer,
            self.cx + r_outer, self.cy + r_outer,
            outline="#0c2333", width=2
        )

        # --- 2. Degree Marks & Compass Telemetry (Every 30 deg) ---
        r_ticks = r_outer - 5
        for deg in range(0, 360, 15):
            rad = math.radians(deg) + self.angle_outer * 0.4
            length = 6 if (deg % 45 == 0) else 3
            tick_color = ring_glow if (deg % 45 == 0) else "#0c3247"
            x1 = self.cx + (r_ticks - length) * math.cos(rad)
            y1 = self.cy + (r_ticks - length) * math.sin(rad)
            x2 = self.cx + r_ticks * math.cos(rad)
            y2 = self.cy + r_ticks * math.sin(rad)
            self.create_line(x1, y1, x2, y2, fill=tick_color, width=1.5 if length == 6 else 1)

        # Cardinal Text Labels (0°, 90°, 180°, 270°)
        cardinals = [(0, "090°"), (math.pi/2, "180°"), (math.pi, "270°"), (3*math.pi/2, "000°")]
        for ang, label in cardinals:
            lx = self.cx + (r_ticks - 14) * math.cos(ang)
            ly = self.cy + (r_ticks - 14) * math.sin(ang)
            self.create_text(lx, ly, text=label, fill="#045677", font=("Consolas", 6, "bold"))

        # --- 3. Segmented Cyber Notches (Counter-Rotating) ---
        n_outer = 18
        r_notch = r_outer - 18
        for i in range(n_outer):
            a = self.angle_outer + (i * (2 * math.pi / n_outer))
            x1 = self.cx + (r_notch - 4) * math.cos(a)
            y1 = self.cy + (r_notch - 4) * math.sin(a)
            x2 = self.cx + (r_notch + 4) * math.cos(a)
            y2 = self.cy + (r_notch + 4) * math.sin(a)
            notch_color = core_glow if (i % 3 == 0) else ring_glow
            self.create_line(x1, y1, x2, y2, fill=notch_color, width=2)

        # --- 4. Middle Flux Track & Glowing Ring ---
        r_mid = r_notch - 10
        self.create_oval(
            self.cx - r_mid, self.cy - r_mid,
            self.cx + r_mid, self.cy + r_mid,
            outline=ring_glow, width=2
        )

        # --- 5. 360-Degree Radar Sweep Luminescence ---
        for sweep_trail in range(8):
            trail_ang = self.angle_sweep - (sweep_trail * 0.08)
            trail_alpha_color = "#042838" if sweep_trail > 3 else ring_glow
            sx = self.cx + (r_mid - 4) * math.cos(trail_ang)
            sy = self.cy + (r_mid - 4) * math.sin(trail_ang)
            self.create_line(self.cx, self.cy, sx, sy, fill=trail_alpha_color, width=1.5)

        # --- 6. Solenoid Magnetic Coils (10 Coils) ---
        n_coils = 10
        r_coil_inner = r_mid - 24
        r_coil_outer = r_mid - 4
        for i in range(n_coils):
            a_center = self.angle_inner + (i * (2 * math.pi / n_coils))
            da = 0.14
            
            p1 = (self.cx + r_coil_inner * math.cos(a_center - da), self.cy + r_coil_inner * math.sin(a_center - da))
            p2 = (self.cx + r_coil_outer * math.cos(a_center - da), self.cy + r_coil_outer * math.sin(a_center - da))
            p3 = (self.cx + r_coil_outer * math.cos(a_center + da), self.cy + r_coil_outer * math.sin(a_center + da))
            p4 = (self.cx + r_coil_inner * math.cos(a_center + da), self.cy + r_coil_inner * math.sin(a_center + da))
            
            # Coil polygon with metallic copper-cyan highlights
            self.create_polygon(
                [p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1]],
                fill="#061c29", outline=ring_glow, width=1.5
            )
            # Solenoid center glow strip
            cx_m = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
            cy_m = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
            self.create_oval(cx_m - 2, cy_m - 2, cx_m + 2, cy_m + 2, fill=core_glow, outline="")

        # --- 7. Inner Core Confinement Ring ---
        r_core_ring = r_coil_inner - 8 + pulse_offset
        self.create_oval(
            self.cx - r_core_ring, self.cy - r_core_ring,
            self.cx + r_core_ring, self.cy + r_core_ring,
            outline=core_glow, width=3
        )

        # Secondary concentric glow ring
        r_core_sub = r_core_ring - 6
        self.create_oval(
            self.cx - r_core_sub, self.cy - r_core_sub,
            self.cx + r_core_sub, self.cy + r_core_sub,
            outline=ring_glow, width=1.5
        )

        # --- 8. Central Palladium Core Reservoir ---
        r_center = r_core_sub - 8
        self.create_oval(
            self.cx - r_center, self.cy - r_center,
            self.cx + r_center, self.cy + r_center,
            fill="#03121c", outline=core_bloom, width=2
        )

        # --- 9. Triangular Mark VI Arc Reactor Iris ---
        n_tri = 3
        r_tri = r_center - 4
        tri_points = []
        for i in range(n_tri):
            a = -self.angle_inner * 1.8 + (i * (2 * math.pi / n_tri))
            px = self.cx + r_tri * math.cos(a)
            py = self.cy + r_tri * math.sin(a)
            tri_points.extend([px, py])
            # Radial energy conduits
            self.create_line(self.cx, self.cy, px, py, fill=accent_glow, width=1.5)
            
        self.create_polygon(tri_points, fill="#042030", outline=core_glow, width=2)

        # Inverted triangle wireframe for cyber geometric depth
        tri_inverted = []
        for i in range(n_tri):
            a = -self.angle_inner * 1.8 + math.pi + (i * (2 * math.pi / n_tri))
            px = self.cx + (r_tri * 0.7) * math.cos(a)
            py = self.cy + (r_tri * 0.7) * math.sin(a)
            tri_inverted.extend([px, py])
        self.create_polygon(tri_inverted, fill="", outline=core_bloom, width=1)

        # --- 10. Center Plasma Spark & Halo ---
        r_spark = 5.0 + (pulse_offset * 0.6)
        self.create_oval(
            self.cx - (r_spark + 4), self.cy - (r_spark + 4),
            self.cx + (r_spark + 4), self.cy + (r_spark + 4),
            fill="", outline=core_bloom, width=1
        )
        self.create_oval(
            self.cx - r_spark, self.cy - r_spark,
            self.cx + r_spark, self.cy + r_spark,
            fill="#ffffff", outline=core_glow, width=1.5
        )

        # ~35 FPS animation frame rate
        self.after(28, self._animate)

    def destroy(self):
        self.running = False
        super().destroy()


class VoiceVisualizer(tk.Canvas):
    """
    STARK INDUSTRIES SPECTRAL AUDIO EQUALIZER
    Dynamic 30-band frequency equalizer that animates during voice activity:
    - Bounces dynamically when Jarvis is speaking or listening
    - High-tech gradient colored bars
    - Peak level indicators with decay physics
    """
    def __init__(self, parent, width=250, height=55, bg="#080c16", **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.num_bars = 28
        self.state = "STANDBY"
        
        # Frequency magnitudes & peaks
        self.bars = [0.1] * self.num_bars
        self.peaks = [0.1] * self.num_bars
        self.running = True
        self._animate()

    def set_state(self, new_state):
        self.state = new_state

    def _animate(self):
        if not self.running:
            return

        self.delete("all")

        # Color themes
        if self.state == "SPEAKING":
            bar_color = "#00f3ff"
            peak_color = "#38bdf8"
            activity_level = 0.85
        elif self.state == "LISTENING":
            bar_color = "#10b981"
            peak_color = "#34d399"
            activity_level = 0.75
        elif self.state == "PROCESSING":
            bar_color = "#f59e0b"
            peak_color = "#fbbf24"
            activity_level = 0.90
        elif self.state == "MUTED":
            bar_color = "#ef4444"
            peak_color = "#f87171"
            activity_level = 0.05
        else: # STANDBY
            bar_color = "#0284c7"
            peak_color = "#0369a1"
            activity_level = 0.20

        # Bar layout
        bar_w = (self.w - (self.num_bars * 2)) / self.num_bars
        mid_y = self.h / 2

        # Draw baseline
        self.create_line(4, mid_y, self.w - 4, mid_y, fill="#0c2333", width=1)

        t = time.time() * 6.0
        for i in range(self.num_bars):
            # Target height based on sinusoidal wave + random jitter
            if activity_level > 0.3:
                wave = (math.sin(t + i * 0.45) + 1.0) * 0.5
                target = (wave * 0.6 + random.uniform(0.1, 0.4)) * activity_level
            else:
                wave = (math.sin(t * 0.5 + i * 0.3) + 1.0) * 0.5
                target = wave * activity_level

            # Smooth interpolation
            self.bars[i] += (target - self.bars[i]) * 0.35
            val = max(0.04, min(0.95, self.bars[i]))
            
            # Peak decay
            if val > self.peaks[i]:
                self.peaks[i] = val
            else:
                self.peaks[i] -= 0.03
            self.peaks[i] = max(val, self.peaks[i])

            bh = val * (self.h * 0.85)
            x0 = 4 + i * (bar_w + 2)
            x1 = x0 + bar_w
            y0 = mid_y - (bh / 2)
            y1 = mid_y + (bh / 2)

            # Draw bar
            self.create_rectangle(x0, y0, x1, y1, fill=bar_color, outline="")

            # Draw peak dot
            pk_y0 = mid_y - (self.peaks[i] * (self.h * 0.85) / 2) - 2
            pk_y1 = pk_y0 + 1.5
            self.create_rectangle(x0, pk_y0, x1, pk_y1, fill=peak_color, outline="")

        self.after(35, self._animate)

    def destroy(self):
        self.running = False
        super().destroy()
