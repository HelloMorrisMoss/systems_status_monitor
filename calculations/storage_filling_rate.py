import datetime
from dataclasses import dataclass
from statistics import stdev, mean
from typing import Union

import pandas as pd

from models.systems_settings import SystemModel

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


@dataclass
class StorageFillingRate:
    start_time: datetime.datetime
    end_time: datetime.datetime
    start_bytes: int
    end_bytes: int
    rate: float

    def __init__(self, start_time: datetime.datetime, end_time: datetime.datetime, start_bytes: int, end_bytes: int):
        self.start_time = start_time
        self.end_time = end_time
        self.start_bytes = start_bytes
        self.end_bytes = end_bytes

        self.change_in_bytes = start_bytes - end_bytes
        self.seconds = (end_time - start_time).total_seconds()

        self.rate = self.change_in_bytes / self.seconds  # bytes/second


def get_storage_filling_rates(system_model_instance: SystemModel) -> Union[dict, None]:
    """Get data about the storage filling rate. All the rates are in bytes per seconds.

    The data returned will be a dictionary with the following key-value pairs:
    overall_filling_rate_bytes_per_second: float, this rate reflects the average of all the records during periods that
     the free bytes were decreasing in the history for this system. Calculated by:
     Total bytes filled between records / total time between records.
    recent_storage_filling_rate: float, this rate reflects the average of all the records during the most recent period.
    filling_rate_cv: float, this is the coefficient of variation, the % of the average that the standard deviation is.
    rates_list: List[StorageFillingRate], list of the rates from the periods as a dataclass.

    If the system does not have any records, such as being newly added, then will return None.

    :param system_model_instance: SystemModel, SQLAlchemy model for the system whose history to analyze.
    :return: dict
    """
    stm = system_model_instance
    records = stm.storage_records
    if not records:
        return
    else:
        df = pd.DataFrame.from_records([storage.__dict__ for storage in stm.storage_records]).sort_values(
            'record_timestamp')
        df.reset_index(inplace=True)

        last_clearance = 0  # the last segment's index
        total_bytes = 0
        total_seconds = 0
        rates_list = []

        # loop over the rows where the free bytes went up (data removed from the drive), unless it's never been cleared then
        #  use all the rows
        clear_rows = list(df[df['bytes_cleared']].iterrows())
        clear_rows = clear_rows if len(clear_rows) else [(len(df), None)]  # use all the rows
        for clr_rn, clear_row in clear_rows:
            filling_rows = df.loc[last_clearance + 1:clr_rn - 1, :]  # the rows between as the drive filled
            if len(filling_rows) > 1:
                fill_rate_start_time = filling_rows['record_timestamp'].min()
                fill_rate_end_time = filling_rows['record_timestamp'].max()
                fill_rate_start_bytes = filling_rows['bytes_free'].min()
                fill_rate_end_bytes = filling_rows['bytes_free'].max()

                this_rate = StorageFillingRate(fill_rate_start_time,  # calculate the rate
                                               fill_rate_end_time, fill_rate_start_bytes, fill_rate_end_bytes)
                # record for overall rate calculations
                total_bytes += this_rate.change_in_bytes
                total_seconds += this_rate.seconds
                rates_list.append(this_rate)
            last_clearance = clr_rn
        overall_filling_rate_bytes_per_second = total_bytes / total_seconds  # for all segments
        just_rate_values = [rate.rate for rate in rates_list]
        return {'overall_filling_rate_bytes_per_second': overall_filling_rate_bytes_per_second,
                'recent_storage_filling_rate': rates_list[-1] if len(rates_list) > 0 else 0.0,
                'filling_rate_cv': stdev(just_rate_values) / mean(just_rate_values) if len(rates_list) > 1 else 0.0,
                'rates_list': rates_list,
                }
