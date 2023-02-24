"""Double-exponential fit to stress-relaxation data

This example reproduces the first entry in figure 5d (cell1) of
:cite:`Battistella_2022`.

Please note that in the original manuscript, not all curves were
used in the final figure. Some curves were excluded based on
curve quality. The data were kindly provided by Alice Battistella.
"""

import pathlib
import shutil
import tempfile

import afmformats

from lmfit.models import ConstantModel, ExponentialModel
import matplotlib.pylab as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np
import pandas
import seaborn as sns
sns.set_theme(style="whitegrid", palette="muted")


# extract the data to a temporary directory
data_path = pathlib.Path(__file__).parent / "data"
wd_path = pathlib.Path(tempfile.mkdtemp())
shutil.unpack_archive(data_path / "10.1002_btm2.10294_fig5d-cell1.zip",
                      wd_path)

# scale conversion constants
xsc = 1
ysc = 1e9
xl = "time [s]"
yl = "force [nN]"

# data extraction
data = []
for path in wd_path.glob("*.jpk-force"):
    data += afmformats.load_data(path)

# this is where the data for the swarm plot is stored
rdat = {
    "tau": [],
    "component": [],
    "cell": [],
}

data_fits = []

for di in data:
    # use intermediate `intr` segment data
    x = di.intr["time"] * xsc
    y = di.intr["force"] * ysc

    # fitting with double-exponential
    const = ConstantModel()
    exp_1 = ExponentialModel(prefix='exp1_')
    exp_2 = ExponentialModel(prefix='exp2_')

    pars = exp_1.guess(y, x=x)
    pars.update(exp_2.guess(y, x=x))
    pars["exp1_decay"].set(value=1, min=0.1)
    pars["exp2_decay"].set(value=8, min=2)
    pars.update(const.guess(y, x=x))
    pars["c"].set(value=np.min(y))

    mod = const + exp_1 + exp_2

    init = mod.eval(pars, x=x)
    out = mod.fit(y, pars, x=x)
    data_fits.append([x, out.best_fit])

    rdat["tau"].append(out.params["exp1_decay"].value)
    rdat["component"].append("tau1")
    rdat["cell"].append("cell1, t=0")

    rdat["tau"].append(out.params["exp2_decay"].value)
    rdat["component"].append("tau2")
    rdat["cell"].append("cell1, t=0")


fig = plt.figure(figsize=(8, 4))

# plot all stress-relaxation curves
ax1 = plt.subplot(121, title="double-exponential fits")
for ii in range(len(data)):
    di = data[ii]
    ax1.plot(di["time"]*xsc, di["force"]*ysc, color="k", lw=3)
    xf, yf = data_fits[ii]
    ax1.plot(xf, yf, color="r", lw=1)
ax1.set_xlabel(xl)
ax1.set_ylabel(yl)

df = pandas.DataFrame(data=rdat)
# Draw a categorical scatterplot to show each observation
ax2 = plt.subplot(122, title="comparison of decay times")
ax2 = sns.swarmplot(data=df, x="cell", y="tau", hue="component")
ax2.set_yscale('log', base=2)
ax2.yaxis.set_major_formatter(ScalarFormatter())
ax2.set_yticks([0.5, 1, 2, 4, 8, 16, 32])
ax2.set(xlabel="", ylabel="tau [s]")

plt.tight_layout()

plt.show()
