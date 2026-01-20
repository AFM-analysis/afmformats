"""Test NT-MDT text export format"""
import pathlib
import numpy as np
import matplotlib.pyplot as plt

import afmformats

data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_chairo_txt_open_check_data():
    data = afmformats.load_data(data_path /
                                "fmt-chiaro-txt_AEBP1_Indentation_002.txt")[0]
    assert data.metadata["imaging mode"] == "force-distance"
    assert data["force"][2000] == 9.399999999999999e-11


def test_chairo_txt_detect():
    path = data_path / "fmt-chiaro-txt_AEBP1_Indentation_002.txt"
    recipe = afmformats.formats.get_recipe(path)
    assert recipe.descr == "exported by Optics11 Chiaro Indenter"
    assert recipe.maker == "Optics11 Life"


def test_chairo_txt_data_columns():
    data = afmformats.load_data(data_path /
                                "fmt-chiaro-txt_AEBP1_Indentation_002.txt")[0]
    assert "force" in data
    assert "height (piezo)" in data
    assert "height (measured)" in data
    assert "time" in data
    assert "segment" in data
    assert "tip position" in data  # already calculated when loaded


def test_chairo_txt_metadata():
    data = afmformats.load_data(data_path /
                                "fmt-chiaro-txt_AEBP1_Indentation_002.txt")[0]
    metadata = data.metadata
    avail_keys = ["date", "duration", "spring constant", "time",
                  "speed approach", "speed retract", "segment count"]
    for key in avail_keys:
        assert key in metadata


def test_chiaro_txt_segments():
    data = afmformats.load_data(data_path /
                                "fmt-chiaro-txt_AEBP1_Indentation_002.txt")[0]

    assert data["force"].size == 13827
    # maximum force is at end of 1st segment
    assert np.sum(data["segment"] == 0) == np.argmax(data["force"]) + 1


def test_plot_recreate_chiaro_load_indentation_curve():
    data = afmformats.load_data(data_path /
                                "fmt-chiaro-txt_AEBP1_Indentation_002.txt")[0]

    # maximum force is at end of 1st segment
    assert np.sum(data["segment"] == 0) == np.argmax(data["force"]) + 1

    piezo_lab = "height (piezo)"
    force_lab = "force"
    unit_sc_x = 1e9
    unit_sc_y = 1e6
    idx = 12663
    piezo_loading = data[piezo_lab][:idx] * unit_sc_x
    piezo_unloading = data[piezo_lab][idx:] * unit_sc_x
    force_loading = data[force_lab][:idx] * unit_sc_y
    force_unloading = data[force_lab][idx:] * unit_sc_y

    fig, ax = plt.subplots()
    ax.scatter(x=piezo_loading, y=force_loading, s=2,
               alpha=0.5, label="Loading", color="blue")
    ax.scatter(x=piezo_unloading, y=force_unloading, s=2,
               alpha=0.5, label="Unloading", color="green")
    # ax.xaxis.set_inverted(True)
    ax.set_xlabel("Indentation (nm)")
    ax.set_ylabel("Load (uN)")
    ax.set_title("Chiaro Text data Load-Indentation curve")
    ax.legend(fontsize="large", markerscale=2, reverse=False)
    # plt.savefig(f"chiaro_recreate_chiaro_load_indentation_curve.png")


def test_plot_recreate_chiaro_time_data():
    data = afmformats.load_data(data_path /
                                "fmt-chiaro-txt_AEBP1_Indentation_002.txt")[0]

    x_lab = "time"
    height_m_lab = "height (measured)"
    tip_position = "tip position"
    piezo_lab = "height (piezo)"
    canilever_data = data[piezo_lab] - data[tip_position]
    unit_sc = 1e6

    fig, ax = plt.subplots()
    ax.scatter(x=data[x_lab], y=data[piezo_lab] * unit_sc, s=2, alpha=0.5,
               label=f"{piezo_lab}=Piezo", color="blue")
    ax.scatter(x=data[x_lab], y=data[height_m_lab] * unit_sc, s=2, alpha=0.5,
               label=f"{height_m_lab}=Indentation", color="red")
    ax.scatter(x=data[x_lab], y=canilever_data * unit_sc, s=2, alpha=0.5,
               label="piezo-tip_position=Cantilever", color="green")
    ax.set_xlabel(x_lab)
    ax.set_ylabel("Displacement (um)")
    ax.set_title("Chiaro Text data")
    ax.yaxis.set_inverted(False)
    ax.legend(fontsize="large", markerscale=2, reverse=False)
    # plt.savefig(f"chiaro_recreate_chiaro_time_data.png")


if __name__ == "__main__":
    # Run all tests
    _loc = locals()
    for _key in list(_loc.keys()):
        if _key.startswith("test_") and hasattr(_loc[_key], "__call__"):
            _loc[_key]()
