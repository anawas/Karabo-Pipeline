import time

from karabo.simulation.interferometer import InterferometerSimulation
from karabo.simulation.observation import Observation
from karabo.simulation.sky_model import SkyModel
from karabo.simulation.telescope import Telescope
from karabo.util.dask import get_number_of_nodes
from karabo.util.file_handle import FileHandle


def main(n_channels: int) -> None:
    start = time.time()

    print("Setting up sky model...")
    sky = SkyModel.get_GLEAM_Sky([76])
    phase_center = [250, -80]

    print("Filtering sky model...")
    sky = sky.filter_by_radius_euclidean_flat_approximation(
        0, 45, phase_center[0], phase_center[1]
    )

    print("Size of sky sources: ", sky.sources.nbytes / 1e6, "MB")

    print("Setting up default wcs...")
    sky.setup_default_wcs(phase_center=phase_center)

    print("Setting up telescope...")
    askap_tel = Telescope.get_ASKAP_Telescope()

    print("Setting up observation...")
    observation_settings = Observation(
        start_frequency_hz=100e6,
        phase_centre_ra_deg=phase_center[0],
        phase_centre_dec_deg=phase_center[1],
        number_of_channels=n_channels,
        number_of_time_steps=24,
    )

    # Create dir for intermediate files
    fh = FileHandle(create_additional_folder_in_dir=True)
    dir_intermediate_files = fh.dir

    print("Saving intermediate files to dir:", dir_intermediate_files)

    print("Running simulation...")
    interferometer_sim = InterferometerSimulation(
        folder_for_multiple_observation=dir_intermediate_files,
        channel_bandwidth_hz=1e6,
        use_gpus=True,
        use_dask=True,
        split_observation_by_channels=True,
        n_split_channels="each",
    )

    visibility_askap = interferometer_sim.run_simulation(
        askap_tel,
        sky,
        observation_settings,
    )

    assert len(visibility_askap) == n_channels
    time_taken = round((time.time() - start) / 60, 2)
    print("Time taken: (minutes)", time_taken)

    with open(
        f"output_{str(get_number_of_nodes())}_nodes_{n_channels}_channels.txt",
        "a",
    ) as file:
        file.write(
            f"Number of channels: {n_channels}. " f"Time taken: {time_taken} min.\n"
        )
        file.flush()

    # Clean up
    fh.remove_dir(dir_intermediate_files)


if __name__ == "__main__":
    main(n_channels=10000)
