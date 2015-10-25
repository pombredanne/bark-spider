from io import BytesIO, StringIO
import json

import pandas
from pyramid.response import Response
from pyramid.view import view_config

from brooks.brooks_law import step
import brooks.communication
from brooks.simulation import simulate
from brooks.state import State
from plotter.plot_timeseries import plot_timeseries


class Schedule:
    def __init__(self, elapsed, added):
        self._elapsed = elapsed
        self._added = added

    def initial(self):
        """Configure the initial model state."""
        return State(
            step_duration_days=1,
            num_function_points_requirements=500,
            num_function_points_developed=0,
            num_new_personnel=20,
            num_experienced_personnel=0,
            personnel_allocation_rate=0,
            personnel_assimilation_rate=0,
            assimilation_delay_days=20,
            nominal_productivity=0.1,
            new_productivity_weight=0.8,
            experienced_productivity_weight=1.2,
            training_overhead_proportion=0.25,
            communication_overhead_function=brooks.communication.gompertz_overhead_proportion,
            software_development_rate=None,
            cumulative_person_days=0,
        )

    def intervene(self, step_number, elapsed_time, state):
        """Intervene in the current step before the main simulation step is
        executed.
        """
        if elapsed_time == self._elapsed:
            state.num_new_personnel += self._added
        return state

    def is_complete(self, step_number, elapsed_time_seconds, state):
        """Determine whether the simulation should end."""
        return state.num_function_points_developed >= state.num_function_points_requirements

    def complete(self, step_number, elapsed_time_seconds, state):
        """Finalise the simulation state for the last recorded step."""
        state.software_development_rate = 0
        return state


@view_config(route_name='home', renderer='templates/main_plot.pt')
def main_plot(request):
    return {'project': 'bark_spider'}


def _run_simulation(params):
    attributes = [params['name']]
    elapsed = params['elapsed']
    added = params['added']

    output_stream = StringIO()
    simulate(Schedule(elapsed, added), step, output_stream, attributes)
    output_stream.seek(0)

    frame = pandas.read_table(output_stream)
    frame['software_development_rate'][0] = 0  # This cleans up the null initial rate
    return frame


# TODO: Where should this really live?
class DataFrameJSONEncoder(json.JSONEncoder):
    @staticmethod
    def string_keys(d):
        "Covert all keys to strings in a dict."
        return {str(k): str(v) for k, v in d.items()}

    def default(self, obj):
        if isinstance(obj, pandas.DataFrame):
            # The DataFrame.to_dict() returns some dicts with integer
            # keys, and the json encoder requires these keys to be
            # strings. Hence the conversion.
            return {
                k: self.string_keys(v)
                for k, v in obj.to_dict().items()
            }
        return json.JSONEncoder.default(self, obj)


@view_config(route_name='simulate',
             request_method='POST')
def simulate_route(request):
    params = request.json_body['simulation_parameter_sets']
    results = [_run_simulation(p) for p in params]
    print(json.dumps(results, cls=DataFrameJSONEncoder))
    return Response(
        body=json.dumps(results, cls=DataFrameJSONEncoder),
        content_type='application/json')
