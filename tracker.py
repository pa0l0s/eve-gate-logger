from config import Ship

class ShipTracker:
    def __init__(self) -> None:
        self._visible: set[Ship] = set()

    def update(self, current: set[Ship]) -> set[Ship]:
        """Return ships that are new this scan. Update internal state."""
        new_ships = current - self._visible
        self._visible = current
        return new_ships
