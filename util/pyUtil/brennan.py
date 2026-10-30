import math
import elemental_data as dat


def sort(n, a, b):
    for i in range(n):
        for j in range(i + 1, n):
            if a[j] < a[i]:
                x = a[j]
                y = a[i]
                a[i] = x
                a[j] = y
                x = b[j]
                y = b[i]
                b[i] = x
                b[j] = y


def lgndr(index):
    x = [0.04691007703067, 0.23076534494716]
    a = [0.11846344252810, 0.23931433524968, 0.28444444444444]
    cc = 0.5
    switch = True
    ip = index
    if ip > 2:
        ip = 4 - ip
        switch = False
    if ip == 2:
        return [a[2], 0.5]
    if switch:
        cc = x[ip]
    else:
        cc = 1.0 - x[ip]
    return [a[ip], cc]


def sigma0(x, xsect_barns, bind_nrg_au, xsect_int, energy_au, icount):
    prod = energy_au**2 * x**2 - bind_nrg_au**2
    if abs(prod) < 1e-30:
        return xsect_int[icount] * bind_nrg_au / math.pow(x, 2)
    else:
        return (xsect_int[icount] * math.pow(bind_nrg_au, 3) / math.pow(x, 2) - bind_nrg_au * xsect_barns * math.pow(energy_au, 2)) / prod


def sigma1(x, bind_nrg_au, xsect_int, energy_au, icount):
    return 0.5 * xsect_int[icount] * math.pow(bind_nrg_au, 3) / (math.sqrt(x) * (math.pow(energy_au, 2) * math.pow(x, 2) - math.pow(bind_nrg_au, 2) * x))


def sigma2(x, xsect_barns, bind_nrg_au, xsect_int, energy_au, icount):
    result = 0.0
    if abs(x) < 1e-31:
        pass
    elif energy_au < 1e-31:
        pass
    elif abs(xsect_int[icount] - xsect_barns) < 1e-31:
        result = -2.0 * xsect_int[icount] * bind_nrg_au / (x**3)
    else:
        x3 = math.pow(x, 3)
        denom = x3 * math.pow(energy_au, 2) - (math.pow(bind_nrg_au, 2) / x)
        if abs(denom) < 1e-31:
            result = -2.0 * xsect_int[icount] * bind_nrg_au / x3
        else:
            result = 2.0 * (xsect_int[icount] * math.pow(bind_nrg_au / x, 3) / x - bind_nrg_au * xsect_barns * math.pow(energy_au, 2)) / denom
    return result


def sigma3(x, bind_nrg_au, xsect_int, energy_au, xsect_edge_au, icount):
    x2 = math.pow(x, 2)
    return math.pow(bind_nrg_au, 3) * (xsect_int[icount] - xsect_edge_au * x2) / (x2 * (x2 * math.pow(energy_au, 2) - math.pow(bind_nrg_au, 2)))


def gauss(sigma, xsect_barns, bind_nrg_au, xsect_int, energy_au, xsect_edge_au):
    resultat = 0.0
    for i in range(5):
        bb, cc = lgndr(i)
        if sigma == 0:
            dd = sigma0(cc, xsect_barns, bind_nrg_au, xsect_int, energy_au, 4 - i)
        elif sigma == 1:
            dd = sigma1(cc, bind_nrg_au, xsect_int, energy_au, 4 - i)
        elif sigma == 2:
            dd = sigma2(cc, xsect_barns, bind_nrg_au, xsect_int, energy_au, 4 - i)
        elif sigma == 3:
            dd = sigma3(cc, bind_nrg_au, xsect_int, energy_au, xsect_edge_au, 4 - i)
        resultat += bb * dd
    return resultat


def mcm(z, energy):
    barns2electron = 1.43110541e-8
    p1 = math.log(energy)
    p2 = p1 * p1
    p3 = p1 * p1 * p1
    fp = 0.0
    fpp = 0.0

    if z == 1:
        if energy >= 14e-6:
            fpp = barns2electron * energy * 1000 * math.exp(2.44964 - 3.34953 * p1 - 0.047137 * p2 + 0.0070996 * p3)
        else:
            fpp = 0.0
    else:
        if energy >= 25e-6:
            fpp = barns2electron * energy * 1000 * math.exp(6.06488 - 3.2905 * p1 - 0.107256 * p2 + 0.0144465 * p3)
        else:
            fpp = 0.0
    return [fp, fpp]


def aknint(log_energy, n, log_nrg, log_xsect):
    index = 0
    if n <= 1:
        return log_xsect[0]
    d = log_nrg[1] - log_nrg[0]
    if d > 0.0:
        i = 0
        while i <= n and log_nrg[i] < log_energy:
            index = i
            i += 1
    else:
        i = 1
        while log_nrg[i] > log_energy and i <= n:
            index = i
            i += 1
    index = min(max(index - 1, 0), n - 2)
    mend = index + 2
    t = [0.0] * 20
    kk = 0
    for i in range(index, mend + 1):
        kk = i - index
        t[kk] = log_xsect[i]
        t[kk + 3] = log_nrg[i] - log_energy
    for i in range(2):
        kk = i + 1
        for j in range(kk, 3):
            t[j] = (t[i] * t[j + 3] - t[j] * t[i + 3]) / (log_nrg[j + index] - log_nrg[i + index])
    return t[2]


class brennan:
    def __init__(self):
        pass

    def table(self, element):
        return brenan_element_table(self, element)

    def at_angstrom(self, wavelength, element):
        """Generates the dispersion correction coefficients f' and f'' at a given wavelength for a given elemnt symbol

        Args:
            wavelength (float): Wavelength for which computation shoudl be carried out in Angstrom
            element (string): Element symbol of the periodic table

        Returns:
            [float,float]: f' and f'' values calculated
        """
        z = dat.elements.index(element)
        energy = dat.angstrom2eV / wavelength / 1000  # convert wavelength to keV(division by 1000)
        log_energy = math.log(energy)
        energy_au = energy / dat.keV_per_hartree  # convert energy to a.u. through divison of keV per hartree
        result = [0.0, 0.0]
        if z < 3:
            result = mcm(z, energy)
            result[0] += dat.total_cor[z]
            return result
        if z > 92:
            if z > 103:
                raise ValueError("Element beyond Lr not supported")
            print("WARNING!!!! The values of Elements beyond Uranium are extrapolated by Florian K. and Florian M., proceed with caution")

        for i in range(dat.n_orb[z]):
            fpp_orb = 0.0
            fp_corr = 0.0
            fp_orb = 0.0
            xsect_barns = 0.0
            nparms = 0
            xsect_edge_au = 0.0
            xsect_int = [0] * 5
            xsect_s = [0] * 11
            log_xsect = [0] * 11
            nrg_int = [0] * 5
            nrg_s = [0] * 11
            log_nrg = [0] * 11

            bind_nrg_au = dat.bind_nrg[z][i] / dat.keV_per_hartree
            if dat.funtype[z][i] == 0:
                xsect_edge_au = dat.xsc[z][i][10] / dat.au
                nparms = 11
            else:
                nparms = 10
            for j in range(5):
                xsect_int[j] = dat.xsc[z][i][j + 5] / dat.au
                nrg_int[j] = dat.nrg[z][i][j]
                nrg_s[j] = dat.nrg[0][0][j]
            for j in range(nparms):
                xsect_s[j] = dat.xsc[z][i][j]
                if j > 4:
                    nrg_s[j] = dat.nrg[z][i][j - 5]

            sort(nparms, nrg_s, xsect_s)
            sort(5, nrg_int, xsect_int)

            for j in range(nparms):
                log_nrg[j] = math.log(nrg_s[j])
                if xsect_s[j] == 0.0:
                    log_xsect[j] = 0.0
                else:
                    log_xsect[j] = math.log(xsect_s[j])

            if dat.bind_nrg[z][i] <= energy:
                i_zero = 0
                while log_xsect[i_zero] == 0.0:
                    i_zero += 1
                i_nxsect = nparms - i_zero - 1
                xsect_barns = aknint(log_energy, i_nxsect, log_nrg[i_zero:], log_xsect[i_zero:])
                xsect_barns = math.exp(xsect_barns) / dat.au

                fpp_orb = dat.inv_fine_struct * xsect_barns * energy_au  # took /4pi to the top in inv_fine_struct

                var = energy_au - bind_nrg_au
                if var == 0.0:
                    var = 1.0
                fp_corr = -0.5 * xsect_barns * energy_au * dat.fine_pi * math.log((energy_au + bind_nrg_au) / var)

            if dat.bind_nrg[z][i] > energy and dat.funtype[z][i] == 0:
                fp_orb = gauss(3, xsect_barns, bind_nrg_au, xsect_int, energy_au, xsect_edge_au) * dat.fine_pi
                fp_corr = 0.5 * xsect_edge_au * bind_nrg_au * bind_nrg_au * math.log((-bind_nrg_au + energy_au) / (-bind_nrg_au - energy_au)) / energy_au * dat.fine_pi
            else:
                fp_orb = gauss(dat.funtype[z][i], xsect_barns, bind_nrg_au, xsect_int, energy_au, 0.0) * dat.fine_pi

            result[0] += fp_orb + fp_corr
            result[1] += fpp_orb
            # print(
            #   "Orbital: "
            #   + "{:2d}".format(i)
            #   + "/"
            #   + "{:1d}".format(dat.funtype[z][i])
            #   + " fp,fdp:"
            #   + "{:16.8e}".format(result[0])
            #   + "{:16.8e}".format(result[1])
            #   + " this Orbital:"
            #   + "{:16.8e}".format(fp_orb + fp_corr)
            #   + "{:16.8e}".format(fpp_orb)
            #   + " ORB/CORR Part:"
            #   + "{:16.8e}".format(fp_orb)
            #   + "{:16.8e}".format(fp_corr)
            # )

        result[0] += dat.total_cor[z]
        # print("Fprime corr:" + "{:25.8e}".format(dat.total_cor[z]))

        return result

    def get_mu_at_angstrom(self, wavelength, element):
        """Generates linear absorption coefficient mu at a given wavelength

        Args:
            wavelength (float): wavlenegth in Angstrom of incident beam for which the calcualtion is carried out
            element (string): Element symbol in the periodic table

        Returns:
            mu (float): Linear absorption coefficient in barns/Atom
        """
        fp, fdp = self.at_angstrom(wavelength, element)
        mu = self.convert_fdp_to_mu(wavelength, fdp, element)
        return mu

    def get_mu_pure_at_angstrom(self, wavelength, element):
        """Generates linear absorption coefficient mu at a given wavelength without ray and comp contributions

        Args:
            wavelength (float): wavlenegth in Angstrom of incident beam for which the calcualtion is carried out
            element (string): Element symbol in the periodic table

        Returns:
            mu (float): Linear absorption coefficient in barns/Atom
        """
        fp, fdp = self.at_angstrom(wavelength, element)
        energy = dat.angstrom2eV / wavelength
        mu = fdp / (energy * dat.barns_to_electrons)
        return mu

    def fp_fdp_mu_at_angstrom(self, wavelength, element):
        """Generates f' f'' and linear absorption coefficient mu at a given wavelength

        Args:
            wavelength (float): wavlenegth in Angstrom of incident beam for which the calcualtion is carried out
            element (string): Element symbol in the periodic table

        Returns:
            [fp,fdp,mu] (float): f', f" in electrons and Linear absorption coefficient mu in barns/Atom
        """
        fp, fdp = self.at_angstrom(wavelength, element)
        mu = self.convert_fdp_to_mu(wavelength, fdp, element)
        return [fp, fdp, mu]

    def print_at_angstrom(self, wavelength, element):
        """Generates linear absorption coefficient mu at a given wavelength

        Args:
            wavelength (float): wavlenegth in Angstrom of incident beam for which the calcualtion is carried out
            element (string): Element symbol in the periodic table
        """
        fp, fdp = self.at_angstrom(wavelength, element)
        mu = self.get_mu_at_angstrom(wavelength, fdp, element)
        print(f"{fp:16.7f} {fdp:16.7f} {mu:16.7f}")

    def get_ray_at_angstrom_in_electrons(self, wl, element):
        """Generates Rayleigh Scattering contribution at given wavelength

        Args:
            wl (float): incoming wavelength in angstrom
            element (string): element symbol

        Returns:
            ray: Rayghleigh scattering contribution in electrons
        """
        z = dat.elements.index(element) - 1
        energy = dat.angstrom2eV / wl
        l_energy = math.log(energy / 1000)
        l_energy2 = l_energy * l_energy
        l_energy3 = l_energy2 * l_energy
        if z > 91:
            return self.get_ray_at_angstrom_in_electrons(wl, dat.elements[92])
        ray = math.exp(dat.ray[z * 4] + dat.ray[z * 4 + 1] * l_energy + dat.ray[z * 4 + 2] * l_energy2 + dat.ray[z * 4 + 3] * l_energy3)
        return ray * energy * dat.barns_to_electrons

    def get_comp_at_angstrom_in_electrons(self, wl, element):
        """Generates Compton Scattering contribution at given wavelength

        Args:
            wl (float): incoming wavelength in angstrom
            element (string): element symbol

        Returns:
            comp: compton scattering contribution in electrons
        """
        z = dat.elements.index(element) - 1
        energy = dat.angstrom2eV / wl
        l_energy = math.log(energy / 1000)
        l_energy2 = l_energy * l_energy
        l_energy3 = l_energy2 * l_energy
        if z > 91:
            return self.get_comp_at_angstrom_in_electrons(wl, dat.elements[92])
        comp = math.exp(dat.comp[z * 4] + dat.comp[z * 4 + 1] * l_energy + dat.comp[z * 4 + 2] * l_energy2 + dat.comp[z * 4 + 3] * l_energy3)
        return comp * energy * dat.barns_to_electrons

    def get_raycomp_at_angstrom(self, wl, element):
        """Generates a list of Rayleigh and Compton scattering contribution at a given wavelength in Angstrom for a given element

        Args:
            wl (float): Wavelength of incoming X-ray in Angstrom
            element (string): Label of the element

        Returns:
            [ray,comp]: reayleigh and compton scattering power in barns/atom
        """

        z = dat.elements.index(element) - 1
        energy = dat.angstrom2eV / wl
        l_energy = math.log(energy / 1000)
        l_energy2 = l_energy * l_energy
        l_energy3 = l_energy2 * l_energy
        if z > 91:
            return self.get_raycomp_at_angstrom(wl, dat.elements[92])
        comp = math.exp(dat.comp[z * 4] + dat.comp[z * 4 + 1] * l_energy + dat.comp[z * 4 + 2] * l_energy2 + dat.comp[z * 4 + 3] * l_energy3)
        ray = math.exp(dat.ray[z * 4] + dat.ray[z * 4 + 1] * l_energy + dat.ray[z * 4 + 2] * l_energy2 + dat.ray[z * 4 + 3] * l_energy3)
        return [ray, comp]

    def convert_fdp_to_mu(self, wavelength, fdp, element):
        """Generates Mu from given fdp at given wavelength

        Args:
            wavelength (float): wavlenegth in Angstrom of incident beam for which the calcualtion is carried out
            fdp (float): value of f'' at the given wavelength
            element (string): Element symbol in the periodic table

        Returns:
            mu (float): Linear absorption coefficient in barns/Atom
        """
        energy = dat.angstrom2eV / wavelength
        ray, comp = self.get_raycomp_at_angstrom(wavelength, element)
        mu = fdp / (energy * dat.barns_to_electrons) + ray + comp
        return mu


## cctbx-like interface
class brenan_element_table:
    class adapter:
        def __init__(self, fp_fdp, mu):
            self.value = fp_fdp
            self.mu = mu

        def fp(self):
            return self.value[0]

        def fdp(self):
            return self.value[1]

        def mu(self):
            return self.mu

    def __init__(self, brennan_inst, element):
        self.brennan_inst = brennan_inst
        self.element = element

    def at_angstrom(self, wavelength):
        res = self.brennan_inst.fp_fdp_mu_at_angstrom(wavelength, self.element)
        return brenan_element_table.adapter((res[0], res[1]), res[2])

    def mu_at_angstrom(self, wavelength):
        return brenan_element_table.adapter((0, 0), self.brennan_inst.get_mu_at_angstrom(wavelength, self.element))

    def fdp_to_mu(self, wavelength, fdp):
        return brenan_element_table.adapter((0, 0), self.brennan_inst.convert_fdp_to_mu(wavelength, fdp, self.element))
