#!/usr/bin/env python
# define some variables
from __future__ import print_function
from builtins import str
import numpy as np
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")
import pylab as plt
try:
  from mpl_toolkits.basemap import Basemap
except ImportError:
  Basemap = None
from pylab import meshgrid

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
from matplotlib import cm
def main():
    """
    NAME
        plot_magmap.py

    DESCRIPTION
        makes a color contour map of desired field model

    SYNTAX
        plot_magmap.py [command line options]

    OPTIONS
        -h prints help and quits
        -f FILE  specify field model file with format:  l m g h 
        -fmt [pdf,jpg,eps,svg]  specify format for output figure  (default is jpg)
        -mod [arch3k,cals3k,pfm9k,hfm10k,cals10k_2,shadif14k,cals10k] specify model for 3ka to 1900 CE, default is  cals10k
        -alt ALT;  specify altitude in km, default is sealevel (0)
        -age specify date in decimal year, default is 2015
        -lon0: 0 longitude for map, default is 0
        -el: [D,I,B,Br]  specify element for plotting

    """
    cmap='RdYlBu'
    if not Basemap:
      print("-W- You must intstall the Basemap module to run plot_magmap.py")
      sys.exit()
    dir_path='.'
    lincr=1 # level increment for contours
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    else: fmt='jpg'
    if '-el' in sys.argv:
        ind = sys.argv.index('-el')
        el=sys.argv[ind+1]
    else:
        el='B'
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt=sys.argv[ind+1]
    else: alt=0
    if '-lon0' in sys.argv:
        ind=sys.argv.index('-lon0')
        lon_0=float(sys.argv[ind+1])
    else: lon_0=0
    if '-mod' in sys.argv:
        ind=sys.argv.index('-mod')
        mod=sys.argv[ind+1]
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        ghfile=sys.argv[ind+1]
        mod='custom'
    else: mod,ghfile='cals10k',''
    if '-age' in sys.argv:
        ind=sys.argv.index('-age')
        date=float(sys.argv[ind+1])
    else: date=2016.
    if '-alt' in sys.argv:
        ind=sys.argv.index('-alt')
        alt=float(sys.argv[ind+1])
    else: alt=0
    Ds,Is,Bs,Brs,lons,lats=pmag.do_mag_map(date,mod=mod,lon_0=lon_0,el=el,alt=alt,file=ghfile)
    m = Basemap(projection='hammer',lon_0=lon_0)
    x,y=m(*meshgrid(lons,lats))
    m.drawcoastlines()
    if mod=='custom':
        d='Custom'
    else: d=str(date)
    if el=='B':
        levmax=Bs.max()+lincr
        levmin=round(Bs.min()-lincr)
        levels=np.arange(levmin,levmax,lincr)
        print (levels)
        cs=m.contourf(x,y,Bs,levels=levels,cmap=cmap)
        plt.title('Field strength ($\mu$T): '+d);
    if el=='Brs':
        levmax=Brs.max()+lincr
        levmin=round(Brs.min()-lincr)
        cs=m.contourf(x,y,Brs,levels=np.arange(levmin,levmax,lincr),cmap=cmap)
        plt.title('Radial field strength ($\mu$T): '+str(date));
    if el=='I':
        levmax=Is.max()+lincr
        levmin=round(Is.min()-lincr)
        cs=m.contourf(x,y,Is,levels=np.arange(levmin,levmax,lincr),cmap=cmap)
        m.contour(x,y,Is,levels=np.arange(-80,90,10),colors='black')
        plt.title('Field inclination: '+str(date));
    if el=='D':
        levmax=Ds.max()+lincr
        levmin=round(Ds.min()-lincr)
        cs=m.contourf(x,y,Ds,levels=np.arange(levmin,levmax,lincr),cmap=cmap)
        m.contour(x,y,Ds,levels=np.arange(0,360,10),colors='black')
        plt.title('Field declination: '+str(date));
    cbar=m.colorbar(cs,location='bottom')
    plt.savefig('igrf'+d+'.'+fmt)
    print('Figure saved as: ','igrf'+d+'.'+fmt)

if __name__ == "__main__":
    main()
