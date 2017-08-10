# Reflection File 
Olex2 will manage the reflection file against which you want to refine your model. Select the file from the drop-down menu and this is the file that will be used. 

# Reflection Graph 
These diagnosic graphs can be very useful when you run into problems with your structure. Please note that some of the graphs available from here are purely a function of the diffraction data, while other's take your model into account. The header 'Reflection Statistics' is therefore not strictly-speaking true -- but calling it only 'Statistics' doesn't seem quite right either!

## Wilson Plot 
A statistical comparison of the observed intensity data with the theoretical distribution for a random atomic arrangement, since the atomic scattering decreases with increasing 2Θ. Establishes an overall displacement parameter for the structure, B and scale factor for the data, k.

## Cumulative Intensity
Provides an indication of whether the data is centric or acentric.

## Systematic Absences
This plots the intensity distribution for any reflections that should be systematically absent. The intensities of these reflections should be very low and insignificant considering the error of the reflection.

## Fobs-Fcalc
This should be a straight line with Fobs about equal to Fcalc, i.e.the gradient of the line should be about 1 and the intercept at about 0. Any omitted data are shown in grey. If a reflection appears to be an outlier hovering over it gives relevant information in the following format (Fobs, Fcalc)(h, k, l).

## Fobs/Fcalc
Plotted against resolution should be around 1.0.

## Completeness
Plots the percentage completeness against the resolution. For good data this should be about 100% complete in all regions.

## Normal probability
This plots the ordered weighted deviations, w(Fobs^2 - k * Fcalc^2), against the deviations that would be expected if the errors in the data are normally distributed. If the errors are truly normally distributed, then this plot should be linear with a slope of one and zero intercept. Significant departures from this ideal may indicate problems with your datatset, model, or weighting scheme.

## Scale factor vs resolution
These should be approximately constant around 1.0 across the whole data range, a low value at high values of 2Θ can indicate that the data is weak or not present in that region.

## R1 factor vs resolution
This value will increase for higher angle data. If there are any sudden changes, this can indicate problems with your data.

## Bijvoet Differences Probability Plot 
Similarly to the 'Normal probability' plot above, this plots the ordered deviations between the observed and calculated Bijvoet differences. Frequently it is observed that this plot can deviate from linearity, suggesting that the errors are not normally distributed. Hooft et. al (2010) suggested that a Student's 't' distribution may better describe the errors in the Bijvoet differences. Olex2 can calculate this plot for both the normal and Student's 't' distribution, allowing you to judge whether or not a Student's 't' distribution is a better model for the errors in your data.

## Bijvoet Differences Scatter Plot 
This plots the calculated Bijvoet differences, Fcalc^2(+) - Fcalc^2(-), against the observed Bijvoet differences, Fobs^2(+) - Fobs^2(-), along with error bars indicating the uncertainty in the measurement of the Bijvoet differences. For a correct, strongly determined absolute structure, this plot should form a positive slope, with gradient close to 1. A negative slope for this plot can indicate incorrect assignment of the absolute structure, and you should try inverting your structure (`inv -f`). 
