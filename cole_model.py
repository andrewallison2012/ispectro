#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
http://www.scipy.org/Cookbook/Least_Squares_Circle
"""

from numpy import *
import pandas as pd
import numpy as np

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QWidget


class Canvas(FigureCanvas, QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        df = pd.read_csv(self.data)

        ratid = '003r'
        Xcmin = mean(df['z_imaginary']) + mean(df['z_imaginary']) * 1.1
        Xcmax = mean(df['z_imaginary']) - mean(df['z_imaginary']) * 1.1

        Rmin = mean(df['z_real']) - mean(df['z_real']) * 1.1
        Rmax = mean(df['z_real']) + mean(df['z_real']) * 1.1

        x = df['z_real']
        y = df['z_imaginary']

        x = np.ma.array(x).round()
        y = np.ma.array(y).round()

        x = np.ma.masked_invalid(x).compressed()
        y = np.ma.masked_invalid(y).compressed()

        print("The input integer masked array is:")
        print(x)

        xnan = np.ma.filled(x.astype(float), np.nan)
        print("Converted to double precision, with nan:")
        print(xnan)

        x_m = mean(x)
        y_m = (max(y) * -1)
        a = 1
        Rzero = min(x)
        Rinf = max(x)
        Rn = (Rzero - Rinf) * 2 * sin(a * pi * 0.5)
        Rzero = x_m - sqrt(Rn ** 2 + y_m ** 2)
        Rinf = x_m + sqrt(Rn ** 2 + y_m ** 2)
        x_m = (Rzero + Rinf) * 0.5
        y_m = (Rzero - Rinf) * 0.5 * cos(a * pi * 0.5) * (sin(a * pi * 0.5)) ** -1
        x_m = mean(x)
        y_m = mean(y)

        # == METHOD 1 ==
        method_1 = 'algebraic'

        # calculation of the reduced coordinates
        u = x - x_m
        v = y - y_m

        Suv = sum(u * v)
        Suu = sum(u ** 2)
        Svv = sum(v ** 2)
        Suuv = sum(u ** 2 * v)
        Suvv = sum(u * v ** 2)
        Suuu = sum(u ** 3)
        Svvv = sum(v ** 3)

        # Solving the linear system
        A = array([[Suu, Suv], [Suv, Svv]])
        B = array([Suuu + Suvv, Svvv + Suuv]) / 2.0
        uc, vc = linalg.solve(A, B)

        xc_1 = x_m + uc
        yc_1 = y_m + vc

        # Calculation of all distances from the center (xc_1, yc_1)
        Ri_1 = sqrt((x - xc_1) ** 2 + (y - yc_1) ** 2)
        R_1 = mean(Ri_1)
        residu_1 = sum((Ri_1 - R_1) ** 2)
        residu2_1 = sum((Ri_1 ** 2 - R_1 ** 2) ** 2)

        # Decorator to count functions calls
        import functools

        def countcalls(fn):
            "decorator function count function calls "

            @functools.wraps(fn)
            def wrapped(*args):
                wrapped.ncalls += 1
                return fn(*args)

            wrapped.ncalls = 0
            return wrapped

        #  == METHOD 2 ==
        from scipy import optimize

        method_2 = "leastsq"

        def calc_R(c):
            """ calculate the distance of each 2D points from the center c=(xc, yc) """
            return sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2)

        @countcalls
        def f_2(c):
            """ calculate the algebraic distance between the 2D points and the mean circle centered at c=(xc, yc) """
            Ri = calc_R(c)
            return Ri - Ri.mean()

        center_estimate = x_m, y_m
        center_2, ier = optimize.leastsq(f_2, center_estimate)
        xc_2, yc_2 = center_2
        Ri_2 = calc_R(center_2)
        R_2 = Ri_2.mean()
        residu_2 = sum((Ri_2 - R_2) ** 2)
        residu2_2 = sum((Ri_2 ** 2 - R_2 ** 2) ** 2)
        ncalls_2 = f_2.ncalls

        #############################################
        # == METHOD 3 ==
        from scipy import odr
        method_3 = "odr"

        @countcalls
        def f_3(beta, x):
            """ implicit function of the circle """
            xc, yc, r = beta
            return (x[0] - xc) ** 2 + (x[1] - yc) ** 2 - r ** 2

        #   return (x[0] - xc) ** 2 + (x[1] - yc) ** 2 - r ** 2

        def calc_estimate(data):
            """ Return a first estimation on the parameter from the data  """
            xc0, yc0 = x_m, y_m
            r0 = sqrt((data.x[0] - xc0) ** 2 + (data.x[1] - yc0) ** 2).mean()
            return xc0, yc0, r0

        # for implicit function :
        #       data.x contains both coordinates of the points
        #       data.y is the dimensionality of the response
        lsc_data = odr.Data(row_stack([x, y]), y=1)
        lsc_model = odr.Model(f_3, implicit=True, estimate=calc_estimate)
        lsc_odr = odr.ODR(lsc_data, lsc_model)
        lsc_out = lsc_odr.run()

        xc_3, yc_3, R_3 = lsc_out.beta
        Ri_3 = calc_R([xc_3, yc_3])
        residu_3 = sum((Ri_3 - R_3) ** 2)
        residu2_3 = sum((Ri_3 ** 2 - R_3 ** 2) ** 2)
        ncalls_3 = f_3.ncalls

        print('lsc_out.sum_square = ', lsc_out.sum_square)

        # == METHOD 4 ==

        method_4 = "odr with jacobian"

        @countcalls
        def f_4(beta, x):
            """ implicit function of the circle """
            xc, yc, r = beta
            xi, yi = x
            return (xi - xc) ** 2 + (yi - yc) ** 2 - r ** 2

        @countcalls
        def jacb(beta, x):
            """ Jacobian function with respect to the parameters beta.
            return df/dbeta
            """

            xc, yc, r = beta
            xi, yi = x

            df_db = empty((beta.size, x.shape[1]))
            df_db[0] = 2 * (xc - xi)  # d_f/dxc
            df_db[1] = 2 * (yc - yi)  # d_f/dyc
            df_db[2] = -2 * r  # d_f/dr

            return df_db

        @countcalls
        def jacd(beta, x):
            """ Jacobian function with respect to the input x.
            return df/dx
            """
            xc, yc, r = beta
            xi, yi = x

            df_dx = empty_like(x)
            df_dx[0] = 2 * (xi - xc)  # d_f/dxi
            df_dx[1] = 2 * (yi - yc)  # d_f/dyi

            return df_dx

        def calc_estimate(data):
            """ Return a first estimation on the parameter from the data  """
            xc0, yc0 = data.x.mean(axis=1)
            r0 = sqrt((data.x[0] - xc0) ** 2 + (data.x[1] - yc0) ** 2).mean()
            return xc0, yc0, r0

        # for implicit function :
        #       data.x contains both coordinates of the points
        #       data.y is the dimensionality of the response
        lsc_data = odr.Data(row_stack([x, y]), y=1)
        lsc_model = odr.Model(f_4, implicit=True, estimate=calc_estimate, fjacd=jacd, fjacb=jacb)
        lsc_odr = odr.ODR(lsc_data, lsc_model)
        lsc_odr.set_job(deriv=3)  # use user derivatives function without checking
        lsc_out = lsc_odr.run()

        xc_4, yc_4, R_4 = lsc_out.beta
        Ri_4 = calc_R([xc_4, yc_4])
        residu_4 = sum((Ri_4 - R_4) ** 2)
        residu2_4 = sum((Ri_4 ** 2 - R_4 ** 2) ** 2)
        ncalls_4 = f_4.ncalls

        print("Method 4 :")
        print("Functions calls : f_4=%d jacb=%d jacd=%d" % (f_4.ncalls, jacb.ncalls, jacd.ncalls))

        Rinf = x_m - sqrt(R_2 ** 2 + yc_2 ** 2)
        Rzero = xc_2 + sqrt(R_2 ** 2 + yc_2 ** 2)

        # Summary
        fmt = '%-18s %10.5f %10.5f %10.5f %10d %10.6f %10.6f %10.2f'
        print(('\n%-18s' + ' %10s' * 7) % tuple('METHOD Xc Yc Rc nb_calls std(Ri) residu residu2'.split()))
        print('-' * (18 + 7 * (10 + 1)))
        # print(fmt % (method_1, xc_1, yc_1, R_1, 1, Ri_1.std(), residu_1, residu2_1))
        print(fmt % (method_2, xc_2, yc_2, R_2, ncalls_2, Ri_2.std(), residu_2, residu2_2))
        print(fmt % (method_3, xc_3, yc_3, R_3, ncalls_3, Ri_3.std(), residu_3, residu2_3))
        print(fmt % (method_4, xc_4, yc_4, R_4, ncalls_4, Ri_4.std(), residu_4, residu2_4))
        print(Rinf, Rzero)

        Rzero = xc_2.round(1) - R_2.round(1)
        Rinf = xc_2.round(1) + R_2.round(1)

        stringoutput = f'Cole Model\nRegression\nXc={xc_2.round(1)}\nYc={yc_2.round(1)}\nRc={R_2.round(1)}\ninterations={ncalls_3}\nRinf={Rinf.round()}\nRzero={Rzero.round()}'.format()
        print(stringoutput)

        from matplotlib import pyplot as p, cm

        def plot_all(residu2=False, basename='circle'):
            """ Draw data points, best fit circles and center for the three methods,
            and adds the iso contours corresponding to the fiel residu or residu2
            """

            f = p.figure(figsize=(6.5, 4.5), dpi=90, facecolor='white')
            p.plot(x, y, 'wo', label='data', ms=6, mec='k', mew=1)

            theta_fit = linspace(-pi, pi, 180)

            x_fit1 = xc_1 + R_1 * cos(theta_fit)
            y_fit1 = yc_1 + R_1 * sin(theta_fit)
            p.plot(x_fit1, y_fit1, 'b-', label=method_1, lw=2)

            x_fit2 = xc_2 + R_2 * cos(theta_fit)
            y_fit2 = yc_2 + R_2 * sin(theta_fit)
            p.plot(x_fit2, y_fit2, 'k--', label=method_2, lw=2)

            x_fit3 = xc_3 + R_3 * cos(theta_fit)
            y_fit3 = yc_3 + R_3 * sin(theta_fit)
            p.plot(x_fit3, y_fit3, 'r-.', label=method_3, lw=2)

            p.plot([xc_1], [yc_1], 'bD', mec='y', mew=1)
            p.plot([xc_2], [yc_2], 'gD', mec='r', mew=1)
            p.plot([xc_3], [yc_3], 'kD', mec='w', mew=1)

            # draw
            p.xlabel('R')
            p.ylabel('X')
            p.legend(loc='best', labelspacing=0.1)

            # plot the residu fields
            nb_pts = 100

            left, right = (xc_2 - (R_2 * 1.1), xc_2 + (R_2 * 1.1))
            bottom, top = (yc_2 - (R_2 * 1.1), yc_2 + (R_2 * 1.1))

            vmin = min(left, bottom)
            vmax = max(right, top)

            xg, yg = ogrid[vmin:vmax:nb_pts * 1j, vmin:vmax:nb_pts * 1j]
            xg = xg[..., newaxis]
            yg = yg[..., newaxis]

            Rig = sqrt((xg - x) ** 2 + (yg - y) ** 2)
            Rig_m = Rig.mean(axis=2)[..., newaxis]

            if residu2:
                residu = sum((Rig ** 2 - Rig_m ** 2) ** 2, axis=2)
            else:
                residu = sum((Rig - Rig_m) ** 2, axis=2)

            lvl = exp(linspace(log(residu.min()), log(residu.max()), 15))

            p.contourf(xg.flat, yg.flat, residu.T, lvl, alpha=0.75, cmap=cm.Reds_r)
            cbar = p.colorbar(format='%.f')

            if residu2:
                cbar.set_label('Residuals')
            else:
                cbar.set_label('Residuals')

            p.xlim(left=vmin, right=vmax)
            p.ylim(bottom=vmin, top=vmax)

            p.axis('equal')

            p.grid()
            p.title(f'Cole Model')

            p.savefig('%s_cole%d.png' % (basename, 2 if residu2 else 1))
            p.draw()
            print(vmax)
            print(vmin)

        ######

        plot_all(residu2=False, basename='circle')
        p.grid(True)


        p.text(xc_2, yc_2, stringoutput, horizontalalignment='right', verticalalignment='top')

        print(Xcmin)
        print(Xcmax)
        print(Rmin)
        print(Rmax)
        p.show()

