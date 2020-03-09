# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# MDAnalysis --- https://www.mdanalysis.org
# Copyright (c) 2006-2017 The MDAnalysis Development Team and contributors
# (see the file AUTHORS for the full list of names)
#
# Released under the GNU Public Licence, v2 or any higher version
#
# Please cite your use of MDAnalysis in published work:
#
# R. J. Gowers, M. Linke, J. Barnoud, T. J. E. Reddy, M. N. Melo, S. L. Seyler,
# D. L. Dotson, J. Domanski, S. Buchoux, I. M. Kenney, and O. Beckstein.
# MDAnalysis: A Python package for the rapid analysis of molecular dynamics
# simulations. In S. Benthall and S. Rostrup editors, Proceedings of the 15th
# Python in Science Conference, pages 102-109, Austin, TX, 2016. SciPy.
# doi: 10.25080/majora-629e541a-00e
#
# N. Michaud-Agrawal, E. J. Denning, T. B. Woolf, and O. Beckstein.
# MDAnalysis: A Toolkit for the Analysis of Molecular Dynamics Simulations.
# J. Comput. Chem. 32 (2011), 2319--2327, doi:10.1002/jcc.21787
#
from __future__ import absolute_import
import MDAnalysis
import pytest

from numpy.testing import assert_equal, assert_almost_equal
import numpy as np
from six.moves import StringIO
import networkx as NX

from MDAnalysis.analysis.leaflet import LeafletFinder, optimize_cutoff
from MDAnalysisTests.datafiles import Martini_membrane_gro

from MDAnalysis.lib.util import NamedStream

LIPID_HEAD_STRING = "name PO4"


@pytest.fixture()
def universe():
    return MDAnalysis.Universe(Martini_membrane_gro)


@pytest.fixture()
def lipid_heads(universe):
    return universe.select_atoms(LIPID_HEAD_STRING)

def lines2one(lines):
    """Join lines and squash all whitespace"""
    return " ".join(" ".join(lines).split())



def namedfile(filename):
    return NamedStream(StringIO(), filename)

def test_leaflet_finder(universe, lipid_heads):
    lfls = LeafletFinder(universe, lipid_heads, pbc=True)
    top_heads, bottom_heads = lfls.groups()
    # Make top be... on top.
    if top_heads.center_of_geometry()[2] < bottom_heads.center_of_geometry()[2]:
        top_heads,bottom_heads = (bottom_heads,top_heads)
    assert_equal(top_heads.indices, np.arange(1,2150,12),
                 err_msg="Found wrong leaflet lipids")
    assert_equal(bottom_heads.indices, np.arange(2521,4670,12),
                 err_msg="Found wrong leaflet lipids")


def test_string_vs_atomgroup_proper(universe, lipid_heads):
    lfls_ag = LeafletFinder(universe, lipid_heads, pbc=True)
    lfls_string = LeafletFinder(universe, LIPID_HEAD_STRING, pbc=True)
    groups_ag = lfls_ag.groups()
    groups_string = lfls_string.groups()
    assert_equal(groups_string[0].indices, groups_ag[0].indices)
    assert_equal(groups_string[1].indices, groups_ag[1].indices)


def test_optimize_cutoff(universe, lipid_heads):
    cutoff, N = optimize_cutoff(universe, lipid_heads, pbc=True)
    assert N == 2
    assert_almost_equal(cutoff, 10.5, decimal=4)

def test_pbc_on_off(universe, lipid_heads):
    lfls_pbc_on = LeafletFinder(universe, lipid_heads, pbc=True)
    lfls_pbc_off = LeafletFinder(universe, lipid_heads, pbc=False)
    assert lfls_pbc_on.graph.size() > lfls_pbc_off.graph.size()

def test_pbc_on_off_difference(universe, lipid_heads):
    lfls_pbc_on = LeafletFinder(universe, lipid_heads, cutoff=7, pbc=True)
    lfls_pbc_off = LeafletFinder(universe, lipid_heads, cutoff=7, pbc=False)
    pbc_on_graph = lfls_pbc_on.graph
    pbc_off_graph = lfls_pbc_off.graph
    diff_graph = NX.difference(pbc_on_graph,pbc_off_graph)
    assert_equal(set(diff_graph.edges), {(69, 153), (73, 79), (206, 317), (313, 319)})

def test_cutoff_update(universe, lipid_heads):
    lfls_ag = LeafletFinder(universe, lipid_heads, cutoff = 15.0, pbc=True)
    lfls_ag.update(cutoff=1.0)
    assert_almost_equal(lfls_ag.cutoff, 1.0, decimal=4)

def test_write_selection(universe, lipid_heads, tmpdir):
    lfls_ag = LeafletFinder(universe, lipid_heads, cutoff = 15.0, pbc=True)
    with tmpdir.as_cwd():
         filename = lfls_ag.write_selection('leaflet.vmd')
         assert len(open('leaflet.vmd').readlines()) == 50, "Leaflet write selection not working"
