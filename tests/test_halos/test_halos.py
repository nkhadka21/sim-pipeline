import numpy as np
from slsim.Halos.halos import (
    colossus_halo_mass_function,
    get_value_if_quantity,
    colossus_halo_mass_sampler,
    number_density_at_redshift,
    growth_factor_at_redshift,
    halo_mass_at_z,
    set_defaults,
    dndz_to_redshifts,
    dv_dz_to_dn_dz,
    dndz_to_N,
    v_per_redshift,
    redshift_halos_array_from_comoving_density,
    redshift_mass_sheet_correction_array_from_comoving_density,
    number_for_certain_mass,
)

from astropy.cosmology import default_cosmology
from astropy.units.quantity import Quantity
from astropy import units
import pytest

cosmo = default_cosmology.get()


def test_colossus_halo_mass_function():
    m_200 = np.array([1e12, 1e13, 1e14])
    z = 0.5
    result = colossus_halo_mass_function(m_200, cosmo, z)
    assert result.shape == m_200.shape

def test_returns_value_if_quantity():
    quantity = Quantity(5, unit='Msun')

    result = get_value_if_quantity(quantity)

    assert result == 5

def test_returns_array_of_size_when_all_parameters_valid():
        # Arrange
        m_min = 1e12
        m_max = 1e15
        resolution = 100
        z = 0.5
        size = 10

        result = colossus_halo_mass_sampler(m_min, m_max, resolution, z, cosmo, size)

        assert len(result) == size
        assert  np.all(result > m_min)
        assert  np.all(result < m_max)

def test_halo_mass_at_z():
    mass = halo_mass_at_z(z=0.5, resolution=100)
    assert mass[0] > 10 ** 10
    assert mass[0] < 10 ** 16
    assert len(mass) == 1

    z_array = np.linspace(0, 1, 100)
    mass_list = halo_mass_at_z(z=z_array, m_min=1e12, m_max=1e16, resolution=100)
    flat_mass_array = np.concatenate(mass_list)
    assert np.all(flat_mass_array > 1e12)
    assert np.all(flat_mass_array < 1e16)
    assert len(mass_list) == 100

    z_list = [0, 1, 2]
    mass_list2 = halo_mass_at_z(z=z_list, resolution=100)
    assert len(mass_list2) == 3


def test_number_density_at_redshift():
    z = 0.5
    CDF = number_density_at_redshift(z=z)
    assert len(CDF) == 1
    assert CDF[0] > 0

    CDF = number_density_at_redshift(z=np.array([np.nan]))
    assert len(CDF) == 1

    z2 = np.array([0, 10, 20])
    CDF2 = number_density_at_redshift(z=z2)
    assert len(CDF2) == 3
    assert CDF2[0] > CDF2[2]


def test_growth_factor_at_redshift():
    growth_factor = growth_factor_at_redshift(z=0, cosmology=cosmo)
    assert isinstance(growth_factor, list)
    assert np.isfinite(growth_factor)
    assert growth_factor == [1.0]

    z_array = np.linspace(0, 1, 100)
    growth_factor = growth_factor_at_redshift(z=z_array, cosmology=cosmo)

    assert len(growth_factor) == 100
    assert growth_factor[0] == 1.0

    z_list = [0, 1, 2]
    growth_factor2 = growth_factor_at_redshift(z=z_list, cosmology=cosmo)
    assert len(growth_factor2) == 3
    assert growth_factor2[0] == 1.0
    assert growth_factor2[1] < growth_factor2[0]


def test_number_for_certain_mass():
    m = np.geomspace(1e12, 1e16, 200)
    massf = np.array([1] * 200)
    cdf = number_for_certain_mass(massf, m)
    massf2 = 2 * m
    cdf2 = number_for_certain_mass(massf2, m)
    s = (1e16 - 1e12) * (1e16 + 1e12)
    assert cdf == pytest.approx(1e16 - 1e12, rel=0.001)
    assert cdf2 == pytest.approx(s, rel=0.001)


def test_defaults_set():
    (
        m_min,
        m_max,
        resolution,
        cosmology,
    ) = set_defaults()
    assert m_min == 1e12
    assert m_max == 1e14
    assert resolution == 100
    from astropy.cosmology import default_cosmology
    assert cosmology == default_cosmology.get()


def test_v_per_redshift():
    sky_area = 41252.96 * units.deg ** 2  # totoal sky
    z = np.linspace(0, 1, 100)
    v = v_per_redshift(redshift_list=z, cosmology=cosmo, sky_area=sky_area)
    totalv = np.trapz(v, z)
    v2 = cosmo.comoving_volume(1).to_value(
        "Mpc3"
    )
    sky_area_2 = 0.0 * units.deg ** 2
    z_2 = 1.0
    v_0 = v_per_redshift(redshift_list=z_2, cosmology=cosmo, sky_area=sky_area_2)
    assert len(v) == 100
    assert totalv == pytest.approx(v2, rel=0.001)
    assert v_0 == 0.0


def test_dndz_to_N():
    z = np.linspace(0, 1, 100)
    dndz = np.ones(100)
    N = dndz_to_N(dndz, z)

    dndz_0 = np.zeros(100)
    N_0 = dndz_to_N(dndz_0, z)

    assert isinstance(N, int)
    assert N == pytest.approx(1, rel=10.0)
    assert N_0 == 0


def test_dndz_to_redshifts():
    z = np.linspace(0, 2, 100)
    dndz = np.concatenate([np.array([0] * 50), np.linspace(0, 1, 50)])
    redshifts = dndz_to_redshifts(18, dndz, z)

    assert len(redshifts) == 18
    assert np.all(redshifts > 0.999)
    assert np.all(redshifts < 2.001)


def test_dv_dz_to_dn_dz():
    z = np.linspace(0, 1, 100)
    dV_dz = np.concatenate([np.array([0] * 50), np.linspace(0, 1, 50)])
    dn_dz = dv_dz_to_dn_dz(dV_dz, z)
    assert len(dn_dz) == 100
    assert dn_dz[0] == dn_dz[10] == 0
    assert dn_dz[60] > 0


def test_redshift_halos_array_from_comoving_density():
    redshift_list = [0.5, 1.0, 1.5]
    sky_area = 1 * units.deg ** 2
    cosmology = cosmo
    m_min = 1e12
    m_max = 1e15
    resolution = 100
    result = redshift_halos_array_from_comoving_density(redshift_list,
                                                        sky_area,
                                                        cosmology,
                                                        m_min,
                                                        m_max,
                                                        resolution)
    assert isinstance(result, np.ndarray)
    assert len(result) > 1

def test_redshift_mass_sheet_correction_array():
    redshift_list = [0.1, 0.2]
    expected_result = np.array([0.025, 0.075, 0.125, 0.175])
    assert np.allclose(
        redshift_mass_sheet_correction_array_from_comoving_density(
            redshift_list),
        expected_result)
