import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import matplotlib.collections as collections
import json


class MyLocator(mticker.MaxNLocator):
    def __init__(self, *args, **kwargs):
        mticker.MaxNLocator.__init__(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return mticker.MaxNLocator.__call__(self, *args, **kwargs)

plt.rc('axes', grid=True)
plt.rc('grid', color='0.75', linestyle='-', linewidth=0.5)
textsize = 9

#####
#
# Rectangle for axises
#
#####
left, width = 0.1, 0.8
rect1 = [left, 0.5, width, 0.4]  # left, bottom, width, height
rect2 = [left, 0.3, width, 0.2]

#####
#
# Figure
#
#####
fig = plt.figure(figsize=(20, 12), facecolor='white')
axescolor = '#f6f6f6'  # axises background color

ax1 = fig.add_axes(rect1, axisbg=axescolor)
ax1t = ax1.twinx()
ax2 = fig.add_axes(rect2, axisbg=axescolor, sharex=ax1)

#####
#
# Plot price and volume
#
#####
from apps.marketdataConsumer import intradaydata_np as intradata
from apps.marketdataConsumer import intradaydata_json

# DATE,CLOSE,HIGH,LOW,OPEN,VOLUME. Note! 1 = CLOSE
prices = intradata[:, 1]
t = intradata[:, 0]
fillcolor = 'darkgoldenrod'

low = intradata[:, 3]
high = intradata[:, 2]

deltas = np.zeros_like(prices)
deltas[1:] = np.diff(prices)
up = deltas > 0
ax1.vlines(t[up], low[up], high[up], color='black', label='_nolegend_')
ax1.vlines(t[~up], low[~up], high[~up], color='red', label='_nolegend_')

volume = (intradata[:, 4] * intradata[:, 5]) / 1e6  # volume in millions
vmax = volume.max()
poly = ax1t.fill_between(t, volume, 0, label='Volume', facecolor=fillcolor, edgecolor=fillcolor)
ax1t.set_ylim(0, 5 * vmax)
ax1t.set_yticks([])

#####
#
# MACD indicator
#
#####
from techmodels.indicators.trend.price.macd import MACDIndicator

fillcolor = 'darkslategrey'
nslow, nfast, nema = 35, 10, 5

macd_oscillator = MACDIndicator(prices, nslow=35, nfast=10, nema=5)
y1 = macd_oscillator.indicator()
y2 = macd_oscillator.indicator_inverse()

ax2.fill_between(t, y1, 0, where=y2 <= y1, alpha=0.5, facecolor='green', edgecolor=fillcolor)
ax2.fill_between(t, y1, 0, where=y2 >= y1, alpha=0.5, facecolor='red', edgecolor=fillcolor)
ax2.vlines(t, y1, 0, color='blue', lw=0.5)
ax2.text(0.025, 0.95, 'MACD (%d, %d, %d)' % (nfast, nslow, nema), va='top', transform=ax2.transAxes, fontsize=textsize)

#####
#
# Shading Region
#
#####
from visualization.matplotlib.utils.transform.regionshadingoverlay.regiontoshade import TranformRegionToShade
from sequences.io.trend.price.macd.chunk import macd_chunk

nfast, nslow, nema = 10, 35, 5
label = 'CHUNK-MACD'
chunkdata = TranformRegionToShade(macd_chunk(
                                            json.loads(intradaydata_json),
                                            nfast, nslow, nema,
                                            getter=lambda x: x[u'close']))

ymin, ymax = ax1.get_ylim()
collection = collections.BrokenBarHCollection.span_where(
                mdates.date2num(chunkdata.positiveTimestamps()),
                ymin,
                ymax,
                where=chunkdata.positiveFlag(),
                facecolor='green',
                alpha=0.1)
ax1.add_collection(collection)

collection = collections.BrokenBarHCollection.span_where(
                mdates.date2num(chunkdata.negativeTimestamps()),
                ymin,
                ymax,
                where=chunkdata.negativeFlag(),
                facecolor='red',
                alpha=0.1)
ax1.add_collection(collection)

ax1.text(0.025, 0.95, '%s (%d, %d, %d)' % (label, nfast, nslow, nema),
         va='top', transform=ax1.transAxes, fontsize=textsize)

#####
#
# Axis labeling
#
#####
# turn off upper axis tick labels, rotate the lower ones, etc
for ax in ax1, ax1t, ax2:
    if ax != ax2:
        for label in ax.get_xticklabels():
            label.set_visible(False)
    else:
        for label in ax.get_xticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment('right')

    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

#####
#
# Eye candy
#
#####
# at most 5 ticks, pruning the upper and lower so they don't overlap
# with other ticks
ax1.yaxis.set_major_locator(MyLocator(5, prune='both'))
ax2.yaxis.set_major_locator(MyLocator(5, prune='both'))

#####
#
# Display plot
#
#####
plt.show()
