import logicsponge.core as ls
from logicsponge.core import source

circuit = (
    source.GoogleDriveSource(
        "https://drive.google.com/file/d/19nDn0mVMxC5U8p3p01OxL-PfNMoMhdI_/view",
        poll_interval_sec=10,
    )
    * source.StringDiff()
    * ls.Print()
)
circuit.start()
