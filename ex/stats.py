"""Example for statistics in logicsponge."""

from __future__ import annotations

import random
import time
from collections.abc import Iterator

import logicsponge.core as ls
from logicsponge.core import dashboard, stats


class GaussSource(ls.SourceTerm):
    """Stream Gaussian random values."""

    def __init__(self, key: str, mu: float = 0.5, sigma: float = 1.0) -> None:
        """Create a GaussSource.

        Args:
            key (str): the key in the DataItem that contains the random value.
            mu (float): mu of the distribution.
            sigma (float): sigma of the distribution.

        """
        super().__init__(name=key, key=key)
        self.key = key
        self.mu = mu
        self.sigma = sigma

    def generate(self) -> Iterator[ls.DataItem]:
        """Generate DataItems with Gaussian random values."""
        for _ in range(200):
            time.sleep(0.05)
            out = ls.DataItem({self.key: random.normalvariate(mu=self.mu, sigma=self.sigma)})
            yield out


def main() -> None:
    """Run two statistical pipelines and print results."""
    dashboard.run(background=True)

    circuit1 = (
        GaussSource("A")
        * dashboard.Plot("GaussSource (1)")
        * stats.OneSampleTTest("t-Test", dim=0, mean=0.0)
        * ls.DataItemFilter(lambda d: d["p-value"] is not None)
        * ls.AddIndex(key="index")
        * ls.Print()  # emit t-test results to console
        * dashboard.Plot("p-value (OneSampleTTest)", x="index", y=["p-value"])
    )

    circuit2 = (
        (GaussSource("A", mu=0.0) | GaussSource("B", mu=0.0) | GaussSource("C", mu=1.0))
        * ls.MergeToSingleStream()
        * ls.Flatten()
        * dashboard.Plot("GaussSource (2)")
        * stats.KruskalWallis("t-Test")
        * ls.DataItemFilter(lambda d: d["p-value"] is not None)
        * ls.AddIndex(key="index")
        * ls.Print()  # emit Kruskal-Wallis results to console
        * dashboard.Plot("p-value (KruskalWallis)", x="index", y=["p-value"])
    )

    circuit = circuit1 * ls.Stop() | circuit2 * ls.Stop()
    circuit.start()
    circuit.join()
    # Dash server is daemonized; script exits after pipelines finish.


if __name__ == "__main__":
    main()
