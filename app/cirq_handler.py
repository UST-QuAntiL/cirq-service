# ******************************************************************************
#  Copyright (c) 2021 University of Stuttgart
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************
from time import sleep

import cirq
from cirq import Simulator
from cirq import Result
from cirq.contrib.routing import gridqubits_to_graph_device
import cirq_google


def get_qpu_spec(qpu):
    """Get backend."""
    if qpu.lower() == "sycamore":
        return cirq_google.Sycamore
    elif qpu.lower() == "sycamore23":
        return cirq_google.Sycamore23
    else:
        raise NotImplementedError("qpu not supported")


def get_backend(qpu):
    if qpu.lower() == "local-simulator":
        return Simulator()
    elif qpu.lower() == "sycamore" or qpu.lower() == "sycamore23":
        return Simulator()
    else:
        raise NotImplementedError("qpu not supported")


def delete_token():
    """Delete account."""
    pass


def transpile_for_qpu(qpu, circuit):
    # TODO: Mapping to device specific QBITS
    if qpu.lower() == "local-simulator":
        return circuit
    else:
        device = get_qpu_spec(qpu)
        return cirq.optimize_for_target_gateset(circuit, gateset=device.metadata.compilation_target_gatesets[0])


def execute_job(transpiled_circuit, shots, backend):
    """Execute and Simulate Job on simulator and return results"""

    result: Result = backend.run(transpiled_circuit, repetitions=shots)

    def fold(l):
        return ''.join(str(e[0]) for e in l)

    stats = result.measurements
    histogram = result.multi_measurement_histogram(keys=stats.keys(), fold_func=fold)
    print(histogram)
    return histogram