#  Reflection File
It is possible to specify in Olex2 the particular reflection file against which the model is to be refined.

## hkl File
Select the .hkl file to be used for refinement from the drop-down menu.

## Write Graphics File?
Tick this box to save the reflection statistics graphs generated from the drop-down menu below. Graphs will be saved as .png files in the current working folder for the structure.


# Reflection Graph
The graphs in this menu are meant to diagnose problems in structure determination. Some of the graphs depend only on the diffraction data, while others depend on the structure model, so it is not strictly accurate to call this tool tab **Reflection Statistics**.
<br>
<br>

Select from the drop-down menu the type of graph desired, then click the **go** button to display the graph. For these graphs, increasing the number of **Bins** creates a more fine-grained plot by dividing the reflections into more data bins, and ticking the **Output csv** box writes a text file in .csv format with the data for the current graph to the working folder. When a graph plots resolution along the *x*-axis, the measure of resolution may be 2&theta;, *d* spacing, square of the reciprocal lattice spacing *d*\*, sin(&theta;)/&lambda;, or (sin(&theta;)/&lambda;)<sup>2</sup>, selected from the drop-down menu. Ticking the **Write graphics file?** box above will save a .png file of the graph in the working folder.

## Wilson Plot
This plot provides a statistical comparison of the observed intensity data with the theoretical distribution expected for a random atomic arrangement, taking into account that atomic scattering decreases with increasing 2&theta;. It is usually linear. The overall displacement parameter *B* for the structure and scale factor *K* for the data are derived from this plot. The <|*E*<sup>2</sup> - 1|> statistic shown below the plot helps distinguish between centrosymmetric (centric) and non-centrosymmetric (acentric) structures. If <|*E*<sup>2</sup> - 1|> &asymp; 0.968, the structure is likely to be centrosymmetric, but if it is closer to 0.736, the structure is likely non-centrosymmetric. Choose either the built-in Olex2 method or the URL[https://cci.lbl.gov/docs/cctbx/,cctbx] method.

## Cumulative Intensity
This graph assists in determining whether the structure is centrosymmetric or non-centrosymmetric. If the plotted data lie mostly along the top black line, the structure is likely to be centrosymmetric; if along the middle blue line, the structure is likely non-centrosymmetric. Finally, if the data lie along the bottom red line, it is likely that the structure is non-centrosymmetric and twinned.

## Systematic Absences
This plots the intensity distribution for any reflections that are expected to be systematically absent. The intensities of these reflections should be very low and insignificant relative to the standard error of each reflection.

## Fobs-Fcalc
This plot of Fobs vs Fcalc is normally a straight line with Fobs about equal to Fcalc throughout their range, i.e., the slope of the line should be about 1 and the intercept about 0. Any omitted reflections are shown in grey. Hovering over a yellow reflection with a mouse shows a readout in the format "OMIT h k l". If the reflection is clicked, an **OMIT** instruction is added to the instruction file for that reflection, and it turns grey. This is useful for removing an outlying reflection from the refinement, e.g., if the reflection is obscured by the beamstop. Clicking on a grey reflection removes its **OMIT** instruction and reintroduces it into the refinement. 
<br>
<br>

If the plot exhibits marked downward curvature at high Fcalc, it may be necessary to apply an extinction correction by ticking the **EXTI** box in the **Refine** tool panel and refining the model again.

## I/sigma vs resolution
The quality of the diffraction data may be evaluated with this graph. I/&sigma; is plotted as the larger green and red squares (green if I/&sigma; &ge; 3&sigma;, red otherwise) and the cumulative number of unique reflections is plotted as the smaller grey squares. It is, of course, desirable to have high I/&sigma; out to high 2&theta;. However, in practice, it is optimal to have I/&sigma; > 3 at least out to the 2&theta; value recommended by the IUCr, in order to ensure that the structure can be determined at an accepted minimum resolution.

## cc half vs resolution
This graph plots the Pearson's correlation coefficient between random half data sets, CC<sub>1/2</sub>, as a function of resolution. Essentially, this method tests how well one half of the data predicts the other half, and constitutes a measure of the "resolution" of the data set as a whole. The coefficient CC<sub>1/2</sub> is generally close to 1 at low resolution (low 2&theta;) and tapers off somewhat at high resolution (high 2&theta;).

## Rmerge vs resolution
Rmerge measures how well multiple measurements of the same reflection agree. Rmerge is plotted as the larger green and red squares (green if Rmerge &le; 0.15, red otherwise) and the cumulative number of unique reflections is plotted as the smaller grey squares. Data corresponding to an Rmerge above 0.15 are considered of questionable value. It is optimal to collect data with an Rmerge < 0.15 out to at least the IUCr-recommended resolution limit.

## Fobs over Fcalc
Ideally, Fcalc ought to be as close as possible to Fobs at the conclusion of refinement, i.e., their ratio is expected to be close to unity. Therefore, this ratio plotted here as a function of resolution is expected to be close to 1 throughout, though deviations may be observed at high resolution. To prevent division of the diffraction into data bins and plot Fobs/Fcalc for individual reflections, untick the **Binning** box.

## Completeness
Plots percent completeness (Laue completeness and point group completeness) of the diffraction data against resolution. Good data will show nearly 100% completeness over the entire resolution range.

## Normal probability
This plots the ordered weighted deviations, w(Fobs<sup>2</sup> - k * Fcalc<sup>2</sup>), against the deviations that would be expected if the errors in the data were normally distributed. If the errors are in fact normally distributed, this plot will be linear with slope 1 and intercept 0. Significant departures from this ideal may indicate problems with the diffraction data, model, or weighting scheme.

## Fractal dimension
This plot ideally appears as a symmetric, inverted parabola, but noise in the data or systematic errors cause deviations from this parabolic shape. The narrower the curve, the flatter the residual electron density distribution; minimum and maximum values of the residual electron density appear as the left and right *x*-intercepts of the plot, respectively. For more information on this plot, see K. Meindl & J. Henn, Acta Cryst. A64, 404 (2008).

Note: This plot takes a little longer to generate than the others.

## Scale factor vs resolution
The scale factor should be approximately constant at 1 across the whole data range if the diffraction data are good. A low value of the scale factor at high values of 2&theta; may indicate that high-angle data are weak or absent.

## R1 factor vs resolution
The value of R1 increases gradually with increasing 2&theta;. Sudden changes in R1 indicate problems with the diffraction data.

## Bijvoet Differences Probability Plot
This is a plot of the deviations in the observed vs calculated Bijvoet differences, analogous to the **Normal probability** plot above. This plot frequently deviates from linearity, indicating that the experimental errors are not normally distributed. Hooft et al. (J. Appl. Cryst. 43, 665 (2010)) have suggested that a Student's "t" distribution may better describe the errors in the Bijvoet differences, especially if the data quality is poor. By default, the plot is generated assuming that the errors obey a normal (Gaussian) distribution. Tick the **Student's t** box to redraw the plot using the Student's "t" distribution instead. A comparison of the two types of plots allows the determination of the most appropriate distribution for the errors in the data.

## Bijvoet Differences Scatter Plot
The observed Bijvoet differences, &Delta;Fobs<sup>2</sup> = Fobs<sup>2</sup>(+) - Fobs<sup>2</sup>(-), are plotted here against the calculated Bijvoet differences &Delta;Fcalc<sup>2</sup> = Fcalc<sup>2</sup>(+) - Fcalc<sup>2</sup>(-), with error bars indicating the uncertainty in the observed Bijvoet differences. For a correctly determined absolute structure, this graph has a positive slope close to 1. As with the **Bijvoet Differences Probability Plot** above, the graph can be created using either the normal distribution (default) or the Student's "t" distribution (by ticking the **Student's t** box). A negative slope for this plot may indicate incorrect assignment of the absolute structure, which may need to be inverted with the following command:

| `inv -f` | Invert the current structure (the '<c>-f</c>' switch forces the inversion). |
