from .plot_utils import (
    get_plot,
    add_axes,
    get_colormapper_add_colorbar,
    add_title,
    add_glyphs,
    add_hover,
    add_age_glyphs,
    add_age_hover,
    add_count_toggle
)


def get_summary_heatmap(df, study_ids):
    from bokeh.models import ColumnDataSource
    from bokeh.document import Document
    # https://github.com/bokeh/bokeh/pull/5872 can simplify when released
    source = ColumnDataSource()
    source.data.update(df[['study_label', 'domain_label', 'count', 'subjects']].to_dict(orient='list'))  # noqa
    y_factors = df[['domain_label']].sort_values(by='domain_label')['domain_label'].unique().tolist()  # noqa
    y_factors_width = df['domain_label'].map(len).max()
    x_factors = study_ids
    max_count = df['count'].max()
    title_text = "Number of observations by domain"
    tooltips = ("Domain: @domain_label <br> Study: @study_label <br> "
                "Count: @count{0a} <br> Subjects: @subjects{0a}")

    plot = get_plot(y_factors, y_factors_width, x_factors)
    color_mapper = get_colormapper_add_colorbar(plot, high=max_count)
    add_axes(plot)
    add_glyphs(plot, source, color_mapper, 'study_label', 'domain_label')
    add_hover(plot, tooltips)
    add_title(plot, title_text)
    column = add_count_toggle(plot)
    # https://github.com/bokeh/bokeh/pull/5909 can remove when released
    Document().add_root(column)

    return column


def get_heatmap(df, study_ids):
    from bokeh.models import ColumnDataSource
    from bokeh.document import Document
    # https://github.com/bokeh/bokeh/pull/5872 can simplify when released
    source = ColumnDataSource()
    source.data.update(df[['study_label', 'var_label', 'count', 'subjects']].to_dict(orient='list'))  # noqa
    try:
        df['var_code'] = df['var_code'].astype('int')
    except ValueError:
        pass
    y_factors = df[['var_code', 'var_label']].sort_values(by='var_code')['var_label'].unique().tolist()   # noqa
    y_factors_width = df['var_label'].map(len).max()
    x_factors = study_ids
    max_count = df['count'].max()
    title_text = "Number of observations by variable"
    tooltips = ("Variable: @var_label <br> Study: @study_label <br> "
                "Count: @count{0a} <br> Subjects: @subjects{0a}")

    plot = get_plot(y_factors, y_factors_width, x_factors)
    color_mapper = get_colormapper_add_colorbar(plot, high=max_count)
    add_axes(plot)
    add_glyphs(plot, source, color_mapper, 'study_label', 'var_label')
    add_hover(plot, tooltips)
    add_title(plot, title_text)
    column = add_count_toggle(plot)
    # https://github.com/bokeh/bokeh/pull/5909 can remove when released
    Document().add_root(column)

    return column


def get_age_heatmap(df):
    from bokeh.document import Document
    show_studies = len(df['study_label'].unique()) <= 16
    try:
        df['var_code'] = df['var_code'].astype('int')
    except ValueError:
        pass
    try:
        df['qual_code'] = df['qual_code'].astype('int')
    except ValueError:
        pass
    y_factors = df[['var_code', 'var_label']].sort_values(by='var_code')['var_label'].unique().tolist()  # noqa
    y_factors_width = df['var_label'].map(len).max()
    x_factors = df[['qual_code', 'qual_label']].sort_values(by='qual_code')['qual_label'].unique().tolist()  # noqa
    max_count = df['count'].max()
    title_text = "Number of observations by variable and age"

    plot = get_plot(y_factors, y_factors_width, x_factors)
    color_mapper = get_colormapper_add_colorbar(plot, high=max_count)
    add_axes(plot)
    hover_renderer = add_age_glyphs(plot, df, color_mapper, show_studies)
    if show_studies:
        tooltips = ("Variable: @var_label <br> Age: @qual_label <br> "
                    "Study: @study_label <br> Count: @count{0a} <br> Subjects: @subjects{0a}")
        add_age_hover(plot, tooltips, hover_renderer)
    else:
        tooltips = ("Variable: @var_label <br> Age: @qual_label <br> "
                    "Count: @count{0a} <br> Subjects: @subjects{0a}")
        add_age_hover(plot, tooltips, hover_renderer)
    add_title(plot, title_text)
    column = add_count_toggle(plot)
    # https://github.com/bokeh/bokeh/pull/5909 can remove when released
    Document().add_root(column)

    return column
