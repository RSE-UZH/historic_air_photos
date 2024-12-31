from pathlib import Path
import matplotlib.patches
import matplotlib.pyplot as plt
import seaborn as sns


def plot_phase(_ax, _phase, _n):
    width = phases[_phase][1] - phases[_phase][0]
    up = pow(-1, _n) > 0

    offset = 5
    max_devs = max([len(d) for d in developments.values()]) + 1

    if not up:
        p = matplotlib.patches.Rectangle((phases[_phase][0], -1), width=width, height=1,
                                         color='0.5', alpha=0.4)
        _ax.add_artist(p)

        _ax.annotate(_phase, (phases[_phase][0], -1), ha='left', va='bottom', size='medium', weight='bold',
                     xytext=(offset, offset), textcoords='offset points')
    else:
        p = matplotlib.patches.Rectangle((phases[_phase][0], 0), width=width, height=1,
                                         color='0.5', alpha=0.4)

        _ax.add_artist(p)
        _ax.annotate(_phase, (phases[_phase][0], 1), ha='left', va='top', size='medium', weight='bold',
                     xytext=(offset, -offset), textcoords='offset points')

    for yind, d in enumerate(developments[_phase]):
        year, dev = d

        yloc = pow(-1, _n) * (yind + 1) / max_devs

        ax.plot([year, year], [0, yloc], 'w--', linewidth=0.5)
        ax.plot(year, yloc, 'wo', markeredgecolor='k', ms=4)

        ax.annotate(str(year), (year, yloc), ha='right', va='center',
                    xytext=(-4, -1), textcoords='offset points', size='small')

        ax.annotate(dev, (year, yloc), ha='left', va='center', xytext=(5, -1),
                    textcoords='offset points', size='small')

    return _ax


phases = {'Phase I': [1858, 1900],
          'Phase II': [1900, 1920],
          'Phase III': [1920, 1940],
          'Phase IV': [1940, 1956],
          'Phase V': [1956, 2000]}

developments = {'Phase I': [(1858, 'First aerial photo from balloon'),
                            (1885, 'Roll film invented')],
                'Phase II': [(1903, 'First aeroplane'),
                             (1908, 'First aerial photo'),
                             (1913, 'First airborne camera'),
                             (1914, 'First air force established'),
                             (1916, 'First stereo airborne image acquisition'),
                             (1917, 'First airborne roll film camera')],
                'Phase III': [(1920, 'First Fairchild camera'),
                              (1922, 'Development/adoption of stereo plotting'),
                              (1924, 'First civil/Commercial aerial mapping'),
                              (1925, 'Fairchild K-3 camera'),
                              (1930, 'First colonial territorial mapping')],
                'Phase IV': [(1940, 'Further camera and aviation advancements'),
                             (1942, 'First false colour film camera'),
                             (1950, 'Mapping new areas'),
                             (1956, 'U-2 spy aircraft')],
                'Phase V': [(1956, '23x23 cm RC8 mapping camera'),
                            (1959, 'Start of satellite photography'),
                            (1960, 'U-2 spy aircraft shot down'),
                            (1978, 'Development of GPS'),
                            (1990, 'Colour infrared film'),
                            (2000, 'Digital aerial camera')]
                }

#
sns.set_theme(style="white")
sns.set_style('ticks')

fig, ax = plt.subplots(1, 1, figsize=(16, 7))

# plot the timeline

ax.plot([1850, 2010], [0, 0], 'k', linewidth=2)

for n, phase in enumerate(phases.keys()):
    plot_phase(ax, phase, n)

# set the axis limits
ax.set_ylim(-1, 1)
ax.set_xlim(1855, 2005)

# set the spines on/off and in the center
for s in ['left', 'right', 'top']:
    ax.spines[s].set_visible(False)

ax.spines['bottom'].set_position('center')

# remove the tick labels
ax.set_yticks([])

# set the year ticks
ax.set_xticks([1860, 1900, 1940, 1980])

# save the figure
fig.savefig(Path('figures', 'FigA1_DevelopmentTimeline.png'), dpi=600, bbox_inches='tight')
