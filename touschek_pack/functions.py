"""Functions_for_TousAnalysis."""
import pyaccel as _pyaccel
import matplotlib.pyplot as _plt
import numpy as _np
import scipy.integrate as _scyint
import scipy.special as _special
from mathphys.beam_optics import beam_rigidity as _beam_rigidity


def calc_amp(acc, energy_offsets, hmax, hmin):
    """Calculates the amplitudes and gets the physical limitants.

    acc            =                                 accelerator model.
    energy_offsets = energy deviation for calculate physical limitants.
    hmax           =                          horizontal max apperture.
    hmin           =                          horizontal min apperture.
    """
    a_def = _np.zeros(energy_offsets.size)
    indices = _np.zeros(energy_offsets.size)
    try:
        for idx, delta in enumerate(energy_offsets):
            twi, *_ = _pyaccel.optics.calc_twiss(
                accelerator=acc, energy_offset=delta, indices="closed"
            )
            if _np.any(_np.isnan(twi[0].betax)):
                raise _pyaccel.optics.OpticsException("error")
            rx = twi.rx
            betax = twi.betax

            a_sup = (hmax - rx) ** 2 / betax
            a_inf = (hmin - rx) ** 2 / betax

            a_max = _np.minimum(a_sup, a_inf)
            idx_min = _np.argmin(a_max)
            indices[idx] = idx_min
            a_def[idx] = a_max[idx_min]
    except (
        _pyaccel.optics.OpticsException,
        _pyaccel.tracking.TrackingException,
    ):
        pass
    return _np.sqrt(a_def), indices

def track_eletrons_d(
    deltas, n_turn, element_idx, model, pos_x=1e-5, pos_y=3e-6
):
    """Tracking simulation for touschek scattering that ocorred in element_idx.

    model  =       accelerator model.
    deltas =        energy deviation.
    n_turn = number of turns desired.
    pos_x  =  small pertubation in x.
    pos_y  =  small pertubation in y.
    """
    orb = _pyaccel.tracking.find_orbit6(model, indices=[0, element_idx])
    orb = orb[:, 1]

    rin = _np.zeros((6, deltas.size))
    rin += orb[:, None]
    rin[0] += pos_x
    rin[2] += pos_y
    rin[4] += deltas

    track = _pyaccel.tracking.ring_pass(
        model,
        rin,
        nr_turns=n_turn,
        turn_by_turn=True,
        element_offset=element_idx,
        parallel=True,
    )

    _, _, turn_lost, element_lost, _ = track

    dic = {}
    t_lost, e_lost, delta = [], [], []

    for i, item in enumerate(turn_lost):
        if item == n_turn and element_lost[i] == element_idx:
            pass
        else:
            t_lost.append(item)
            e_lost.append(element_lost[i])
            delta.append(deltas[i])

    dic["turn_lost"] = _np.array(t_lost)
    dic["element_lost"] = _np.intp(e_lost)
    dic["energy_deviation"] = _np.array(delta)

    return dic


def plot_track_d(
    acc,
    dic_tracked,
    index_list,
    offs_list,
    par,
    element_idx,
    accep,
    delt,
    f_dens,
):
    """Plot the tracking results for a given s position.

    acc         =                                    accelerator model.
    dic_tracked =      dictionary of informations provided by tracking.
    index_list  =     defines the physical limitants from linear model.
    offs_list   =                       list of e_dev used in tracking.
    par         =  defines the analysis for positive or negative e_dev.
    element_idx =              defines initial conditions for tracking.
    accep       =                           touschek energy acceptance.
    delt        =  energy deviation for the touschek loss rate density.
    fdens       =                           touschek loss rate density.
    """
    # ----------------

    turn_lost = dic_tracked["turn_lost"]
    element_lost = dic_tracked["element_lost"]
    deltas = dic_tracked["energy_deviation"] * 1e2

    cm = 1 / 2.54  # 'poster'
    twi0, *_ = _pyaccel.optics.calc_twiss(acc, indices="open")
    betax = twi0.betax
    betax = betax * (1 / 5)
    spos = _pyaccel.lattice.find_spos(acc)

    fig = _plt.figure(figsize=(38.5 * cm, 18 * cm))
    gs = _plt.GridSpec(
        1,
        3,
        left=0.1,
        right=0.98,
        wspace=0.03,
        top=0.95,
        bottom=0.1,
        width_ratios=[2, 3, 8],
    )
    a1 = fig.add_subplot(gs[0, 0])
    a2 = fig.add_subplot(gs[0, 1], sharey=a1)
    a3 = fig.add_subplot(gs[0, 2], sharey=a1)
    a1.tick_params(axis="both", labelsize=18)
    a2.tick_params(
        axis="y",
        which="both",
        left=False,
        right=False,
        labelleft=False,
        labelsize=18,
    )
    a3.tick_params(
        axis="y",
        which="both",
        left=False,
        right=False,
        labelleft=False,
        labelsize=18,
    )
    a2.tick_params(axis="both", labelsize=18)
    a3.tick_params(axis="both", labelsize=18)
    a1.set_title(r"$\delta \times scat. rate$", fontsize=20)
    a2.set_title(r"$\delta \times$ lost turn", fontsize=20)
    a3.set_title(r"tracking ", fontsize=20)

    a1.set_xlabel(r"$\tau _T$ [1/s]", fontsize=25)
    a2.set_xlabel(r"number of turns", fontsize=25)
    a3.set_xlabel(r"$s$ [m]", fontsize=25)

    a1.grid(True, alpha=0.5, ls="--", color="k", axis="y")
    a2.grid(True, alpha=0.5, ls="--", color="k", axis="y")
    a3.grid(True, alpha=0.5, ls="--", color="k", axis="y")
    _plt.subplots_adjust(wspace=0.1)

    if "pos" in par:
        a1.set_ylabel(r"positive $\delta$ [%]", fontsize=25)
        a3.plot(spos[element_lost], deltas, "r.", label="lost pos. (track)")
        acp_s = accep[1][element_idx]
        indx = _np.argmin(_np.abs(offs_list - acp_s))
        a3.plot(
            spos[index_list][:indx],
            offs_list[:indx] * 1e2,
            "b.",
            label=r"accep. limit",
            alpha=0.25,
        )

    elif "neg" in par:
        a1.set_ylabel(r"negative $\delta$ [%]", fontsize=25)
        a3.plot(spos[element_lost], deltas, "r.", label="lost pos. (track)")
        acp_s = accep[0][element_idx]
        indx = _np.argmin(_np.abs(offs_list + acp_s))
        a3.plot(
            spos[index_list][:indx],
            -offs_list[:indx] * 1e2,
            "b.",
            label=r"accep. limit",
            alpha=0.25,
        )

    a1.plot(f_dens, delt, label="Scattering touschek rate", color="black")
    a2.plot(turn_lost, deltas, "k.")
    stri = f"{acc[element_idx].fam_name}, ({spos[element_idx]:.2f} m)"
    a3.plot(spos[element_idx], 0, "ko", label=stri)
    a3.plot(
        spos, _np.sqrt(betax), color="orange", label=r"$ \sqrt{\beta_x}  $"
    )
    _plt.hlines(
        acp_s * 1e2,
        spos[0],
        spos[-1],
        color="black",
        linestyles="dashed",
        alpha=0.5,
    )
    _pyaccel.graphics.draw_lattice(acc, offset=-0.5, height=0.5, gca=True)
    a3.legend(loc="upper right", ncol=1, fontsize=15)
    fig.show()


# def t_list(elmnt): # não sei se isso é útil
#     """."""
#     #this condition significates that if the input is only a number, then
#     #the fucntion transforms it into a list to avoid errors.
#     if isinstance(elmnt,(float,int)):
#         return [elmnt]
#     else:
#         return list(elmnt)


def f_function_arg_mod(kappa, kappam, b1_, b2_, norm):
    """Returns the touschek loss rate density.

    kappa  =            substitution that turns easier calculations.
    kappam = kappa minimum that defines the lower integration limit.
    b1_    =        optical parameter obtained by accelerator model.
    b2_    =        optical parameter obtained by accelerator model.
    norm   =    defines if the function will returns density or not.
    """
    tau = (_np.tan(kappa) ** 2)[:, None]
    taum = _np.tan(kappam) ** 2
    beta = _beam_rigidity(energy=3)[2]
    ratio = tau / taum / (1 + tau)
    arg = (2 * tau + 1) ** 2 * (ratio - 1) / tau
    arg += tau - _np.sqrt(tau * taum * (1 + tau))
    arg -= (2 + 1 / (2 * tau)) * _np.log(ratio)
    arg *= _np.sqrt(1 + tau)
    #     arg *= beta* _np.cos(kappa)[:, None]**2
    arg *= 1 / (2 * _np.sqrt(tau)) * 1 / (1 + tau)
    arg *= 2 * beta * _np.sqrt(tau)

    bessel = _np.exp(-(b1_ - b2_) * tau) * _special.i0e(b2_ * tau)

    if norm:
        pass

    else:
        arg *= 2 * _np.sqrt(_np.pi * (b1_**2 - b2_**2)) * taum

    return arg * bessel


def get_scaccep(acc, accep):
    """Returns the s position and the energy acceptance every 10 cm.

    acc   = accelerator model used to acquire the optical parameters.
    accep =                  positive and negative energy acceptance.
    """
    spos = _pyaccel.lattice.find_spos(acc, indices="closed")

    npt = int((spos[-1] - spos[0]) / 0.1)
    scalc = _np.linspace(spos[0], spos[-1], npt)
    daccpp = _np.interp(scalc, spos, accep[1])
    daccpn = _np.interp(scalc, spos, accep[0])

    return scalc, daccpp, daccpn


# Como discutido no dia 23.08.2023 corte para a definição da densidade
# de espalhamento Touschek ocorre na aceitância de energia para deter
# minado ponto.


def norm_cutacp(acc, lsps, npt, accep, norm=False):
    """Plot loss rate for a list of s positions.

    acc   =  accelerator model used to acquire the optical parameters.
    lsps  =             list of s positions to calculate loss density.
    npt   =                      number of points to a linspace array.
    accep =                   positive and negative energy acceptance.
    norm  =   parameter to define if the function will return density.
    """
    dic = {}

    scalc, daccpp, daccpn = get_scaccep(acc, accep)
    beta = _beam_rigidity(energy=3)[2]

    taum_p = (beta * daccpp) ** 2
    taum_n = (beta * daccpn) ** 2
    kappam_p = _np.arctan(_np.sqrt(taum_p))
    kappam_n = _np.arctan(_np.sqrt(taum_n))

    ltime = _pyaccel.lifetime.Lifetime(acc)
    b1 = ltime.touschek_data["touschek_coeffs"]["b1"]
    b2 = ltime.touschek_data["touschek_coeffs"]["b2"]

    fdens_p, fdens_n = [], []
    deltasp, deltasn = [], []

    for _, s in enumerate(lsps):
        idx = _np.argmin(_np.abs(scalc - s))
        kappam_p0 = kappam_p[idx]
        kappam_n0 = kappam_n[idx]

        kappap = _np.linspace(kappam_p0, _np.pi / 2, npt)
        deltap = 1 / beta * _np.tan(kappap)
        kappan = _np.linspace(kappam_n0, _np.pi / 2, npt)
        deltan = 1 / beta * _np.tan(kappan)

        y_p = f_function_arg_mod(
            kappa=kappap, kappam=kappam_p0, b1_=b1[idx], b2_=b2[idx], norm=norm
        ).squeeze()
        y_n = f_function_arg_mod(
            kappa=kappan, kappam=kappam_n0, b1_=b1[idx], b2_=b2[idx], norm=norm
        ).squeeze()
        norm_facp = _scyint.trapz(y_p, deltap)
        norm_facn = _scyint.trapz(y_n, deltan)

        y_p /= norm_facp
        y_n /= norm_facn

        # eliminating the negative values from array
        indp = _np.where(y_p < 0)[0]
        indn = _np.where(y_n < 0)[0]
        y_p[indp] = 0
        y_n[indn] = 0

        fdens_p.append(y_p)
        fdens_n.append(y_n)
        deltasp.append(deltap)
        deltasn.append(deltan)

    fdens_p = _np.array(fdens_p)
    fdens_n = _np.array(fdens_n)
    deltasp = _np.array(deltasp)
    deltasn = _np.array(deltasn)

    dic["fdensp"] = fdens_p
    dic["fdensn"] = fdens_n
    dic["deltasp"] = deltasp
    dic["deltasn"] = deltasn

    return dic


def create_particles(cov_matrix, num_part):
    """Creates the beam to realize the Monte-Carlo simulation.

    cov_matrix = covariant matrix to generate beam distribution.
    num_part   =          particles' number for M.C. simulation.
    """
    # permute indices to change the order of the columns:
    # [rx, px, ry, py, de, dl]^T -> [px, py, de, rx, ry, dl]^T
    idcs = [1, 3, 4, 0, 2, 5]
    # [px, py, de, rx, ry, dl]^T -> [rx, px, ry, py, de, dl]^T
    idcs_r = [3, 0, 4, 1, 2, 5]

    cov_matrix = cov_matrix[:, idcs][idcs, :]

    sig_xx = cov_matrix[:3, :3]
    sig_xy = cov_matrix[:3, 3:]
    sig_yx = cov_matrix[3:, :3]
    sig_yy = cov_matrix[3:, 3:]
    inv_yy = _np.linalg.inv(sig_yy)

    part1 = _np.random.Generator.multivariate_normal(
        _np.zeros(6), cov_matrix, num_part
    ).T

    part2 = part1.copy()

    vec_a = part2[3:]
    new_mean = (sig_xy @ inv_yy) @ vec_a
    new_cov = sig_xx - sig_xy @ inv_yy @ sig_yx

    part2[:3] = _np.random.Generator.multivariate_normal(
        _np.zeros(3), new_cov, num_part
    ).T
    part2[:3] += new_mean

    part2 = part2[idcs_r, :]
    part1 = part1[idcs_r, :]

    return part1, part2


def get_cross_section_distribution(psim, npts=3000):
    """Calculates the Moller's cross section.

    psim = minimum scattering angle (lower integration limitant).
    npts =               number of point for a logspace function.

    if beta_bar equals zero then the total cross section diverges when using
    piwinski's relation for the total cross section by the 1/beta_bar
    dependence. Therefore, is necessary to neglect this factor contribution.
    """
    beta_bar = 0
    psi = _np.logspace(_np.log10(_np.pi / 2 - psim), 0, npts)
    psi = _np.pi / 2 - psi
    psi = psi[::-1]
    cpsi = _np.cos(psi)
    cross = _np.zeros(cpsi.size)
    if beta_bar > 1e-19:
        cross += (1 + 1 / beta_bar**2) ** 2 * (
            2 * (1 + cpsi**2) / cpsi**3 - 3 / cpsi
        )
    cross += 4 / cpsi + 1
    cross *= _np.sin(psi)
    cross = _scyint.cumtrapz(cross, x=psi, initial=0.0)
    cross /= cross[-1]
    return psi, cross


def cross_section_draw_samples(psim, num_part):
    """Interpolates the cross section effect.

    psim     = minimum scat. angle that remains the electrons' orbit stable.
    num_part =                           number of particles for simulation.
    """
    psi, cross = get_cross_section_distribution(psim)
    crs = _np.random.Generator.rand(num_part)
    return _np.interp(crs, cross, psi)


def scatter_particles(part1, part2, de_min):
    """M.C. simulation of the Touschek scattering process.

    part1  =   1st partcile's coordinates.
    part2  =   2nd partcile's coordinates.
    de_min = mimimum energy deviation.
    """
    gamma = 3e9 / 0.510e6
    beta = _np.sqrt(1 - 1 / gamma / gamma)
    num_part = part1.shape[1]

    xl1, yl1, de1 = part1[1], part1[3], part1[4]
    xl2, yl2, de2 = part2[1], part2[3], part2[4]

    # calculating the changing base matrix for every particle
    pz1 = _np.sqrt((1 + de1) ** 2 - xl1 * xl1 - yl1 * yl1)
    pz2 = _np.sqrt((1 + de2) ** 2 - xl2 * xl2 - yl2 * yl2)

    # desired vectors to construct the transformation matrix
    p_1 = _np.vstack([xl1, yl1, pz1])
    p_2 = _np.vstack([xl2, yl2, pz2])

    # new coordinate system
    p_j = p_1 + p_2
    p_j /= _np.linalg.norm(p_j, axis=0)  # sum
    p_k = _np.cross(p_1.T, p_2.T).T
    p_k /= _np.linalg.norm(p_k, axis=0)  # cross product
    p_l = _np.cross(p_j.T, p_k.T).T

    jkl2xyz = _np.zeros([num_part, 3, 3])
    jkl2xyz[:, :, 0] = p_j.T
    jkl2xyz[:, :, 1] = p_k.T
    jkl2xyz[:, :, 2] = p_l.T

    theta = xl1 - xl2
    zeta = yl1 - yl2
    chi = _np.sqrt(zeta**2 + theta**2) / 2

    # draw the scattering angles from uniform distribution:
    phi = _np.random.Generator.rand(num_part) * 2 * _np.pi
    psi = _np.random.Generator.rand(num_part) * _np.pi / 2

    # draw the psi angle from the cross section probability density:
    # we need to define a maximum angle to normalize the cross section
    # distribution because it diverges when the full interval [0, pi/2]
    # is considered.
    # To estimate this angle we define a threshold for the minimum energy
    # deviation we care about (de_min) and consider the worst case scenario
    # in terms of chi that could create such scattering.
    # The worst case happens when chi is maximum, because in this way a small
    # scattering angle would create a larger energy deviation.
    # We considered here a chi twice as large as the maximum chi draw from
    # the particles distribution.
    # This method of doing things should be tested and thought about very
    # carefully, though.
    psim = _np.arccos(de_min / gamma / (chi.max() * 2))
    fact = psim * 2 / _np.pi
    print(psim * 2 / _np.pi)
    psi = cross_section_draw_samples(psim, num_part)

    # new momentum in j,k,l (eq. 16 of Piwinski paper)
    gammat = gamma / _np.sqrt(1 + beta * beta * gamma * gamma * chi * chi)
    dp_ = _np.sin(chi[None, :]) * _np.vstack(
        [
            gammat * _np.cos(psi),
            _np.sin(psi) * _np.cos(phi),
            _np.sin(psi) * _np.sin(phi),
        ]
    )
    p_prime1 = _np.zeros((3, chi.size))
    p_prime1[0] = _np.cos(chi)
    p_prime2 = p_prime1.copy()
    p_prime1 += dp_
    p_prime2 -= dp_

    # returning to momentum x,y,z
    pnew_1 = (jkl2xyz @ p_prime1.T[:, :, None]).squeeze().T
    pnew_2 = (jkl2xyz @ p_prime2.T[:, :, None]).squeeze().T

    delta1 = _np.linalg.norm(pnew_1, axis=0) - 1
    delta2 = _np.linalg.norm(pnew_2, axis=0) - 1

    part1_new = part1.copy()
    part1_new[1] = pnew_1[0]
    part1_new[3] = pnew_1[1]
    part1_new[4] = delta1

    part2_new = part2.copy()
    part2_new[1] = pnew_2[0]
    part2_new[3] = pnew_2[1]
    part2_new[4] = delta2

    return part1_new, part2_new, fact


def histgms(acc, l_spos, num_part, accep, de_min, cutaccep):
    """Calculates the touschek scattering densities.

    l_spos   =                           list of positions.
    num_part =            number of particles for M.C. sim.
    accep    =                  touschek energy acceptance.
    de_min   =                minimum energy deviation for.
    cutaccep = defines the cutoff on the energy acceptance.
    """
    envelopes = _pyaccel.optics.calc_beamenvelope(acc)
    spos = _pyaccel.lattice.find_spos(acc, indices="closed")
    scalc, daccpp, daccpn = get_scaccep(acc, accep)

    histsp1, histsp2, indices = [], [], []

    for iten in l_spos:
        idx_model = _np.argmin(_np.abs(spos - iten))
        idx = _np.argmin(_np.abs(scalc - iten))
        indices.append(idx_model)

        env = envelopes[idx_model]

        part1, part2 = create_particles(env, num_part)
        part1_new, part2_new, _ = scatter_particles(part1, part2, de_min)

        if cutaccep:  # if true the cutoff is the accp at the s
            acpp, acpn = daccpp[idx], daccpn[idx]
            check1 = acpp - part1_new[4]
            check2 = -(acpn - part2_new[4])

            ind1 = _np.intp(_np.where(check1 < 0)[0])
            ind2 = _np.intp(_np.where(check2 < 0)[0])

            histsp1.append(part1_new[4][ind1] * 1e2)
            histsp2.append(part2_new[4][ind2] * 1e2)

        else:  # ximenes cutoff
            ind1 = _np.intp(_np.where(part1_new[4] >= 0.01)[0])
            ind2 = _np.intp(_np.where(part2_new[4] <= -0.01)[0])

            histsp1.append(part1_new[4][ind1] * 1e2)
            histsp2.append(part2_new[4][ind2] * 1e2)

    indices = _np.array(indices)

    return histsp1, histsp2, indices
