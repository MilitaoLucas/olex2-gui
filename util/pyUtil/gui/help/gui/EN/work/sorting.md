# Sort Order
Sort atoms in the structure according to the categories shown in the drop-down menus. Atoms are sorted starting with the left-most category, then by further sub-categories proceeding to the right. For example, suppose the first category is **Part**, the second **Z**, the third **Label**, and the fourth **Suffix**. When the **Sort** button is clicked, the atoms will be sorted according to increasing PART number first, then according to decreasing atomic number *Z*, then according to increasing label number, and finally according to increasing suffix.

Note: Any hydrogen atoms attached to other atoms will be sorted along with the atoms to which they are attached.


# Moiety
If **None** is selected in the **Moiety** drop-down menu, all atoms in the structure will be sorted regardless of which fragment they are in, according to the categories chosen in **Sort Order**. If a category is chosen here, all fragments composing the structure will first be sorted based on the chosen category, after which atoms will be sorted within each moiety according to the **Sort Order** categories. For example, suppose a structure has two fragments, one large and one small, and **Size** is selected from the moiety drop-down menu. When the **Sort** button is clicked, the atoms in the large fragment will be listed first in sort order, followed by the atoms in the small fragment, also in sort order.


# Specific Order
When the **Sort** button is clicked, atoms in the structure will be sorted according to the order specified in these boxes.
