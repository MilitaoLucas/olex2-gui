#DispRadial
f' and f'' are stored as constants and enter Fc unchanged at every scattering angle, while f0 decays. This tool gives them a decay of their own, the same one for both, refined with the structure:

f'(u) = f' R(u), f''(u) = f'' R(u), R(u) = 1 + c<sub>1</sub>u + c<sub>2</sub>u<sup>2</sup> + ...

u is 1 - cos 2&theta;, or sin(&theta;)/&lambda; with **spy.disprad.setup basis=stol**. A polynomial in cos 2&theta; is a polynomial in the *even* powers of sin(&theta;)/&lambda; only, so the default restricts the model to the physical family and makes the correction turn on quadratically from forward scattering.

There is no constant term: it would be exactly degenerate with f' itself. R(0) = 1, so the tabulated values stand untouched at forward scattering. Twinned data is refused.

#DispRadial Groups
##Element
Pick an element and tick **Correct** to give it its own R(u). One group per element; one group per *atom* is command line only:

**spy.disprad.setup atoms=Pd1 n=1**

##Terms
The number of coefficients in R(u). Start with 1.

#DispRadial Buttons
##Refine
Refine the coefficients with the structure. They start at zero, where nothing has changed. They correlate strongly with U of the same atoms, and with f' and f'' where those are refined too: treat a large correction with suspicion. R is held above 0.1 over the measured resolution range.

##Dispersion Plot
The tabulated constants and the refined curves against sin(&theta;)/&lambda;.

##Report
The coefficients and what they do to R, in the console. Same as **spy.disprad.print_current**.

##Off
Switch the correction off and forget the coefficients.

#DispRadial Table
The current coefficients per group. Values put in by hand stand until you change them; refined values are reused as a starting point only while they still match the model they came from. Holding one group while another refines is command line only:

**spy.disprad.set group=Pd c=-1.8,2.0 fix=True**
