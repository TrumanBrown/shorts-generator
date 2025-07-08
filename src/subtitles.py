from moviepy.editor import TextClip

def styled_subtitle(text, duration):
    try:
        subtitle = (
            TextClip(
                txt=text,
                fontsize=48,                    # Smaller font size
                font="Arial-Bold",
                color="yellow",                 # Ensure color is yellow
                stroke_color="black",
                stroke_width=4,                 # Slightly thinner border
                size=(960, None),               # Wrap earlier, but not too narrow
                method="caption"
            )
            .set_position(("center", "bottom"))
            .set_duration(duration)
            .margin(bottom=40)                 # Lower down (closer to bottom)
            .fadein(0.3)
            .fadeout(0.3)
        )
        return subtitle
    except Exception as e:
        print(f"Subtitle render failed: {e}")
        return None
