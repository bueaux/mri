from inspect import isroutine

from mri.util import generate_hex_ticks

from matplotlib import pyplot as plt
import matplotlib.ticker as ticker

def draw_graph_mpl(graph_data, **kwargs):
        thumb = kwargs.pop('thumb', False)
        outputfile = kwargs.pop('filename', None)
        title = kwargs.pop('title', None)
        xlabel = kwargs.pop('xlabel', None)
        size = kwargs.pop('size', None)
        dpi = kwargs.pop('dpi', 100.0)
        legend = kwargs.pop('legend', False)
        font_size = kwargs.pop('xtick_font_size', False)

        # Set up subplots.
        fig, ax = plt.subplots()
        fig.hold(True)

        for n, plot_data in enumerate(graph_data['plots']):
            pt = plot_data['type']
            if pt in _plot_map:
                _plot_map[pt](ax, plot_data, thumb=thumb, zorder=n)
            else:
                raise Exception("Invalid plot type")

        xlim = graph_data['xlim']
        ylim = graph_data['ylim']

        if not thumb:
            # Omitting boundary labels for now
            for bound in graph_data.get('boundaries', []):
                ax.vlines(bound['offset'], ylim[0], ylim[1], 
                    linewidth=1.5, zorder=100, linestyle='dashed')

            # Omitting point labels
            # Just marking points of interest e.g. entrypoint.
            for point in graph_data.get('points', []):
                ax.scatter(bound['offset'], 0, s=60.0, color='black', zorder=100)

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        xaxis_max = xlim[1]

        if not thumb:
            # Adjust x-ticks to be in hex, and on sane boundaries.
            ticks = ax.get_xticks()
            ax.set_xticks(generate_hex_ticks(ticks, xaxis_max))
            ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%x'))
            locs, labels = plt.xticks()
            if font_size:
                plt.setp(labels, rotation=25, horizontalalignment='right', fontsize=font_size)
            else:
                plt.setp(labels, rotation=25, horizontalalignment='right')
            ax.grid()

            if xlabel:
                ax.set_xlabel(xlabel)
            if title:
                ax.set_title(title)

            if legend and 'legend_order' in graph_data:
                order = graph_data['legend_order']
                labels = ax.get_legend_handles_labels()
                labels = zip(*labels)
                labels = sorted(labels, key=lambda x: order.index(x[1]))

                ax.legend(*zip(*labels), loc="best", prop={'size':8})
        else:
            plt.tick_params(axis='x', which='both',bottom='off',
                top='off',labelbottom='off')

        # Omit the y coordinates altogether since they're sort of normalised.
        plt.tick_params(axis='y', which='both',left='off',
            top='off',labelleft='off', right='off')

        if outputfile is None:
            plt.show()
        else:
            if size:
                fig.set_size_inches(size)
            fig.savefig(outputfile, bbox_inches='tight', dpi=dpi, pad_inches=0.01)

def _plot_graph_plot(ax, plot_data, **kwargs):
    plot_args = []
    plot_kwargs = {}

    thumb = kwargs.get('thumb', False)

    plot_args = plot_data['data']
    xaxis, yaxis = plot_args
    color = plot_data['color']

    for prop in [ 'label', 'linewidth', 'zorder']:
        if prop not in plot_data:
            continue
        value = plot_data[prop]
        if isroutine(value):
            value = value(thumb)
        plot_kwargs[prop] = value

    ax.plot(xaxis, yaxis, color, **plot_kwargs)

    if plot_data.get('fill', False):
        where = [ True for x in xaxis ]
        alpha = plot_data.get('fillalpha', 1.0)        
        plt.fill_between(xaxis, yaxis, where=where, interpolate=True, 
            color=color, alpha=alpha)


def _plot_graph_bar(ax, plot_data, **kwargs):
    plot_kwargs = {}

    color = plot_data['color']
    plot_kwargs['color'] = color
    plot_kwargs['edgecolor'] = color
    for prop in ['label', 'width', 'zorder']:
        if prop not in plot_data:
            continue
        plot_kwargs[prop] = plot_data[prop]
    data = plot_data['data']
    if not data:
        return

    ax.bar(*data, **plot_kwargs)

_plot_map = {
    'plot': _plot_graph_plot,
    'bar': _plot_graph_bar,
}
