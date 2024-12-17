import json, shlex, sys, subprocess, argparse, os, tempfile, re
import datetime, collections
from .conf import conf
import matplotlib.pyplot as plt
import numpy as np
import tomllib

def main():
    p = argparse.ArgumentParser(prog="stdvis", description="StdTest's Visualization part")
    p.add_argument("input", help="File to visualize")
    args = p.parse_args()
    inputfile = os.path.abspath(args.input)
    dat = tomllib.loads(open(inputfile).read())
    poly = list(filter(lambda c: c, dat["poly"].split()))
    assert len(poly) % 2 == 0
    poly = np.array(poly, dtype=float).reshape(len(poly) // 2, 2)
    
    lsegs = list(filter(lambda c: c, dat["lseg"].split()))
    assert len(lsegs) >= 4 and len(lsegs) % 4 == 0
    lsegs = np.array(lsegs, dtype=float).reshape(len(lsegs) // 4, 2, 2)

    pltgeo(poly, lsegs)
    

def pltgeo(poly, lsegs: list[list[tuple]]):
    
    from matplotlib import collections, transforms

    # Make a list of colors cycling through the default series.
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    fig, ax = plt.subplots()
    fig.subplots_adjust(top=0.92, left=0.07, right=0.97,
                        hspace=0.3, wspace=0.3)


    col = collections.LineCollection(lsegs,)
    ax.add_collection(col, autolim=True)
    col.set_color('b')
    ax.autoscale_view()  # See comment above, after ax1.add_collection.
    ax.set_title('LineCollection using offsets')

    # The same data as above, but fill the curves.
    col = collections.PolyCollection(
        [poly], )
    ax.add_collection(col, autolim=True)
    col.set_color('k')

    ax.autoscale_view()
    ax.set_title('PolyCollection using offsets')

    plt.show()
    
def layout_graph():
    pass



if __name__ == '__main__':
    main()