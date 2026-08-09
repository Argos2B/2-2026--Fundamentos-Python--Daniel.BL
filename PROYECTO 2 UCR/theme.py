"""Design system and theme configuration for Data Analyzer Pro."""
import customtkinter as ctk
class Colors:
    """Application color palette — dark mode optimized."""
    # Backgrounds
    BG_PRIMARY = "#0F1117"
    BG_SIDEBAR = "#1A1D27"
    BG_CARD = "#21252F"
    BG_CARD_HOVER = "#2A2E3A"
    BG_INPUT = "#171B24"
    BG_TABLE_ROW = "#181C25"
    BG_TABLE_ALT = "#1E2230"
    # Accents
    ACCENT = "#6366F1"
    ACCENT_HOVER = "#818CF8"
    ACCENT_LIGHT = "#4F46E5"
    ACCENT_SECONDARY = "#22D3EE"
    ACCENT_SECONDARY_HOVER = "#67E8F9"
    # Semantic
    SUCCESS = "#10B981"
    SUCCESS_HOVER = "#34D399"
    WARNING = "#F59E0B"
    WARNING_HOVER = "#FBBF24"
    ERROR = "#EF4444"
    ERROR_HOVER = "#F87171"
    INFO = "#3B82F6"
    # Text
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"
    TEXT_DISABLED = "#475569"
    # Borders & surfaces
    BORDER = "#2D3344"
    BORDER_LIGHT = "#374151"
    DIVIDER = "#1E293B"
    SCROLLBAR = "#3B4252"
    # Chart palette
    CHART_COLORS = [
        "#6366F1", "#22D3EE", "#10B981", "#F59E0B", "#EF4444",
        "#EC4899", "#8B5CF6", "#14B8A6", "#F97316", "#06B6D4",
    ]
class Theme:
    """Helper methods for creating consistently styled widgets."""
    FONT_FAMILY = "Segoe UI"
    @staticmethod
    def heading(size: int = 20) -> tuple:
        return (Theme.FONT_FAMILY, size, "bold")
    @staticmethod
    def subheading(size: int = 16) -> tuple:
        return (Theme.FONT_FAMILY, size, "bold")
    @staticmethod
    def body(size: int = 13) -> tuple:
        return (Theme.FONT_FAMILY, size)
    @staticmethod
    def small(size: int = 11) -> tuple:
        return (Theme.FONT_FAMILY, size)
    @staticmethod
    def mono(size: int = 12) -> tuple:
        return ("Consolas", size)
    # ── Widget factories ──────────────────────────────────────────────
    @staticmethod
    def create_card(parent, **kwargs) -> ctk.CTkFrame:
        defaults = {
            "fg_color": Colors.BG_CARD,
            "corner_radius": 12,
            "border_width": 1,
            "border_color": Colors.BORDER,
        }
        defaults.update(kwargs)
        return ctk.CTkFrame(parent, **defaults)
    @staticmethod
    def create_section_title(parent, text: str, icon: str = "") -> ctk.CTkLabel:
        display = f"{icon}  {text}" if icon else text
        return ctk.CTkLabel(
            parent,
            text=display,
            font=Theme.heading(18),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
    @staticmethod
    def create_metric_card(
        parent, title: str, value: str, subtitle: str = "", accent: str = Colors.ACCENT
    ) -> ctk.CTkFrame:
        card = Theme.create_card(parent)
        accent_bar = ctk.CTkFrame(card, width=4, fg_color=accent, corner_radius=2)
        accent_bar.pack(side="left", fill="y", padx=(12, 0), pady=12)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(
            content, text=title, font=Theme.small(),
            text_color=Colors.TEXT_SECONDARY, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            content, text=str(value), font=Theme.heading(24),
            text_color=Colors.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w", pady=(2, 0))
        if subtitle:
            ctk.CTkLabel(
                content, text=subtitle, font=Theme.small(),
                text_color=Colors.TEXT_MUTED, anchor="w",
            ).pack(anchor="w")
        return card
    @staticmethod
    def create_primary_button(
        parent, text: str, command=None, icon: str = "", width: int = 140, **kwargs
    ) -> ctk.CTkButton:
        display = f"{icon}  {text}" if icon else text
        defaults = {
            "text": display,
            "command": command,
            "font": Theme.body(13),
            "fg_color": Colors.ACCENT,
            "hover_color": Colors.ACCENT_HOVER,
            "corner_radius": 8,
            "height": 38,
            "width": width,
        }
        defaults.update(kwargs)
        return ctk.CTkButton(parent, **defaults)
    @staticmethod
    def create_secondary_button(
        parent, text: str, command=None, icon: str = "", width: int = 140, **kwargs
    ) -> ctk.CTkButton:
        display = f"{icon}  {text}" if icon else text
        defaults = {
            "text": display,
            "command": command,
            "font": Theme.body(13),
            "fg_color": Colors.BG_CARD,
            "hover_color": Colors.BG_CARD_HOVER,
            "border_width": 1,
            "border_color": Colors.BORDER,
            "corner_radius": 8,
            "height": 38,
            "width": width,
        }
        defaults.update(kwargs)
        return ctk.CTkButton(parent, **defaults)
    @staticmethod
    def create_danger_button(
        parent, text: str, command=None, width: int = 140, **kwargs
    ) -> ctk.CTkButton:
        defaults = {
            "text": text,
            "command": command,
            "font": Theme.body(13),
            "fg_color": Colors.ERROR,
            "hover_color": Colors.ERROR_HOVER,
            "corner_radius": 8,
            "height": 38,
            "width": width,
        }
        defaults.update(kwargs)
        return ctk.CTkButton(parent, **defaults)
    @staticmethod
    def create_input(
        parent, placeholder: str = "", width: int = 200, **kwargs
    ) -> ctk.CTkEntry:
        defaults = {
            "placeholder_text": placeholder,
            "font": Theme.body(),
            "fg_color": Colors.BG_INPUT,
            "border_color": Colors.BORDER,
            "text_color": Colors.TEXT_PRIMARY,
            "placeholder_text_color": Colors.TEXT_MUTED,
            "corner_radius": 8,
            "height": 38,
            "width": width,
        }
        defaults.update(kwargs)
        return ctk.CTkEntry(parent, **defaults)
    @staticmethod
    def create_dropdown(
        parent, values: list, command=None, width: int = 200, **kwargs
    ) -> ctk.CTkOptionMenu:
        defaults = {
            "values": values,
            "command": command,
            "font": Theme.body(),
            "fg_color": Colors.BG_INPUT,
            "button_color": Colors.ACCENT,
            "button_hover_color": Colors.ACCENT_HOVER,
            "dropdown_fg_color": Colors.BG_CARD,
            "dropdown_hover_color": Colors.BG_CARD_HOVER,
            "dropdown_text_color": Colors.TEXT_PRIMARY,
            "text_color": Colors.TEXT_PRIMARY,
            "corner_radius": 8,
            "width": width,
        }
        defaults.update(kwargs)
        return ctk.CTkOptionMenu(parent, **defaults)
    @staticmethod
    def create_label(parent, text: str, style: str = "body", **kwargs) -> ctk.CTkLabel:
        styles = {
            "heading": {"font": Theme.heading(), "text_color": Colors.TEXT_PRIMARY},
            "subheading": {"font": Theme.subheading(), "text_color": Colors.TEXT_PRIMARY},
            "body": {"font": Theme.body(), "text_color": Colors.TEXT_PRIMARY},
            "secondary": {"font": Theme.body(), "text_color": Colors.TEXT_SECONDARY},
            "small": {"font": Theme.small(), "text_color": Colors.TEXT_MUTED},
            "mono": {"font": Theme.mono(), "text_color": Colors.TEXT_PRIMARY},
        }
        defaults = styles.get(style, styles["body"])
        defaults["text"] = text
        defaults["anchor"] = "w"
        defaults.update(kwargs)
        return ctk.CTkLabel(parent, **defaults)
    @staticmethod
    def create_badge(parent, text: str, color: str = Colors.ACCENT) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            parent,
            text=f"  {text}  ",
            font=Theme.small(10),
            fg_color=color,
            corner_radius=6,
            text_color="#FFFFFF",
            height=22,
        )
    @staticmethod
    def apply_matplotlib_style():
        """Apply dark theme to matplotlib plots."""
        import matplotlib.pyplot as plt
        plt.rcParams.update({
            "figure.facecolor": Colors.BG_CARD,
            "axes.facecolor": Colors.BG_PRIMARY,
            "axes.edgecolor": Colors.BORDER,
            "axes.labelcolor": Colors.TEXT_SECONDARY,
            "text.color": Colors.TEXT_PRIMARY,
            "xtick.color": Colors.TEXT_MUTED,
            "ytick.color": Colors.TEXT_MUTED,
            "grid.color": Colors.BORDER,
            "grid.alpha": 0.3,
            "legend.facecolor": Colors.BG_CARD,
            "legend.edgecolor": Colors.BORDER,
            "font.family": "Segoe UI",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
        })
