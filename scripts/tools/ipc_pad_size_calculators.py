from __future__ import division
import math
import re

from KicadModTree.Size import TolerancedSize


def roundToBase(value, base):
    return round(value/base) * base


def ipc_body_edge_inside(ipc_data, ipc_round_base, manf_tol, body_size, lead_width,
                         lead_len=None, lead_inside=None, heel_reduction=0):
    pull_back = TolerancedSize(nominal=0)

    return ipc_body_edge_inside_pull_back(
        ipc_data, ipc_round_base, manf_tol, body_size, lead_width,
        lead_len=lead_len, lead_inside=lead_inside, pull_back=pull_back,
        heel_reduction=heel_reduction
    )


def ipc_body_edge_inside_pull_back(ipc_data, ipc_round_base, manf_tol, body_size, lead_width,
                                   lead_len=None, lead_inside=None, body_to_inside_lead_edge=None, pull_back=None, lead_outside=None, heel_reduction=0):
    # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
    # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
    # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

    # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal lenght (T)
    # Then one can calculate
    # Stol(RMS) = √(Ltol^2 + 2*^2)
    # Smin = Lmin - 2*Tmax
    # Smax(RMS) = Smin + Stol(RMS)

    F = manf_tol.get('manufacturing_tolerance', 0.1)
    P = manf_tol.get('placement_tolerance', 0.05)

    if lead_outside is None:
        if pull_back is None:
            raise KeyError("Either lead outside or pull back distance must be given")
        lead_outside = body_size - pull_back * 2

    if lead_inside is not None:
        S = lead_inside
    elif lead_len is not None:
        S = lead_outside - lead_len * 2
    elif body_to_inside_lead_edge is not None:
        S = body_size - body_to_inside_lead_edge * 2
    else:
        raise KeyError("either lead inside distance, lead to body edge or lead lenght must be given")

    Gmin = S.maximum_RMS - 2 * ipc_data['heel'] + 2 * heel_reduction - math.sqrt(S.ipc_tol_RMS**2 + F**2 + P**2)

    Zmax = lead_outside.minimum_RMS + 2 * ipc_data['toe'] + math.sqrt(lead_outside.ipc_tol_RMS**2 + F**2 + P**2)
    Xmax = lead_width.minimum_RMS + 2 * ipc_data['side'] + math.sqrt(lead_width.ipc_tol_RMS**2 + F**2 + P**2)

    Zmax = roundToBase(Zmax, ipc_round_base['toe'])
    Gmin = roundToBase(Gmin, ipc_round_base['heel'])
    Xmax = roundToBase(Xmax, ipc_round_base['side'])

    return Gmin, Zmax, Xmax


def ipc_gull_wing(ipc_data, ipc_round_base, manf_tol, lead_width, lead_outside,
                  lead_len=None, lead_inside=None, heel_reduction=0):
    # Zmax = Lmin + 2JT + √(CL^2 + F^2 + P^2)
    # Gmin = Smax − 2JH − √(CS^2 + F^2 + P^2)
    # Xmax = Wmin + 2JS + √(CW^2 + F^2 + P^2)

    # Some manufacturers do not list the terminal spacing (S) in their datasheet but list the terminal lenght (T)
    # Then one can calculate
    # Stol(RMS) = √(Ltol^2 + 2*^2)
    # Smin = Lmin - 2*Tmax
    # Smax(RMS) = Smin + Stol(RMS)

    F = manf_tol.get('manufacturing_tolerance', 0.1)
    P = manf_tol.get('placement_tolerance', 0.05)

    if lead_inside is not None:
        S = lead_inside
    elif lead_len is not None:
        S = lead_outside - lead_len * 2
    else:
        raise KeyError("either lead inside distance or lead lenght must be given")

    Gmin = S.maximum_RMS - 2 * ipc_data['heel'] + 2 * heel_reduction - math.sqrt(S.ipc_tol_RMS**2 + F**2 + P**2)

    Zmax = lead_outside.minimum_RMS + 2 * ipc_data['toe'] + math.sqrt(lead_outside.ipc_tol_RMS**2 + F**2 + P**2)
    Xmax = lead_width.minimum_RMS + 2 * ipc_data['side'] + math.sqrt(lead_width.ipc_tol_RMS**2 + F**2 + P**2)

    Zmax = roundToBase(Zmax, ipc_round_base['toe'])
    Gmin = roundToBase(Gmin, ipc_round_base['heel'])
    Xmax = roundToBase(Xmax, ipc_round_base['side'])

    return Gmin, Zmax, Xmax


def ipc_pad_center_plus_size(ipc_data, ipc_round_base, manf_tol,
                             center_position, lead_length, lead_width):
    F = manf_tol.get('manufacturing_tolerance', 0.1)
    P = manf_tol.get('placement_tolerance', 0.05)

    S = center_position * 2 - lead_length
    lead_outside = center_position * 2 + lead_length

    Gmin = S.maximum_RMS - 2 * ipc_data['heel'] - math.sqrt(S.ipc_tol_RMS**2 + F**2 + P**2)
    Zmax = lead_outside.minimum_RMS + 2 * ipc_data['toe'] + math.sqrt(lead_outside.ipc_tol_RMS**2 + F**2 + P**2)

    Xmax = lead_width.minimum_RMS + 2 * ipc_data['side'] + math.sqrt(lead_width.ipc_tol_RMS**2 + F**2 + P**2)

    Zmax = roundToBase(Zmax, ipc_round_base['toe'])
    Gmin = roundToBase(Gmin, ipc_round_base['heel'])
    Xmax = roundToBase(Xmax, ipc_round_base['side'])

    return Gmin, Zmax, Xmax
