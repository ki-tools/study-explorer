# Imports MUST be inside function or app won't deploy
# from bokeh.palettes import viridis
FONT = 'Roboto'
MONO_FONT = 'Roboto Mono'


def add_axes(plot):
    from bokeh.models import (
        CategoricalAxis,
        Grid,
    )
    x_axis = CategoricalAxis(major_label_orientation=0.785, major_label_text_font=MONO_FONT)
    y_axis = CategoricalAxis(major_label_text_font=MONO_FONT)
    plot.add_layout(x_axis, 'below')
    plot.add_layout(y_axis, 'left')
    plot.add_layout(Grid(dimension=0, ticker=x_axis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=y_axis.ticker))


def add_hover(plot, tooltips):
    from bokeh.models import (
        HoverTool,
    )
    hover = HoverTool(tooltips=tooltips)
    plot.add_tools(hover)


def add_age_hover(plot, tooltips, renderer):
    from bokeh.models import (
        HoverTool,
    )
    hover = HoverTool(tooltips=tooltips, renderers=[renderer])
    plot.add_tools(hover)


def add_title(plot, title_text):
    from bokeh.models import (
        Label
    )
    plot.add_layout(
        Label(
            text=title_text,
            text_font_size='10pt',
            text_font_style='bold',
            text_font=FONT,
            render_mode='css',
            x=0, y=6, x_units='screen', y_units='screen'
        ), 'above'
    )


def get_plot(y_factors, y_factors_width, x_factors):
    from bokeh.models import (
        Plot,
        FactorRange,
    )
    x_range = FactorRange(*x_factors)
    y_range = FactorRange(*y_factors)
    if len(x_factors) < 10:
        x_factor = 40
    else:
        x_factor = 20
    plot_width = (len(x_range.factors) * x_factor) + (y_factors_width * 8) + 60
    plot_height = len(y_range.factors) * 25 + 200
    plot = Plot(
        x_range=x_range, y_range=y_range,
        logo=None, toolbar_location=None,
        plot_height=plot_height, plot_width=plot_width,
        outline_line_color=None, title=None,
    )
    return plot


def get_colormapper_add_colorbar(plot, high):
    from bokeh.models import (
        FixedTicker,
        ColorBar,
        NumeralTickFormatter,
        LinearColorMapper,
    )
    from bokeh.palettes import viridis
    PALETTE_N = 10
    palette = viridis(PALETTE_N)
    palette.reverse()

    color_mapper = LinearColorMapper(palette=palette, low=0, high=high)

    ticker = FixedTicker(ticks=[0, high])
    formatter = NumeralTickFormatter(format='0 a')
    color_bar = ColorBar(
        color_mapper=color_mapper,
        ticker=ticker,
        formatter=formatter,
        location=(0, 0),
        label_standoff=2,
        height=PALETTE_N * 5,
        width=10,
        major_tick_line_color=None,
        major_label_text_align='left',
        major_label_text_font=FONT,
    )
    plot.add_layout(color_bar, 'right')
    return color_mapper


def add_glyphs(plot, source, color_mapper, x_label, y_label):
    from bokeh.models import (
        Rect, Circle
    )
    # Transparent Rect for improved hovering
    plot.add_glyph(
        source,
        Rect(
            x=x_label, y=y_label, width=0.9, height=0.9,
            fill_color=None, line_color=None
        )
    )
    plot.add_glyph(
        source,
        Circle(
            x=x_label, y=y_label, size=10,
            fill_color={'field': 'count', 'transform': color_mapper},
            line_color=None
        )
    )


def add_age_glyphs(plot, df, color_mapper, show_studies=True):
    from bokeh.models import (
        Rect, Circle, ColumnDataSource
    )
    if show_studies:
        df = add_categorical_offsets(df)
        cols = ['study_label', 'var_label', 'qual_label', 'count', 'subjects',
                'age_label_adjusted', 'var_label_adjusted']

        # https://github.com/bokeh/bokeh/pull/5872 can simplify when released
        source = ColumnDataSource()
        source.data.update(df[cols].to_dict(orient='list'))
        plot.add_glyph(
            source,
            Rect(
                x='qual_label', y='var_label', width=0.9, height=0.9,
                fill_color={'field': 'count', 'transform': color_mapper},
                fill_alpha=0.1,
                line_color=None
            )
        )

        hover_renderer = plot.add_glyph(
            source,
            Circle(
                x='age_label_adjusted', y='var_label_adjusted', radius=0.1,
                fill_color={'field': 'count', 'transform': color_mapper},
                line_color=None
            )
        )

    else:
        # TODO: This needs a test
        group_cols = ['qual_code', 'qual_label', 'var_label', 'var_code']
        grouped = df.groupby(group_cols)
        filtered_df = grouped['count', 'subjects'].sum()
        n_studies = grouped['study'].nunique()
        filtered_df['n_studies'] = (n_studies / (n_studies.max() + 1))
        filtered_df = filtered_df.reset_index()

        # https://github.com/bokeh/bokeh/pull/5872 can simplify when released
        filtered_source = ColumnDataSource()
        filtered_cols = ['qual_label', 'var_label', 'count', 'subjects', 'n_studies']
        filtered_source.data.update(filtered_df[filtered_cols].to_dict(orient='list'))
        hover_renderer = plot.add_glyph(
            filtered_source,
            Rect(
                x='qual_label', y='var_label', width=0.9, height=0.9,
                fill_color={'field': 'count', 'transform': color_mapper},
                fill_alpha={'field': 'n_studies'},
                line_color=None
            )
        )

    return hover_renderer


def add_categorical_offsets(df):
    # TODO: This needs a test
    """
    Applies the following mapping
    adjust_map = {
        0: {'x': .2, 'y': .8},
        1: {'x': .4, 'y': .8},
        2: {'x': .6, 'y': .8},
        3: {'x': .8, 'y': .8},
        4: {'x': .2, 'y': .6},
        5: {'x': .4, 'y': .6},
        6: {'x': .6, 'y': .6},
        7: {'x': .8, 'y': .6},
        8: {'x': .2, 'y': .4},
        9: {'x': .4, 'y': .4},
        10: {'x': .6, 'y': .4},
        11: {'x': .8, 'y': .4},
        12: {'x': .2, 'y': .2},
        13: {'x': .4, 'y': .2},
        14: {'x': .6, 'y': .2},
        15: {'x': .8, 'y': .2},
    }
    """
    studies = list(df['study_label'].unique())
    index = df['study_label'].apply(studies.index)
    df['age_label_adjusted'] = (df['qual_label'] + ':' +
                                ((index % 4) * .2 + .2).astype(str))
    df['var_label_adjusted'] = (df['var_label'] + ':' +
                                (((-index + 15) / 4).astype(int) * .2 + .2).astype(str))
    return df


def add_count_toggle(plot):
    from bokeh.layouts import widgetbox
    from bokeh.models import (
        CustomJS, Column, Circle, Rect, ColumnDataSource,
        LinearColorMapper, ColorBar, Label
    )
    from bokeh.models.widgets import RadioButtonGroup

    args = dict(
        circle=None,
        rect=None,
    )
    for r in plot.references():
        if isinstance(r, Circle):
            args['circle'] = r
        elif isinstance(r, Rect):
            args['rect'] = r
        elif isinstance(r, LinearColorMapper):
            args['cmapper'] = r
        elif isinstance(r, ColorBar):
            args['cbar'] = r
        elif isinstance(r, ColumnDataSource):
            args['ds'] = r
        elif isinstance(r, Label):
            args['title'] = r

    callback = CustomJS(args=args, code="""
       var label = cb_obj.labels[cb_obj.active];
       var selection = {Observations: 'count', Subjects: 'subjects'}[label];
       if (circle !== null) {circle.fill_color.field = selection};
       if (rect !== null && rect.fill_color) {rect.fill_color.field = selection };
       var max_val = Math.max.apply(null, ds.data[selection]);
       cmapper.high = max_val;
       cbar.ticker.ticks = [0, max_val];
       split_title = title.text.split(' ');
       split_title[2] = label.toLowerCase();
       title.text = split_title.join(' ');
       ds.trigger("change");
    """)

    plot.min_border_top = 50
    radio_button_group = RadioButtonGroup(
        labels=["Observations", "Subjects"], active=0)
    radio_button_group.callback = callback
    widgets = widgetbox(radio_button_group, width=300)
    return Column(widgets, plot)
