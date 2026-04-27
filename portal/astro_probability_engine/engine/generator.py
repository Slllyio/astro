
import datetime
from typing import List
from config import ANCHOR_LOCATIONS
from astrology.interface import AstrologyService
from engine.models import MatrixEntry
from utils.time_utils import generate_time_slices

class MatrixGenerator:
    def __init__(self, service: AstrologyService):
        self.service = service

    def generate_matrix(self, dob: datetime.date) -> List[MatrixEntry]:
        """
        Phase 1: The Matrix Generation.
        Iterates 96 time-slices x 20 locations.
        Returns flattened list of 1920 Matrix/Chart entries.
        """
        slices = generate_time_slices(dob)
        matrix = []

        for t_idx, time_slice in enumerate(slices):
            for l_idx, location in enumerate(ANCHOR_LOCATIONS):
                chart = self.service.calculate_chart(time_slice, location)
                entry = MatrixEntry(
                    time_slice_index=t_idx,
                    location_index=l_idx,
                    chart=chart
                )
                matrix.append(entry)
        
        return matrix
