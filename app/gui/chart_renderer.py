from __future__ import annotations

import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
import pandas as pd

from app.core.ohlc_detector import get_ohlc_frame
from app.gui.theme import Colors


def _style_axis(ax: plt.Axes, bg_color: str, fg_color: str, grid: bool = True, border_color: str = Colors.BORDER) -> None:
    ax.set_facecolor(bg_color)
    if grid:
        ax.grid(color=border_color, alpha=0.15)
    else:
        ax.grid(False)
        
    for spine in ax.spines.values():
        spine.set_color(border_color)
        
    ax.xaxis.label.set_color(fg_color)
    ax.yaxis.label.set_color(fg_color)
    ax.title.set_color(fg_color)
    ax.tick_params(colors=fg_color, labelcolor=fg_color)


def _compute_bar_width(xs: np.ndarray) -> float:
    if len(xs) < 2:
        return 0.6
    spacing = np.median(np.diff(xs))
    return max(0.2, min(1.0, spacing * 0.7))


def _make_datetime_index(df: pd.DataFrame, timestamp_column: str) -> np.ndarray:
    return mdates.date2num(pd.to_datetime(df[timestamp_column], errors="coerce"))


def _create_annotation(ax: plt.Axes, df: pd.DataFrame, metadata: dict[str, str], style: str) -> tuple[plt.Annotation, np.ndarray, pd.DataFrame]:
    timestamp_column = metadata["timestamp_column"]
    xs = _make_datetime_index(df, timestamp_column)
    
    bg_color = "#111111" if style == "Neon Candlestick" else Colors.BG_CARD
    fg_color = "#FFFFFF" if style == "Neon Candlestick" else Colors.TEXT_PRIMARY
    border = "#333333" if style == "Neon Candlestick" else Colors.BORDER
    
    annotation = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        bbox={"boxstyle": "round", "fc": bg_color, "ec": border, "alpha": 0.95},
        color=fg_color,
        fontsize=9,
        zorder=10,
    )
    annotation.set_visible(False)
    return annotation, xs, df


def _update_candlestick_annotation(event, annotation: plt.Annotation, xs: np.ndarray, df: pd.DataFrame, metadata: dict[str, str]) -> None:
    if event.inaxes is None or event.xdata is None:
        annotation.set_visible(False)
        return

    idx = np.searchsorted(xs, event.xdata)
    idx = max(0, min(len(xs) - 1, idx))
    row = df.iloc[idx]

    timestamp = pd.to_datetime(row[metadata["timestamp_column"]])
    open_val = float(row[metadata["open_column"]])
    high_val = float(row[metadata["high_column"]])
    low_val = float(row[metadata["low_column"]])
    close_val = float(row[metadata["close_column"]])
    change = close_val - open_val
    change_pct = (change / open_val * 100) if open_val != 0 else 0.0
    volume_str = "" if metadata.get("volume_column") is None else f"Volumen: {int(row[metadata['volume_column']])}\n"

    text = (
        f"{timestamp:%Y-%m-%d %H:%M:%S}\n"
        f"Open: {open_val:.2f}\n"
        f"High: {high_val:.2f}\n"
        f"Low: {low_val:.2f}\n"
        f"Close: {close_val:.2f}\n"
        f"Cambio: {change:.2f} ({change_pct:.2f} %)\n"
        f"{volume_str}"
    )
    annotation.set_text(text)
    annotation.xy = (event.xdata, event.ydata if event.ydata is not None else close_val)
    annotation.set_visible(True)
    event.canvas.draw_idle()


def _draw_story_texts(
    ax: plt.Axes,
    xs: np.ndarray,
    highs: pd.Series,
    story_texts: list[str],
    style: str,
) -> None:
    if not story_texts:
        return

    text_color = "#FFFFFF" if style == "Neon Candlestick" else Colors.TEXT_PRIMARY
    spacer = float((highs.max() - highs.min()) * 0.06) if len(highs) else 1.0
    max_values = highs.fillna(highs.max())
    for i, word in enumerate(story_texts[: len(xs)]):
        x = xs[i]
        y = max_values.iloc[i] + spacer * (1 + (i % 3) * 0.4)
        ax.text(
            x,
            y,
            word,
            color=text_color,
            fontsize=12,
            fontweight="bold",
            ha="center",
            va="bottom",
            alpha=0.95,
            bbox={"boxstyle": "round,pad=0.2", "fc": "#000000", "ec": "none", "alpha": 0.45},
            zorder=6,
        )


def render_candlestick_chart(
    df: pd.DataFrame,
    metadata: dict[str, str],
    style: str = "Profesional",
    options: dict = None,
    figsize: tuple[float, float] = (10, 6),
    story_texts: list[str] | None = None,
) -> plt.Figure:
    
    if options is None:
        options = {}

    ohlc_df = get_ohlc_frame(df, metadata)
    
    show_volume = bool(metadata.get("volume_column"))
    rows = [3]
    if show_volume:
        rows.append(1)

    fig, axes = plt.subplots(
        len(rows),
        1,
        sharex=True,
        figsize=figsize,
        gridspec_kw={"height_ratios": rows},
        constrained_layout=True,
    )
    
    if len(rows) == 1:
        axes = [axes]

    # Style palette selection
    if style == "Neon Candlestick":
        fig_bg = "#000000"
        ax_bg = "#0B0B0F"
        fg_color = "#FFFFFF"
        border_color = "#222222"
        c_inc = "#39FF14"
        c_dec = "#FF073A"
        wick_width = 1.4
        body_alpha = 0.95
    else:
        fig_bg = "#08090D"
        ax_bg = "#08090D"
        fg_color = "#F4F7FA"
        border_color = "#22262E"
        c_inc = "#00C060"
        c_dec = "#E74C3C"
        wick_width = 1.2
        body_alpha = 1.0

    fig.patch.set_facecolor(fig_bg)

    price_ax = axes[0]
    _style_axis(price_ax, ax_bg, fg_color, grid=False, border_color=border_color)
    price_ax.set_facecolor(ax_bg)
    for spine in price_ax.spines.values():
        spine.set_visible(False)

    xs = _make_datetime_index(ohlc_df, metadata["timestamp_column"])
    opens = ohlc_df[metadata["open_column"]].astype(float)
    highs = ohlc_df[metadata["high_column"]].astype(float)
    lows = ohlc_df[metadata["low_column"]].astype(float)
    closes = ohlc_df[metadata["close_column"]].astype(float)
    
    width = _compute_bar_width(xs)
    increasing = closes >= opens
    decreasing = ~increasing

    price_ax.vlines(xs[increasing], lows[increasing], highs[increasing], color=c_inc, linewidth=wick_width, zorder=2)
    price_ax.vlines(xs[decreasing], lows[decreasing], highs[decreasing], color=c_dec, linewidth=wick_width, zorder=2)

    price_ax.bar(xs[increasing], closes[increasing] - opens[increasing], bottom=opens[increasing], width=width, align="center", color=c_inc, edgecolor=c_inc, linewidth=0.6, alpha=body_alpha, zorder=3)
    price_ax.bar(xs[decreasing], closes[decreasing] - opens[decreasing], bottom=closes[decreasing], width=width, align="center", color=c_dec, edgecolor=c_dec, linewidth=0.6, alpha=body_alpha, zorder=3)

    if style == "Neon Candlestick":
        glow_w = width * 1.75
        price_ax.bar(xs[increasing], closes[increasing] - opens[increasing], bottom=opens[increasing], width=glow_w, align="center", color=c_inc, alpha=0.18, zorder=1)
        price_ax.bar(xs[decreasing], closes[decreasing] - opens[decreasing], bottom=closes[decreasing], width=glow_w, align="center", color=c_dec, alpha=0.18, zorder=1)

    price_ax.xaxis_date()
    price_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    price_ax.tick_params(colors=fg_color, labelsize=9)
    
    if options.get("labels", False):
        price_ax.set_ylabel("Precio", color=fg_color)

    if options.get("sma", False) and len(closes) >= 20:
        sma_20 = closes.rolling(window=20).mean()
        sma_color = "#FFD700" if style == "Neon Candlestick" else "#2196F3"
        price_ax.plot(xs, sma_20, color=sma_color, linewidth=1.4, alpha=0.85, label="SMA 20", zorder=4)
        price_ax.legend(loc="upper left", frameon=True, facecolor=ax_bg, edgecolor=border_color, labelcolor=fg_color, fontsize=9)

    if story_texts:
        _draw_story_texts(price_ax, xs, highs, story_texts, style)

    if show_volume:
        vol_ax = axes[1]
        _style_axis(vol_ax, ax_bg, fg_color, grid=False, border_color=border_color)
        vol_ax.set_facecolor(ax_bg)
        vol_data = ohlc_df[metadata["volume_column"]].astype(float)
        
        vol_ax.bar(xs[increasing], vol_data[increasing], width=width, color=c_inc, alpha=0.65, zorder=2)
        vol_ax.bar(xs[decreasing], vol_data[decreasing], width=width, color=c_dec, alpha=0.65, zorder=2)
        
        if options.get("labels", False):
            vol_ax.set_ylabel("Volumen", color=fg_color)
    
    if options.get("tooltip", False):
        cursor = Cursor(price_ax, useblit=True, color=fg_color, linewidth=0.7, alpha=0.5)
        price_ax._cursor = cursor 
        candlestick_annotation, ann_xs, ann_df = _create_annotation(price_ax, ohlc_df, metadata, style)
        fig.canvas.mpl_connect(
            "motion_notify_event",
            lambda event: _update_candlestick_annotation(event, candlestick_annotation, ann_xs, ann_df, metadata),
        )

    return fig


def render_standard_chart(
    df: pd.DataFrame,
    chart_type: str,
    col_x: str | None,
    col_y: str,
    options: dict = None,
    figsize: tuple[float, float] = (10, 6),
) -> plt.Figure:
    
    if options is None:
        options = {}

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    
    bg_color = Colors.BG_PRIMARY
    fg_color = Colors.TEXT_PRIMARY
    fig.patch.set_facecolor(bg_color)
    
    _style_axis(ax, bg_color, fg_color, grid=options.get("grid", True))
    
    series_y = df[col_y].astype(float) if pd.api.types.is_numeric_dtype(df[col_y]) else df[col_y]
    
    if col_x and col_x in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col_x]):
            x_values = mdates.date2num(df[col_x])
            ax.xaxis_date()
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        else:
            x_values = df[col_x]
    else:
        x_values = np.arange(len(series_y))
        
    c = Colors.ACCENT
        
    if chart_type == "Histogram":
        ax.hist(series_y.dropna(), bins=30, color=c, edgecolor=Colors.BORDER)
    elif chart_type == "Line":
        ax.plot(x_values, series_y, color=c, linewidth=1.8)
    elif chart_type == "Bar":
        ax.bar(x_values, series_y, color=c, edgecolor=Colors.BORDER)
    elif chart_type == "Area":
        ax.fill_between(x_values, series_y, color=c, alpha=0.35)
        ax.plot(x_values, series_y, color=c, linewidth=1.4)
    elif chart_type == "Scatter":
        ax.scatter(x_values, series_y, color=c, s=18)
    elif chart_type == "Boxplot":
        ax.boxplot(series_y.dropna(), vert=True, patch_artist=True)
    elif chart_type == "Pie":
        counts = df[col_y].value_counts()
        ax.pie(counts, labels=counts.index if options.get("labels", True) else None, autopct='%1.1f%%')
    elif chart_type == "Donut":
        counts = df[col_y].value_counts()
        ax.pie(counts, labels=counts.index if options.get("labels", True) else None, autopct='%1.1f%%')
        centre_circle = plt.Circle((0,0),0.70,fc=bg_color)
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
    else:
        ax.plot(x_values, series_y, color=c, linewidth=1.8)
        
    if options.get("labels", True) and chart_type not in ["Pie", "Donut"]:
        ax.set_ylabel(col_y, color=fg_color)
        if col_x:
            ax.set_xlabel(col_x, color=fg_color)
            
    if options.get("legend", True) and chart_type not in ["Pie", "Donut", "Histogram", "Boxplot"]:
        ax.legend([col_y], frameon=True, facecolor=Colors.BG_CARD, edgecolor=Colors.BORDER, labelcolor=fg_color)
        
    return fig
