from __future__ import annotations
from typing import TYPE_CHECKING


def f() -> Vector[int, int]:
	raise NotImplementedError()

def g() -> Vector[int, int, int]:
	raise NotImplementedError()

if TYPE_CHECKING:
	# Hypothetical packages that the plugin targets
	from lib import Vector  # fullname: "lib.Vector"
	import mylib            # functions/methods under: "mylib.*"

	x2: Vector[int, int] = f()
	y2: Vector[int, int] = f()
	z3: Vector[int, int, int] = g()
	
	sum2 = x2 + y2
	sum3 = x2 + z3