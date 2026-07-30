"""Plot the refined f' and f'' against sin(theta)/lambda.

Built on the same Analysis machinery as the anomalous dispersion plot in
Analysis.py, so it looks like the rest of Olex2's diagnostics and pops out the
same way. The axis is sin(theta)/lambda rather than wavelength, which is the
whole point: the tabulated f' and f'' are constants and are drawn as the flat
lines they are, and the refined ones as the curves the refinement made of them.

Reading it: how far the curve departs from its flat line is the size of the
correction, and it should be read with suspicion rather than satisfaction. The
coefficients correlate strongly with U of the same atoms, and with f' and f''
themselves where those are refined too, so a curve that has run a long way from
its line is at least as likely to be absorbing model error as measuring
dispersion.
"""
import olx

from cctbx.array_family import flex

from olexFunctions import OV

import disp_radial


STEPS = 250


def _colour_for(element, IT):
  """The element's own sphere colour, as the other plots use."""
  try:
    return IT.decimalColorToRGB(
      int(olx.GetMaterial("{}.Sphere".format(element)).split(";")[1]))
  except Exception:
    return (128, 128, 128)


def group_details(xray_structure, dc):
  """(name, element, fp, fdp) for each group of the correction.

  fp and fdp are taken from the first scatterer of the group. In element mode
  every scatterer of a group shares them by construction; in atom mode a group
  is one scatterer.
  """
  names = getattr(dc, 'group_names', None) or \
    ['group %i' % g for g in range(dc.n_groups)]
  details = [None]*dc.n_groups
  scatterers = xray_structure.scatterers()
  for i in range(dc.group_of_scatterer.size()):
    g = dc.group_of_scatterer[i]
    if g < 0 or details[g] is not None:
      continue
    sc = scatterers[i]
    details[g] = (names[g], sc.scattering_type, sc.fp, sc.fdp)
  return [d for d in details if d is not None]


def make_plot():
  """Draw it, or say why there is nothing to draw."""
  from Analysis import Analysis, Dataset
  from ImageTools import IT
  from cctbx_olex_adapter import OlexCctbxAdapter

  if not OV.GetParam('snum.DispRadial.enabled', False):
    print('DispRadial: not enabled, nothing to plot')
    return
  xs = OlexCctbxAdapter().xray_structure()
  dc = disp_radial.build_correction(xs, log=False)
  if dc is None:
    print('DispRadial: nothing to plot')
    return
  details = group_details(xs, dc)
  if not details:
    print('DispRadial: no group has f\' or f\'\', nothing to plot')
    return

  class DispRadialPlot(Analysis):
    def __init__(self):
      Analysis.__init__(self, scale=4)
      self.item = "DispRadialPlot"
      self.graphInfo["pop_html"] = self.item
      self.graphInfo["pop_name"] = self.item
      self.graphInfo["TopRightTitle"] = self.TopRightTitle
      self.scale = 4

      self.auto_axes = True
      # the measured range, which is the only place the curves mean anything
      self.min_x = 0.
      self.max_x = dc.s_max if dc.s_max > 0 else 1.
      self.delta_x = 0.1
      self.params.n_divisions = 10
      self.draw_origin = True
      self.make_disp_radial_plot()
      self.popout()

    def make_disp_radial_plot(self):
      import numpy as np
      self.x = flex.double(STEPS)
      xs_values = np.linspace(self.min_x, self.max_x, STEPS)
      for i, v in enumerate(xs_values):
        self.x[i] = v
      self.metadata.setdefault(
        "x_label", IT.get_unicode_characters("stol (1/Angstrom)"))
      self.metadata.setdefault("y_label", "f' / f'' (electrons)")

      keys = []
      colours = []
      flat = []
      min_y, max_y = 0., 0.
      for n, (name, element, fp, fdp) in enumerate(details):
        col = _colour_for(element, IT)
        colours.append(col)
        y_fp = flex.double(STEPS)
        y_fdp = flex.double(STEPS)
        for i, s in enumerate(xs_values):
          # R is a function of d*^2, and s = sqrt(d*^2)/2
          r = dc.R_at(4*s*s, n)
          y_fp[i] = fp*r
          y_fdp[i] = fdp*r
          min_y = min(min_y, y_fp[i], y_fdp[i])
          max_y = max(max_y, y_fp[i], y_fdp[i])
        min_y = min(min_y, fp, fdp)
        max_y = max(max_y, fp, fdp)
        self.data.setdefault(name + " fp", Dataset(self.x, y_fp))
        self.data.setdefault(name + " fdp", Dataset(self.x, y_fdp))
        flat.append((fp, fdp, col))
        keys.append({'type': 'function',
                     'number': n + 1,
                     'label': name,
                     'colour': col})
      span = max(max_y - min_y, 1e-3)
      self.min_y = min_y - 0.1*span
      self.max_y = max_y + 0.1*span

      self.graphInfo["Title"] = OV.TranslatePhrase(
        "Refined radial dependence of f' and f''")
      self.make_empty_graph(axis_x=True, square=False)
      self.ax_marker_length = int(self.imX * 0.006)

      self.get_division_spacings_and_scale()
      self.draw_x_axis()
      self.draw_y_axis()

      # what f' and f'' were before the refinement gave them a shape: flat.
      # No rotate_text here, unlike the vertical wavelength markers in
      # AnomDispPlot: rotated labels are placed at the top left of the graph
      # regardless of the line, which suits a vertical line and would stack
      # every one of these in the same corner. Unrotated, the label sits at
      # the left end of its own line, at its own height.
      for n, (fp, fdp, col) in enumerate(flat):
        for value, label in ((fp, "f'"), (fdp, "f''")):
          self.draw_fit_line(slope=0,
                             y_intercept=value,
                             write_equation=False,
                             write_text="%s %s" % (details[n][0], label),
                             width=1,
                             colour=col)

      key = self.draw_key(tuple(keys))
      self.im.paste(key,
                    (int(self.graph_right - (key.size[0] + 10 * self.scale)),
                     int(self.graph_top + 12 * self.scale)))
      # f' then f'' of each group, so a group keeps one colour throughout
      for i, data in enumerate(self.data.values()):
        self.plot_data_points(data.xy_pairs(), width=2,
                              colour=colours[i//2])

  DispRadialPlot()
